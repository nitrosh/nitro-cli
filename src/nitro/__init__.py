"""Nitro CLI - A static site generator built on YDNATL."""

__version__ = "0.1.0"
__author__ = "Sean Nieuwoudt"

from .core.config import Config
from .core.project import Page, load_data
from .core.datastore import NitroDataStore

__all__ = ["Config", "Page", "load_data", "NitroDataStore", "__version__"]
