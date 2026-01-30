"""Check command for validating site without building."""

import re
import sys
import click
from pathlib import Path
from typing import List, Tuple

from ..core.page import get_project_root
from ..core.config import load_config
from ..core.renderer import Renderer
from ..utils import console, success, error, info, warning


def extract_internal_links(html: str) -> List[str]:
    """Extract internal links from HTML content.

    Args:
        html: HTML content string

    Returns:
        List of internal link paths
    """
    # Match href attributes that start with / (internal links)
    pattern = r'href=["\'](/[^"\']*)["\']'
    matches = re.findall(pattern, html)

    # Filter out anchors and external-looking paths
    internal_links = []
    for link in matches:
        # Skip anchor-only links
        if link.startswith("/#"):
            continue
        # Remove query strings and anchors
        path = link.split("?")[0].split("#")[0]
        if path:
            internal_links.append(path)

    return internal_links


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
@click.option(
    "--links/--no-links", default=True, help="Check internal links (default: enabled)"
)
def check(verbose, links):
    """Validate the site without building."""
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

    # Track results
    render_errors: List[Tuple[str, str]] = []
    link_errors: List[Tuple[str, str, str]] = []
    rendered_pages: dict = {}
    valid_paths: set = set()

    info("Checking pages...")

    # Find all pages
    page_files = sorted([f for f in pages_dir.rglob("*.py") if f.name != "__init__.py"])

    if not page_files:
        warning("No pages found")
        sys.exit(0)

    # Pass 1: Render check - try to render each page
    for py_file in page_files:
        relative_path = py_file.relative_to(project_root)

        if verbose:
            console.print(f"  [dim]Checking {relative_path}[/]")

        # Check if dynamic route
        is_dynamic = renderer.is_dynamic_route(py_file)

        if is_dynamic:
            # Try to get dynamic paths and render each
            try:
                dynamic_paths = renderer.get_dynamic_paths(py_file, project_root)
                for params in dynamic_paths:
                    try:
                        html = renderer.render_dynamic_page_single(
                            py_file, project_root, params
                        )
                        if html:
                            # Build output path
                            param_name = py_file.stem[1:-1]
                            param_value = params.get(param_name, "")
                            parent = py_file.parent.relative_to(pages_dir)

                            if str(parent) == ".":
                                url_path = f"/{param_value}"
                            else:
                                url_path = f"/{parent}/{param_value}"

                            valid_paths.add(url_path)
                            valid_paths.add(url_path + "/")
                            rendered_pages[url_path] = html
                    except Exception as e:
                        render_errors.append((str(relative_path), str(e)))
            except Exception as e:
                render_errors.append((str(relative_path), f"Failed to get paths: {e}"))
        else:
            # Static page
            try:
                html = renderer.render_page(py_file, project_root)
                if html:
                    # Build output path
                    stem = py_file.stem
                    parent = py_file.parent.relative_to(pages_dir)

                    if stem == "index":
                        if str(parent) == ".":
                            url_path = "/"
                        else:
                            url_path = f"/{parent}/"
                    else:
                        if str(parent) == ".":
                            url_path = f"/{stem}"
                        else:
                            url_path = f"/{parent}/{stem}"

                    valid_paths.add(url_path)
                    if not url_path.endswith("/"):
                        valid_paths.add(url_path + "/")
                    rendered_pages[url_path] = html
            except Exception as e:
                render_errors.append((str(relative_path), str(e)))

    # Add common static paths (these would be served from public/ or static/)
    public_dir = source_dir / "public"
    static_dir = project_root / "static"

    for static_source in [public_dir, static_dir]:
        if static_source.exists():
            for f in static_source.rglob("*"):
                if f.is_file():
                    rel = f.relative_to(static_source)
                    valid_paths.add(f"/{rel}")

    # Pass 2: Link check - verify internal links exist
    if links and rendered_pages:
        info("Checking internal links...")

        for page_path, html in rendered_pages.items():
            internal_links = extract_internal_links(html)

            for link in internal_links:
                # Normalize link path
                normalized = link.rstrip("/") if link != "/" else link
                normalized_with_slash = (
                    normalized + "/" if not normalized.endswith("/") else normalized
                )

                # Check if target exists
                if (
                    normalized not in valid_paths
                    and normalized_with_slash not in valid_paths
                    and not link.startswith("/__")
                ):  # Skip internal nitro paths
                    link_errors.append((page_path, link, "Target not found"))

    # Report results
    console.print()

    has_errors = bool(render_errors or link_errors)

    if render_errors:
        console.print("[bold red]Render Errors:[/]")
        for page, err in render_errors:
            console.print(f"  [red]✗[/] {page}")
            if verbose:
                console.print(f"    [dim]{err}[/]")
        console.print()

    if link_errors:
        console.print("[bold yellow]Broken Links:[/]")
        for page, link, reason in link_errors:
            console.print(f"  [yellow]⚠[/] {page} → {link}")
            if verbose:
                console.print(f"    [dim]{reason}[/]")
        console.print()

    # Summary
    total_pages = len(rendered_pages)

    if has_errors:
        error(
            f"Found {len(render_errors)} render error(s) and {len(link_errors)} broken link(s)"
        )
        sys.exit(1)
    else:
        success(f"All {total_pages} page(s) validated successfully")
