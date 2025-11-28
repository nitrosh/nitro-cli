"""Renderer for generating HTML from nitro-ui pages."""

from typing import Any, Dict, Optional
from pathlib import Path
import importlib.util
import sys

from ..core.project import Page
from ..utils import error, warning


class Renderer:
    """Handles rendering of nitro-ui pages to HTML."""

    def __init__(self, config: Any):
        """Initialize renderer.

        Args:
            config: Nitro configuration object
        """
        self.config = config
        self.pretty_print = config.renderer.get("pretty_print", False)
        self.minify_html = config.renderer.get("minify_html", False)

    def render_page(self, page_path: Path, project_root: Path) -> Optional[str]:
        """Render a page file to HTML.

        Args:
            page_path: Path to page Python file
            project_root: Root directory of the project

        Returns:
            Rendered HTML string or None if error
        """
        try:
            # Add project root to Python path
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            # Load the page module
            spec = importlib.util.spec_from_file_location(
                f"page_{page_path.stem}", page_path
            )

            if not spec or not spec.loader:
                error(f"Failed to load page: {page_path}")
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # Check if module has render function
            if not hasattr(module, "render"):
                error(f"Page {page_path} missing render() function")
                return None

            # Call render function
            page = module.render()

            # Handle Page object
            if isinstance(page, Page):
                html = self._render_page_object(page)
            else:
                # Assume it's a nitro-ui element
                html = self._render_element(page)

            # Apply post-processing
            if html:
                html = self._post_process(html)

            return html

        except Exception as e:
            error(f"Error rendering {page_path}: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _render_page_object(self, page: Page) -> str:
        """Render a Page object to HTML.

        Args:
            page: Page object

        Returns:
            HTML string
        """
        # Check if content has render method (nitro-ui element)
        if hasattr(page.content, "render"):
            return page.content.render()

        # Otherwise, just convert to string
        return str(page.content)

    def _render_element(self, element: Any) -> str:
        """Render a nitro-ui element to HTML.

        Args:
            element: nitro-ui element

        Returns:
            HTML string
        """
        if hasattr(element, "render"):
            return element.render()
        return str(element)

    def _post_process(self, html: str) -> str:
        """Post-process HTML (minify, pretty print, etc.).

        Args:
            html: HTML string

        Returns:
            Processed HTML string
        """
        # Minification
        if self.minify_html:
            try:
                import htmlmin

                html = htmlmin.minify(html, remove_empty_space=True)
            except ImportError:
                warning("htmlmin not installed, skipping minification")

        # Pretty printing (if not minified)
        elif self.pretty_print:
            try:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(html, "html.parser")
                html = soup.prettify()
            except ImportError:
                # Pretty print not available, return as-is
                pass

        return html

    def get_output_path(
        self, page_path: Path, source_dir: Path, build_dir: Path
    ) -> Path:
        """Get output path for a page.

        Args:
            page_path: Path to source page file
            source_dir: Source directory (src/pages/)
            build_dir: Build output directory

        Returns:
            Output HTML file path
        """
        # Get relative path from pages directory
        pages_dir = source_dir / "pages"
        relative = page_path.relative_to(pages_dir)

        # Change extension to .html
        html_name = relative.stem + ".html"

        # Handle nested paths
        if relative.parent != Path("."):
            output_path = build_dir / relative.parent / html_name
        else:
            output_path = build_dir / html_name

        return output_path
