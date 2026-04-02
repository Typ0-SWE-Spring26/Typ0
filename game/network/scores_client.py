"""Async HTTP client for the TYP0 score API.

Works in two environments:
* Browser (pygbag WASM) — uses JavaScript's fetch API via platform.window.eval()
* Native (desktop / CI) — uses urllib in a thread executor

The server runs at HTTP_PORT (14024) on the same host as the game.
"""

import asyncio
import json
import sys

HTTP_PORT = 14024
_IN_BROWSER: bool = sys.platform == "emscripten"


def _api_base() -> str:
    if _IN_BROWSER:
        import platform
        loc = platform.window.location
        scheme = "https" if loc.protocol == "https:" else "http"
        host = str(loc.hostname)
        return f"{scheme}://{host}:{HTTP_PORT}"
    return f"http://localhost:{HTTP_PORT}"


async def fetch_scores(game_type: str) -> list:
    """Return the top-10 scores for *game_type* from the server."""
    url = f"{_api_base()}/scores/{game_type}"
    if _IN_BROWSER:
        return await _browser_get(url)
    return await _native_request(url, "GET", None)


async def submit_score(name: str, score: int, game_type: str) -> list:
    """Submit a score to the server and return the updated top-10 list."""
    url = f"{_api_base()}/scores/{game_type}"
    body = {"name": name, "score": score}
    if _IN_BROWSER:
        return await _browser_post(url, body)
    return await _native_request(url, "POST", body)


# ── Browser (pygbag) implementation ─────────────────────────────────────────

async def _browser_get(url: str) -> list:
    import platform
    safe_url = json.dumps(url)   # produces a properly JS-escaped string literal
    platform.window.eval("window._typ0_score_result = undefined;")
    platform.window.eval(
        f"(async()=>{{try{{const r=await fetch({safe_url});"
        f"window._typ0_score_result=await r.json();}}"
        f"catch(e){{window._typ0_score_result=[];}}}})();"
    )
    return await _poll_browser_result()


async def _browser_post(url: str, body: dict) -> list:
    import platform
    safe_url = json.dumps(url)
    safe_body = json.dumps(json.dumps(body))  # inner dumps → JSON string, outer → JS string literal
    platform.window.eval("window._typ0_score_result = undefined;")
    platform.window.eval(
        f"(async()=>{{try{{const r=await fetch({safe_url},{{"
        f"method:'POST',headers:{{'Content-Type':'application/json'}},"
        f"body:{safe_body}}});"
        f"window._typ0_score_result=await r.json();}}"
        f"catch(e){{window._typ0_score_result=[];}}}})();"
    )
    return await _poll_browser_result()


async def _poll_browser_result(timeout_s: float = 5.0) -> list:
    """Poll the JS global until the fetch resolves or times out."""
    import platform
    steps = int(timeout_s / 0.05)
    for _ in range(steps):
        await asyncio.sleep(0.05)
        raw = platform.window.eval(
            "window._typ0_score_result !== undefined"
            " ? JSON.stringify(window._typ0_score_result) : null"
        )
        if raw is not None:
            try:
                return json.loads(str(raw))
            except Exception:
                return []
    return []


# ── Native (desktop / CI) implementation ────────────────────────────────────

async def _native_request(url: str, method: str, body) -> list:
    import urllib.request

    def _do() -> list:
        try:
            data = json.dumps(body).encode() if body else None
            headers = {"Content-Type": "application/json"} if body else {}
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            return []

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _do)
