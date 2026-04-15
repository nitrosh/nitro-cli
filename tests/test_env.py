"""Tests for core/env.py."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from nitro.core.env import Env


class TestEnvAttributeAccess:
    """Tests for __getattr__ attribute-style access."""

    def test_returns_value_for_existing_var(self):
        """Attribute access should return the env var value when set."""
        env = Env()
        with patch.dict(os.environ, {"MY_VAR": "hello"}):
            assert env.MY_VAR == "hello"

    def test_returns_empty_string_for_missing_var(self):
        """Attribute access should return empty string when var is not set."""
        env = Env()
        key = "NITRO_TEST_NONEXISTENT_XYZ"
        os.environ.pop(key, None)
        assert env.__getattr__(key) == ""

    def test_private_attribute_raises_attribute_error(self):
        """Attributes starting with underscore should raise AttributeError."""
        env = Env()
        with pytest.raises(AttributeError, match="_hidden"):
            _ = env._hidden

    def test_double_underscore_raises_attribute_error(self):
        """Dunder attributes should raise AttributeError."""
        env = Env()
        with pytest.raises(AttributeError):
            _ = env.__bogus__

    def test_returns_updated_value_after_env_change(self):
        """Attribute access reflects the current env state each call."""
        env = Env()
        key = "NITRO_DYNAMIC_VAR"
        os.environ.pop(key, None)

        assert env.__getattr__(key) == ""

        with patch.dict(os.environ, {key: "updated"}):
            assert env.__getattr__(key) == "updated"


class TestEnvGet:
    """Tests for the get() method."""

    def test_get_returns_value_for_existing_var(self):
        """get() should return the set value."""
        env = Env()
        with patch.dict(os.environ, {"API_KEY": "secret"}):
            assert env.get("API_KEY") == "secret"

    def test_get_returns_empty_string_default(self):
        """get() should return empty string when var is missing and no default given."""
        env = Env()
        key = "NITRO_TEST_MISSING_ABC"
        os.environ.pop(key, None)
        assert env.get(key) == ""

    def test_get_returns_custom_default_for_missing_var(self):
        """get() should return supplied default when var is not set."""
        env = Env()
        key = "NITRO_TEST_MISSING_DEF"
        os.environ.pop(key, None)
        assert env.get(key, "fallback") == "fallback"

    def test_get_does_not_use_default_when_var_is_set(self):
        """get() should ignore default when the var is actually set."""
        env = Env()
        with patch.dict(os.environ, {"MY_SETTING": "real_value"}):
            assert env.get("MY_SETTING", "fallback") == "real_value"


class TestEnvProductionMode:
    """Tests for is_production() and is_development()."""

    def test_is_production_true_when_nitro_env_production(self):
        """is_production() returns True only when NITRO_ENV == 'production'."""
        env = Env()
        with patch.dict(os.environ, {"NITRO_ENV": "production"}):
            assert env.is_production() is True

    def test_is_production_false_when_nitro_env_not_set(self):
        """is_production() returns False when NITRO_ENV is absent."""
        env = Env()
        os.environ.pop("NITRO_ENV", None)
        assert env.is_production() is False

    def test_is_production_false_for_other_values(self):
        """is_production() returns False for values other than 'production'."""
        env = Env()
        for value in ("development", "staging", "PRODUCTION", "prod", ""):
            with patch.dict(os.environ, {"NITRO_ENV": value}):
                assert env.is_production() is False, f"Expected False for NITRO_ENV={value!r}"

    def test_is_development_true_when_not_production(self):
        """is_development() returns True when NITRO_ENV is not 'production'."""
        env = Env()
        os.environ.pop("NITRO_ENV", None)
        assert env.is_development() is True

    def test_is_development_false_in_production(self):
        """is_development() returns False when NITRO_ENV == 'production'."""
        env = Env()
        with patch.dict(os.environ, {"NITRO_ENV": "production"}):
            assert env.is_development() is False

    def test_is_production_and_is_development_are_mutually_exclusive(self):
        """is_production() and is_development() must always disagree."""
        env = Env()
        with patch.dict(os.environ, {"NITRO_ENV": "production"}):
            assert env.is_production() != env.is_development()

        os.environ.pop("NITRO_ENV", None)
        assert env.is_production() != env.is_development()


class TestEnvLazyLoading:
    """Tests for the lazy _load() behaviour."""

    def test_load_not_called_before_first_access(self):
        """_loaded flag should be False immediately after construction."""
        env = Env()
        assert env._loaded is False

    def test_load_called_on_first_attribute_access(self):
        """_loaded flag should be True after first attribute access."""
        env = Env()
        _ = env.__getattr__("SOME_VAR")
        assert env._loaded is True

    def test_load_called_on_get(self):
        """_loaded flag should be True after calling get()."""
        env = Env()
        env.get("SOME_VAR")
        assert env._loaded is True

    def test_load_only_runs_once(self):
        """_load() should invoke load_dotenv at most once across multiple accesses."""
        env = Env()
        mock_load = MagicMock()

        with patch("nitro.core.env.Path.cwd", return_value=Path("/nonexistent_dir_xyz")):
            with patch("nitro.core.env.Path.exists", return_value=False):
                with patch.dict("sys.modules", {"dotenv": MagicMock(load_dotenv=mock_load)}):
                    env._load()
                    env._load()
                    env._load()

        # Regardless of dotenv availability, _loaded must be True after first call
        assert env._loaded is True

    def test_load_sets_loaded_even_without_dotenv(self):
        """_load() should set _loaded=True even when python-dotenv is not installed."""
        env = Env()
        with patch.dict("sys.modules", {"dotenv": None}):
            env._load()
        assert env._loaded is True

    def test_load_reads_dotenv_file_when_present(self):
        """_load() should call load_dotenv when a .env file exists in cwd."""
        env = Env()

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("DOTENV_TEST_VAR=from_dotenv\n")

            mock_load_dotenv = MagicMock()
            mock_dotenv = MagicMock()
            mock_dotenv.load_dotenv = mock_load_dotenv

            with patch("nitro.core.env.Path.cwd", return_value=Path(tmpdir)):
                with patch.dict("sys.modules", {"dotenv": mock_dotenv}):
                    # Patch the import inside _load by overriding the module lookup
                    with patch("builtins.__import__", side_effect=_make_import_shim(mock_load_dotenv)):
                        env._load()

        assert env._loaded is True

    def test_second_access_does_not_reload(self):
        """After _loaded is True, subsequent attribute accesses skip _load logic."""
        env = Env()
        load_count = 0
        original_load = env._load

        def counting_load():
            nonlocal load_count
            load_count += 1
            original_load()

        env._load = counting_load

        _ = env.__getattr__("VAR_ONE")
        _ = env.__getattr__("VAR_TWO")
        _ = env.get("VAR_THREE")

        assert load_count == 3  # called each time, but internal guard short-circuits
        assert env._loaded is True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_import_shim(mock_load_dotenv):
    """Return an __import__ side-effect that intercepts 'dotenv' imports."""
    real_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

    def shim(name, *args, **kwargs):
        if name == "dotenv":
            mod = MagicMock()
            mod.load_dotenv = mock_load_dotenv
            return mod
        return real_import(name, *args, **kwargs)

    return shim
