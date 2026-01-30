"""Main CLI entry point for Nitro."""

import click
from rich.console import Console
from rich.text import Text
from rich.table import Table
from . import __version__
from .commands import (
    new,
    serve,
    dev,
    build,
    preview,
    clean,
    info,
    deploy,
    init,
    export_cmd,
    routes,
    check,
)
from .core.page import get_project_root

console = Console()


def detect_project_context():
    """
    Detect if we're inside a Nitro project.

    Returns:
        tuple: (project_root, project_name) or (None, None)
    """
    project_root = get_project_root()
    if project_root:
        return project_root, project_root.name
    return None, None


def show_welcome():
    """Display the welcome banner with commands and project info."""
    project_root, project_name = detect_project_context()

    # Header
    header = Text()
    header.append("\n⚡ ", style="bold magenta")
    header.append("Nitro", style="bold cyan")
    header.append(f" v{__version__}", style="dim")
    header.append(" - https://nitro.sh\n", style="dim")

    if project_root:
        header.append("\n  Project: ", style="dim")
        header.append(project_name, style="bold green")
        header.append("\n  Path:    ", style="dim")
        header.append(str(project_root), style="blue")
        header.append("\n")

    console.print(header)

    # Commands table
    table = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
    table.add_column("command", style="cyan")
    table.add_column("description", style="dim")

    table.add_row(" nitro new [dim]<name>[/dim]", "Create a new project")
    table.add_row(" nitro init", "Initialize Nitro in current directory")
    table.add_row(" nitro dev", "Start dev server with hot reload")
    table.add_row(" nitro build", "Build for production")
    table.add_row(" nitro preview", "Preview production build")
    table.add_row(" nitro routes", "List all routes")
    table.add_row(" nitro check", "Validate site without building")
    table.add_row(" nitro export", "Export site as zip")
    table.add_row(" nitro clean", "Clean build artifacts")

    console.print(" [bold]Commands:[/bold]\n")
    console.print(table)

    footer = Text()
    footer.append("\nRun", style="dim")
    footer.append(" nitro <command> --help", style="cyan")
    footer.append(" for more options\n", style="dim")
    console.print(footer)


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="nitro")
@click.pass_context
def main(ctx):
    """
    Nitro: Static sites without the JavaScript fatigue.
    """
    ctx.ensure_object(dict)
    if ctx.invoked_subcommand is None:
        show_welcome()


# Register commands (type: ignore needed because Click decorators transform functions to Commands)

main.add_command(new)  # type: ignore[arg-type]
main.add_command(serve)  # type: ignore[arg-type]
main.add_command(dev)  # type: ignore[arg-type]
main.add_command(build)  # type: ignore[arg-type]
main.add_command(preview)  # type: ignore[arg-type]
main.add_command(clean)  # type: ignore[arg-type]
main.add_command(info)  # type: ignore[arg-type]
main.add_command(deploy)  # type: ignore[arg-type]
main.add_command(init)  # type: ignore[arg-type]
main.add_command(export_cmd, name="export")  # type: ignore[arg-type]
main.add_command(routes)  # type: ignore[arg-type]
main.add_command(check)  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
