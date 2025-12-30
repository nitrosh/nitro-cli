"""File watcher for development mode."""

from typing import Callable, Optional
from pathlib import Path
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from ..utils import info, success


class NitroFileHandler(FileSystemEventHandler):
    """Handles file system events for Nitro projects."""

    def __init__(
        self,
        project_root: Path,
        on_change: Callable[[Path], None],
        debounce_seconds: float = 0.5,
    ):
        super().__init__()
        self.project_root = project_root
        self.on_change = on_change
        self.debounce_seconds = debounce_seconds
        self.last_modified: dict[str, float] = {}

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return

        path = Path(event.src_path)
        if self._should_ignore(path):
            return

        current_time = time.time()
        last_time = self.last_modified.get(event.src_path, 0)

        if current_time - last_time < self.debounce_seconds:
            return

        self.last_modified[event.src_path] = current_time
        self.on_change(path)

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return

        path = Path(event.src_path)
        if self._should_ignore(path):
            return

        info(f"New file detected: {path.name}")
        self.on_change(path)

    def _should_ignore(self, path: Path) -> bool:
        ignore_patterns = [
            "__pycache__",
            ".pyc",
            ".pyo",
            ".git",
            ".nitro",
            "build/",
            ".idea",
            ".vscode",
            ".DS_Store",
        ]

        path_str = str(path)
        for pattern in ignore_patterns:
            if pattern in path_str:
                return True

        name = path.name
        if name.endswith("~") or name.startswith(".#") or name.endswith(".swp"):
            return True

        return False


class Watcher:
    """File watcher for automatic regeneration."""

    def __init__(self, project_root: Path, on_change: Callable[[Path], None]):
        self.project_root = project_root
        self.on_change = on_change
        self.observer: Optional[Observer] = None

    def start(self) -> None:
        """Start watching for file changes."""
        info("Starting file watcher...")

        event_handler = NitroFileHandler(self.project_root, self.on_change)
        self.observer = Observer()

        src_path = self.project_root / "src"
        if src_path.exists():
            self.observer.schedule(event_handler, str(src_path), recursive=True)

        config_path = self.project_root / "nitro.config.py"
        if config_path.exists():
            self.observer.schedule(
                event_handler, str(config_path.parent), recursive=False
            )

        self.observer.start()
        success("File watcher started")

    def stop(self) -> None:
        """Stop watching for file changes."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            info("File watcher stopped")
