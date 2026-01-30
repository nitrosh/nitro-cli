"""Environment variable utilities for Nitro sites."""

import os
from pathlib import Path


class Env:
    """Lazy-loading environment variable accessor.

    Automatically loads .env file on first access if python-dotenv is installed.

    Usage:
        from nitro import env

        # Access environment variables as attributes
        api_key = env.API_KEY

        # Check if in production
        if env.is_production():
            # Production-only code
            pass
    """

    def __init__(self):
        self._loaded = False

    def _load(self):
        """Load .env file if not already loaded."""
        if self._loaded:
            return

        try:
            from dotenv import load_dotenv

            # Try to find .env file, starting from cwd
            env_file = Path.cwd() / ".env"
            if env_file.exists():
                load_dotenv(env_file)
        except ImportError:
            # python-dotenv not installed, just use existing env vars
            pass

        self._loaded = True

    def __getattr__(self, name: str) -> str:
        """Get environment variable by attribute name.

        Args:
            name: Environment variable name

        Returns:
            Value of environment variable, or empty string if not set
        """
        if name.startswith("_"):
            raise AttributeError(name)

        self._load()
        return os.environ.get(name, "")

    def get(self, name: str, default: str = "") -> str:
        """Get environment variable with optional default.

        Args:
            name: Environment variable name
            default: Default value if not set

        Returns:
            Value of environment variable, or default if not set
        """
        self._load()
        return os.environ.get(name, default)

    def is_production(self) -> bool:
        """Check if running in production mode.

        Returns:
            True if NITRO_ENV is set to 'production'
        """
        return os.environ.get("NITRO_ENV") == "production"

    def is_development(self) -> bool:
        """Check if running in development mode.

        Returns:
            True if not in production mode
        """
        return not self.is_production()


# Global env instance for convenient imports
env = Env()
