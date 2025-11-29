"""Plugin loader for Nitro using nitro-dispatch."""

from typing import Any, Dict, List, Optional
from pathlib import Path
import importlib
import importlib.util
import sys

from nitro_dispatch import PluginManager

from .base import NitroPlugin
from ..utils import info, warning, error


class PluginLoader:
    """Handles plugin discovery and loading using nitro-dispatch.

    This class wraps nitro-dispatch's PluginManager to provide
    Nitro-specific plugin loading and hook triggering.

    Example:
        loader = PluginLoader()
        loader.load_plugins(['my-plugin'], project_root=Path('/my/project'))

        # Trigger hooks
        result = loader.trigger('nitro.pre_generate', {'config': config})
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize plugin loader.

        Args:
            config: Optional configuration dictionary for plugins
        """
        self.manager = PluginManager(config=config or {})
        self._plugin_classes: List[type] = []

    def load_plugins(
        self, plugin_names: List[str], project_root: Optional[Path] = None
    ) -> None:
        """Load plugins by name.

        Args:
            plugin_names: List of plugin names to load
            project_root: Optional project root directory
        """
        for plugin_name in plugin_names:
            plugin_class = self._discover_plugin(plugin_name, project_root)
            if plugin_class:
                self.manager.register(plugin_class)
                self._plugin_classes.append(plugin_class)
                info(f"Registered plugin: {plugin_class.name} v{plugin_class.version}")

        # Load all registered plugins
        self.manager.load_all()

    def _discover_plugin(
        self, plugin_name: str, project_root: Optional[Path] = None
    ) -> Optional[type]:
        """Discover a plugin class by name.

        Args:
            plugin_name: Name of the plugin
            project_root: Optional project root directory

        Returns:
            Plugin class or None if not found
        """
        # Try to import as installed package
        try:
            module = importlib.import_module(plugin_name)
            if hasattr(module, "Plugin"):
                return module.Plugin
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
                            return module.Plugin
                except Exception as e:
                    error(f"Failed to load plugin {plugin_name}: {e}")

        warning(f"Plugin not found: {plugin_name}")
        return None

    def discover_plugins(
        self, directory: Path, pattern: str = "*.py", recursive: bool = True
    ) -> None:
        """Auto-discover plugins from a directory.

        Args:
            directory: Directory to search for plugins
            pattern: Glob pattern for plugin files
            recursive: Whether to search recursively
        """
        self.manager.discover_plugins(
            str(directory), pattern=pattern, recursive=recursive
        )

    def trigger(self, event: str, data: Optional[Dict[str, Any]] = None) -> Any:
        """Trigger a plugin hook/event.

        Args:
            event: Event name (e.g., 'nitro.pre_generate')
            data: Data to pass to hook handlers

        Returns:
            Modified data from hooks
        """
        return self.manager.trigger(event, data or {})

    async def trigger_async(
        self, event: str, data: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Trigger a plugin hook/event asynchronously.

        Args:
            event: Event name (e.g., 'nitro.pre_generate')
            data: Data to pass to hook handlers

        Returns:
            Modified data from hooks
        """
        return await self.manager.trigger_async(event, data or {})

    def trigger_hook(self, hook_name: str, *args, **kwargs) -> Any:
        """Trigger a plugin hook (legacy compatibility).

        Args:
            hook_name: Name of the hook to trigger (e.g., 'on_pre_generate')
            *args: Positional arguments (ignored, use data dict instead)
            **kwargs: Keyword arguments passed as data

        Returns:
            Result from hooks
        """
        # Convert legacy hook names to event names
        event_map = {
            "on_init": "nitro.init",
            "on_pre_generate": "nitro.pre_generate",
            "on_post_generate": "nitro.post_generate",
            "on_pre_build": "nitro.pre_build",
            "on_post_build": "nitro.post_build",
            "process_data": "nitro.process_data",
            "add_commands": "nitro.add_commands",
        }

        event = event_map.get(hook_name, f"nitro.{hook_name}")
        return self.trigger(event, kwargs)

    def reload_plugin(self, plugin_name: str) -> None:
        """Hot-reload a plugin.

        Args:
            plugin_name: Name of the plugin to reload
        """
        self.manager.reload(plugin_name)
        info(f"Reloaded plugin: {plugin_name}")

    def enable_plugin(self, plugin_name: str) -> None:
        """Enable a disabled plugin.

        Args:
            plugin_name: Name of the plugin to enable
        """
        self.manager.enable_plugin(plugin_name)

    def disable_plugin(self, plugin_name: str) -> None:
        """Disable a plugin without unloading.

        Args:
            plugin_name: Name of the plugin to disable
        """
        self.manager.disable_plugin(plugin_name)

    def enable_tracing(self) -> None:
        """Enable hook tracing for debugging."""
        self.manager.enable_hook_tracing()

    @property
    def plugins(self) -> List[NitroPlugin]:
        """Get list of loaded plugin instances."""
        # Access the manager's internal plugin instances
        return (
            list(self.manager._plugins.values())
            if hasattr(self.manager, "_plugins")
            else []
        )
