"""Base plugin class for Nitro."""

from typing import Any, Dict, Optional


class NitroPlugin:
    """Base class for all Nitro plugins."""

    name: str = "base-plugin"
    version: str = "0.1.0"

    def on_init(self, config: Any) -> None:
        """Called when plugin is loaded.

        Args:
            config: Nitro configuration object
        """
        pass

    def on_pre_generate(self, context: Dict[str, Any]) -> None:
        """Called before HTML generation.

        Args:
            context: Generation context
        """
        pass

    def on_post_generate(self, context: Dict[str, Any], output: str) -> str:
        """Called after HTML generation, can modify output.

        Args:
            context: Generation context
            output: Generated HTML output

        Returns:
            Modified HTML output
        """
        return output

    def on_pre_build(self, context: Dict[str, Any]) -> None:
        """Called before production build.

        Args:
            context: Build context
        """
        pass

    def on_post_build(self, context: Dict[str, Any]) -> None:
        """Called after production build.

        Args:
            context: Build context
        """
        pass

    def add_commands(self, cli: Any) -> None:
        """Add custom CLI commands.

        Args:
            cli: Click CLI group
        """
        pass

    def process_data(self, data_file: str, content: Any) -> Any:
        """Process data files (e.g., markdown -> JSON).

        Args:
            data_file: Path to data file
            content: File content

        Returns:
            Processed content
        """
        return content
