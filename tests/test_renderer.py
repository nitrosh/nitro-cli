"""Tests for core/renderer.py."""

import pytest
from pathlib import Path
import tempfile
import os

from nitro.core.renderer import Renderer
from nitro.core.config import Config
from nitro.core.page import Page


class MockElement:
    """Mock element with render method."""

    def __init__(self, html: str):
        self._html = html

    def render(self) -> str:
        return self._html


class TestRendererInit:
    """Tests for Renderer initialization."""

    def test_default_config(self):
        """Renderer should use config defaults."""
        config = Config()
        renderer = Renderer(config)

        assert renderer.pretty_print is False
        assert renderer.minify_html is False

    def test_custom_config(self):
        """Renderer should respect custom config values."""
        config = Config(renderer={"pretty_print": True, "minify_html": True})
        renderer = Renderer(config)

        assert renderer.pretty_print is True
        assert renderer.minify_html is True


class TestIsDynamicRoute:
    """Tests for is_dynamic_route method."""

    def test_static_page(self):
        """Regular pages should not be dynamic."""
        config = Config()
        renderer = Renderer(config)

        assert renderer.is_dynamic_route(Path("index.py")) is False
        assert renderer.is_dynamic_route(Path("about.py")) is False
        assert renderer.is_dynamic_route(Path("blog/post.py")) is False

    def test_dynamic_page(self):
        """Pages with [param] pattern should be dynamic."""
        config = Config()
        renderer = Renderer(config)

        assert renderer.is_dynamic_route(Path("[slug].py")) is True
        assert renderer.is_dynamic_route(Path("[id].py")) is True
        assert renderer.is_dynamic_route(Path("blog/[slug].py")) is True

    def test_edge_cases(self):
        """Edge cases for dynamic route detection."""
        config = Config()
        renderer = Renderer(config)

        # Partial brackets should not be dynamic
        assert renderer.is_dynamic_route(Path("[incomplete.py")) is False
        assert renderer.is_dynamic_route(Path("incomplete].py")) is False


class TestGetDynamicOutputName:
    """Tests for _get_dynamic_output_name method."""

    def test_dict_params(self):
        """Should replace param placeholders with dict values."""
        config = Config()
        renderer = Renderer(config)

        result = renderer._get_dynamic_output_name(
            Path("[slug].py"), {"slug": "my-post"}
        )
        assert result == "my-post.html"

    def test_multiple_params(self):
        """Should handle multiple params in filename."""
        config = Config()
        renderer = Renderer(config)

        result = renderer._get_dynamic_output_name(
            Path("[year]-[month].py"), {"year": "2024", "month": "01"}
        )
        assert result == "2024-01.html"

    def test_simple_param(self):
        """Should handle simple non-dict params."""
        config = Config()
        renderer = Renderer(config)

        result = renderer._get_dynamic_output_name(Path("[id].py"), "123")
        assert result == "123.html"


class TestGetOutputPath:
    """Tests for get_output_path method."""

    def test_root_page(self):
        """Should output root pages to build directory."""
        config = Config()
        renderer = Renderer(config)

        source_dir = Path("/project/src")
        build_dir = Path("/project/build")
        page_path = Path("/project/src/pages/index.py")

        result = renderer.get_output_path(page_path, source_dir, build_dir)
        assert result == Path("/project/build/index.html")

    def test_nested_page(self):
        """Should preserve directory structure for nested pages."""
        config = Config()
        renderer = Renderer(config)

        source_dir = Path("/project/src")
        build_dir = Path("/project/build")
        page_path = Path("/project/src/pages/blog/post.py")

        result = renderer.get_output_path(page_path, source_dir, build_dir)
        assert result == Path("/project/build/blog/post.html")

    def test_deeply_nested_page(self):
        """Should handle deeply nested pages."""
        config = Config()
        renderer = Renderer(config)

        source_dir = Path("/project/src")
        build_dir = Path("/project/build")
        page_path = Path("/project/src/pages/docs/api/v1/endpoint.py")

        result = renderer.get_output_path(page_path, source_dir, build_dir)
        assert result == Path("/project/build/docs/api/v1/endpoint.html")


