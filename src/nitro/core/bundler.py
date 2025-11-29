"""Asset bundler and optimizer for production builds."""

from typing import List, Dict
from pathlib import Path
import hashlib

from ..utils import success, warning, error


class Bundler:
    """Handles asset optimization and bundling."""

    def __init__(self, build_dir: Path):
        """Initialize bundler.

        Args:
            build_dir: Build output directory
        """
        self.build_dir = build_dir
        self.manifest: Dict[str, str] = {}

    def optimize_css(self, minify: bool = True) -> int:
        """Optimize CSS files.

        Args:
            minify: Enable CSS minification

        Returns:
            Number of files optimized
        """
        css_files = list(self.build_dir.rglob("*.css"))

        if not css_files:
            return 0

        count = 0
        for css_file in css_files:
            try:
                if minify:
                    # Minify CSS
                    try:
                        import csscompressor

                        content = css_file.read_text()
                        minified = csscompressor.compress(content)
                        css_file.write_text(minified)
                        count += 1
                    except ImportError:
                        warning(
                            "csscompressor not installed, skipping CSS minification"
                        )
                        break
            except Exception as e:
                error(f"Error optimizing {css_file.name}: {e}")

        if count > 0:
            success(f"Optimized {count} CSS file(s)")

        return count

    def optimize_images(self, quality: int = 85) -> int:
        """Optimize image files.

        Args:
            quality: JPEG quality (1-100)

        Returns:
            Number of files optimized
        """
        image_extensions = {".jpg", ".jpeg", ".png"}
        image_files = [
            f for f in self.build_dir.rglob("*") if f.suffix.lower() in image_extensions
        ]

        if not image_files:
            return 0

        count = 0
        try:
            from PIL import Image

            for img_file in image_files:
                try:
                    with Image.open(img_file) as img:
                        # Convert RGBA to RGB for JPEG
                        if (
                            img_file.suffix.lower() in {".jpg", ".jpeg"}
                            and img.mode == "RGBA"
                        ):
                            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                            rgb_img.paste(img, mask=img.split()[3])
                            img = rgb_img

                        # Save optimized image
                        save_kwargs = {"optimize": True}
                        if img_file.suffix.lower() in {".jpg", ".jpeg"}:
                            save_kwargs["quality"] = quality
                            save_kwargs["progressive"] = True

                        img.save(img_file, **save_kwargs)
                        count += 1

                except Exception as e:
                    error(f"Error optimizing {img_file.name}: {e}")

        except ImportError:
            warning("Pillow not installed, skipping image optimization")
            return 0

        if count > 0:
            success(f"Optimized {count} image(s)")

        return count

    def generate_sitemap(
        self, base_url: str, html_files: List[Path], output_path: Path
    ) -> None:
        """Generate sitemap.xml.

        Args:
            base_url: Base URL of the site
            html_files: List of HTML files
            output_path: Output path for sitemap
        """
        from datetime import datetime

        # Build sitemap XML
        urls = []
        for html_file in html_files:
            # Get relative path from build dir
            rel_path = html_file.relative_to(self.build_dir)

            # Convert to URL
            url_path = str(rel_path).replace("\\", "/")
            if url_path == "index.html":
                url_path = ""
            elif url_path.endswith("/index.html"):
                url_path = url_path[:-11]  # Remove /index.html

            full_url = f"{base_url.rstrip('/')}/{url_path}"

            # Get last modified time
            mtime = datetime.fromtimestamp(html_file.stat().st_mtime)
            lastmod = mtime.strftime("%Y-%m-%d")

            urls.append(
                {
                    "loc": full_url,
                    "lastmod": lastmod,
                    "changefreq": "weekly",
                    "priority": "1.0" if url_path == "" else "0.8",
                }
            )

        # Generate XML
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]

        for url in urls:
            xml_lines.append("  <url>")
            xml_lines.append(f"    <loc>{url['loc']}</loc>")
            xml_lines.append(f"    <lastmod>{url['lastmod']}</lastmod>")
            xml_lines.append(f"    <changefreq>{url['changefreq']}</changefreq>")
            xml_lines.append(f"    <priority>{url['priority']}</priority>")
            xml_lines.append("  </url>")

        xml_lines.append("</urlset>")

        # Write sitemap
        output_path.write_text("\n".join(xml_lines))
        success(f"Generated sitemap with {len(urls)} URL(s)")

    def generate_robots_txt(self, base_url: str, output_path: Path) -> None:
        """Generate robots.txt.

        Args:
            base_url: Base URL of the site
            output_path: Output path for robots.txt
        """
        sitemap_url = f"{base_url.rstrip('/')}/sitemap.xml"

        robots_content = f"""User-agent: *
Allow: /

Sitemap: {sitemap_url}
"""

        output_path.write_text(robots_content)
        success("Generated robots.txt")

    def create_asset_manifest(self, output_path: Path) -> None:
        """Create asset manifest with file hashes.

        Args:
            output_path: Output path for manifest
        """
        manifest = {}

        # Hash all files in build directory
        for file_path in self.build_dir.rglob("*"):
            if file_path.is_file():
                # Calculate hash
                hasher = hashlib.md5()
                hasher.update(file_path.read_bytes())
                file_hash = hasher.hexdigest()[:8]

                # Get relative path
                rel_path = str(file_path.relative_to(self.build_dir))

                manifest[rel_path] = {
                    "hash": file_hash,
                    "size": file_path.stat().st_size,
                }

        # Write manifest
        import json

        output_path.write_text(json.dumps(manifest, indent=2))
        success(f"Created asset manifest with {len(manifest)} file(s)")

    def calculate_build_size(self) -> Dict[str, int]:
        """Calculate total build size.

        Returns:
            Dictionary with size statistics
        """
        total_size = 0
        file_count = 0
        type_sizes = {"html": 0, "css": 0, "js": 0, "images": 0, "other": 0}

        for file_path in self.build_dir.rglob("*"):
            if file_path.is_file():
                size = file_path.stat().st_size
                total_size += size
                file_count += 1

                # Categorize by type
                suffix = file_path.suffix.lower()
                if suffix == ".html":
                    type_sizes["html"] += size
                elif suffix == ".css":
                    type_sizes["css"] += size
                elif suffix == ".js":
                    type_sizes["js"] += size
                elif suffix in {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp"}:
                    type_sizes["images"] += size
                else:
                    type_sizes["other"] += size

        return {"total": total_size, "count": file_count, "types": type_sizes}

    @staticmethod
    def format_size(size: int) -> str:
        """Format size in bytes to human-readable string.

        Args:
            size: Size in bytes

        Returns:
            Formatted string (e.g., "1.5 KB")
        """
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
