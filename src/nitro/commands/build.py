"""Build command for production optimization."""

import os
import sys
from datetime import datetime

import click

from ..core.bundler import Bundler
from ..core.config import load_config
from ..core.generator import Generator
from ..core.images import ImageOptimizer, ImageConfig
from ..core.islands import IslandProcessor, IslandConfig
from ..utils import (
    LogLevel,
    set_level,
    error,
    verbose,
    header,
    spinner,
    error_panel,
    build_complete,
)


@click.command()
@click.option(
    "--minify/--no-minify", default=True, help="Minify HTML and CSS (default: enabled)"
)
@click.option(
    "--optimize/--no-optimize",
    default=True,
    help="Optimize images and assets (default: enabled)",
)
@click.option(
    "--responsive/--no-responsive",
    default=False,
    help="Generate responsive images with WebP/AVIF variants (default: disabled)",
)
@click.option(
    "--fingerprint/--no-fingerprint",
    default=True,
    help="Add content hashes to asset filenames for cache busting (default: enabled)",
)
@click.option(
    "--islands/--no-islands",
    default=True,
    help="Process islands and inject hydration scripts (default: enabled)",
)
@click.option("--output", "-o", default="build", help="Output directory")
@click.option("--clean", is_flag=True, help="Clean build directory before building")
@click.option("--force", "-f", is_flag=True, help="Force full rebuild, ignore cache")
@click.option(
    "--verbose", "-v", "verbose_flag", is_flag=True, help="Enable verbose output"
)
@click.option("--quiet", "-q", is_flag=True, help="Only show errors and final summary")
@click.option("--debug", is_flag=True, help="Enable debug mode with full tracebacks")
def build(
    minify,
    optimize,
    responsive,
    fingerprint,
    islands,
    output,
    clean,
    force,
    verbose_flag,
    quiet,
    debug,
):
    """Build the site for production."""
    if debug:
        set_level(LogLevel.DEBUG)
    elif verbose_flag:
        set_level(LogLevel.VERBOSE)
    elif quiet:
        set_level(LogLevel.QUIET)

    try:
        # Set production environment variable
        os.environ["NITRO_ENV"] = "production"

        header("Building for production...")
        start_time = datetime.now()

        generator = Generator()

        if output != "build":
            generator.build_dir = generator.project_root / output

        verbose(f"Output directory: {generator.build_dir}")

        config = load_config(generator.project_root / "nitro.config.py")
        if minify:
            config.renderer["minify_html"] = True
            generator.renderer.minify_html = True

        generator.plugin_loader.trigger(
            "nitro.pre_build",
            {
                "config": config,
                "build_dir": str(generator.build_dir),
                "minify": minify,
                "optimize": optimize,
            },
        )

        with spinner("Generating pages...") as update:
            if clean:
                update("Cleaning build directory...")
                generator.clean()

            update("Generating pages...")
            success_result = generator.generate(
                verbose=verbose_flag, force=force or clean, production=True
            )

            if not success_result:
                error_panel(
                    "Build Failed",
                    "Failed to generate site during build",
                    hint="Check your page files for syntax errors",
                )
                sys.exit(1)

            bundler = Bundler(generator.build_dir)

            if minify:
                update("Optimizing CSS...")
                css_count = bundler.optimize_css(minify=True)
                if css_count:
                    verbose(f"Minified {css_count} CSS file(s)")

            if optimize:
                update("Optimizing images...")
                img_count = bundler.optimize_images(quality=85)
                if img_count:
                    verbose(f"Optimized {img_count} image(s)")

            if responsive:
                update("Generating responsive images...")
                img_optimizer = ImageOptimizer(
                    ImageConfig(
                        formats=["avif", "webp", "original"],
                        sizes=[320, 640, 768, 1024, 1280, 1920],
                        lazy_load=True,
                    )
                )

                html_files = list(generator.build_dir.rglob("*.html"))
                resp_count = 0
                for html_file in html_files:
                    original_content = html_file.read_text()
                    processed_content = img_optimizer.process_html(
                        original_content,
                        source_dir=generator.project_root / "static",
                        output_dir=generator.build_dir,
                        base_url="/",
                    )
                    if processed_content != original_content:
                        html_file.write_text(processed_content)
                        resp_count += 1

                if resp_count:
                    verbose(
                        f"Processed {resp_count} HTML file(s) with responsive images"
                    )

            if fingerprint:
                update("Fingerprinting assets...")
                asset_mapping = bundler.fingerprint_assets()
                if asset_mapping:
                    verbose(f"Fingerprinted {len(asset_mapping)} asset(s)")

            if islands:
                update("Processing islands...")
                island_processor = IslandProcessor(IslandConfig(debug=debug))
                html_files = list(generator.build_dir.rglob("*.html"))
                islands_count = 0
                for html_file in html_files:
                    content = html_file.read_text()
                    if "data-island=" in content:
                        processed = island_processor.process_html(content)
                        html_file.write_text(processed)
                        islands_count += 1

                if islands_count:
                    verbose(f"Processed {islands_count} page(s) with islands")

            update("Generating metadata...")
            html_files = list(generator.build_dir.rglob("*.html"))
            sitemap_path = generator.build_dir / "sitemap.xml"
            # Pass page metadata for enhanced sitemap generation
            page_metadata = getattr(generator, "page_metadata", None)
            bundler.generate_sitemap(
                base_url=config.base_url,
                html_files=html_files,
                output_path=sitemap_path,
                page_metadata=page_metadata,
            )
            verbose(f"Created sitemap.xml with {len(html_files)} URLs")

            robots_path = generator.build_dir / "robots.txt"
            bundler.generate_robots_txt(config.base_url, robots_path)
            verbose("Created robots.txt")

            manifest_path = generator.build_dir / "manifest.json"
            bundler.create_asset_manifest(manifest_path)
            verbose("Created manifest.json")

        stats = bundler.calculate_build_size()

        generator.plugin_loader.trigger(
            "nitro.post_build",
            {
                "config": config,
                "build_dir": str(generator.build_dir),
                "stats": stats,
                "minify": minify,
                "optimize": optimize,
            },
        )

        elapsed = (datetime.now() - start_time).total_seconds()
        elapsed_str = f"{elapsed:.2f}s" if elapsed >= 1 else f"{elapsed * 1000:.0f}ms"

        build_complete(stats=stats, elapsed=elapsed_str)

    except Exception as e:
        error_panel("Build Error", str(e), hint="Use --debug for full traceback")
        sys.exit(1)
