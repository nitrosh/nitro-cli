"""Environment variable utilities for Nitro sites."""

import os
from pathlib import Path


class Env:
    """Lazy-loading accessor for environment variables.

    Reads variables from `os.environ` and, if `python-dotenv` is installed,
    auto-loads a `.env` file from the current working directory on first
    access. Missing variables return `""` rather than raising, so pages can
    treat optional config as falsy without guarding every lookup.

    A module-level instance is exported as `nitro.env` - prefer that over
    constructing `Env()` directly.

    Example:
        >>> from nitro import env
        >>> api_key = env.API_KEY
        >>> if env.is_production():
        ...     ...
    """

    def __init__(self):
        """Initialize the accessor in an unloaded state.

        The `.env` file is not touched until the first variable read.
        """
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
        """Return the environment variable named `name`.

        Triggers a one-time `.env` load on first access.

        Args:
            name: Environment variable name. Leading underscores are reserved
                for internal state and raise `AttributeError`.

        Returns:
            The variable's value, or `""` if it is not set.

        Raises:
            AttributeError: If `name` starts with an underscore.

        Example:
            >>> from nitro import env
            >>> env.DATABASE_URL
            'postgres://...'
        """
        if name.startswith("_"):
            raise AttributeError(name)

        self._load()
        return os.environ.get(name, "")

    def get(self, name: str, default: str = "") -> str:
        """Return an environment variable, falling back to `default`.

        Use this instead of attribute access when you need a non-empty
        fallback, or when the variable name is only known at runtime.

        Args:
            name: Environment variable name.
            default: Value to return when the variable is unset.

        Returns:
            The variable's value, or `default` if it is not set.

        Example:
            >>> from nitro import env
            >>> env.get("LOG_LEVEL", "info")
            'info'
        """
        self._load()
        return os.environ.get(name, default)

    def is_production(self) -> bool:
        """Return True when running under a production build.

        Detected by `NITRO_ENV=production` in the environment; the CLI sets
        this for you during `nitro build`.

        Returns:
            True if `NITRO_ENV` equals `"production"`, else False.
        """
        return os.environ.get("NITRO_ENV") == "production"

    def is_development(self) -> bool:
        """Return True when not running under a production build.

        Complement of `is_production()`; treats any missing or non-production
        `NITRO_ENV` value as development.

        Returns:
            True unless `NITRO_ENV` equals `"production"`.
        """
        return not self.is_production()


# Global env instance for convenient imports
env = Env()
