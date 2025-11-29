"""Build command for production optimization."""

import sys

import click

from ..core.bundler import Bundler
from ..core.config import load_config
from ..core.generator import Generator
from ..utils import logger, LogLevel, info, success, verbose, configure


@click.command()
@click.option(
    "--minify/--no-minify", default=True, help="Minify HTML and CSS (default: enabled)"
)
@click.option(
    "--optimize/--no-optimize",
    default=True,
    help="Optimize images and assets (default: enabled)",
)
@click.option("--output", "-o", default="build", help="Output directory")
@click.option("--clean", is_flag=True, help="Clean build directory before building")
@click.option(
    "--verbose", "-v", "verbose_flag", is_flag=True, help="Enable verbose output"
)
@click.option("--quiet", "-q", is_flag=True, help="Only show errors and final summary")
@click.option("--debug", is_flag=True, help="Enable debug mode with full tracebacks")
@click.option("--log-file", type=click.Path(), help="Write logs to a file")
def build(minify, optimize, output, clean, verbose_flag, quiet, debug, log_file):
    """
    Build the site for production.

    Generates an optimized production build with minification,
    image optimization, sitemap generation, and more.
    """
    # Configure logging
    if debug:
        configure(level=LogLevel.DEBUG, log_file=log_file)
    elif verbose_flag:
        configure(level=LogLevel.VERBOSE, log_file=log_file)
    elif quiet:
        configure(level=LogLevel.QUIET, log_file=log_file)
    elif log_file:
        configure(log_file=log_file)

    try:
        # Show banner
        logger.banner("Production Build")
        logger.start_timer()

        generator = Generator()

        # Override build directory if specified
        if output != "build":
            generator.build_dir = generator.project_root / output

        # Clean build directory if requested
        if clean:
            info("Cleaning build directory...")
            generator.clean()

        info("Building site for production...")
        verbose(f"Output directory: {generator.build_dir}")

        # Enable production settings
        config = load_config(generator.project_root / "nitro.config.py")
        if minify:
            config.renderer["minify_html"] = True
            generator.renderer.minify_html = True

        # Trigger pre-build hook
        generator.plugin_loader.trigger(
            "nitro.pre_build",
            {
                "config": config,
                "build_dir": str(generator.build_dir),
                "minify": minify,
                "optimize": optimize,
            },
        )

        # Generate site
        logger.section("Generating Pages")
        success_result = generator.generate(verbose=verbose_flag)

        if not success_result:
            logger.error_panel(
                "Build Failed",
                "Failed to generate site during build",
                hint="Check your page files for syntax errors",
            )
            sys.exit(1)

        # Initialize bundler
        bundler = Bundler(generator.build_dir)

        # Optimize CSS
        if minify:
            logger.section("Optimizing CSS")
            css_count = bundler.optimize_css(minify=True)
            if css_count:
                verbose(f"Minified {css_count} CSS file(s)")

        # Optimize images
        if optimize:
            logger.section("Optimizing Images")
            img_count = bundler.optimize_images(quality=85)
            if img_count:
                verbose(f"Optimized {img_count} image(s)")

        # Generate sitemap
        logger.section("Generating Metadata")
        html_files = list(generator.build_dir.rglob("*.html"))
        sitemap_path = generator.build_dir / "sitemap.xml"
        bundler.generate_sitemap(
            base_url=config.base_url, html_files=html_files, output_path=sitemap_path
        )
        verbose(f"Created sitemap.xml with {len(html_files)} URLs")

        # Generate robots.txt
        robots_path = generator.build_dir / "robots.txt"
        bundler.generate_robots_txt(config.base_url, robots_path)
        verbose("Created robots.txt")

        # Create asset manifest
        manifest_path = generator.build_dir / "manifest.json"
        bundler.create_asset_manifest(manifest_path)
        verbose("Created manifest.json")

        # Calculate build statistics
        stats = bundler.calculate_build_size()

        # Trigger post-build hook
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

        # Build optimizations list
        optimizations = []
        if minify:
            optimizations.append("HTML & CSS Minification")
        if optimize:
            optimizations.append("Image Optimization")
        optimizations.extend(["Sitemap Generation", "Asset Manifest"])

        # Display build summary
        logger.newline()
        logger.build_summary(
            stats=stats,
            build_dir=generator.build_dir,
            elapsed=logger.get_elapsed(),
            optimizations=optimizations,
        )

        logger.newline()
        success(f"Production build complete! Output: {generator.build_dir}")

    except Exception as e:
        if debug:
            logger.exception(e, show_trace=True)
        else:
            logger.error_panel(
                "Build Error", str(e), hint="Use --debug for full traceback"
            )
        sys.exit(1)
