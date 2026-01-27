"""Info command - display project and environment information."""

import sys
import platform
from pathlib import Path

import click
from rich.table import Table
from rich.panel import Panel
from rich.box import ROUNDED
from rich.text import Text

from ..core.config import load_config
from ..core.page import get_project_root
from ..utils import console, header


@click.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def info(as_json):
    """Display project and environment information."""
    project_root = get_project_root()

    if as_json:
        _output_json(project_root)
    else:
        _output_rich(project_root)


def _output_rich(project_root):
    """Output info using Rich formatting."""
    from .. import __version__

    header("Project info")

    env_table = Table(box=ROUNDED, show_header=False, padding=(0, 2), expand=False)
    env_table.add_column("Key", style="dim")
    env_table.add_column("Value", style="cyan")

    env_table.add_row("Nitro CLI", f"v{__version__}")
    env_table.add_row(
        "Python",
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    )
    env_table.add_row("Platform", platform.system())
    env_table.add_row("Architecture", platform.machine())

    console.print(
        Panel(
            env_table,
            title=Text.from_markup("[bold]Environment[/]"),
            border_style="blue",
        )
    )

    if project_root:
        config_path = project_root / "nitro.config.py"
        if config_path.exists():
            config = load_config(config_path)

            proj_table = Table(
                box=ROUNDED, show_header=False, padding=(0, 2), expand=False
            )
            proj_table.add_column("Key", style="dim")
            proj_table.add_column("Value", style="green")

            proj_table.add_row("Name", config.site_name)
            proj_table.add_row("Root", str(project_root))
            proj_table.add_row("Source", str(config.source_dir))
            proj_table.add_row("Build", str(config.build_dir))
            proj_table.add_row("Base URL", config.base_url)

            if config.plugins:
                proj_table.add_row("Plugins", ", ".join(config.plugins))

            console.print(
                Panel(
                    proj_table,
                    title=Text.from_markup("[bold]Project[/]"),
                    border_style="green",
                )
            )

            _show_directory_stats(project_root, config)
        else:
            console.print(
                Panel(
                    f"[dim]Project root:[/] {project_root}\n[yellow]No nitro.config.py found[/]",
                    title=Text.from_markup("[bold]Project[/]"),
                    border_style="yellow",
                )
            )
    else:
        console.print(
            Panel(
                "[yellow]Not inside a Nitro project[/]\n[dim]Run 'nitro new <name>' to create one[/]",
                title=Text.from_markup("[bold]Project[/]"),
                border_style="yellow",
            )
        )

    _show_dependencies()


def _show_directory_stats(project_root: Path, config):
    """Show statistics about project directories."""
    stats_table = Table(box=ROUNDED, show_header=True, padding=(0, 2), expand=False)
    stats_table.add_column("Directory", style="dim")
    stats_table.add_column("Files", justify="right", style="cyan")
    stats_table.add_column("Size", justify="right", style="green")

    source_dir = project_root / config.source_dir
    if source_dir.exists():
        pages_dir = source_dir / "pages"
        components_dir = source_dir / "components"

        if pages_dir.exists():
            page_count = len(list(pages_dir.rglob("*.py"))) - len(
                list(pages_dir.rglob("__init__.py"))
            )
            stats_table.add_row("Pages", str(page_count), _format_dir_size(pages_dir))

        if components_dir.exists():
            comp_count = len(list(components_dir.rglob("*.py"))) - len(
                list(components_dir.rglob("__init__.py"))
            )
            stats_table.add_row(
                "Components", str(comp_count), _format_dir_size(components_dir)
            )

    build_dir = project_root / config.build_dir
    if build_dir.exists():
        html_count = len(list(build_dir.rglob("*.html")))
        stats_table.add_row(
            "Build (HTML)", str(html_count), _format_dir_size(build_dir)
        )

    cache_dir = project_root / ".nitro"
    if cache_dir.exists():
        cache_files = len(list(cache_dir.rglob("*")))
        stats_table.add_row("Cache", str(cache_files), _format_dir_size(cache_dir))

    if stats_table.row_count > 0:
        console.print(
            Panel(
                stats_table,
                title=Text.from_markup("[bold]Statistics[/]"),
                border_style="cyan",
            )
        )


def _show_dependencies():
    """Show installed Nitro ecosystem dependencies."""
    from importlib.metadata import version as pkg_version, PackageNotFoundError

    deps_table = Table(box=ROUNDED, show_header=True, padding=(0, 2), expand=False)
    deps_table.add_column("Package", style="dim")
    deps_table.add_column("Version", style="cyan")
    deps_table.add_column("Status", style="green")

    packages = [
        "nitro-ui",
        "nitro-datastore",
        "nitro-dispatch",
        "click",
        "rich",
        "watchdog",
        "aiohttp",
        "pillow",
    ]

    for package_name in packages:
        try:
            version = pkg_version(package_name)
            deps_table.add_row(package_name, version, "✓")
        except PackageNotFoundError:
            deps_table.add_row(package_name, "-", "[red]✗ missing[/]")

    console.print(
        Panel(
            deps_table,
            title=Text.from_markup("[bold]Dependencies[/]"),
            border_style="magenta",
        )
    )


def _output_json(project_root):
    """Output info as JSON."""
    import json
    from .. import __version__

    data = {
        "environment": {
            "nitro_version": __version__,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": platform.system(),
            "architecture": platform.machine(),
        },
        "project": None,
    }

    if project_root:
        config_path = project_root / "nitro.config.py"
        if config_path.exists():
            config = load_config(config_path)
            data["project"] = {
                "name": config.site_name,
                "root": str(project_root),
                "source_dir": str(config.source_dir),
                "build_dir": str(config.build_dir),
                "base_url": config.base_url,
                "plugins": config.plugins,
            }

    print(json.dumps(data, indent=2))


def _format_dir_size(path: Path) -> str:
    """Format directory size."""
    total = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except (OSError, PermissionError):
                    # Skip files we can't stat
                    pass
    except (OSError, PermissionError):
        # Return unknown if we can't access the directory
        return "?"

    if total < 1024:
        return f"{total}B"
    elif total < 1024 * 1024:
        return f"{total / 1024:.1f}KB"
    else:
        return f"{total / (1024 * 1024):.1f}MB"
