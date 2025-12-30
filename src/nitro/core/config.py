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
        renderer: Optional[Dict[str, Any]] = None,
        plugins: Optional[List[str]] = None,
    ):
        self.site_name = site_name
        self.base_url = base_url
        self.build_dir = Path(build_dir)
        self.source_dir = Path(source_dir)
        self.renderer = {
            "pretty_print": False,
            "minify_html": False,
            **(renderer or {}),
        }
        self.plugins = plugins or []


def load_config(config_path: Path) -> Config:
    """Load configuration from a Python file."""
    import importlib.util
    import sys

    if not config_path.exists():
        return Config()

    try:
        spec = importlib.util.spec_from_file_location("nitro_config", config_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules["nitro_config"] = module

            try:
                spec.loader.exec_module(module)
            finally:
                if "nitro_config" in sys.modules:
                    del sys.modules["nitro_config"]

            if hasattr(module, "config"):
                config = module.config
                if not isinstance(config, Config):
                    raise ValueError(
                        f"nitro.config.py 'config' must be a Config object, "
                        f"got {type(config).__name__}"
                    )
                return config

        return Config()

    except SyntaxError as e:
        raise SyntaxError(
            f"Syntax error in {config_path}: {e.msg} at line {e.lineno}"
        ) from e
    except Exception as e:
        if isinstance(e, (SyntaxError, ValueError)):
            raise
        raise ValueError(f"Error loading {config_path}: {e}") from e
