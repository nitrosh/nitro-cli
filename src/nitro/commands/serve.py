"""Serve command for local development server."""

import asyncio
import sys
from pathlib import Path

import click

from ..core.generator import Generator
from ..core.server import LiveReloadServer
from ..core.watcher import Watcher
from ..utils import logger, LogLevel, info, success, error, configure


@click.command()
@click.option(
    "--port", "-p", default=3000, help="Port number for the development server"
)
@click.option(
    "--host", "-h", default="localhost", help="Host address for the development server"
)
@click.option("--no-reload", is_flag=True, help="Disable live reload")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--debug", is_flag=True, help="Enable debug mode with full tracebacks")
@click.option("--log-file", type=click.Path(), help="Write logs to a file")
def serve(port, host, no_reload, verbose, debug, log_file):
    """
    Start a local development server.

    Serves the built site and watches for changes.
    """
    # Configure logging
    if debug:
        configure(level=LogLevel.DEBUG, log_file=log_file)
    elif verbose:
        configure(level=LogLevel.VERBOSE, log_file=log_file)
    elif log_file:
        configure(log_file=log_file)

    try:
        asyncio.run(serve_async(port, host, not no_reload, debug))
    except KeyboardInterrupt:
        logger.newline()
        info("Server stopped")
        sys.exit(0)
    except Exception as e:
        if debug:
            logger.exception(e, show_trace=True)
        else:
            error(f"Server error: {e}")
        sys.exit(1)


async def serve_async(
    port: int, host: str, enable_reload: bool, debug_mode: bool = False
):
    """Async serve implementation.

    Args:
        port: Port number
        host: Host address
        enable_reload: Enable live reload
        debug_mode: Enable debug mode
    """
    # Show banner
    logger.banner("Development Server")

    # Initialize generator
    generator = Generator()

    # Check if build directory exists and contains any HTML file (including nested)
    if not generator.build_dir.exists() or not list(
        generator.build_dir.rglob("*.html")
    ):
        info("Build directory is empty or doesn't exist. Generating site...")
        logger.start_timer()
        success_result = generator.generate(verbose=False)
        if not success_result:
            logger.error_panel(
                "Generation Failed",
                "Failed to generate site before starting server",
                hint="Check your page files for syntax errors",
            )
            return
        success(f"Site generated in {logger.get_elapsed()}")

    # Initialize server
    server = LiveReloadServer(
        build_dir=generator.build_dir, host=host, port=port, enable_reload=enable_reload
    )

    # Start server
    await server.start()

    # Display server panel
    logger.server_panel(
        host=host,
        port=port,
        live_reload=enable_reload,
        watching="src/" if enable_reload else None,
    )

    # Setup file watcher if live reload is enabled
    watcher = None
    if enable_reload:
        # Get the current event loop for thread-safe scheduling
        loop = asyncio.get_running_loop()

        async def on_file_change(path: Path) -> None:
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
            should_notify = False

            if "pages" in str(path):
                # Regenerate specific page
                if path.suffix == ".py" and path.name != "__init__.py":
                    logger.hmr_rebuilding(1, "page")
                    if generator.regenerate_page(path, verbose=False):
                        should_notify = True
            elif "components" in str(path):
                # Component changed - regenerate all pages
                logger.hmr_rebuilding(target="site")
                if generator.generate(verbose=False):
                    should_notify = True
            elif "styles" in str(path) or "public" in str(path):
                # Recopy assets
                logger.hmr_rebuilding(target="assets")
                generator._copy_assets(verbose=False)
                should_notify = True
            elif path.name == "nitro.config.py":
                # Config changed - regenerate entire site
                logger.hmr_rebuilding(target="site")
                generator = Generator()  # Reload config
                if generator.generate(verbose=False):
                    should_notify = True
            else:
                # Other changes - regenerate entire site
                logger.hmr_rebuilding(target="site")
                if generator.generate(verbose=False):
                    should_notify = True

            # Notify clients to reload
            if should_notify:
                await server.notify_reload()
                logger.hmr_done()

        def on_file_change_sync(path: Path) -> None:
            """Sync wrapper for file change handler (called from watcher thread)."""
            # Schedule the coroutine on the main event loop from another thread
            asyncio.run_coroutine_threadsafe(on_file_change(path), loop)

        watcher = Watcher(generator.project_root, on_file_change_sync)
        watcher.start()

    try:
        # Run server forever
        info("Press Ctrl+C to stop the server")
        logger.newline()
        await asyncio.Event().wait()

    except asyncio.CancelledError:
        pass
    finally:
        # Cleanup
        if watcher:
            watcher.stop()
        await server.stop()
