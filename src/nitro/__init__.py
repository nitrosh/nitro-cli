"""Nitro CLI - A static site generator"""

__version__ = "1.0.0"
__author__ = "Sean Nieuwoudt"

from .core.config import Config
from .core.project import Page, load_data
from .core.markdown import (
    MarkdownDocument,
    parse_markdown,
    parse_markdown_file,
    find_markdown_files,
)
from .core.images import (
    ImageConfig,
    ImageOptimizer,
    OptimizedImage,
    responsive_image,
    lazy_image,
)
from .core.islands import (
    Island,
    IslandConfig,
    IslandProcessor,
    island,
    client_component,
    lazy_island,
    eager_island,
    interactive_island,
    static_island,
)

__all__ = [
    "Config",
    "Page",
    "load_data",
    # Markdown
    "MarkdownDocument",
    "parse_markdown",
    "parse_markdown_file",
    "find_markdown_files",
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
    "island",
    "client_component",
    "lazy_island",
    "eager_island",
    "interactive_island",
    "static_island",
    "__version__",
]