class TestRenderPageObject:
    """Tests for _render_page_object method."""

    def test_page_with_element_content(self):
        """Should call render() on content with render method."""
        config = Config()
        renderer = Renderer(config)

        element = MockElement("<h1>Hello</h1>")
        page = Page(title="Test", content=element)

        result = renderer._render_page_object(page)
        assert result == "<h1>Hello</h1>"

    def test_page_with_string_content(self):
        """Should convert string content directly."""
        config = Config()
        renderer = Renderer(config)

        page = Page(title="Test", content="<p>Plain text</p>")

        result = renderer._render_page_object(page)
        assert result == "<p>Plain text</p>"


class TestRenderElement:
    """Tests for _render_element method."""

    def test_element_with_render(self):
        """Should call render() on elements."""
        config = Config()
        renderer = Renderer(config)

        element = MockElement("<div>Content</div>")

        result = renderer._render_element(element)
        assert result == "<div>Content</div>"

    def test_element_without_render(self):
        """Should stringify elements without render method."""
        config = Config()
        renderer = Renderer(config)

        result = renderer._render_element("plain string")
        assert result == "plain string"


class TestSuggestNameFix:
    """Tests for _suggest_name_fix method."""

    def test_suggests_similar_name(self):
        """Should suggest similar nitro-ui names."""
        config = Config()
        renderer = Renderer(config)

        result = renderer._suggest_name_fix("name 'Dvi' is not defined")
        assert "Div" in result

    def test_suggests_page_fix(self):
        """Should suggest Page for common typo."""
        config = Config()
        renderer = Renderer(config)

        result = renderer._suggest_name_fix("name 'Pag' is not defined")
        assert "Page" in result

    def test_returns_generic_hint(self):
        """Should return generic hint for unknown names."""
        config = Config()
        renderer = Renderer(config)

        result = renderer._suggest_name_fix("name 'xyzabc' is not defined")
        assert "typos" in result.lower()


class TestPostProcess:
    """Tests for _post_process method."""

    def test_no_processing_by_default(self):
        """Should return HTML unchanged by default."""
        config = Config()
        renderer = Renderer(config)

        html = "<html>\n  <body>\n    <h1>Title</h1>\n  </body>\n</html>"
        result = renderer._post_process(html)
        assert result == html

    def test_minification(self):
        """Should minify when enabled."""
        config = Config(renderer={"minify_html": True})
        renderer = Renderer(config)

        html = "<html>  <body>  <h1>Title</h1>  </body>  </html>"
        result = renderer._post_process(html)

        # Minified HTML should have less whitespace
        assert len(result) <= len(html)
        assert "<h1>Title</h1>" in result


class TestRenderPage:
    """Tests for render_page method with actual page files."""

    def test_renders_simple_page(self):
        """Should render a simple page file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)

            # Create a simple page
            page_file = pages_dir / "test.py"
            page_file.write_text(
                """
from nitro.core.page import Page

def render():
    return Page(title="Test", content="<h1>Hello World</h1>")
"""
            )

            config = Config()
            renderer = Renderer(config)

            result = renderer.render_page(page_file, project_root)

            assert result is not None
            assert "<h1>Hello World</h1>" in result

    def test_renders_page_with_element(self):
        """Should render a page that returns an element."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)

            # Create a page with a mock element
            page_file = pages_dir / "element.py"
            page_file.write_text(
                """
class MockElement:
    def render(self):
        return "<div>Element content</div>"

def render():
    return MockElement()
"""
            )

            config = Config()
            renderer = Renderer(config)

            result = renderer.render_page(page_file, project_root)

            assert result is not None
            assert "<div>Element content</div>" in result

    def test_returns_none_for_missing_render(self):
        """Should return None when page lacks render function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)

            # Create a page without render function
            page_file = pages_dir / "bad.py"
            page_file.write_text("x = 1")

            config = Config()
            renderer = Renderer(config)

            result = renderer.render_page(page_file, project_root)

            assert result is None

    def test_returns_none_for_syntax_error(self):
        """Should return None for page with syntax error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)

            # Create a page with syntax error
            page_file = pages_dir / "syntax.py"
            page_file.write_text("def render( broken")

            config = Config()
            renderer = Renderer(config)

            result = renderer.render_page(page_file, project_root)

            assert result is None
