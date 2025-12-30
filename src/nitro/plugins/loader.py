"""Plugin loader for Nitro using nitro-dispatch."""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from nitro_dispatch import PluginManager, PluginBase

from ..utils import info, warning, error


class PluginLoader:
    """Loads, registers, and manages plugins via nitro-dispatch."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.manager = PluginManager(config=config or {})
        self._plugin_classes: List[type] = []

    def load_plugins(
        self, plugin_names: List[str], project_root: Optional[Path] = None
    ) -> None:
        """Load and register plugins by name."""
        for plugin_name in plugin_names:
            plugin_class = self._discover_plugin(plugin_name, project_root)
            if plugin_class:
                self.manager.register(plugin_class)
                self._plugin_classes.append(plugin_class)
                info(f"Registered plugin: {plugin_class.name} v{plugin_class.version}")

        self.manager.load_all()

    def _discover_plugin(
        self, plugin_name: str, project_root: Optional[Path] = None
    ) -> Optional[type]:
        """Find plugin by name. Checks installed packages first, then src/plugins/."""
        try:
            module = importlib.import_module(plugin_name)
            if hasattr(module, "Plugin"):
                return module.Plugin
        except ImportError:
            pass

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
                            return module.Plugin
                except Exception as e:
                    error(f"Failed to load plugin {plugin_name}: {e}")

        warning(f"Plugin not found: {plugin_name}")
        return None

    def discover_plugins(
        self, directory: Path, pattern: str = "*.py", recursive: bool = True
    ) -> None:
        """Auto-discover plugins from a directory."""
        self.manager.discover_plugins(
            str(directory), pattern=pattern, recursive=recursive
        )

    def trigger(self, event: str, data: Optional[Dict[str, Any]] = None) -> Any:
        """Trigger a plugin event (e.g., 'nitro.pre_generate')."""
        return self.manager.trigger(event, data or {})

    async def trigger_async(
        self, event: str, data: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Trigger a plugin event asynchronously."""
        return await self.manager.trigger_async(event, data or {})

    def reload_plugin(self, plugin_name: str) -> None:
        """Hot-reload a plugin."""
        self.manager.reload(plugin_name)
        info(f"Reloaded plugin: {plugin_name}")

    def enable_plugin(self, plugin_name: str) -> None:
        """Enable a disabled plugin."""
        self.manager.enable_plugin(plugin_name)

    def disable_plugin(self, plugin_name: str) -> None:
        """Disable a plugin without unloading."""
        self.manager.disable_plugin(plugin_name)

    def enable_tracing(self, enabled: bool = True) -> None:
        """Enable or disable hook tracing for debugging."""
        self.manager.enable_hook_tracing(enabled)

    @property
    def plugins(self) -> List[PluginBase]:
        """Get a list of loaded plugin instances."""
        return list(self.manager.get_all_plugins().values())
