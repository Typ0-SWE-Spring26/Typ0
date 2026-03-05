"""Multiplayer WebSocket client — compatible with native Python and pygbag (browser/WASM).

In the browser (pygbag/pyodide) the standard `websockets` library is unavailable,
so we fall back to the browser's native WebSocket API via the `js` and `pyodide.ffi`
modules.  Both paths expose the same `MultiplayerClient` interface.
"""
import asyncio
import json

# ---------------------------------------------------------------------------
# Environment detection
# ---------------------------------------------------------------------------

try:
    import js as _js                    # noqa: F401  (browser-only)
    import pyodide.ffi as _pyodide_ffi  # noqa: F401  (browser-only)
    _IN_BROWSER = True
except ImportError:
    _IN_BROWSER = False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class MultiplayerClient:
    """Async WebSocket client for TYP0 multiplayer.

    Usage (both environments):
        client = MultiplayerClient()
        await client.connect("Alice", settings_flags=0)
        msg = await client.poll()   # non-blocking; returns dict or None
        await client.send_sequence_add("left")
        await client.disconnect()
    """

    SERVER_URL = "ws://localhost:8765"

    def __init__(self):
        self._ws = None           # native websockets connection or JS WebSocket
        self._queue: asyncio.Queue = asyncio.Queue()
        self._open_event: asyncio.Event = asyncio.Event()
        self.username: str = ""
        self.role: str | None = None        # 'host' or 'guest'
        self.opponent: str | None = None
        self.connected: bool = False

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    async def connect(self, username: str, settings_flags: int = 0) -> None:
        """Open WebSocket and announce presence to the server."""
        self.username = username
        self._open_event.clear()

        if _IN_BROWSER:
            await self._connect_browser()
        else:
            await self._connect_native()

        # Send hello after connection is established
        await self.send({"type": "hello", "username": username, "settings": settings_flags})
        self.connected = True

    async def _connect_browser(self) -> None:
        """Browser path: use pyodide js.WebSocket."""
        from js import WebSocket as _JSWebSocket
        from pyodide.ffi import create_proxy

        loop = asyncio.get_event_loop()

        ws = _JSWebSocket.new(self.SERVER_URL)
        self._ws = ws

        def _on_open(e):
            loop.call_soon_threadsafe(self._open_event.set)

        def _on_message(e):
            try:
                data = json.loads(str(e.data))
            except Exception:
                return
            loop.call_soon_threadsafe(self._queue.put_nowait, data)

        def _on_close(e):
            self.connected = False

        ws.onopen    = create_proxy(_on_open)
        ws.onmessage = create_proxy(_on_message)
        ws.onclose   = create_proxy(_on_close)

        # Wait up to 10 s for the connection to open
        await asyncio.wait_for(self._open_event.wait(), timeout=10)

    async def _connect_native(self) -> None:
        """Native Python path: use the `websockets` library."""
        import websockets  # type: ignore
        self._ws = await websockets.connect(self.SERVER_URL)
        self._open_event.set()
        # Start background reader task
        asyncio.get_event_loop().create_task(self._native_reader())

    async def _native_reader(self) -> None:
        """Background task: read messages from native websockets and queue them."""
        try:
            import websockets
            async for raw in self._ws:
                try:
                    data = json.loads(raw)
                    await self._queue.put(data)
                except Exception:
                    pass
        except Exception:
            self.connected = False

    # ------------------------------------------------------------------
    # Sending
    # ------------------------------------------------------------------

    async def send(self, msg: dict) -> None:
        """Serialize *msg* as JSON and send it over the WebSocket."""
        raw = json.dumps(msg)
        if _IN_BROWSER:
            self._ws.send(raw)
        else:
            await self._ws.send(raw)

    async def send_sequence_add(self, button: str) -> None:
        await self.send({"type": "sequence_add", "button": button})

    async def send_input_result(self, index: int, result: str, score: int) -> None:
        await self.send({"type": "input_result", "index": index, "result": result, "score": score})

    async def send_game_over(self, score: int, reason: str) -> None:
        await self.send({"type": "game_over", "score": score, "reason": reason})

    # ------------------------------------------------------------------
    # Receiving
    # ------------------------------------------------------------------

    async def poll(self) -> dict | None:
        """Return the next queued message without blocking, or None."""
        try:
            return self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    # ------------------------------------------------------------------
    # Disconnect
    # ------------------------------------------------------------------

    async def disconnect(self) -> None:
        if not self.connected:
            return
        try:
            await self.send({"type": "goodbye"})
        except Exception:
            pass
        self.connected = False
        if _IN_BROWSER:
            self._ws.close()
        else:
            await self._ws.close()
