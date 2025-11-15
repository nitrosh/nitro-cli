"""Configuration management for Nitro projects."""

from typing import Dict, List, Any, Optional
from pathlib import Path


class Config:
    """Configuration class for Nitro projects."""

    def __init__(
        self,
        site_name: str = "My Site (built with nitro.sh)",
        base_url: str = "http://localhost:8008",
        build_dir: str = "build",
        source_dir: str = "src",
        dev_server: Optional[Dict[str, Any]] = None,
        renderer: Optional[Dict[str, Any]] = None,
        plugins: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """Initialize configuration.

        Args:
            site_name: Name of the site
            base_url: Base URL for the site
            build_dir: Output directory for built files
            source_dir: Source directory containing pages/components
            dev_server: Development server configuration
            renderer: Rendering options
            plugins: List of plugin names to load
            metadata: Additional site metadata
            **kwargs: Additional custom configuration
        """
        self.site_name = site_name
        self.base_url = base_url
        self.build_dir = Path(build_dir)
        self.source_dir = Path(source_dir)

        # Development server defaults
        self.dev_server = {
            "port": 8008,
            "host": "localhost",
            "live_reload": True,
            **(dev_server or {}),
        }

        # Renderer defaults
        self.renderer = {
            "pretty_print": False,
            "minify_html": False,
            **(renderer or {}),
        }

        # Plugins
        self.plugins = plugins or []

        # Metadata
        self.metadata = metadata or {}

        # Store any additional configuration
        self.custom = kwargs

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return getattr(self, key, self.custom.get(key, default))

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration
        """
        return {
            "site_name": self.site_name,
            "base_url": self.base_url,
            "build_dir": str(self.build_dir),
            "source_dir": str(self.source_dir),
            "dev_server": self.dev_server,
            "renderer": self.renderer,
            "plugins": self.plugins,
            "metadata": self.metadata,
            **self.custom,
        }


def load_config(config_path: Path) -> Config:
    """Load configuration from a Python file.

    Args:
        config_path: Path to nitro.config.py

    Returns:
        Loaded configuration object
    """
    import importlib.util
    import sys

    if not config_path.exists():
        return Config()

    spec = importlib.util.spec_from_file_location("nitro_config", config_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules["nitro_config"] = module
        spec.loader.exec_module(module)

        if hasattr(module, "config"):
            return module.config

    return Config()
