"""Project utilities for working with Nitro sites."""

from pathlib import Path
from typing import Dict, Any, Optional


class Page:
    """A single rendered page in a Nitro site.

    Page functions return a `Page` to bundle the document title, the
    nitro-ui content tree, and rendering metadata. The renderer converts the
    `content` element's `.render()` output into HTML and writes it to
    `build/` at a path mirroring the source file.

    Attributes:
        title: Page title exposed to plugins and sitemap generation.
        content: A nitro-ui element (anything with `.render() -> str`).
        meta: Arbitrary meta tags keyed by name (e.g. `{"description": "..."}`).
        template: Optional template name when rendering with a layout.
        draft: When True, the page is skipped during production builds.

    Example:
        >>> from nitro import Page
        >>> from nitro_ui import HTML, Body, H1
        >>> def render():
        ...     return Page(title="Home", content=HTML(Body(H1("Welcome"))))
    """

    def __init__(
        self,
        title: str,
        content: Any,
        meta: Optional[Dict[str, Any]] = None,
        template: Optional[str] = None,
        draft: bool = False,
    ):
        """Initialize a page with its title, content, and metadata.

        Args:
            title: Page title used in `<title>` and sitemap output.
            content: A nitro-ui element whose `.render()` produces the HTML body.
            meta: Meta tags dictionary applied by the renderer.
            template: Template name when rendering with a layout.
            draft: If True, the page is excluded from production builds.
        """
        self.title = title
        self.content = content
        self.meta = meta or {}
        self.template = template
        self.draft = draft


def get_project_root() -> Optional[Path]:
    """Find the Nitro project root by looking for nitro.config.py.

    Returns:
        Path to project root, or None if not found
    """
    current = Path.cwd()

    # Search up the directory tree for nitro.config.py
    for parent in [current, *current.parents]:
        config_file = parent / "nitro.config.py"
        if config_file.exists():
            return parent

    return None
