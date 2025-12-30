"""
Image optimization pipeline for Nitro.

Features:
- Responsive image generation (multiple sizes)
- WebP/AVIF format conversion
- Automatic srcset generation
- Lazy loading support
- Build-time optimization
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import re

from ..utils import warning, error


@dataclass
class ImageConfig:
    """Configuration for image optimization."""

    # Responsive breakpoints (widths in pixels)
    sizes: List[int] = field(default_factory=lambda: [320, 640, 768, 1024, 1280, 1920])

    # Output formats (in order of preference)
    formats: List[str] = field(default_factory=lambda: ["avif", "webp", "original"])

    # Quality settings per format (0-100)
    quality: Dict[str, int] = field(
        default_factory=lambda: {
            "avif": 80,
            "webp": 85,
            "jpeg": 85,
            "png": 85,
        }
    )

    # Enable lazy loading
    lazy_load: bool = True

    # Default sizes attribute for responsive images
    default_sizes: str = "(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"

    # Output directory for optimized images (relative to build)
    output_dir: str = "_images"

    # Skip images smaller than this (bytes)
    min_size: int = 1024

    # Maximum dimension to generate
    max_width: int = 2560


@dataclass
class OptimizedImage:
    """Represents an optimized image with all variants."""

    original_path: Path
    original_width: int
    original_height: int
    variants: Dict[str, Dict[int, Path]]  # format -> width -> path
    hash: str

    def get_srcset(self, format: str = "webp") -> str:
        """Generate srcset attribute for a format.

        Args:
            format: Image format (webp, avif, or original extension)

        Returns:
            srcset string
        """
        if format not in self.variants:
            return ""

        parts = []
        for width, path in sorted(self.variants[format].items()):
            parts.append(f"{path} {width}w")

        return ", ".join(parts)

    def get_src(self, format: str = "webp", width: Optional[int] = None) -> str:
        """Get single src for a format/width.

        Args:
            format: Image format
            width: Specific width (or largest if None)

        Returns:
            Path string
        """
        if format not in self.variants:
            return str(self.original_path)

        widths = self.variants[format]
        if width and width in widths:
            return str(widths[width])

        # Return largest available
        max_width = max(widths.keys())
        return str(widths[max_width])


class ImageOptimizer:
    """Handles image optimization for builds."""

    def __init__(self, config: Optional[ImageConfig] = None):
        """Initialize the image optimizer.

        Args:
            config: Image optimization configuration
        """
        self.config = config or ImageConfig()
        self._cache: Dict[str, OptimizedImage] = {}
        self._pillow_available = None
        self._avif_available = None

    def _check_pillow(self) -> bool:
        """Check if Pillow is available."""
        if self._pillow_available is None:
            try:
                import PIL  # noqa: F401

                self._pillow_available = True
            except ImportError:
                self._pillow_available = False
                warning("Pillow not installed. Install with: pip install Pillow")
        return self._pillow_available

    def _check_avif(self) -> bool:
        """Check if AVIF support is available."""
        if self._avif_available is None:
            try:
                from PIL import Image

                # Check for AVIF support
                self._avif_available = "AVIF" in Image.registered_extensions().values()
            except ImportError:
                self._avif_available = False
        return self._avif_available

    def _get_image_hash(self, path: Path) -> str:
        """Calculate hash of image file.

        Args:
            path: Path to image

        Returns:
            Hash string
        """
        hasher = hashlib.md5()
        hasher.update(path.read_bytes())
        return hasher.hexdigest()[:12]

    def optimize_image(
        self,
        source_path: Path,
        output_dir: Path,
        base_url: str = "",
    ) -> Optional[OptimizedImage]:
        """Optimize a single image.

        Args:
            source_path: Path to source image
            output_dir: Directory for optimized outputs
            base_url: Base URL prefix for paths

        Returns:
            OptimizedImage with all variants, or None on failure
        """
        if not self._check_pillow():
            return None

        from PIL import Image

        # Check cache
        img_hash = self._get_image_hash(source_path)
        cache_key = f"{source_path}:{img_hash}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Skip small images
        if source_path.stat().st_size < self.config.min_size:
            return None

        try:
            with Image.open(source_path) as img:
                original_width, original_height = img.size
                aspect_ratio = original_height / original_width

                # Determine which sizes to generate
                sizes_to_generate = [
                    s
                    for s in self.config.sizes
                    if s <= original_width and s <= self.config.max_width
                ]

                # Always include original size if not in list
                if (
                    original_width <= self.config.max_width
                    and original_width not in sizes_to_generate
                ):
                    sizes_to_generate.append(original_width)

                sizes_to_generate.sort()

                if not sizes_to_generate:
                    return None

                # Create output directory
                img_output_dir = output_dir / self.config.output_dir
                img_output_dir.mkdir(parents=True, exist_ok=True)

                # Generate variants
                variants: Dict[str, Dict[int, Path]] = {}
                original_format = source_path.suffix.lower().lstrip(".")

                # Map format names
                format_map = {
                    "jpg": "jpeg",
                    "jpeg": "jpeg",
                    "png": "png",
                    "gif": "gif",
                }
                pil_format = format_map.get(original_format, original_format)

                for output_format in self.config.formats:
                    if output_format == "original":
                        output_format = original_format

                    # Skip AVIF if not supported
                    if output_format == "avif" and not self._check_avif():
                        continue

                    variants[output_format] = {}

                    for width in sizes_to_generate:
                        height = int(width * aspect_ratio)

                        # Create resized image
                        resized = img.copy()
                        resized.thumbnail((width, height), Image.Resampling.LANCZOS)

                        # Determine output filename
                        out_name = (
                            f"{source_path.stem}-{width}w-{img_hash}.{output_format}"
                        )
                        out_path = img_output_dir / out_name

                        # Save with appropriate settings
                        save_kwargs = self._get_save_kwargs(output_format, resized)

                        if output_format == "avif":
                            resized.save(out_path, "AVIF", **save_kwargs)
                        elif output_format == "webp":
                            resized.save(out_path, "WEBP", **save_kwargs)
                        else:
                            # Convert RGBA to RGB for JPEG
                            if pil_format == "jpeg" and resized.mode == "RGBA":
                                background = Image.new(
                                    "RGB", resized.size, (255, 255, 255)
                                )
                                background.paste(resized, mask=resized.split()[3])
                                resized = background

                            resized.save(out_path, **save_kwargs)

                        # Store relative path with base URL
                        rel_path = out_path.relative_to(output_dir)
                        variants[output_format][width] = Path(base_url) / rel_path

                result = OptimizedImage(
                    original_path=source_path,
                    original_width=original_width,
                    original_height=original_height,
                    variants=variants,
                    hash=img_hash,
                )

                self._cache[cache_key] = result
                return result

        except Exception as e:
            error(f"Failed to optimize {source_path.name}: {e}")
            return None

    def _get_save_kwargs(self, format: str, img) -> Dict:
        """Get save kwargs for a format.

        Args:
            format: Output format
            img: PIL Image

        Returns:
            Dictionary of save options
        """
        quality = self.config.quality.get(format, 85)

        if format == "avif":
            return {"quality": quality}
        elif format == "webp":
            return {"quality": quality, "method": 4}
        elif format == "jpeg":
            return {"quality": quality, "optimize": True, "progressive": True}
        elif format == "png":
            return {"optimize": True}

        return {}

    def generate_picture_element(
        self,
        optimized: OptimizedImage,
        alt: str = "",
        css_class: str = "",
        sizes: Optional[str] = None,
    ) -> str:
        """Generate HTML picture element with sources.

        Args:
            optimized: OptimizedImage instance
            alt: Alt text
            css_class: CSS class for img tag
            sizes: sizes attribute (or use default)

        Returns:
            HTML string
        """
        sizes_attr = sizes or self.config.default_sizes
        lazy_attr = 'loading="lazy"' if self.config.lazy_load else ""
        class_attr = f'class="{css_class}"' if css_class else ""

        sources = []

        # Add sources in format preference order
        for format in self.config.formats:
            if format == "original":
                continue

            if format in optimized.variants:
                srcset = optimized.get_srcset(format)
                mime = f"image/{format}"
                sources.append(
                    f'  <source type="{mime}" srcset="{srcset}" sizes="{sizes_attr}">'
                )

        # Fallback img tag (use original format or first available)
        original_format = optimized.original_path.suffix.lower().lstrip(".")
        if original_format in optimized.variants:
            fallback_srcset = optimized.get_srcset(original_format)
            fallback_src = optimized.get_src(original_format)
        else:
            # Use first available format
            first_format = list(optimized.variants.keys())[0]
            fallback_srcset = optimized.get_srcset(first_format)
            fallback_src = optimized.get_src(first_format)

        img_tag = (
            f'  <img src="{fallback_src}" '
            f'srcset="{fallback_srcset}" '
            f'sizes="{sizes_attr}" '
            f'alt="{alt}" '
            f"{class_attr} {lazy_attr} "
            f'width="{optimized.original_width}" '
            f'height="{optimized.original_height}">'
        )

        return f"<picture>\n{''.join(f'{s}' + chr(10) for s in sources)}{img_tag}\n</picture>"

    def process_html(
        self,
        html_content: str,
        source_dir: Path,
        output_dir: Path,
        base_url: str = "",
    ) -> str:
        """Process HTML and optimize referenced images.

        Finds img tags and replaces them with picture elements.

        Args:
            html_content: HTML content
            source_dir: Directory containing source images
            output_dir: Build output directory
            base_url: Base URL for image paths

        Returns:
            Modified HTML with optimized images
        """
        if not self._check_pillow():
            return html_content

        # Find all img tags
        img_pattern = re.compile(
            r'<img\s+([^>]*?)src=["\']([^"\']+)["\']([^>]*?)/?>', re.IGNORECASE
        )

        def replace_img(match):
            before_attrs = match.group(1)
            src = match.group(2)
            after_attrs = match.group(3)

            # Skip external images and data URLs
            if src.startswith(("http://", "https://", "data:", "//")):
                return match.group(0)

            # Skip already optimized images
            if "/_images/" in src:
                return match.group(0)

            # Find source image
            if src.startswith("/"):
                img_path = source_dir / src.lstrip("/")
            else:
                img_path = source_dir / src

            if not img_path.exists():
                return match.group(0)

            # Check if it's an optimizable image
            if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".gif"}:
                return match.group(0)

            # Optimize the image
            optimized = self.optimize_image(img_path, output_dir, base_url)
            if not optimized:
                return match.group(0)

            # Extract alt and class from original attributes
            alt_match = re.search(
                r'alt=["\']([^"\']*)["\']', before_attrs + after_attrs
            )
            alt = alt_match.group(1) if alt_match else ""

            class_match = re.search(
                r'class=["\']([^"\']*)["\']', before_attrs + after_attrs
            )
            css_class = class_match.group(1) if class_match else ""

            sizes_match = re.search(
                r'sizes=["\']([^"\']*)["\']', before_attrs + after_attrs
            )
            sizes = sizes_match.group(1) if sizes_match else None

            return self.generate_picture_element(optimized, alt, css_class, sizes)

        return img_pattern.sub(replace_img, html_content)
