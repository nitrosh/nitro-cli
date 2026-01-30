"""Nitro CLI - A static site generator"""

__version__ = "1.0.0"
__author__ = "Sean Nieuwoudt"

from .core.config import Config
from .core.page import Page
from .core.env import env
from .core.images import (
    ImageConfig,
    ImageOptimizer,
    OptimizedImage,
)
from .core.islands import (
    Island,
    IslandConfig,
    IslandProcessor,
)

__all__ = [
    "Config",
    "Page",
    "env",
    # Images
    "ImageConfig",
    "ImageOptimizer",
    "OptimizedImage",
    # Islands
    "Island",
    "IslandConfig",
    "IslandProcessor",
    "__version__",
]
