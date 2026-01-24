"""Tests for core/bundler.py."""

import pytest
from pathlib import Path
import tempfile
import json

from nitro.core.bundler import Bundler


class TestBundlerInit:
    """Tests for Bundler initialization."""

    def test_stores_build_dir(self):
        """Bundler should store build directory."""
        build_dir = Path("/project/build")
        bundler = Bundler(build_dir)

        assert bundler.build_dir == build_dir

    def test_initializes_empty_manifest(self):
        """Bundler should start with empty manifest."""
        bundler = Bundler(Path("/project/build"))

        assert bundler.manifest == {}


class TestOptimizeCss:
    """Tests for optimize_css method."""

    def test_returns_zero_when_no_css(self):
        """Should return 0 when no CSS files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_dir = Path(tmpdir)
            bundler = Bundler(build_dir)

            count = bundler.optimize_css()

            assert count == 0

    def test_optimizes_css_files(self):
        """Should optimize CSS files when present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_dir = Path(tmpdir)

            # Create a CSS file with whitespace
            css_file = build_dir / "styles.css"
            css_file.write_text("body {   color: red;   }")

            bundler = Bundler(build_dir)
            count = bundler.optimize_css()

            assert count == 1
            # Minified CSS should be smaller
            assert len(css_file.read_text()) <= len("body {   color: red;   }")

    def test_handles_multiple_css_files(self):
        """Should optimize multiple CSS files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_dir = Path(tmpdir)

            # Create multiple CSS files
            (build_dir / "a.css").write_text("a { color: blue; }")
            (build_dir / "b.css").write_text("b { color: green; }")

            bundler = Bundler(build_dir)
            count = bundler.optimize_css()

            assert count == 2


class TestOptimizeImages:
    """Tests for optimize_images method."""

    def test_returns_zero_when_no_images(self):
        """Should return 0 when no image files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_dir = Path(tmpdir)
            bundler = Bundler(build_dir)

            count = bundler.optimize_images()

            assert count == 0

    def test_optimizes_png_image(self):
        """Should optimize PNG images."""
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmpdir:
            build_dir = Path(tmpdir)

            # Create a simple PNG image
            img_path = build_dir / "test.png"
            img = Image.new("RGB", (100, 100), color="red")
            img.save(img_path)

            original_size = img_path.stat().st_size

            bundler = Bundler(build_dir)
            count = bundler.optimize_images()

            assert count == 1

    def test_optimizes_jpeg_image(self):
        """Should optimize JPEG images."""
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmpdir:
            build_dir = Path(tmpdir)

            # Create a simple JPEG image
            img_path = build_dir / "test.jpg"
            img = Image.new("RGB", (100, 100), color="blue")
            img.save(img_path)

            bundler = Bundler(build_dir)
            count = bundler.optimize_images()

            assert count == 1


class TestGenerateSitemap:
    """Tests for generate_sitemap method."""

    def test_generates_valid_sitemap(self):
        """Should generate valid sitemap XML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_dir = Path(tmpdir)

            # Create HTML files
            (build_dir / "index.html").write_text("<html></html>")
            (build_dir / "about.html").write_text("<html></html>")

            html_files = list(build_dir.glob("*.html"))
            output_path = build_dir / "sitemap.xml"

            bundler = Bundler(build_dir)
            bundler.generate_sitemap("https://example.com", html_files, output_path)

            assert output_path.exists()
            content = output_path.read_text()

            assert '<?xml version="1.0" encoding="UTF-8"?>' in content
            assert "<urlset" in content
            assert "<url>" in content
            assert "<loc>https://example.com/</loc>" in content
            assert "<loc>https://example.com/about.html</loc>" in content

    def test_index_has_higher_priority(self):
        """Index page should have priority 1.0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_dir = Path(tmpdir)
            (build_dir / "index.html").write_text("<html></html>")

            html_files = list(build_dir.glob("*.html"))
            output_path = build_dir / "sitemap.xml"

            bundler = Bundler(build_dir)
            bundler.generate_sitemap("https://example.com", html_files, output_path)

            content = output_path.read_text()
            # Index entry should have 1.0 priority
            assert "<priority>1.0</priority>" in content


