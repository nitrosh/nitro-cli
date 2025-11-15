"""Build command for production optimization."""

import sys
from pathlib import Path

import click
from rich.panel import Panel
from rich.table import Table

from ..core.bundler import Bundler
from ..core.config import load_config
from ..core.generator import Generator
from ..utils import info, success, error


@click.command()
@click.option(
    "--minify/--no-minify",
    default=True,
    help="Minify HTML and CSS (default: enabled)"
)
@click.option(
    "--optimize/--no-optimize",
    default=True,
    help="Optimize images and assets (default: enabled)",
)
@click.option(
    "--output", "-o",
    default="build",
    help="Output directory"
)
@click.option(
    "--clean",
    is_flag=True,
    help="Clean build directory before building"
)
def build(minify, optimize, output, clean):
    """
    Build the site for production.

    Generates an optimized production build with minification,
    image optimization, sitemap generation, and more.
    """
    try:
        generator = Generator()

        # Override build directory if specified
        if output != "build":
            generator.build_dir = generator.project_root / output

        # Clean build directory if requested
        if clean:
            info("Cleaning build directory...")
            generator.clean()

        info("Building site for production...")
        info(f"Output directory: {generator.build_dir}\n")

        # Enable production settings
        config = load_config(generator.project_root / "nitro.config.py")
        if minify:
            config.renderer["minify_html"] = True
            generator.renderer.minify_html = True

        # Generate site
        success_result = generator.generate(verbose=False)

        if not success_result:
            error("Build failed during generation")
            sys.exit(1)

        # Initialize bundler
        bundler = Bundler(generator.build_dir)

        # Optimize CSS
        if minify:
            info("\nOptimizing CSS...")
            bundler.optimize_css(minify=True)

        # Optimize images
        if optimize:
            info("\nOptimizing images...")
            bundler.optimize_images(quality=85)

        # Generate sitemap
        info("\nGenerating sitemap...")
        html_files = list(generator.build_dir.rglob("*.html"))
        sitemap_path = generator.build_dir / "sitemap.xml"
        bundler.generate_sitemap(
            base_url=config.base_url, html_files=html_files, output_path=sitemap_path
        )

        # Generate robots.txt
        robots_path = generator.build_dir / "robots.txt"
        bundler.generate_robots_txt(config.base_url, robots_path)

        # Create asset manifest
        info("\nCreating asset manifest...")
        manifest_path = generator.build_dir / "manifest.json"
        bundler.create_asset_manifest(manifest_path)

        # Calculate build statistics
        stats = bundler.calculate_build_size()

        # Display build summary
        info("\n")
        display_build_summary(stats, generator.build_dir, minify, optimize)

        success(f"\nProduction build complete! Output: {generator.build_dir}")

    except Exception as e:
        error(f"Build failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def display_build_summary(
        stats: dict, build_dir: Path, minify: bool, optimize: bool
) -> None:
    """Display build summary.

    Args:
        stats: Build statistics
        build_dir: Build directory path
        minify: Whether minification was enabled
        optimize: Whether optimization was enabled
    """
    from ..utils import logger

    # Create summary table
    table = Table(
        title="Build Summary",
        show_header=True,
        header_style="bold cyan"
    )
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Total Files", str(stats["count"]))
    table.add_row("Total Size", Bundler.format_size(stats["total"]))
    # table.add_row("", "")  # Separator

    # Add type breakdown
    for file_type, size in stats["types"].items():
        if size > 0:
            table.add_row(f"{file_type.upper()} Files", Bundler.format_size(size))

    logger.print(table)

    optimizations = []
    if minify:
        optimizations.append("HTML & CSS Minification")
    if optimize:
        optimizations.append("Image Optimization")
    optimizations.extend(["Sitemap Generation", "Asset Manifest"])

    logger.print(
        Panel(
            "\n".join(f"✓ {opt}" for opt in optimizations),
            title="Optimizations Applied",
            border_style="green",
        )
    )
