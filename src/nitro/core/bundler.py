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

    def generate_rss_feed(
        self,
        items: List[Dict],
        base_url: str,
        output_path: Path,
        title: str = "Site Feed",
        description: str = "Latest updates",
        language: str = "en-us",
    ) -> None:
        """Generate an RSS 2.0 feed.

        Args:
            items: List of feed items with keys: title, link, description, pubDate, guid
            base_url: Base URL of the site
            output_path: Output path for feed
            title: Feed title
            description: Feed description
            language: Feed language
        """
        from datetime import datetime
        import html

        # RFC 822 date format for RSS
        def format_rss_date(dt):
            if isinstance(dt, datetime):
                return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
            return dt

        # Build RSS XML
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
            "  <channel>",
            f"    <title>{html.escape(title)}</title>",
            f"    <link>{base_url}</link>",
            f"    <description>{html.escape(description)}</description>",
            f"    <language>{language}</language>",
            f"    <lastBuildDate>{format_rss_date(datetime.now())}</lastBuildDate>",
            f'    <atom:link href="{base_url.rstrip("/")}/feed.xml" rel="self" type="application/rss+xml"/>',
        ]

        for item in items:
            item_title = html.escape(item.get("title", "Untitled"))
            item_link = item.get("link", base_url)
            item_desc = html.escape(item.get("description", ""))
            item_date = format_rss_date(item.get("pubDate", datetime.now()))
            item_guid = item.get("guid", item_link)

            xml_lines.extend(
                [
                    "    <item>",
                    f"      <title>{item_title}</title>",
                    f"      <link>{item_link}</link>",
                    f"      <description>{item_desc}</description>",
                    f"      <pubDate>{item_date}</pubDate>",
                    f"      <guid>{item_guid}</guid>",
                    "    </item>",
                ]
            )

        xml_lines.extend(
            [
                "  </channel>",
                "</rss>",
            ]
        )

        output_path.write_text("\n".join(xml_lines))
        success(f"Generated RSS feed with {len(items)} item(s)")

    def generate_atom_feed(
        self,
        items: List[Dict],
        base_url: str,
        output_path: Path,
        title: str = "Site Feed",
        subtitle: str = "Latest updates",
        author_name: str = "Author",
    ) -> None:
        """Generate an Atom feed.

        Args:
            items: List of feed items with keys: title, link, summary, updated, id
            base_url: Base URL of the site
            output_path: Output path for feed
            title: Feed title
            subtitle: Feed subtitle
            author_name: Author name
        """
        from datetime import datetime
        import html

        # ISO 8601 date format for Atom
        def format_atom_date(dt):
            if isinstance(dt, datetime):
                return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            return dt

        feed_id = f"{base_url.rstrip('/')}/atom.xml"
        updated = format_atom_date(datetime.now())

        # Build Atom XML
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<feed xmlns="http://www.w3.org/2005/Atom">',
            f"  <title>{html.escape(title)}</title>",
            f"  <subtitle>{html.escape(subtitle)}</subtitle>",
            f'  <link href="{base_url}" rel="alternate"/>',
            f'  <link href="{feed_id}" rel="self"/>',
            f"  <id>{feed_id}</id>",
            f"  <updated>{updated}</updated>",
            "  <author>",
            f"    <name>{html.escape(author_name)}</name>",
            "  </author>",
        ]

        for item in items:
            item_title = html.escape(item.get("title", "Untitled"))
            item_link = item.get("link", base_url)
            item_summary = html.escape(item.get("summary", item.get("description", "")))
            item_updated = format_atom_date(
                item.get("updated", item.get("pubDate", datetime.now()))
            )
            item_id = item.get("id", item.get("guid", item_link))

            xml_lines.extend(
                [
                    "  <entry>",
                    f"    <title>{item_title}</title>",
                    f'    <link href="{item_link}"/>',
                    f"    <id>{item_id}</id>",
                    f"    <updated>{item_updated}</updated>",
                    f"    <summary>{item_summary}</summary>",
                    "  </entry>",
                ]
            )

        xml_lines.append("</feed>")

        output_path.write_text("\n".join(xml_lines))
        success(f"Generated Atom feed with {len(items)} item(s)")

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

    def fingerprint_assets(self) -> Dict[str, str]:
        """Add content hashes to CSS and JS filenames for cache busting.

        Renames files like main.css to main.a1b2c3d4.css and updates
        all HTML references.

        Returns:
            Dictionary mapping original paths to new paths
        """
        # Find all CSS and JS files
        asset_files = []
        for pattern in ["*.css", "*.js"]:
            asset_files.extend(self.build_dir.rglob(pattern))

        if not asset_files:
            return {}

        # Create mapping of old paths to new paths
        path_mapping = {}

        for asset_path in asset_files:
            # Calculate content hash
            content = asset_path.read_bytes()
            hasher = hashlib.md5()
            hasher.update(content)
            content_hash = hasher.hexdigest()[:8]

            # Create new filename with hash
            stem = asset_path.stem
            suffix = asset_path.suffix
            new_name = f"{stem}.{content_hash}{suffix}"
            new_path = asset_path.parent / new_name

            # Store mapping (relative to build dir)
            old_rel = str(asset_path.relative_to(self.build_dir))
            new_rel = str(new_path.relative_to(self.build_dir))
            path_mapping[old_rel] = new_rel

            # Rename the file
            asset_path.rename(new_path)

        # Update references in HTML files
        if path_mapping:
            html_files = list(self.build_dir.rglob("*.html"))

            for html_path in html_files:
                content = html_path.read_text()
                modified = False

                for old_path, new_path in path_mapping.items():
                    # Handle various path formats in HTML
                    # e.g., /assets/styles/main.css, assets/styles/main.css, ./assets/styles/main.css
                    old_filename = Path(old_path).name
                    new_filename = Path(new_path).name

                    # Replace in href and src attributes
                    patterns = [
                        (f'href="{old_path}"', f'href="{new_path}"'),
                        (f"href='{old_path}'", f"href='{new_path}'"),
                        (f'src="{old_path}"', f'src="{new_path}"'),
                        (f"src='{old_path}'", f"src='{new_path}'"),
                        (f'href="/{old_path}"', f'href="/{new_path}"'),
                        (f"href='/{old_path}'", f"href='/{new_path}'"),
                        (f'src="/{old_path}"', f'src="/{new_path}"'),
                        (f"src='/{old_path}'", f"src='/{new_path}'"),
                        # Also handle just filename references
                        (f'href="{old_filename}"', f'href="{new_filename}"'),
                        (f"href='{old_filename}'", f"href='{new_filename}'"),
                        (f'src="{old_filename}"', f'src="{new_filename}"'),
                        (f"src='{old_filename}'", f"src='{new_filename}'"),
                    ]

                    for old_pattern, new_pattern in patterns:
                        if old_pattern in content:
                            content = content.replace(old_pattern, new_pattern)
                            modified = True

                if modified:
                    html_path.write_text(content)

            success(f"Fingerprinted {len(path_mapping)} asset(s)")

        return path_mapping

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
