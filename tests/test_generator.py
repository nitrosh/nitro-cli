"""Tests for core/generator.py."""

import pytest
from pathlib import Path
import tempfile
import os
import threading
from concurrent.futures import ThreadPoolExecutor

from nitro.core.generator import Generator
from nitro.core.config import Config


class TestGeneratorInit:
    """Tests for Generator initialization."""

    def test_default_initialization(self):
        """Generator should initialize with defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "src" / "pages").mkdir(parents=True)

            generator = Generator(project_root=project_root)

            assert generator.project_root == project_root
            assert generator.source_dir == project_root / "src"
            assert generator.build_dir == project_root / "build"

    def test_with_config_file(self):
        """Generator should load config from nitro.config.py."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "src" / "pages").mkdir(parents=True)

            # Create config file
            config_file = project_root / "nitro.config.py"
            config_file.write_text(
                """from nitro import Config
config = Config(site_name="Test Site", build_dir="dist")
"""
            )

            generator = Generator(project_root=project_root)

            assert generator.config.site_name == "Test Site"
            assert generator.build_dir == project_root / "dist"


class TestGenerateQuietMode:
    """Tests for generate() with quiet parameter."""

    def _create_test_project(self, tmpdir: Path) -> Path:
        """Helper to create a minimal test project."""
        project_root = tmpdir
        pages_dir = project_root / "src" / "pages"
        pages_dir.mkdir(parents=True)

        # Create a simple page
        page_file = pages_dir / "index.py"
        page_file.write_text(
            """
from nitro.core.page import Page

def render():
    return Page(title="Test", content="<h1>Hello</h1>")
"""
        )

        # Create config
        config_file = project_root / "nitro.config.py"
        config_file.write_text(
            """from nitro import Config
config = Config()
"""
        )

        return project_root

    def test_generate_with_quiet_true(self):
        """generate() should work with quiet=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = self._create_test_project(Path(tmpdir))

            generator = Generator(project_root=project_root, use_cache=False)
            result = generator.generate(verbose=False, quiet=True)

            assert result is True
            assert (project_root / "build" / "index.html").exists()

    def test_generate_with_quiet_false(self):
        """generate() should work with quiet=False (default)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = self._create_test_project(Path(tmpdir))

            generator = Generator(project_root=project_root, use_cache=False)
            result = generator.generate(verbose=False, quiet=False)

            assert result is True
            assert (project_root / "build" / "index.html").exists()

    def test_generate_quiet_default_is_false(self):
        """quiet parameter should default to False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = self._create_test_project(Path(tmpdir))

            generator = Generator(project_root=project_root, use_cache=False)
            # Call without quiet parameter - should use default (False)
            result = generator.generate(verbose=False)

            assert result is True

    def test_generate_quiet_in_thread(self):
        """generate(quiet=True) should work when called from a background thread."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = self._create_test_project(Path(tmpdir))

            generator = Generator(project_root=project_root, use_cache=False)

            # Simulate HMR scenario: run generate in a thread
            result_holder = {"result": None, "error": None}

            def run_generate():
                try:
                    result_holder["result"] = generator.generate(
                        verbose=False, quiet=True
                    )
                except Exception as e:
                    result_holder["error"] = e

            thread = threading.Thread(target=run_generate)
            thread.start()
            thread.join(timeout=10)

            assert (
                result_holder["error"] is None
            ), f"Error in thread: {result_holder['error']}"
            assert result_holder["result"] is True

    def test_generate_quiet_in_thread_pool(self):
        """generate(quiet=True) should work in ThreadPoolExecutor."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = self._create_test_project(Path(tmpdir))

            generator = Generator(project_root=project_root, use_cache=False)

            # Simulate asyncio.to_thread scenario
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(generator.generate, verbose=False, quiet=True)
                result = future.result(timeout=10)

            assert result is True
            assert (project_root / "build" / "index.html").exists()


class TestGeneratePagesHelpers:
    """Tests for _generate_pages_quiet and _generate_pages_with_progress."""

    def _create_multi_page_project(self, tmpdir: Path, num_pages: int = 5) -> Path:
        """Helper to create a project with multiple pages."""
        project_root = tmpdir
        pages_dir = project_root / "src" / "pages"
        pages_dir.mkdir(parents=True)

        # Create multiple pages
        for i in range(num_pages):
            page_file = pages_dir / f"page{i}.py"
            page_file.write_text(
                f"""
