"""Tests for core/config.py."""

import pytest
from pathlib import Path
import tempfile
import os

from nitro.core.config import Config, load_config


class TestConfig:
    """Tests for Config class."""

    def test_default_values(self):
        """Config should have sensible defaults."""
        config = Config()

        assert config.site_name == "My Site (built with nitro.sh)"
        assert config.base_url == "http://localhost:8008"
        assert config.build_dir == Path("build")
        assert config.source_dir == Path("src")
        assert config.renderer["pretty_print"] is False
        assert config.renderer["minify_html"] is False
        assert config.plugins == []

    def test_custom_values(self):
        """Config should accept custom values."""
        config = Config(
            site_name="Test Site",
            base_url="https://example.com",
            build_dir="dist",
            source_dir="source",
            renderer={"minify_html": True},
            plugins=["plugin1", "plugin2"],
        )

        assert config.site_name == "Test Site"
        assert config.base_url == "https://example.com"
        assert config.build_dir == Path("dist")
        assert config.source_dir == Path("source")
        assert config.renderer["minify_html"] is True
        assert config.plugins == ["plugin1", "plugin2"]

    def test_renderer_merges_defaults(self):
        """Renderer options should merge with defaults."""
        config = Config(renderer={"minify_html": True})

        assert config.renderer["minify_html"] is True
        assert config.renderer["pretty_print"] is False


class TestLoadConfig:
    """Tests for load_config function."""

    def test_returns_default_when_no_file(self):
        """Should return default config when file doesn't exist."""
        config = load_config(Path("/nonexistent/nitro.config.py"))

        assert isinstance(config, Config)
        assert config.site_name == "My Site (built with nitro.sh)"

    def test_loads_config_from_file(self):
        """Should load config from Python file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nitro.config.py"
            config_path.write_text(
                """
from nitro import Config

config = Config(
    site_name="Loaded Site",
    base_url="https://loaded.com",
)
"""
            )
            loaded = load_config(config_path)

            assert loaded.site_name == "Loaded Site"
            assert loaded.base_url == "https://loaded.com"

    def test_raises_on_syntax_error(self):
        """Should raise SyntaxError for invalid Python."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nitro.config.py"
            config_path.write_text("this is not valid python {{{{")

            with pytest.raises(SyntaxError):
                load_config(config_path)

    def test_raises_on_invalid_config_type(self):
        """Should raise ValueError if config is not a Config object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nitro.config.py"
            config_path.write_text('config = "not a config object"')

            with pytest.raises(ValueError, match="must be a Config object"):
                load_config(config_path)

    def test_returns_default_when_no_config_variable(self):
        """Should return default config when file has no config variable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nitro.config.py"
            config_path.write_text("# Empty config file\nx = 1")

            config = load_config(config_path)

            assert isinstance(config, Config)
            assert config.site_name == "My Site (built with nitro.sh)"
