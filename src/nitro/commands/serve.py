"""Serve command for the local development server."""

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
    header,
    spinner,
    server_ready,
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
def serve(port, host, no_reload, open_browser, verbose, debug):
    """Start a local development server with live reload."""
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
    """Async serve implementation."""

    header("Starting dev server...")

    generator = Generator()

    with spinner("Generating site...") as update:
        # Run blocking generation in thread pool to avoid blocking event loop
        # Force rebuild to ensure fresh state when starting dev server
        success_result = await asyncio.to_thread(
            generator.generate, verbose=False, quiet=True, force=True
        )
        if not success_result:
            error_panel(
                "Generation Failed",
                "Failed to generate site before starting server",
                hint="Check your page files for syntax errors",
            )
            return

    server = LiveReloadServer(
        build_dir=generator.build_dir, host=host, port=port, enable_reload=enable_reload
    )
    await server.start()

    server_ready(host=host, port=port, live_reload=enable_reload)

    if open_browser:
        import webbrowser

        url = f"http://{host}:{port}"
        await asyncio.to_thread(webbrowser.open, url)
        info(f"Opened browser at {url}")

    watcher = None
    if enable_reload:
        loop = asyncio.get_running_loop()
        regeneration_lock = asyncio.Lock()

        async def on_file_change(path: Path) -> None:
            nonlocal generator

            async with regeneration_lock:
                try:
                    relative_path = str(path.relative_to(generator.project_root))
                except ValueError:
                    relative_path = path.name

                hmr_update(relative_path)

                should_notify = False

                # Run blocking generator operations in thread pool
                if "pages" in str(path):
                    if path.suffix == ".py" and path.name != "__init__.py":
                        hmr_update("page", "rebuilding...")
                        if await asyncio.to_thread(
                            generator.regenerate_page, path, verbose=False
                        ):
                            should_notify = True
                elif "components" in str(path):
                    hmr_update("site", "rebuilding...")
                    if await asyncio.to_thread(
                        generator.generate, verbose=False, quiet=True
                    ):
                        should_notify = True
                elif "styles" in str(path) or "public" in str(path):
                    hmr_update("assets", "rebuilding...")
                    await asyncio.to_thread(generator._copy_assets, verbose=False)
                    should_notify = True
                elif path.name == "nitro.config.py":
                    hmr_update("config", "rebuilding...")
                    generator = Generator()
                    if await asyncio.to_thread(
                        generator.generate, verbose=False, quiet=True
                    ):
                        should_notify = True
                else:
                    hmr_update("site", "rebuilding...")
                    if await asyncio.to_thread(
                        generator.generate, verbose=False, quiet=True
                    ):
                        should_notify = True

                if should_notify:
                    await server.notify_reload()
                    success("Done")

        def _handle_async_exception(f):
            """Handle exceptions from async file change processing."""
            try:
                f.result()
            except Exception:
                # Log but don't crash - this runs in watcher thread
                import traceback

                traceback.print_exc()

        def on_file_change_sync(path: Path) -> None:
            future = asyncio.run_coroutine_threadsafe(on_file_change(path), loop)
            future.add_done_callback(_handle_async_exception)

        watcher = Watcher(generator.project_root, on_file_change_sync)
        watcher.start()

    shutdown_event = asyncio.Event()

    def signal_handler():
        newline()
        info("Stopping server...")
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
        if watcher:
            # Stop watcher in thread to avoid blocking event loop
            await asyncio.to_thread(watcher.stop)
        await server.stop()