from nitro.core.page import Page

def render():
    return Page(title="Page {i}", content="<h1>Page {i}</h1>")
"""
            )

        # Create config
        config_file = project_root / "nitro.config.py"
        config_file.write_text(
            """from nitro import Config
config = Config()
"""
        )

        return project_root

    def test_generate_pages_quiet_sequential(self):
        """_generate_pages_quiet should work with sequential generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = self._create_multi_page_project(Path(tmpdir), num_pages=2)

            generator = Generator(project_root=project_root, use_cache=False)
            pages = generator._find_pages()

            # Force sequential (use_parallel=False)
            success_count, failed_pages = generator._generate_pages_quiet(
                pages, use_parallel=False, max_workers=1, verbose=False
            )

            assert success_count == 2
            assert len(failed_pages) == 0

    def test_generate_pages_quiet_parallel(self):
        """_generate_pages_quiet should work with parallel generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Need at least 4 pages for parallel mode to kick in
            project_root = self._create_multi_page_project(Path(tmpdir), num_pages=5)

            generator = Generator(project_root=project_root, use_cache=False)
            pages = generator._find_pages()

            success_count, failed_pages = generator._generate_pages_quiet(
                pages, use_parallel=True, max_workers=2, verbose=False
            )

            assert success_count == 5
            assert len(failed_pages) == 0

    def test_generate_pages_with_progress_sequential(self):
        """_generate_pages_with_progress should work with sequential generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = self._create_multi_page_project(Path(tmpdir), num_pages=2)

            generator = Generator(project_root=project_root, use_cache=False)
            pages = generator._find_pages()

            success_count, failed_pages = generator._generate_pages_with_progress(
                pages, use_parallel=False, max_workers=1, verbose=False
            )

            assert success_count == 2
            assert len(failed_pages) == 0

    def test_generate_pages_with_progress_parallel(self):
        """_generate_pages_with_progress should work with parallel generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = self._create_multi_page_project(Path(tmpdir), num_pages=5)

            generator = Generator(project_root=project_root, use_cache=False)
            pages = generator._find_pages()

            success_count, failed_pages = generator._generate_pages_with_progress(
                pages, use_parallel=True, max_workers=2, verbose=False
            )

            assert success_count == 5
            assert len(failed_pages) == 0


class TestRenderPageSequential:
    """Tests for _render_page_sequential method."""

    def test_renders_valid_page(self):
        """Should render a valid page and write output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)

            page_file = pages_dir / "test.py"
            page_file.write_text(
                """
from nitro.core.page import Page

def render():
    return Page(title="Test", content="<p>Content</p>")
"""
            )

            (project_root / "nitro.config.py").write_text(
                "from nitro import Config\nconfig = Config()"
            )

            generator = Generator(project_root=project_root, use_cache=False)
            generator.build_dir.mkdir(parents=True, exist_ok=True)

            result = generator._render_page_sequential(page_file, verbose=False)

            assert result is True
            assert (generator.build_dir / "test.html").exists()

    def test_returns_false_for_invalid_page(self):
        """Should return False for page without render function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)

            page_file = pages_dir / "bad.py"
            page_file.write_text("x = 1  # No render function")

            (project_root / "nitro.config.py").write_text(
                "from nitro import Config\nconfig = Config()"
            )

            generator = Generator(project_root=project_root, use_cache=False)
            generator.build_dir.mkdir(parents=True, exist_ok=True)

            result = generator._render_page_sequential(page_file, verbose=False)

            assert result is False


class TestGenerateNoPages:
    """Tests for generate() edge cases."""

    def test_generate_returns_false_without_pages(self):
        """generate() should return False when no pages exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "src" / "pages").mkdir(parents=True)

            (project_root / "nitro.config.py").write_text(
                "from nitro import Config\nconfig = Config()"
            )

            generator = Generator(project_root=project_root, use_cache=False)
            result = generator.generate(verbose=False, quiet=True)

            assert result is False


