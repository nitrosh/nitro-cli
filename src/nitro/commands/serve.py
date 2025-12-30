"""Serve command for local development server."""

import asyncio
import signal
import sys
from pathlib import Path

import click

from ..core.generator import Generator
from ..core.server import LiveReloadServer
from ..core.watcher import Watcher
from ..utils import (
    LogLevel,
    set_level,
    info,
    success,
    error,
    banner,
    server_panel,
    error_panel,
    hmr_update,
    newline,
)


@click.command()
@click.option(
    "--port", "-p", default=3000, help="Port number for the development server"
)
@click.option(
    "--host", "-h", default="localhost", help="Host address for the development server"
)
@click.option("--no-reload", is_flag=True, help="Disable live reload")
@click.option(
    "--open", "-o", "open_browser", is_flag=True, help="Open browser automatically"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--debug", is_flag=True, help="Enable debug mode with full tracebacks")
@click.option("--log-file", type=click.Path(), help="Write logs to a file")
def serve(port, host, no_reload, open_browser, verbose, debug, log_file):
    """
    Start a local development server.

    Serves the built site and watches for changes.
    """
    if debug:
        set_level(LogLevel.DEBUG)
    elif verbose:
        set_level(LogLevel.VERBOSE)

    try:
        asyncio.run(serve_async(port, host, not no_reload, open_browser, debug))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        error(f"Server error: {e}")
        sys.exit(1)


async def serve_async(
    port: int,
    host: str,
    enable_reload: bool,
    open_browser: bool = False,
    debug_mode: bool = False,
):
    """Async serve implementation.

    Args:
        port: Port number
        host: Host address
        enable_reload: Enable live reload
        open_browser: Open browser automatically
        debug_mode: Enable debug mode
    """
    banner("Development Server")

    generator = Generator()

    if not generator.build_dir.exists() or not list(
        generator.build_dir.rglob("*.html")
    ):
        info("Build directory is empty. Generating site...")
        success_result = generator.generate(verbose=False)
        if not success_result:
            error_panel(
                "Generation Failed",
                "Failed to generate site before starting server",
                hint="Check your page files for syntax errors",
            )
            return
        success("Site generated")

    server = LiveReloadServer(
        build_dir=generator.build_dir, host=host, port=port, enable_reload=enable_reload
    )
    await server.start()

    server_panel(host=host, port=port, live_reload=enable_reload)

    # Open browser if requested
    if open_browser:
        import webbrowser

        url = f"http://{host}:{port}"
        webbrowser.open(url)
        info(f"Opened browser at {url}")

    # Setup file watcher if live reload is enabled
    watcher = None
    if enable_reload:
        # Get the current event loop for thread-safe scheduling
        loop = asyncio.get_running_loop()

        # Lock to prevent concurrent regeneration (race condition)
        regeneration_lock = asyncio.Lock()

        async def on_file_change(path: Path) -> None:
            """Handle file changes."""
            nonlocal generator

            async with regeneration_lock:
                try:
                    relative_path = str(path.relative_to(generator.project_root))
                except ValueError:
                    relative_path = path.name
                hmr_update(relative_path)

                should_notify = False

                if "pages" in str(path):
                    if path.suffix == ".py" and path.name != "__init__.py":
                        hmr_update("page", "rebuilding...")
                        if generator.regenerate_page(path, verbose=False):
                            should_notify = True
                elif "components" in str(path):
                    hmr_update("site", "rebuilding...")
                    if generator.generate(verbose=False):
                        should_notify = True
                elif "styles" in str(path) or "public" in str(path):
                    hmr_update("assets", "rebuilding...")
                    generator._copy_assets(verbose=False)
                    should_notify = True
                elif path.name == "nitro.config.py":
                    hmr_update("config", "rebuilding...")
                    generator = Generator()
                    if generator.generate(verbose=False):
                        should_notify = True
                else:
                    hmr_update("site", "rebuilding...")
                    if generator.generate(verbose=False):
                        should_notify = True

                if should_notify:
                    await server.notify_reload()
                    success("Done")

        def on_file_change_sync(path: Path) -> None:
            """Sync wrapper for file change handler (called from watcher thread)."""
            # Schedule the coroutine on the main event loop from another thread
            asyncio.run_coroutine_threadsafe(on_file_change(path), loop)

        watcher = Watcher(generator.project_root, on_file_change_sync)
        watcher.start()

    # Create shutdown event
    shutdown_event = asyncio.Event()

    def signal_handler():
        """Handle shutdown signals."""
        newline()
        info("Shutting down...")
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            pass

    try:
        info("Press Ctrl+C to stop the server")
        newline()
        await shutdown_event.wait()

    except asyncio.CancelledError:
        pass
    finally:
        # Cleanup in proper order
        if watcher:
            watcher.stop()

        # Give pending tasks a moment to complete
        await asyncio.sleep(0.1)

        await server.stop()
