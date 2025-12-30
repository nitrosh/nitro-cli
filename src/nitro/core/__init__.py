"""Core modules for Nitro CLI."""

from .config import Config, load_config
from .project import Page, get_project_root, load_data
from .renderer import Renderer
from .generator import Generator
from .watcher import Watcher
from .server import LiveReloadServer
from .bundler import Bundler
from .images import (
    ImageConfig,
    ImageOptimizer,
    OptimizedImage,
    responsive_image,
    lazy_image,
)
from .islands import (
    Island,
    IslandConfig,
    IslandProcessor,
    IslandRegistry,
    island,
    client_component,
    lazy_island,
    eager_island,
    interactive_island,
    static_island,
    get_registry,
)

__all__ = [
    "Config",
    "load_config",
    "Page",
    "load_data",
    "get_project_root",
    "Renderer",
    "Generator",
    "Watcher",
    "LiveReloadServer",
    "Bundler",
    # Images
    "ImageConfig",
    "ImageOptimizer",
    "OptimizedImage",
    "responsive_image",
    "lazy_image",
    # Islands
    "Island",
    "IslandConfig",
    "IslandProcessor",
    "IslandRegistry",
    "island",
    "client_component",
    "lazy_island",
    "eager_island",
    "interactive_island",
    "static_island",
    "get_registry",
]
