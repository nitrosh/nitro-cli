"""Development server for Nitro sites."""

import asyncio
import mimetypes
from pathlib import Path
from typing import Set, Optional

import aiofiles
from aiohttp import web, WSMsgType

from ..utils import success, info, error, warning, verbose, debug, console


class LiveReloadServer:
    """Development server with live reload capability."""

    def __init__(
        self,
        build_dir: Path,
        host: str = "localhost",
        port: int = 3000,
        enable_reload: bool = True,
    ):
        self.build_dir = build_dir
        self.host = host
        self.port = port
        self.enable_reload = enable_reload
        self.app = web.Application(middlewares=[self._access_log_middleware])
        self.websockets: Set[web.WebSocketResponse] = set()
        self.runner: Optional[web.AppRunner] = None
        self._setup_routes()
        mimetypes.init()

    @web.middleware
    async def _access_log_middleware(self, request, handler):
        """Log requests in a clean, minimal format."""
        resp = await handler(request)
        if not request.path.startswith("/__nitro__"):
            status = resp.status
            if status >= 400:
                console.print(f"  [red]{request.method} {request.path} {status}[/red]")
            else:
                console.print(f"  [dim]{request.method} {request.path} {status}[/dim]")
        return resp

    def _setup_routes(self) -> None:
        self.app.router.add_get("/", self.handle_index)
        self.app.router.add_get("/__nitro__/livereload", self.handle_websocket)
        self.app.router.add_get("/__nitro__/livereload.js", self.handle_livereload_js)
        self.app.router.add_get("/{path:.*}", self.handle_static)

    async def handle_index(self, request: web.Request) -> web.Response:
        return await self.serve_file("index.html")

    async def handle_static(self, request: web.Request) -> web.Response:
        path = request.match_info["path"]

        if not Path(path).suffix:
            html_path = f"{path}.html" if path else "index.html"
            return await self.serve_file(html_path)

        return await self.serve_file(path)

    async def serve_file(self, path: str) -> web.Response:
        file_path = self.build_dir / path

        # Resolve paths asynchronously to avoid blocking the event loop
        try:
            resolved_path = await asyncio.to_thread(file_path.resolve)
            build_dir_resolved = await asyncio.to_thread(self.build_dir.resolve)
            if not resolved_path.is_relative_to(build_dir_resolved):
                warning(f"Path traversal attempt blocked: {path}")
                return web.Response(text="Forbidden", status=403)
        except (ValueError, OSError):
            return web.Response(text="Forbidden", status=403)

        # Use resolved_path consistently after security check
        if not await asyncio.to_thread(resolved_path.exists):
            if resolved_path.suffix == ".html":
                alt_path = build_dir_resolved / path.replace(".html", "")
                alt_resolved = await asyncio.to_thread(alt_path.resolve)
                if not alt_resolved.is_relative_to(build_dir_resolved):
                    warning(f"Path traversal attempt blocked: {path}")
                    return web.Response(text="Forbidden", status=403)
                if await asyncio.to_thread(alt_resolved.exists):
                    resolved_path = alt_resolved
                else:
                    return web.Response(text="Not Found", status=404)
            else:
                return web.Response(text="Not Found", status=404)

        try:
            async with aiofiles.open(resolved_path, "rb") as f:
                content = await f.read()

            mime_type, _ = mimetypes.guess_type(str(resolved_path))
            if mime_type is None:
                mime_type = "application/octet-stream"

            if self.enable_reload and mime_type == "text/html":
                content = self._inject_livereload(content)

            return web.Response(body=content, content_type=mime_type)

        except Exception as e:
            error(f"Error serving file {path}: {e}")
            return web.Response(text="Internal Server Error", status=500)

    def _inject_livereload(self, html_content: bytes) -> bytes:
        livereload_script = b"""
<script src="/__nitro__/livereload.js"></script>
</body>"""

        if b"</body>" in html_content:
            return html_content.replace(b"</body>", livereload_script)
        return html_content + livereload_script

    async def handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self.websockets.add(ws)
        debug(f"Client connected (total: {len(self.websockets)})")

        try:
            async for msg in ws:
                if msg.type == WSMsgType.ERROR:
                    error(f"WebSocket error: {ws.exception()}")
        finally:
            self.websockets.discard(ws)
            if not ws.closed:
                await ws.close()
            debug(f"Client disconnected (total: {len(self.websockets)})")

        return ws

    async def handle_livereload_js(self, request: web.Request) -> web.Response:
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

        dead_sockets = set()
        for ws in list(self.websockets):
            try:
                await ws.send_str(message)
            except Exception as e:
                warning(f"Failed to send reload notification to client: {e}")
                dead_sockets.add(ws)

        self.websockets -= dead_sockets

        if self.websockets:
            debug(f"Sent reload notification to {len(self.websockets)} client(s)")

    async def start(self) -> None:
        """Start the server."""
        self.runner = web.AppRunner(self.app, access_log=None)
        await self.runner.setup()

        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()

        success(f"Development server running at http://{self.host}:{self.port}")
        if self.enable_reload:
            info("Live reload enabled")

    async def stop(self) -> None:
        """Stop the server gracefully."""
        if self.websockets:
            for ws in list(self.websockets):
                try:
                    if not ws.closed:
                        await ws.close(code=1001, message=b"Server shutting down")
                except Exception as e:
                    # Log but continue cleanup - client may already be disconnected
                    warning(f"Error closing WebSocket during shutdown: {e}")
            self.websockets.clear()

        if self.runner:
            await self.runner.cleanup()
            info("Server stopped")
