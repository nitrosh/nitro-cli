"""Project utilities for working with Nitro sites."""

from pathlib import Path
from typing import Dict, Any, Optional


class Page:
    """Represents a page in the Nitro site."""

    def __init__(
        self,
        title: str,
        content: Any,
        meta: Optional[Dict[str, Any]] = None,
        template: Optional[str] = None,
        draft: bool = False,
    ):
        """
        Initialize a page.

        Args:
            title: Page title
            content: nitro-ui content (HTML element)
            meta: Meta tags dictionary
            template: Template name (if using a layout)
            draft: If True, page is excluded from production builds
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
