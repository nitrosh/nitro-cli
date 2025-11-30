"""Build cache for incremental builds."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set


class BuildCache:
    """Manages build cache for incremental builds.

    Tracks file hashes to determine what needs to be rebuilt.
    """

    CACHE_FILE = ".nitro/cache.json"
    CACHE_VERSION = 1

    def __init__(self, project_root: Path):
        """Initialize the build cache.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.cache_path = project_root / self.CACHE_FILE
        self.cache_dir = project_root / ".nitro"
        self._cache: Dict = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cache from disk."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r") as f:
                    data = json.load(f)

                # Check cache version
                if data.get("version") != self.CACHE_VERSION:
                    self._cache = self._empty_cache()
                else:
                    self._cache = data
            except (json.JSONDecodeError, IOError):
                self._cache = self._empty_cache()
        else:
            self._cache = self._empty_cache()

    def _empty_cache(self) -> Dict:
        """Create an empty cache structure."""
        return {
            "version": self.CACHE_VERSION,
            "pages": {},
            "components": {},
            "data": {},
            "config_hash": None,
            "last_build": None,
        }

    def save(self) -> None:
        """Save cache to disk."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache["last_build"] = datetime.now().isoformat()

        with open(self.cache_path, "w") as f:
            json.dump(self._cache, f, indent=2)

    def clear(self) -> None:
        """Clear the cache."""
        self._cache = self._empty_cache()
        if self.cache_path.exists():
            self.cache_path.unlink()

    def _get_file_hash(self, path: Path) -> Optional[str]:
        """Calculate hash of a file.

        Args:
            path: Path to file

        Returns:
            SHA256 hash or None if file doesn't exist
        """
        if not path.exists():
            return None

        hasher = hashlib.sha256()
        try:
            hasher.update(path.read_bytes())
            return hasher.hexdigest()[:16]  # Use first 16 chars for brevity
        except IOError:
            return None

    def _get_relative_path(self, path: Path) -> str:
        """Get path relative to project root."""
        try:
            return str(path.relative_to(self.project_root))
        except ValueError:
            return str(path)

    def is_config_changed(self, config_path: Path) -> bool:
        """Check if config file has changed.

        Args:
            config_path: Path to nitro.config.py

        Returns:
            True if config changed
        """
        current_hash = self._get_file_hash(config_path)
        return current_hash != self._cache.get("config_hash")

    def update_config_hash(self, config_path: Path) -> None:
        """Update the stored config hash.

        Args:
            config_path: Path to nitro.config.py
        """
        self._cache["config_hash"] = self._get_file_hash(config_path)

    def get_changed_pages(
        self,
        pages: List[Path],
        components_dir: Path,
        data_dir: Path,
    ) -> List[Path]:
        """Get list of pages that need to be rebuilt.

        Args:
            pages: List of page file paths
            components_dir: Path to components directory
            data_dir: Path to data directory

        Returns:
            List of pages that need to be rebuilt
        """
        # First, update component and data hashes
        components_changed = self._update_component_hashes(components_dir)
        data_changed = self._update_data_hashes(data_dir)

        # If components or data changed, rebuild all pages that depend on them
        changed_pages = []

        for page_path in pages:
            rel_path = self._get_relative_path(page_path)
            current_hash = self._get_file_hash(page_path)

            cached_info = self._cache["pages"].get(rel_path, {})
            cached_hash = cached_info.get("hash")

            # Page needs rebuild if:
            # 1. Hash changed
            # 2. Components changed (we don't track dependencies, so rebuild all)
            # 3. Data files changed (we don't track dependencies, so rebuild all)
            # 4. Page not in cache
            if (
                current_hash != cached_hash
                or components_changed
                or data_changed
                or rel_path not in self._cache["pages"]
            ):
                changed_pages.append(page_path)

        return changed_pages

    def _update_component_hashes(self, components_dir: Path) -> bool:
        """Update component file hashes.

        Args:
            components_dir: Path to components directory

        Returns:
            True if any component changed
        """
        if not components_dir.exists():
            return False

        changed = False
        current_hashes = {}

        for py_file in components_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            rel_path = self._get_relative_path(py_file)
            current_hash = self._get_file_hash(py_file)
            current_hashes[rel_path] = current_hash

            cached_hash = self._cache["components"].get(rel_path)
            if current_hash != cached_hash:
                changed = True

        # Check for deleted components
        for cached_path in list(self._cache["components"].keys()):
            if cached_path not in current_hashes:
                changed = True

        self._cache["components"] = current_hashes
        return changed

    def _update_data_hashes(self, data_dir: Path) -> bool:
        """Update data file hashes.

        Args:
            data_dir: Path to data directory

        Returns:
            True if any data file changed
        """
        if not data_dir.exists():
            return False

        changed = False
        current_hashes = {}

        for data_file in data_dir.rglob("*"):
            if data_file.is_file() and data_file.suffix in (".json", ".yaml", ".yml"):
                rel_path = self._get_relative_path(data_file)
                current_hash = self._get_file_hash(data_file)
                current_hashes[rel_path] = current_hash

                cached_hash = self._cache["data"].get(rel_path)
                if current_hash != cached_hash:
                    changed = True

        # Check for deleted data files
        for cached_path in list(self._cache["data"].keys()):
            if cached_path not in current_hashes:
                changed = True

        self._cache["data"] = current_hashes
        return changed

    def update_page_hash(self, page_path: Path) -> None:
        """Update the hash for a page after successful build.

        Args:
            page_path: Path to page file
        """
        rel_path = self._get_relative_path(page_path)
        current_hash = self._get_file_hash(page_path)

        self._cache["pages"][rel_path] = {
            "hash": current_hash,
            "built_at": datetime.now().isoformat(),
        }

    def remove_page(self, page_path: Path) -> None:
        """Remove a page from the cache.

        Args:
            page_path: Path to page file
        """
        rel_path = self._get_relative_path(page_path)
        if rel_path in self._cache["pages"]:
            del self._cache["pages"][rel_path]

    def get_stats(self) -> Dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        return {
            "pages_cached": len(self._cache["pages"]),
            "components_tracked": len(self._cache["components"]),
            "data_files_tracked": len(self._cache["data"]),
            "last_build": self._cache.get("last_build"),
        }
