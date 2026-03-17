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

import sys

_IN_BROWSER = sys.platform == "emscripten"

if not _IN_BROWSER:
    try:
        import js as _js                    # noqa: F401  (browser-only)
        _IN_BROWSER = True
    except ImportError:
        pass


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

    SERVER_URL = "ws://10.22.16.243:8765"

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
        print(f"[WS] connect() called, _IN_BROWSER={_IN_BROWSER}")
        self.username = username
        self._open_event.clear()

        if _IN_BROWSER:
            print("[WS] Taking browser path")
            await self._connect_browser()
        else:
            print("[WS] Taking native path")
            await self._connect_native()

        # Send hello after connection is established
        await self.send({"type": "hello", "username": username, "settings": settings_flags})
        self.connected = True

    async def _connect_browser(self) -> None:
        """Browser path: create JS WebSocket and buffer messages in JS."""
        import platform
        self._window = platform.window

        # Create WebSocket and message queue entirely in JavaScript
        self._window.eval(f"""
            window._ws = new WebSocket("{self.SERVER_URL}");
            window._ws_open = false;
            window._ws_closed = false;
            window._ws_msgs = [];
            window._ws.onopen = function() {{ window._ws_open = true; }};
            window._ws.onmessage = function(e) {{ window._ws_msgs.push(e.data); }};
            window._ws.onclose = function() {{ window._ws_closed = true; }};
            window._ws.onerror = function() {{ window._ws_closed = true; }};
        """)

        # Wait up to 10 s for the connection to open
        for _ in range(100):
            if self._window.eval("window._ws_open"):
                return
            if self._window.eval("window._ws_closed"):
                raise RuntimeError("WebSocket connection closed")
            await asyncio.sleep(0.1)
        raise RuntimeError("WebSocket connection timed out")

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
            # Escape backslashes and quotes for JS string
            js_safe = raw.replace("\\", "\\\\").replace("'", "\\'")
            self._window.eval(f"window._ws.send('{js_safe}');")
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
        if _IN_BROWSER:
            # Drain JS message buffer
            count = int(self._window.eval("window._ws_msgs.length"))
            if count > 0:
                raw = str(self._window.eval("window._ws_msgs.shift()"))
                try:
                    return json.loads(raw)
                except Exception:
                    return None
            # Check if connection was closed
            if self._window.eval("window._ws_closed"):
                self.connected = False
            return None
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
            self._window.eval("window._ws.close();")
        else:
            await self._ws.close()
