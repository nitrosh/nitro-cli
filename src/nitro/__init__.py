"""Nitro CLI - A static site generator"""

__version__ = "0.1.0"
__author__ = "Sean Nieuwoudt"

from .core.config import Config
from .core.project import Page, load_data

__all__ = ["Config", "Page", "load_data", "__version__"]