class TestErrorHandlingInQuietMode:
    """Tests for error handling during generation in quiet mode."""

    def test_syntax_error_handled_gracefully_in_thread(self):
        """Syntax errors should not crash when running in a background thread."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)

            # Create a page with syntax error
            page_file = pages_dir / "broken.py"
            page_file.write_text("def render( broken syntax")

            (project_root / "nitro.config.py").write_text(
                "from nitro import Config\nconfig = Config()"
            )

            generator = Generator(project_root=project_root, use_cache=False)

            # Run in background thread (like HMR does)
            result_holder = {"result": None, "error": None}

            def run_generate():
                try:
                    result_holder["result"] = generator.generate(
                        verbose=False, quiet=True
                    )
                except Exception as e:
                    result_holder["error"] = e

            thread = threading.Thread(target=run_generate)
            thread.start()
            thread.join(timeout=10)

            # Should not crash, should return True (generation completes but page fails)
            assert (
                result_holder["error"] is None
            ), f"Unexpected error: {result_holder['error']}"
            # Result is True because generation completes, even if page failed
            assert result_holder["result"] is True

    def test_name_error_handled_gracefully_in_thread(self):
        """NameError should not crash when running in a background thread."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)

            # Create a page with NameError
            page_file = pages_dir / "name_error.py"
            page_file.write_text(
                """
from nitro.core.page import Page

def render():
    return Page(title="Test", content=undefined_variable)
"""
            )

            (project_root / "nitro.config.py").write_text(
                "from nitro import Config\nconfig = Config()"
            )

            generator = Generator(project_root=project_root, use_cache=False)

            # Run in ThreadPoolExecutor (like asyncio.to_thread does)
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(generator.generate, verbose=False, quiet=True)
                result = future.result(timeout=10)

            # Should complete without raising
            assert result is True  # Generation completes, page is marked as failed

    def test_import_error_handled_gracefully_in_thread(self):
        """ImportError should not crash when running in a background thread."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)

            # Create a page with ImportError
            page_file = pages_dir / "import_error.py"
            page_file.write_text(
                """
from nonexistent_module import something

def render():
    return something()
"""
            )

            (project_root / "nitro.config.py").write_text(
                "from nitro import Config\nconfig = Config()"
            )

            generator = Generator(project_root=project_root, use_cache=False)

            result_holder = {"result": None, "error": None}

            def run_generate():
                try:
                    result_holder["result"] = generator.generate(
                        verbose=False, quiet=True
                    )
                except Exception as e:
                    result_holder["error"] = e

            thread = threading.Thread(target=run_generate)
            thread.start()
            thread.join(timeout=10)

            assert result_holder["error"] is None
            assert result_holder["result"] is True

    def test_mixed_valid_and_invalid_pages_in_thread(self):
        """Should handle mix of valid and invalid pages without crashing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)

            # Create valid page
            valid_page = pages_dir / "valid.py"
            valid_page.write_text(
                """
from nitro.core.page import Page

def render():
    return Page(title="Valid", content="<h1>Works</h1>")
"""
            )

            # Create invalid page
            invalid_page = pages_dir / "invalid.py"
            invalid_page.write_text("def render( broken")

            (project_root / "nitro.config.py").write_text(
                "from nitro import Config\nconfig = Config()"
            )

            generator = Generator(project_root=project_root, use_cache=False)

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(generator.generate, verbose=False, quiet=True)
                result = future.result(timeout=10)

            # Should complete
            assert result is True
            # Valid page should be generated
            assert (project_root / "build" / "valid.html").exists()
