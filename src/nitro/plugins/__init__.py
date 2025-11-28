"""Plugin system for Nitro CLI using nitro-dispatch."""

from nitro_dispatch import hook

from .base import NitroPlugin
from .loader import PluginLoader

__all__ = ["NitroPlugin", "PluginLoader", "hook"]
