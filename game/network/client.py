"""Async WebSocket client for TYP0 multiplayer.

Works in two environments automatically:

* **Desktop / native** — uses the ``websockets`` library (pip install websockets).
* **Browser / pygbag WASM** — uses the browser's native JavaScript WebSocket API
  via pygbag's ``platform.window`` bridge.

  All message handling is done in JavaScript (stored in a JS array buffer).
  Python polls that buffer each frame with eval() — this avoids the fragile
  Python-function-as-JS-callback proxy that pygbag doesn't reliably support.

No code changes are needed between local dev and production.
"""

import asyncio
import json
import sys

WS_PORT = 8765
NATIVE_SERVER_URL = f"ws://localhost:{WS_PORT}"

_IN_BROWSER: bool = sys.platform == "emscripten"


def _browser_server_url() -> str:
    """Derive the WS server URL from the current page location."""
    import platform
    loc = platform.window.location
    scheme = "wss" if loc.protocol == "https:" else "ws"
    host   = str(loc.hostname)
    return f"{scheme}://{host}:{WS_PORT}"


class WebSocketClient:
    def __init__(self, url: str | None = None):
        self._override_url = url
        self._ws   = None          # native websockets connection
        self._inbox: asyncio.Queue = asyncio.Queue()
        self.connected: bool = False
        self._receive_task: asyncio.Task | None = None

    @property
    def url(self) -> str:
        if self._override_url:
            return self._override_url
        return _browser_server_url() if _IN_BROWSER else NATIVE_SERVER_URL

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Open the connection.  Raises RuntimeError on failure."""
        if _IN_BROWSER:
            await self._connect_browser()
        else:
            await self._connect_native()

    async def close(self) -> None:
        self.connected = False
        if _IN_BROWSER:
            import platform
            platform.window.eval(
                "if(window._typ0_ws){"
                "  window._typ0_ws.close();"
                "  delete window._typ0_ws;"
                "  delete window._typ0_msgs;"
                "}"
            )
        else:
            if self._receive_task:
                self._receive_task.cancel()
                self._receive_task = None
            if self._ws:
                try:
                    await self._ws.close()
                except Exception:
                    pass
                self._ws = None

    # ------------------------------------------------------------------
    # Sending / receiving
    # ------------------------------------------------------------------

    async def send(self, data: dict) -> None:
        if not self.connected:
            return
        payload = json.dumps(data)
        try:
            if _IN_BROWSER:
                import platform
                # .send() is a regular method call — works fine via the proxy
                platform.window._typ0_ws.send(payload)
            else:
                await self._ws.send(payload)
        except Exception:
            self.connected = False

    def poll(self) -> dict | None:
        """Non-blocking: returns the next incoming message dict or None."""
        if _IN_BROWSER:
            return self._poll_browser()
        try:
            return self._inbox.get_nowait()
        except asyncio.QueueEmpty:
            return None

    # ------------------------------------------------------------------
    # Native (desktop) implementation
    # ------------------------------------------------------------------

    async def _connect_native(self) -> None:
        try:
            import websockets  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "The 'websockets' package is required for multiplayer.\n"
                "Install it with:  pip install websockets"
            ) from exc

        self._ws = await websockets.connect(self.url)
        self.connected = True
        self._receive_task = asyncio.ensure_future(self._receive_loop_native())

    async def _receive_loop_native(self) -> None:
        try:
            async for raw in self._ws:
                try:
                    msg = json.loads(raw)
                except (json.JSONDecodeError, ValueError):
                    continue
                await self._inbox.put(msg)
        except Exception:
            pass
        finally:
            self.connected = False

    # ------------------------------------------------------------------
    # Browser (pygbag WASM) implementation
    #
    # Python-function-as-JS-callback proxying is unreliable in pygbag.
    # Instead, all message handling lives in JavaScript: incoming messages
    # are pushed onto a JS array (_typ0_msgs).  Python polls that array
    # every frame via eval(), which is fully reliable.
    # ------------------------------------------------------------------

    async def _connect_browser(self) -> None:
        import platform

        target_url = self.url
        safe_url   = target_url.replace("\\", "\\\\").replace("'", "\\'")

        # Create the WebSocket entirely in JS, with a JS-side message buffer.
        platform.window.eval(
            f"window._typ0_msgs = [];"
            f"window._typ0_ws = new WebSocket('{safe_url}');"
            f"window._typ0_ws.onmessage = function(e){{ _typ0_msgs.push(e.data); }};"
            f"window._typ0_ws.onclose   = function(){{ window._typ0_ws_open = false; }};"
            f"window._typ0_ws.onerror   = function(){{ window._typ0_ws_open = false; }};"
            f"window._typ0_ws.onopen    = function(){{ window._typ0_ws_open = true; }};"
            f"window._typ0_ws_open = false;"
        )

        # Poll readyState until OPEN (1) or CLOSED/ERROR (3)
        for _ in range(100):
            await asyncio.sleep(0.05)
            state = platform.window._typ0_ws.readyState
            if state == 1:          # OPEN
                self.connected = True
                return
            if state == 3:          # CLOSED
                break

        raise RuntimeError(f"Could not connect to {target_url}")

    def _poll_browser(self) -> dict | None:
        """Pop one message from the JS-side buffer, or return None."""
        import platform
        try:
            # Check if the connection dropped
            if not self.connected:
                return None
            if platform.window._typ0_ws.readyState != 1:
                self.connected = False
                return None
            # Atomically pop one message from the JS array
            raw = platform.window.eval(
                "_typ0_msgs.length ? _typ0_msgs.shift() : null"
            )
            if raw is None:
                return None
            return json.loads(str(raw))
        except Exception:
            return None
