"""Plugin loader for Nitro."""

from typing import Any, List, Optional
from pathlib import Path
import importlib
import importlib.util
import sys

from .base import NitroPlugin
from ..utils import info, warning, error


class PluginLoader:
    """Handles plugin discovery and loading."""

    def __init__(self):
        """Initialize plugin loader."""
        self.plugins: List[NitroPlugin] = []

    def load_plugins(
        self, plugin_names: List[str], project_root: Optional[Path] = None
    ) -> None:
        """Load plugins by name.

        Args:
            plugin_names: List of plugin names to load
            project_root: Optional project root directory
        """
        for plugin_name in plugin_names:
            plugin = self._load_plugin(plugin_name, project_root)
            if plugin:
                self.plugins.append(plugin)
                info(f"Loaded plugin: {plugin.name} v{plugin.version}")

    def _load_plugin(
        self, plugin_name: str, project_root: Optional[Path] = None
    ) -> Optional[NitroPlugin]:
        """Load a single plugin.

        Args:
            plugin_name: Name of the plugin
            project_root: Optional project root directory

        Returns:
            Plugin instance or None if failed
        """
        # Try to import as installed package
        try:
            module = importlib.import_module(plugin_name)
            if hasattr(module, "Plugin"):
                return module.Plugin()
        except ImportError:
            pass

        # Try to load from project plugins directory
        if project_root:
            plugin_path = project_root / "src" / "plugins" / f"{plugin_name}.py"
            if plugin_path.exists():
                try:
                    spec = importlib.util.spec_from_file_location(
                        plugin_name, plugin_path
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[plugin_name] = module
                        spec.loader.exec_module(module)
                        if hasattr(module, "Plugin"):
                            return module.Plugin()
                except Exception as e:
                    error(f"Failed to load plugin {plugin_name}: {e}")

        warning(f"Plugin not found: {plugin_name}")
        return None

    def trigger_hook(self, hook_name: str, *args, **kwargs) -> Any:
        """Trigger a plugin hook.

        Args:
            hook_name: Name of the hook to trigger
            *args: Positional arguments for the hook
            **kwargs: Keyword arguments for the hook

        Returns:
            Result from hooks
        """
        result = kwargs.get("initial_value")

        for plugin in self.plugins:
            if hasattr(plugin, hook_name):
                hook = getattr(plugin, hook_name)
                result = hook(*args, **kwargs) or result

        return result
