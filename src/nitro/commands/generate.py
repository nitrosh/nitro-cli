"""Generate command for building HTML from YDNATL pages."""

import sys
import time
from pathlib import Path

import click

from ..core.generator import Generator
from ..core.watcher import Watcher
from ..utils import logger, LogLevel, info, success, error, verbose, configure


@click.command()
@click.option(
    "--watch", "-w",
    is_flag=True,
    help="Watch for file changes and regenerate"
)
@click.option(
    "--output", "-o",
    default="build",
    help="Output directory for generated files"
)
@click.option(
    "--verbose", "-v",
    "verbose_flag",
    is_flag=True,
    help="Enable verbose output"
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    help="Only show errors and final summary"
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode with full tracebacks"
)
@click.option(
    "--log-file",
    type=click.Path(),
    help="Write logs to a file"
)
def generate(watch, output, verbose_flag, quiet, debug, log_file):
    """
    Generate static HTML files from source files.

    Scans src/pages/ for Python files and generates HTML.
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
        logger.banner("Site Generator")
        logger.start_timer()

        # Initialize generator
        generator = Generator()

        # Override build directory if specified
        if output != "build":
            generator.build_dir = generator.project_root / output

        verbose(f"Source directory: {generator.project_root / 'src'}")
        verbose(f"Output directory: {generator.build_dir}")

        # Generate site
        logger.section("Generating Pages")
        success_result = generator.generate(verbose=verbose_flag)

        if not success_result:
            logger.error_panel(
                "Generation Failed",
                "Failed to generate site",
                hint="Check your page files for syntax errors"
            )
            sys.exit(1)

        # Show completion message
        elapsed = logger.get_elapsed()
        logger.newline()
        success(f"Site generated in {elapsed}")
        verbose(f"Output: {generator.build_dir}")

        # Watch mode
        if watch:
            logger.newline()
            info("Watch mode enabled. Press Ctrl+C to stop.")
            logger.newline()

            def on_file_change(path: Path) -> None:
                """Handle file changes."""
                nonlocal generator
                logger.start_timer()

                # Log the file change with HMR style
                try:
                    relative_path = str(path.relative_to(generator.project_root))
                except ValueError:
                    relative_path = path.name
                logger.hmr_change(relative_path)

                # Determine what changed
                if "pages" in str(path):
                    # Regenerate specific page
                    if path.suffix == ".py" and path.name != "__init__.py":
                        logger.hmr_rebuilding(1, "page")
                        generator.regenerate_page(path, verbose=verbose_flag)
                elif "components" in str(path):
                    # Component changed - regenerate all pages
                    logger.hmr_rebuilding(target="site")
                    generator.generate(verbose=verbose_flag)
                elif "styles" in str(path) or "public" in str(path):
                    # Recopy assets
                    logger.hmr_rebuilding(target="assets")
                    generator._copy_assets(verbose=verbose_flag)
                elif path.name == "nitro.config.py":
                    # Config changed - regenerate entire site
                    logger.hmr_rebuilding(target="site")
                    generator = Generator()  # Reload config
                    generator.generate(verbose=verbose_flag)
                else:
                    # Other changes - regenerate entire site
                    logger.hmr_rebuilding(target="site")
                    generator.generate(verbose=verbose_flag)

                logger.hmr_done()

            watcher = Watcher(generator.project_root, on_file_change)

            try:
                watcher.start()

                # Keep running
                while watcher.is_running():
                    time.sleep(1)

            except KeyboardInterrupt:
                logger.newline()
                info("Stopping watch mode...")
                watcher.stop()
                success("Done!")

    except KeyboardInterrupt:
        logger.newline()
        info("Generation cancelled")
        sys.exit(0)
    except Exception as e:
        if debug:
            logger.exception(e, show_trace=True)
        else:
            logger.error_panel(
                "Generation Error",
                str(e),
                hint="Use --debug for full traceback"
            )
        sys.exit(1)