"""Development server for Nitro sites."""

import asyncio
import mimetypes
from pathlib import Path
from typing import Set, Optional

import aiofiles
from aiohttp import web, WSMsgType

from ..utils import success, info, error


class LiveReloadServer:
    """Development server with live reload capability."""

    def __init__(
        self,
        build_dir: Path,
        host: str = "localhost",
        port: int = 3000,
        enable_reload: bool = True,
    ):
        """
        Initialize server.

        Args:
            build_dir: Directory containing built files
            host: Host address
            port: Port number
            enable_reload: Enable live reload
        """
        self.build_dir = build_dir
        self.host = host
        self.port = port
        self.enable_reload = enable_reload
        self.app = web.Application()
        self.websockets: Set[web.WebSocketResponse] = set()
        self.runner: Optional[web.AppRunner] = None

        # Setup routes
        self._setup_routes()

        # Initialize MIME types
        mimetypes.init()

    def _setup_routes(self) -> None:
        """Setup HTTP routes."""
        self.app.router.add_get("/", self.handle_index)
        self.app.router.add_get("/__nitro__/livereload", self.handle_websocket)
        self.app.router.add_get("/__nitro__/livereload.js", self.handle_livereload_js)
        self.app.router.add_get("/{path:.*}", self.handle_static)

    async def handle_index(self, request: web.Request) -> web.Response:
        """Handle index page request.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        return await self.serve_file("index.html")

    async def handle_static(self, request: web.Request) -> web.Response:
        """Handle static file requests.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        path = request.match_info["path"]

        # If no extension, try adding .html
        if not Path(path).suffix:
            html_path = f"{path}.html" if path else "index.html"
            return await self.serve_file(html_path)

        return await self.serve_file(path)

    async def serve_file(self, path: str) -> web.Response:
        """Serve a file from build directory.

        Args:
            path: File path

        Returns:
            HTTP response
        """
        file_path = self.build_dir / path

        # Security: Prevent path traversal attacks
        try:
            resolved_path = file_path.resolve()
            build_dir_resolved = self.build_dir.resolve()
            if not resolved_path.is_relative_to(build_dir_resolved):
                return web.Response(text="Forbidden", status=403)
        except (ValueError, OSError):
            return web.Response(text="Forbidden", status=403)

        if not file_path.exists():
            # Try without .html
            if file_path.suffix == ".html":
                alt_path = self.build_dir / path.replace(".html", "")
                if alt_path.exists():
                    file_path = alt_path
                else:
                    return web.Response(text="Not Found", status=404)
            else:
                return web.Response(text="Not Found", status=404)

        try:
            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()

            # Get MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type is None:
                mime_type = "application/octet-stream"

            # Inject live reload script for HTML files
            if self.enable_reload and mime_type == "text/html":
                content = self._inject_livereload(content)

            return web.Response(body=content, content_type=mime_type)

        except Exception as e:
            error(f"Error serving file {path}: {e}")
            return web.Response(text="Internal Server Error", status=500)

    def _inject_livereload(self, html_content: bytes) -> bytes:
        """Inject live reload script into HTML.

        Args:
            html_content: Original HTML content

        Returns:
            Modified HTML content
        """
        livereload_script = b"""
<script src="/__nitro__/livereload.js"></script>
</body>"""

        # Try to inject before closing body tag
        if b"</body>" in html_content:
            return html_content.replace(b"</body>", livereload_script)

        # Fallback: append to end
        return html_content + livereload_script

    async def handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connections for live reload.

        Args:
            request: HTTP request

        Returns:
            WebSocket response
        """
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self.websockets.add(ws)
        info(f"Client connected (total: {len(self.websockets)})")

        try:
            async for msg in ws:
                if msg.type == WSMsgType.ERROR:
                    error(f"WebSocket error: {ws.exception()}")
        finally:
            self.websockets.discard(ws)
            # Explicitly close the WebSocket connection
            if not ws.closed:
                await ws.close()
            info(f"Client disconnected (total: {len(self.websockets)})")

        return ws

    async def handle_livereload_js(self, request: web.Request) -> web.Response:
        """Serve live reload JavaScript client.

        Args:
            request: HTTP request

        Returns:
            HTTP response with JavaScript
        """
        js_content = """
(function() {
    console.log('[Nitro] Live reload enabled');

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const ws = new WebSocket(protocol + '//' + host + '/__nitro__/livereload');

    ws.onopen = function() {
        console.log('[Nitro] Connected to live reload server');
    };

    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        console.log('[Nitro] Received:', data);

        if (data.type === 'reload') {
            console.log('[Nitro] Reloading page...');
            window.location.reload();
        }
    };

    ws.onclose = function() {
        console.log('[Nitro] Disconnected from live reload server');
        // Try to reconnect after 1 second
        setTimeout(function() {
            window.location.reload();
        }, 1000);
    };

    ws.onerror = function(error) {
        console.error('[Nitro] WebSocket error:', error);
    };
})();
"""
        return web.Response(text=js_content, content_type="application/javascript")

    async def notify_reload(self) -> None:
        """Notify all connected clients to reload."""
        if not self.websockets:
            return

        message = '{"type": "reload"}'

        # Send reload message to all connected clients
        # Copy the set to avoid modification during iteration (race condition)
        dead_sockets = set()
        for ws in list(self.websockets):
            try:
                await ws.send_str(message)
            except Exception:
                dead_sockets.add(ws)

        # Clean up dead connections
        self.websockets -= dead_sockets

        if self.websockets:
            info(f"Sent reload notification to {len(self.websockets)} client(s)")

    async def start(self) -> None:
        """Start the server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()

        success(f"Development server running at http://{self.host}:{self.port}")
        if self.enable_reload:
            info("Live reload enabled")

    async def stop(self) -> None:
        """Stop the server gracefully."""
        # Close all WebSocket connections first
        if self.websockets:
            for ws in list(self.websockets):
                try:
                    if not ws.closed:
                        await ws.close(code=1001, message=b"Server shutting down")
                except Exception:
                    pass
            self.websockets.clear()

        # Cleanup the runner (stops accepting new connections)
        if self.runner:
            await self.runner.cleanup()
            info("Server stopped")

    async def run_forever(self) -> None:
        """Run the server forever."""
        await self.start()

        try:
            # Keep running
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()
