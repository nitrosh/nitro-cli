"""Configuration management for Nitro projects."""

from typing import Dict, List, Any, Optional
from pathlib import Path


class Config:
    """Project-level configuration for a Nitro site.

    A `Config` instance is typically declared in `nitro.config.py` at the
    project root as a module-level `config = Config(...)` binding. The CLI
    loads it via `load_config()` during build and dev workflows, and its
    fields drive output paths, URL rewriting, renderer behavior, and plugin
    activation.

    Attributes:
        site_name: Human-readable site name, available to plugins and templates.
        base_url: Canonical site URL, used for sitemaps, absolute links, and RSS.
        build_dir: Directory where generated HTML and assets are written.
        source_dir: Directory containing `pages/`, `data/`, and other source files.
        renderer: Renderer options (e.g. `minify_html`, `pretty_print`). Merges
            with defaults; user keys win.
        plugins: Dotted import paths of plugins to activate for this project.
        clean_urls: If True, emit `about/index.html` so URLs can omit `.html`.

    Example:
        >>> from nitro import Config
        >>> config = Config(
        ...     site_name="My Site",
        ...     base_url="https://mysite.com",
        ...     renderer={"minify_html": True},
        ... )
    """

    def __init__(
        self,
        site_name: str = "My Site (built with nitro.sh)",
        base_url: str = "http://localhost:8008",
        build_dir: str = "build",
        source_dir: str = "src",
        renderer: Optional[Dict[str, Any]] = None,
        plugins: Optional[List[str]] = None,
        clean_urls: bool = True,
    ):
        """Initialize a Config with project settings.

        Args:
            site_name: Human-readable site name.
            base_url: Canonical site URL (no trailing slash required).
            build_dir: Output directory for generated files, relative to project root.
            source_dir: Source directory containing pages and data.
            renderer: Renderer overrides merged on top of
                `{"pretty_print": False, "minify_html": False}`.
            plugins: Dotted import paths of plugins to enable.
            clean_urls: When True, write `about/index.html` instead of `about.html`.
        """
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
        self.clean_urls = clean_urls


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