class TestGenerateRobotsTxt:
    """Tests for generate_robots_txt method."""

    def test_generates_robots_txt(self):
        """Should generate valid robots.txt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_dir = Path(tmpdir)
            output_path = build_dir / "robots.txt"

            bundler = Bundler(build_dir)
            bundler.generate_robots_txt("https://example.com", output_path)

            assert output_path.exists()
            content = output_path.read_text()

            assert "User-agent: *" in content
            assert "Allow: /" in content
            assert "Sitemap: https://example.com/sitemap.xml" in content


class TestCreateAssetManifest:
    """Tests for create_asset_manifest method."""

    def test_creates_manifest(self):
        """Should create asset manifest with file hashes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_dir = Path(tmpdir)

            # Create some files
            (build_dir / "index.html").write_text("<html></html>")
            (build_dir / "style.css").write_text("body { }")

            output_path = build_dir / "manifest.json"

            bundler = Bundler(build_dir)
            bundler.create_asset_manifest(output_path)

            assert output_path.exists()
            manifest = json.loads(output_path.read_text())

            assert "index.html" in manifest
            assert "style.css" in manifest
            assert "hash" in manifest["index.html"]
            assert "size" in manifest["index.html"]


class TestFingerprintAssets:
    """Tests for fingerprint_assets method."""

    def test_returns_empty_when_no_assets(self):
        """Should return empty dict when no CSS/JS files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_dir = Path(tmpdir)
            bundler = Bundler(build_dir)

            result = bundler.fingerprint_assets()

            assert result == {}

    def test_fingerprints_css_file(self):
        """Should add hash to CSS filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_dir = Path(tmpdir)

            # Create a CSS file
            css_content = "body { color: red; }"
            (build_dir / "style.css").write_text(css_content)

            bundler = Bundler(build_dir)
            mapping = bundler.fingerprint_assets()

            assert "style.css" in mapping
            # New filename should have hash
            new_name = mapping["style.css"]
            assert new_name.startswith("style.")
            assert new_name.endswith(".css")
            assert len(new_name) > len("style.css")

    def test_updates_html_references(self):
        """Should update references in HTML files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_dir = Path(tmpdir)

            # Create CSS and HTML files
            css_content = "body { color: red; }"
            (build_dir / "style.css").write_text(css_content)
            (build_dir / "index.html").write_text(
                '<link href="style.css" rel="stylesheet">'
            )

            bundler = Bundler(build_dir)
            mapping = bundler.fingerprint_assets()

            # HTML should be updated with new CSS filename
            html_content = (build_dir / "index.html").read_text()
            new_css_name = Path(mapping["style.css"]).name
            assert new_css_name in html_content


class TestCalculateBuildSize:
    """Tests for calculate_build_size method."""

    def test_empty_build(self):
        """Should return zeros for empty build."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_dir = Path(tmpdir)
            bundler = Bundler(build_dir)

            result = bundler.calculate_build_size()

            assert result["total"] == 0
            assert result["count"] == 0

    def test_counts_files_correctly(self):
        """Should count files and sizes correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_dir = Path(tmpdir)

            # Create files
            html_content = "<html>test</html>"
            css_content = "body { color: red; }"
            (build_dir / "index.html").write_text(html_content)
            (build_dir / "style.css").write_text(css_content)

            bundler = Bundler(build_dir)
            result = bundler.calculate_build_size()

            assert result["count"] == 2
            assert result["total"] == len(html_content) + len(css_content)
            assert result["types"]["html"] == len(html_content)
            assert result["types"]["css"] == len(css_content)

    def test_categorizes_file_types(self):
        """Should categorize files by type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_dir = Path(tmpdir)

            (build_dir / "index.html").write_text("<html></html>")
            (build_dir / "style.css").write_text("a{}")
            (build_dir / "app.js").write_text("x=1")
            (build_dir / "data.json").write_text("{}")

            bundler = Bundler(build_dir)
            result = bundler.calculate_build_size()

            assert result["types"]["html"] > 0
            assert result["types"]["css"] > 0
            assert result["types"]["js"] > 0
            assert result["types"]["other"] > 0
