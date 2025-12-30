"""Build cache for incremental builds."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class BuildCache:
    """Tracks file hashes to determine what needs rebuilding."""

    CACHE_FILE = ".nitro/cache.json"
    CACHE_VERSION = 1

    def __init__(self, project_root: Path):
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
                if data.get("version") != self.CACHE_VERSION:
                    self._cache = self._empty_cache()
                else:
                    self._cache = data
            except (json.JSONDecodeError, IOError):
                self._cache = self._empty_cache()
        else:
            self._cache = self._empty_cache()

    def _empty_cache(self) -> Dict:
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

    def _get_file_hash(self, path: Path) -> Optional[str]:
        """Calculate SHA256 hash of a file (first 16 chars)."""
        if not path.exists():
            return None
        try:
            hasher = hashlib.sha256()
            hasher.update(path.read_bytes())
            return hasher.hexdigest()[:16]
        except IOError:
            return None

    def _get_relative_path(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.project_root))
        except ValueError:
            return str(path)

    def is_config_changed(self, config_path: Path) -> bool:
        """Check if config file has changed."""
        current_hash = self._get_file_hash(config_path)
        return current_hash != self._cache.get("config_hash")

    def update_config_hash(self, config_path: Path) -> None:
        """Update the stored config hash."""
        self._cache["config_hash"] = self._get_file_hash(config_path)

    def get_changed_pages(
        self,
        pages: List[Path],
        components_dir: Path,
        data_dir: Path,
    ) -> List[Path]:
        """Get a list of pages that need rebuilding."""
        components_changed = self._update_component_hashes(components_dir)
        data_changed = self._update_data_hashes(data_dir)

        changed_pages = []
        for page_path in pages:
            rel_path = self._get_relative_path(page_path)
            current_hash = self._get_file_hash(page_path)
            cached_info = self._cache["pages"].get(rel_path, {})
            cached_hash = cached_info.get("hash")

            if (
                current_hash != cached_hash
                or components_changed
                or data_changed
                or rel_path not in self._cache["pages"]
            ):
                changed_pages.append(page_path)

        return changed_pages

    def _update_component_hashes(self, components_dir: Path) -> bool:
        """Update component hashes. Returns True if any changed."""
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
            if current_hash != self._cache["components"].get(rel_path):
                changed = True

        # Check for deleted components
        for cached_path in self._cache["components"]:
            if cached_path not in current_hashes:
                changed = True

        self._cache["components"] = current_hashes
        return changed

    def _update_data_hashes(self, data_dir: Path) -> bool:
        """Update data file hashes. Returns True if any changed."""
        if not data_dir.exists():
            return False

        changed = False
        current_hashes = {}

        for data_file in data_dir.rglob("*"):
            if data_file.is_file() and data_file.suffix in (".json", ".yaml", ".yml"):
                rel_path = self._get_relative_path(data_file)
                current_hash = self._get_file_hash(data_file)
                current_hashes[rel_path] = current_hash
                if current_hash != self._cache["data"].get(rel_path):
                    changed = True

        # Check for deleted data files
        for cached_path in self._cache["data"]:
            if cached_path not in current_hashes:
                changed = True

        self._cache["data"] = current_hashes
        return changed

    def update_page_hash(self, page_path: Path) -> None:
        """Update the hash for a page after successful build."""
        rel_path = self._get_relative_path(page_path)
        self._cache["pages"][rel_path] = {
            "hash": self._get_file_hash(page_path),
            "built_at": datetime.now().isoformat(),
        }
