"""Serve command for local development server."""

import asyncio
import sys
from pathlib import Path

import click

from ..core.generator import Generator
from ..core.server import LiveReloadServer
from ..core.watcher import Watcher
from ..utils import info, success, error


@click.command()
@click.option(
    "--port", "-p",
    default=3000,
    help="Port number for the development server"
)
@click.option(
    "--host", "-h",
    default="localhost",
    help="Host address for the development server"
)
@click.option(
    "--no-reload",
    is_flag=True,
    help="Disable live reload"
)
def serve(port, host, no_reload):
    """
    Start a local development server.

    Serves the built site and watches for changes.
    """
    try:
        asyncio.run(serve_async(port, host, not no_reload))
    except KeyboardInterrupt:
        info("\nServer stopped")
        sys.exit(0)
    except Exception as e:
        error(f"Server error: {e}")
        sys.exit(1)


async def serve_async(port: int, host: str, enable_reload: bool):
    """Async serve implementation.

    Args:
        port: Port number
        host: Host address
        enable_reload: Enable live reload
    """
    # Initialize generator
    generator = Generator()

    # Check if build directory exists and contains any HTML file (including nested)
    # Use rglob to account for pages generated in subdirectories
    if not generator.build_dir.exists() or not list(generator.build_dir.rglob("*.html")):
        info("Build directory is empty or doesn't exist. Generating site...")
        success_result = generator.generate(verbose=False)
        if not success_result:
            error("Failed to generate site")
            return

    # Initialize server
    server = LiveReloadServer(
        build_dir=generator.build_dir, host=host, port=port, enable_reload=enable_reload
    )

    # Start server
    await server.start()

    # Setup file watcher if live reload is enabled
    watcher = None
    if enable_reload:

        async def on_file_change(path: Path) -> None:
            """Handle file changes."""
            # We reassign `generator` below when config changes; declare nonlocal to
            # avoid UnboundLocalError due to Python's scope rules.
            nonlocal generator
            info(f"\nFile changed: {path.name}")

            # Determine what changed
            should_notify = False

            if "pages" in str(path):
                # Regenerate specific page
                if path.suffix == ".py" and path.name != "__init__.py":
                    if generator.regenerate_page(path, verbose=False):
                        should_notify = True
            elif "components" in str(path):
                # Component changed - regenerate all pages
                info("Component changed, regenerating all pages...")
                if generator.generate(verbose=False):
                    should_notify = True
            elif "styles" in str(path) or "public" in str(path):
                # Recopy assets
                info("Copying assets...")
                generator._copy_assets(verbose=False)
                should_notify = True
            elif path.name == "nitro.config.py":
                # Config changed - regenerate entire site
                info("Config changed, regenerating site...")
                generator = Generator()  # Reload config
                if generator.generate(verbose=False):
                    should_notify = True
            else:
                # Other changes - regenerate entire site
                if generator.generate(verbose=False):
                    should_notify = True

            # Notify clients to reload
            if should_notify:
                await server.notify_reload()
                success("Changes applied, browser reloaded")

        def on_file_change_sync(path: Path) -> None:
            """Sync wrapper for file change handler."""
            asyncio.create_task(on_file_change(path))

        watcher = Watcher(generator.project_root, on_file_change_sync)
        watcher.start()

    try:
        # Run server forever
        info("\nPress Ctrl+C to stop the server\n")
        await asyncio.Event().wait()

    except asyncio.CancelledError:
        pass
    finally:
        # Cleanup
        if watcher:
            watcher.stop()
        await server.stop()
