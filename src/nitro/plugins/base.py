"""Base plugin class for Nitro using nitro-dispatch."""

from nitro_dispatch import PluginBase, hook


class NitroPlugin(PluginBase):
    """Base class for all Nitro plugins.

    This class extends nitro-dispatch's PluginBase to provide
    Nitro-specific lifecycle hooks for the static site generator.

    Available hooks:
        - nitro.init: Called when plugin is loaded
        - nitro.pre_generate: Called before HTML generation
        - nitro.post_generate: Called after HTML generation (can modify output)
        - nitro.pre_build: Called before production build
        - nitro.post_build: Called after production build
        - nitro.process_data: Called to process data files
        - nitro.add_commands: Called to add CLI commands

    Example:
        from nitro.plugins import NitroPlugin, hook

        class MyPlugin(NitroPlugin):
            name = "my-plugin"
            version = "1.0.0"

            @hook('nitro.post_generate', priority=50)
            def add_analytics(self, data):
                # Modify HTML output
                html = data.get('output', '')
                data['output'] = html.replace('</body>', '<script>...</script></body>')
                return data
    """

    name: str = "base-plugin"
    version: str = "0.1.0"
    description: str = "Nitro plugin"
    author: str = ""
    dependencies: list = []

    def on_load(self) -> None:
        """Called when plugin is loaded by the plugin manager."""
        pass

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        pass

    def on_error(self, error: Exception) -> None:
        """Called when an error occurs in the plugin.

        Args:
            error: The exception that occurred
        """
        pass


__all__ = ["NitroPlugin", "hook"]
