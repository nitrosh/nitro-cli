"""Routes command for listing all site routes."""

import json
import sys
import click
from pathlib import Path

from ..core.page import get_project_root
from ..core.config import load_config
from ..core.renderer import Renderer
from ..utils import console, error


@click.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def routes(as_json):
    """List all routes the site will generate."""
    project_root = get_project_root()

    if not project_root:
        error("Not in a Nitro project directory")
        sys.exit(1)

    # Load config
    config_path = project_root / "nitro.config.py"
    config = load_config(config_path) if config_path.exists() else None
    source_dir = project_root / (config.source_dir if config else "src")
    pages_dir = source_dir / "pages"

    if not pages_dir.exists():
        error("No pages directory found")
        sys.exit(1)

    renderer = Renderer(config)

    # Find all pages
    pages = []
    for py_file in sorted(pages_dir.rglob("*.py")):
        if py_file.name == "__init__.py":
            continue

        relative_path = py_file.relative_to(pages_dir)
        source_file = str(py_file.relative_to(project_root))

        # Check if dynamic route
        is_dynamic = renderer.is_dynamic_route(py_file)

        if is_dynamic:
            # Get all paths from dynamic route
            try:
                dynamic_paths = renderer.get_dynamic_paths(py_file, project_root)
                for params in dynamic_paths:
                    # Build the output URL from params
                    param_name = py_file.stem[1:-1]  # Extract name from [slug].py
                    param_value = params.get(param_name, "")

                    # Build URL path
                    parent = relative_path.parent
                    if str(parent) == ".":
                        url = f"/{param_value}"
                    else:
                        url = f"/{parent}/{param_value}"

                    # Check for draft status
                    draft = params.get("draft", False)

                    pages.append(
                        {
                            "source": source_file,
                            "url": url,
                            "type": "dynamic",
                            "params": params,
                            "draft": draft,
                        }
                    )
            except Exception as e:
                pages.append(
                    {
                        "source": source_file,
                        "url": f"/{relative_path.with_suffix('')}",
                        "type": "dynamic",
                        "error": str(e),
                        "draft": False,
                    }
                )
        else:
            # Static route
            # Convert path to URL
            stem = py_file.stem
            parent = relative_path.parent

            if stem == "index":
                if str(parent) == ".":
                    url = "/"
                else:
                    url = f"/{parent}/"
            else:
                if str(parent) == ".":
                    url = f"/{stem}"
                else:
                    url = f"/{parent}/{stem}"

            # Try to detect draft status by importing the page
            draft = False
            try:
                page_result = renderer.render_page(
                    py_file, project_root, return_page=True
                )
                if hasattr(page_result, "draft"):
                    draft = page_result.draft
            except Exception:
                pass

            pages.append(
                {
                    "source": source_file,
                    "url": url,
                    "type": "static",
                    "draft": draft,
                }
            )

    if as_json:
        print(json.dumps(pages, indent=2))
    else:
        # Rich table output
        from rich.table import Table

        table = Table(show_header=True, header_style="bold")
        table.add_column("URL", style="cyan")
        table.add_column("Source", style="dim")
        table.add_column("Type", style="green")
        table.add_column("Status", style="yellow")

        for page in pages:
            status = ""
            if page.get("draft"):
                status = "[yellow]draft[/]"
            if page.get("error"):
                status = f"[red]error: {page['error'][:30]}[/]"

            table.add_row(
                page["url"],
                page["source"],
                page["type"],
                status,
            )

        console.print(table)
        console.print(f"\n[dim]Total: {len(pages)} route(s)[/]")
