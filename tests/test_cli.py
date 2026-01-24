"""Tests for CLI entry point."""

import pytest
from click.testing import CliRunner
from pathlib import Path
import tempfile
import os

from nitro.cli import main, detect_project_context
from nitro import __version__


class TestMainGroup:
    """Tests for main CLI group."""

    def test_shows_welcome_without_command(self):
        """Should show welcome message when no command given."""
        runner = CliRunner()
        result = runner.invoke(main)

        assert result.exit_code == 0
        assert "Nitro" in result.output
        assert "Commands:" in result.output

    def test_shows_version(self):
        """Should display version with --version flag."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert __version__ in result.output

    def test_shows_help(self):
        """Should display help with --help flag."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Nitro:" in result.output
        assert "Options:" in result.output
        assert "Commands:" in result.output


class TestDetectProjectContext:
    """Tests for detect_project_context function."""

    def test_returns_none_outside_project(self):
        """Should return (None, None) outside a Nitro project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                project_root, project_name = detect_project_context()

                assert project_root is None
                assert project_name is None
            finally:
                os.chdir(original_cwd)

    def test_detects_project_root(self):
        """Should detect project root when inside a Nitro project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nitro.config.py
            config_path = Path(tmpdir) / "nitro.config.py"
            config_path.write_text("# config")

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                project_root, project_name = detect_project_context()

                assert project_root == Path(tmpdir)
                assert project_name == Path(tmpdir).name
            finally:
                os.chdir(original_cwd)


class TestNewCommand:
    """Tests for 'nitro new' command."""

    def test_new_requires_name(self):
        """Should require project name argument."""
        runner = CliRunner()
        result = runner.invoke(main, ["new"])

        assert result.exit_code != 0
        assert "Missing argument" in result.output

    def test_new_creates_project(self):
        """Should create a new project directory."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            with runner.isolated_filesystem(temp_dir=tmpdir):
                result = runner.invoke(
                    main, ["new", "test-project", "--no-git", "--no-install"]
                )

                assert result.exit_code == 0
                assert Path("test-project").exists()
                assert (Path("test-project") / "nitro.config.py").exists()
                assert (Path("test-project") / "src" / "pages").exists()


class TestBuildCommand:
    """Tests for 'nitro build' command."""

    def test_build_fails_without_pages(self):
        """Should fail when no pages exist."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["build"])

            assert result.exit_code != 0
            # Should mention build failure or no pages
            assert "Build Failed" in result.output or "No pages found" in result.output


class TestCleanCommand:
    """Tests for 'nitro clean' command."""

    def test_clean_removes_build_dir(self):
        """Should remove build directory when it exists."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            with runner.isolated_filesystem(temp_dir=tmpdir):
                # Create project structure
                Path("nitro.config.py").write_text(
                    "from nitro import Config\nconfig = Config()"
                )
                Path("src/pages").mkdir(parents=True)
                Path("build").mkdir()
                (Path("build") / "index.html").write_text("<html></html>")

                result = runner.invoke(main, ["clean"])

                assert result.exit_code == 0
                assert not Path("build").exists()


class TestInfoCommand:
    """Tests for 'nitro info' command."""

    def test_info_shows_project_details(self):
        """Should show project information."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            with runner.isolated_filesystem(temp_dir=tmpdir):
                # Create project structure
                config_content = """from nitro import Config
config = Config(site_name="Test Site", base_url="https://test.com")
"""
                Path("nitro.config.py").write_text(config_content)
                Path("src/pages").mkdir(parents=True)

                result = runner.invoke(main, ["info"])

                assert result.exit_code == 0
                assert "Test Site" in result.output


class TestCommandHelp:
    """Tests for command help output."""

    def test_new_help(self):
        """Should show help for new command."""
        runner = CliRunner()
        result = runner.invoke(main, ["new", "--help"])

        assert result.exit_code == 0
        assert "Create a new Nitro project" in result.output

    def test_build_help(self):
        """Should show help for build command."""
        runner = CliRunner()
        result = runner.invoke(main, ["build", "--help"])

        assert result.exit_code == 0
        assert "Build" in result.output

    def test_serve_help(self):
        """Should show help for serve command."""
        runner = CliRunner()
        result = runner.invoke(main, ["serve", "--help"])

        assert result.exit_code == 0
        assert "Start" in result.output

    def test_dev_help(self):
        """Should show help for dev command."""
        runner = CliRunner()
        result = runner.invoke(main, ["dev", "--help"])

        assert result.exit_code == 0
