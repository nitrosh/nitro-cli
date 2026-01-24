"""Tests for core/page.py."""

import pytest
from pathlib import Path
import tempfile
import os

from nitro.core.page import Page, get_project_root


class TestPage:
    """Tests for Page class."""

    def test_required_attributes(self):
        """Page should store title and content."""
        page = Page(title="Test Title", content="<h1>Hello</h1>")

        assert page.title == "Test Title"
        assert page.content == "<h1>Hello</h1>"

    def test_default_meta(self):
        """Meta should default to empty dict."""
        page = Page(title="Test", content="content")

        assert page.meta == {}

    def test_custom_meta(self):
        """Page should accept custom meta."""
        page = Page(
            title="Test",
            content="content",
            meta={"description": "A test page", "author": "Tester"},
        )

        assert page.meta["description"] == "A test page"
        assert page.meta["author"] == "Tester"

    def test_template_attribute(self):
        """Page should support optional template."""
        page = Page(title="Test", content="content", template="blog")

        assert page.template == "blog"

    def test_template_defaults_none(self):
        """Template should default to None."""
        page = Page(title="Test", content="content")

        assert page.template is None


class TestGetProjectRoot:
    """Tests for get_project_root function."""

    def test_returns_none_when_no_config(self):
        """Should return None when not in a Nitro project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = get_project_root()
                assert result is None
            finally:
                os.chdir(original_cwd)

    def test_finds_project_root(self):
        """Should find project root with nitro.config.py."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nitro.config.py
            config_path = Path(tmpdir) / "nitro.config.py"
            config_path.write_text("# config")

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = get_project_root()
                assert result == Path(tmpdir)
            finally:
                os.chdir(original_cwd)

    def test_finds_project_root_from_subdirectory(self):
        """Should find project root from nested subdirectory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nitro.config.py at root
            config_path = Path(tmpdir) / "nitro.config.py"
            config_path.write_text("# config")

            # Create nested subdirectory
            subdir = Path(tmpdir) / "src" / "pages" / "blog"
            subdir.mkdir(parents=True)

            original_cwd = os.getcwd()
            try:
                os.chdir(subdir)
                result = get_project_root()
                assert result == Path(tmpdir)
            finally:
                os.chdir(original_cwd)
