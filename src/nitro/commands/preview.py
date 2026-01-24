"""Preview command - serve production build locally."""

import asyncio
import signal
import sys
from pathlib import Path

import click

from ..core.config import load_config
from ..core.page import get_project_root
from ..core.server import LiveReloadServer
from ..utils import (
    LogLevel,
    set_level,
    info,
    error,
    warning,
    header,
    server_ready,
    newline,
)


@click.command()
@click.option("--port", "-p", default=4000, help="Port number for the preview server")
@click.option(
    "--host", "-h", default="localhost", help="Host address for the preview server"
)
@click.option(
    "--open", "-o", "open_browser", is_flag=True, help="Open browser automatically"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.pass_context
def preview(ctx, port, host, open_browser, verbose, debug):
    """Preview the production build locally."""
    if debug:
        set_level(LogLevel.DEBUG)
    elif verbose:
        set_level(LogLevel.VERBOSE)

    try:
        asyncio.run(preview_async(port, host, open_browser, debug))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        error(f"Preview error: {e}")
        sys.exit(1)


async def preview_async(
    port: int, host: str, open_browser: bool, debug_mode: bool = False
):
    """Async preview implementation."""
    header("Starting preview server...")

    project_root = get_project_root()
    if not project_root:
        project_root = Path.cwd()

    config_path = project_root / "nitro.config.py"
    if config_path.exists():
        config = load_config(config_path)
        build_dir = project_root / config.build_dir
    else:
        build_dir = project_root / "build"

    if not build_dir.exists():
        error(f"Build directory not found: {build_dir}")
        info("Run 'nitro build' first to create a production build")
        return

    html_files = list(build_dir.rglob("*.html"))
    if not html_files:
        error("Build directory is empty")
        info("Run 'nitro build' first to create a production build")
        return

    server = LiveReloadServer(
        build_dir=build_dir, host=host, port=port, enable_reload=False
    )
    await server.start()

    server_ready(host=host, port=port, live_reload=False)

    if open_browser:
        import webbrowser

        url = f"http://{host}:{port}"
        await asyncio.to_thread(webbrowser.open, url)
        info(f"Opened browser at {url}")

    shutdown_event = asyncio.Event()

    def signal_handler():
        newline()
        info("Shutting down preview server...")
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
        await server.stop()
