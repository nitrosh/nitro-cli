"""Asset bundler and optimizer for production builds."""

from typing import List, Dict, Optional
from pathlib import Path
import hashlib
import re

from ..utils import success, warning, error


class Bundler:
    """Handles asset optimization and bundling."""

    def __init__(self, build_dir: Path):
        self.build_dir = build_dir
        self.manifest: Dict[str, str] = {}

    def optimize_css(self, minify: bool = True) -> int:
        """Optimize CSS files. Returns number of files optimized."""
        css_files = list(self.build_dir.rglob("*.css"))
        if not css_files:
            return 0

        count = 0
        csscompressor_available = True

        for css_file in css_files:
            try:
                if minify and csscompressor_available:
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
                        csscompressor_available = False
                    except (IOError, OSError) as e:
                        error(f"Error writing {css_file.name}: {e}")
            except Exception as e:
                error(f"Error optimizing {css_file.name}: {e}")

        if count > 0:
            success(f"Optimized {count} CSS file(s)")

        return count

    def optimize_images(self, quality: int = 85) -> int:
        """Optimize image files. Returns number of files optimized."""
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
                        if (
                            img_file.suffix.lower() in {".jpg", ".jpeg"}
                            and img.mode == "RGBA"
                        ):
                            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                            rgb_img.paste(img, mask=img.split()[3])
                            img = rgb_img

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
        self,
        base_url: str,
        html_files: List[Path],
        output_path: Path,
        page_metadata: Optional[Dict[str, Dict]] = None,
    ) -> None:
        """Generate sitemap.xml.

        Args:
            base_url: Site base URL
            html_files: List of HTML file paths
            output_path: Path to write sitemap.xml
            page_metadata: Optional dict of page metadata for enhanced sitemap
                Keys are relative paths, values can include:
                - sitemap: False to exclude from sitemap
                - lastmod or published: Date string for lastmod
                - sitemap_priority: Priority value (0.0-1.0)
                - sitemap_changefreq: Change frequency
        """
        from datetime import datetime

        page_metadata = page_metadata or {}

        urls = []
        for html_file in html_files:
            rel_path = html_file.relative_to(self.build_dir)
            rel_path_str = str(rel_path).replace("\\", "/")

            # Get metadata for this page
            meta = page_metadata.get(rel_path_str, {})

            # Check if page should be excluded from sitemap
            if meta.get("sitemap") is False:
                continue

            # Skip draft pages
            if meta.get("draft"):
                continue

            url_path = rel_path_str
            if url_path == "index.html":
                url_path = ""
            elif url_path.endswith("/index.html"):
                url_path = url_path[:-11]

            full_url = f"{base_url.rstrip('/')}/{url_path}"

            # Determine lastmod from metadata or file mtime
            if meta.get("lastmod"):
                lastmod = meta["lastmod"]
            elif meta.get("published"):
                lastmod = meta["published"]
            else:
                mtime = datetime.fromtimestamp(html_file.stat().st_mtime)
                lastmod = mtime.strftime("%Y-%m-%d")

            # Determine priority from metadata or defaults
            if meta.get("sitemap_priority"):
                priority = str(meta["sitemap_priority"])
            else:
                priority = "1.0" if url_path == "" else "0.8"

            # Determine changefreq from metadata or default
            changefreq = meta.get("sitemap_changefreq", "weekly")

            urls.append(
                {
                    "loc": full_url,
                    "lastmod": lastmod,
                    "changefreq": changefreq,
                    "priority": priority,
                }
            )

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

        try:
            output_path.write_text("\n".join(xml_lines))
            success(f"Generated sitemap with {len(urls)} URL(s)")
        except (IOError, OSError) as e:
            error(f"Failed to write sitemap: {e}")

    def generate_robots_txt(self, base_url: str, output_path: Path) -> None:
        """Generate robots.txt."""
        sitemap_url = f"{base_url.rstrip('/')}/sitemap.xml"
        robots_content = f"""User-agent: *
Allow: /

Sitemap: {sitemap_url}
"""
        try:
            output_path.write_text(robots_content)
            success("Generated robots.txt")
        except (IOError, OSError) as e:
            error(f"Failed to write robots.txt: {e}")

    def create_asset_manifest(self, output_path: Path) -> None:
        """Create asset manifest with file hashes."""
        manifest = {}

        for file_path in self.build_dir.rglob("*"):
            if file_path.is_file():
                hasher = hashlib.md5()
                hasher.update(file_path.read_bytes())
                file_hash = hasher.hexdigest()[:8]
                rel_path = str(file_path.relative_to(self.build_dir))

                manifest[rel_path] = {
                    "hash": file_hash,
                    "size": file_path.stat().st_size,
                }

        import json

        try:
            output_path.write_text(json.dumps(manifest, indent=2))
            success(f"Created asset manifest with {len(manifest)} file(s)")
        except (IOError, OSError) as e:
            error(f"Failed to write asset manifest: {e}")

    def fingerprint_assets(self) -> Dict[str, str]:
        """Add content hashes to CSS and JS filenames for cache busting."""
        asset_files = []
        for pattern in ["*.css", "*.js"]:
            asset_files.extend(self.build_dir.rglob(pattern))

        if not asset_files:
            return {}

        path_mapping = {}

        for asset_path in asset_files:
            content = asset_path.read_bytes()
            hasher = hashlib.md5()
            hasher.update(content)
            content_hash = hasher.hexdigest()[:8]

            stem = asset_path.stem
            suffix = asset_path.suffix
            new_name = f"{stem}.{content_hash}{suffix}"
            new_path = asset_path.parent / new_name

            old_rel = str(asset_path.relative_to(self.build_dir))
            new_rel = str(new_path.relative_to(self.build_dir))
            path_mapping[old_rel] = new_rel

            asset_path.rename(new_path)

        if path_mapping:
            html_files = list(self.build_dir.rglob("*.html"))

            for html_path in html_files:
                content = html_path.read_text()
                modified = False

                for old_path, new_path in path_mapping.items():
                    old_filename = Path(old_path).name
                    new_filename = Path(new_path).name

                    # Use regex to match href/src with optional quotes and optional leading slash
                    # This handles quoted, unquoted, and minified HTML attributes
                    for path_variant in [old_path, old_filename]:
                        # Pattern matches: href="path", href='path', href=/path, href=path
                        # Captures the attribute name (href or src) and replaces with quoted new path
                        pattern = (
                            r'((?:href|src)=)["\']?(/?'
                            + re.escape(path_variant)
                            + r')["\']?(?=[\s>])'
                        )
                        replacement = r'\1"/' + new_path + '"'
                        new_content = re.sub(pattern, replacement, content)
                        if new_content != content:
                            content = new_content
                            modified = True

                if modified:
                    html_path.write_text(content)

            success(f"Fingerprinted {len(path_mapping)} asset(s)")

        return path_mapping

    def calculate_build_size(self) -> Dict[str, int]:
        """Calculate total build size."""
        total_size = 0
        file_count = 0
        type_sizes = {"html": 0, "css": 0, "js": 0, "images": 0, "other": 0}

        for file_path in self.build_dir.rglob("*"):
            if file_path.is_file():
                size = file_path.stat().st_size
                total_size += size
                file_count += 1

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
