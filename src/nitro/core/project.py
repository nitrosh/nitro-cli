"""Project utilities for working with Nitro sites."""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Union

import yaml

from nitro_datastore import NitroDataStore


class Page:
    """Represents a page in the Nitro site."""

    def __init__(
        self,
        title: str,
        content: Any,
        meta: Optional[Dict[str, Any]] = None,
        template: Optional[str] = None,
    ):
        """
        Initialize a page.

        Args:
            title: Page title
            content: nitro-ui content (HTML element)
            meta: Meta tags dictionary
            template: Template name (if using a layout)
        """
        self.title = title
        self.content = content
        self.meta = meta or {}
        self.template = template


def load_data(
    data_path: Union[str, Path], wrap: bool = True
) -> Union[NitroDataStore, Any]:
    """
    Load data from a file (JSON, YAML, etc.).

    Args:
        data_path: Relative path to data file or directory from project root
        wrap: If True, wrap JSON data in NitroDataStore (default: True)

    Returns:
        NitroDataStore for JSON files (if wrap=True), or raw data structure

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format not supported

    Example:
        >>> # Load as NitroDataStore (flexible access)
        >>> data = load_data("data/site.json")
        >>> print(data.site.name)  # Dot notation
        >>> print(data.get('site.name'))  # Path notation
        >>>
        >>> # Load as raw dict
        >>> data = load_data("data/site.json", wrap=False)
        >>> print(data['site']['name'])  # Dictionary access
    """
    # This will be called from within user's page files
    # We need to find the project root
    current_dir = Path.cwd()
    file_path = Path(data_path) if isinstance(data_path, str) else data_path

    # If relative path, resolve from current directory
    if not file_path.is_absolute():
        file_path = current_dir / file_path

    # If directory, use NitroDataStore.from_directory
    if file_path.is_dir():
        return NitroDataStore.from_directory(file_path)

    if not file_path.exists():
        # Try with src/ prefix
        file_path = current_dir / "src" / data_path
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {data_path}")

    suffix = file_path.suffix.lower()

    if suffix == ".json":
        if wrap:
            return NitroDataStore.from_file(file_path)
        else:
            with open(file_path, "r") as f:
                return json.load(f)
    elif suffix in [".yaml", ".yml"]:
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
            if wrap and isinstance(data, dict):
                return NitroDataStore(data)
            return data
    else:
        raise ValueError(f"Unsupported data file format: {suffix}")


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
