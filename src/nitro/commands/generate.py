"""Generate command for building HTML from YDNATL pages."""

import click
import sys
from pathlib import Path

from ..core.generator import Generator
from ..core.watcher import Watcher
from ..utils import info, success, error


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
    is_flag=True,
    help="Verbose output"
)
def generate(watch, output, verbose):
    """
    Generate static HTML files from source files.

    Scans src/pages/ for Python files and generates HTML.
    """
    try:
        # Initialize generator
        generator = Generator()

        # Override build directory if specified
        if output != "build":
            generator.build_dir = generator.project_root / output

        # Generate site
        success_result = generator.generate(verbose=verbose)

        if not success_result:
            sys.exit(1)

        # Watch mode
        if watch:
            info("\nWatch mode enabled. Press Ctrl+C to stop.")

            def on_file_change(path: Path) -> None:
                """Handle file changes."""
                info(f"\nFile changed: {path.name}")

                # Determine what changed
                if "pages" in str(path):
                    # Regenerate specific page
                    if path.suffix == ".py" and path.name != "__init__.py":
                        generator.regenerate_page(path, verbose=verbose)
                elif "styles" in str(path) or "public" in str(path):
                    # Recopy assets
                    info("Copying assets...")
                    generator._copy_assets(verbose=verbose)
                elif path.name == "nitro.config.py":
                    # Regenerate entire site
                    info("Config changed, regenerating site...")
                    generator = Generator()  # Reload config
                    generator.generate(verbose=verbose)
                else:
                    # Regenerate entire site for other changes
                    generator.generate(verbose=verbose)

            watcher = Watcher(generator.project_root, on_file_change)

            try:
                watcher.start()

                # Keep running
                import time

                while watcher.is_running():
                    time.sleep(1)

            except KeyboardInterrupt:
                info("\nStopping watch mode...")
                watcher.stop()
                success("Done!")

    except KeyboardInterrupt:
        info("\nGeneration cancelled")
        sys.exit(0)
    except Exception as e:
        error(f"Generation failed: {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)
