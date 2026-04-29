#!/usr/bin/env python3
"""TYP0 unified server — game static files, multiplayer WebSocket, and Score API
all served from a single aiohttp app on one port.

Run with:
    pip install -r server/requirements.txt
    ADMIN_PASSWORD=your_password STATIC_DIR=build/web python server/server.py

Routes:
    GET  /ws                      -> multiplayer WebSocket
    GET  /scores/{game_type}      -> JSON array of top 10
    POST /scores/{game_type}      -> body {"name":"..","score":0}, returns top 10
    GET  /admin                   -> admin login + vitals dashboard (HTML)
    GET  /api/admin/vitals        -> project health/stats (requires Authorization: Bearer ADMIN_PASSWORD)
    GET  /*                       -> pygbag build (STATIC_DIR)

Valid game_type values: simon, bopit, keys_ninja, multiplayer
"""

import asyncio
import hmac
import json
import os
import random
import subprocess
import time
from datetime import datetime
from pathlib import Path

from aiohttp import WSMsgType, web

try:
    from scores import load_scores, add_score, is_high_score, VALID_GAME_TYPES
except ImportError:
    from server.scores import load_scores, add_score, is_high_score, VALID_GAME_TYPES

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "15090"))
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin_secret_123")
STATIC_DIR = os.environ.get(
    "STATIC_DIR",
    str(Path(__file__).resolve().parent.parent / "build" / "web"),
)

# Server startup time for uptime tracking
_server_start_time = time.time()

CORS_HEADERS = {"Access-Control-Allow-Origin": "*"}

# Admin endpoint accepts a custom Authorization header, which makes it a
# non-simple CORS request — browsers send a preflight OPTIONS that needs
# Allow-Headers explicitly listed.
ADMIN_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Authorization",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
}

# name -> websocket connection
_players: dict[str, web.WebSocketResponse] = {}

# challenger_name -> (target_name, settings_bitmask)
_pending_challenges: dict[str, tuple[str, int]] = {}

# player_name -> session_id
_active_games: dict[str, str] = {}

# session_id -> session dict
_sessions: dict[str, dict] = {}


async def _broadcast_lobby() -> None:
    """Send the current available-player list to every connected client."""
    available = [n for n in _players if n not in _active_games]
    msg = json.dumps({"type": "player_list", "players": available})
    for ws in list(_players.values()):
        try:
            await ws.send_str(msg)
        except Exception:
            pass


async def _safe_send(name: str, data: dict) -> None:
    """Send to a player by name, swallowing errors if they've disconnected."""
    ws = _players.get(name)
    if ws:
        try:
            await ws.send_str(json.dumps(data))
        except Exception:
            pass


async def ws_handler(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    await _ws_session(ws)
    return ws


async def _ws_session(ws) -> None:
    """Run a single WebSocket session.

    Extracted from ws_handler so unit tests can pass a fake ws without
    needing a real aiohttp request to call .prepare() on.
    """
    name: str | None = None
    try:
        async for aio_msg in ws:
            if aio_msg.type != WSMsgType.TEXT:
                continue
            try:
                msg = json.loads(aio_msg.data)
            except (json.JSONDecodeError, ValueError):
                continue

            t = msg.get("type", "")

            # ── JOIN ────────────────────────────────────────────────────
            if t == "join":
                requested = str(msg.get("name", "")).strip()[:20]
                if not requested:
                    await ws.send_str(json.dumps(
                        {"type": "error", "message": "Name cannot be empty"}
                    ))
                    continue
                if requested in _players:
                    await ws.send_str(json.dumps(
                        {"type": "error", "message": "Name already taken"}
                    ))
                    continue
                name = requested
                _players[name] = ws
                await ws.send_str(json.dumps({"type": "joined", "name": name}))
                print(f"[+] {name} joined  ({len(_players)} online)")
                await _broadcast_lobby()

            # ── CHALLENGE ───────────────────────────────────────────────
            elif t == "challenge" and name:
                target = str(msg.get("target", ""))
                # Clamp settings to 8 bits
                settings = int(msg.get("settings", 0)) & 0xFF

                if target == name:
                    continue
                if target not in _players:
                    await ws.send_str(json.dumps(
                        {"type": "error", "message": "Player not found"}
                    ))
                    continue
                if target in _active_games:
                    await ws.send_str(json.dumps(
                        {"type": "error", "message": f"{target} is already in a game"}
                    ))
                    continue
                if name in _active_games:
                    continue

                _pending_challenges[name] = (target, settings)
                await _safe_send(target, {
                    "type": "challenge_received",
                    "from": name,
                    "settings": settings,
                })

            # ── CHALLENGE RESPONSE ──────────────────────────────────────
            elif t == "challenge_response" and name:
                accepted = bool(msg.get("accepted", False))

                # Find which challenger sent us a challenge
                challenger = next(
                    (ch for ch, (tgt, _) in _pending_challenges.items()
                     if tgt == name),
                    None,
                )
                if not challenger or challenger not in _players:
                    continue

                _, settings = _pending_challenges.pop(challenger)

                if accepted:
                    seed = random.randint(0, 2 ** 31 - 1)
                    session_id = f"{challenger}:{name}"
                    _sessions[session_id] = {
                        "players": [challenger, name],
                        "seed": seed,
                        "settings": settings,
                        "scores": {challenger: 0, name: 0},
                        "finished": False,
                    }
                    _active_games[challenger] = session_id
                    _active_games[name] = session_id

                    for player, opponent in [(challenger, name), (name, challenger)]:
                        await _safe_send(player, {
                            "type": "game_start",
                            "seed": seed,
                            "settings": settings,
                            "opponent": opponent,
                        })

                    print(f"[game] {challenger} vs {name}  seed={seed}  settings={settings:#04x}")
                    await _broadcast_lobby()
                else:
                    await _safe_send(challenger, {
                        "type": "challenge_declined",
                        "opponent": name,
                    })

            # ── SCORE UPDATE (round completed) ───────────────────────────
            elif t == "score_update" and name:
                session_id = _active_games.get(name)
                if not session_id or session_id not in _sessions:
                    continue
                session = _sessions[session_id]
                score = int(msg.get("score", 0))
                session["scores"][name] = score
                opponent = next(p for p in session["players"] if p != name)
                await _safe_send(opponent, {
                    "type": "opponent_score",
                    "score": score,
                })

            # ── MISTAKE (player lost) ────────────────────────────────────
            elif t == "mistake" and name:
                session_id = _active_games.get(name)
                if not session_id or session_id not in _sessions:
                    continue
                session = _sessions[session_id]
                if session["finished"]:
                    continue  # second mistake in same session — ignore
                session["finished"] = True

                opponent = next(p for p in session["players"] if p != name)
                loser_score = session["scores"].get(name, 0)
                winner_score = session["scores"].get(opponent, 0)

                await _safe_send(name, {
                    "type": "you_lose",
                    "your_score": loser_score,
                    "opponent_score": winner_score,
                    "opponent": opponent,
                })
                await _safe_send(opponent, {
                    "type": "you_win",
                    "your_score": winner_score,
                    "opponent_score": loser_score,
                    "opponent": name,
                })

                print(f"[end] {opponent} beat {name}  ({winner_score} vs {loser_score})")

                _active_games.pop(name, None)
                _active_games.pop(opponent, None)
                _sessions.pop(session_id, None)
                await _broadcast_lobby()

    finally:
        if name:
            print(f"[-] {name} disconnected")
            _players.pop(name, None)
            _pending_challenges.pop(name, None)

            # Cancel any pending challenge targeting this player
            for ch in list(_pending_challenges):
                if _pending_challenges[ch][0] == name:
                    del _pending_challenges[ch]

            # Notify opponent of abandoned active game
            session_id = _active_games.pop(name, None)
            if session_id and session_id in _sessions:
                session = _sessions.pop(session_id)
                if not session["finished"]:
                    opponent = next(
                        (p for p in session["players"] if p != name), None
                    )
                    if opponent:
                        _active_games.pop(opponent, None)
                        await _safe_send(opponent, {"type": "opponent_disconnected"})

            await _broadcast_lobby()


# ── HTTP Score API ───────────────────────────────────────────────────────────

async def handle_get_scores(request: web.Request) -> web.Response:
    game_type = request.match_info["game_type"]
    if game_type not in VALID_GAME_TYPES:
        return web.Response(status=404, text="Unknown game type")
    return web.json_response(load_scores(game_type))


async def handle_close_connections(request: web.Request) -> web.Response:
    """Administratively close WebSocket connections.

    POST /admin/close                -> close every active connection
    POST /admin/close/{name}         -> close a single player by name
    """
    target = request.match_info.get("name")
    closed = []

    # Snapshot first so mutations from the finally block in handler() don't
    # invalidate the iteration.
    if target:
        ws = _players.get(target)
        candidates = [(target, ws)] if ws else []
    else:
        candidates = list(_players.items())

    for name, ws in candidates:
        try:
            await ws.close(code=1001, reason="Server requested close")
            closed.append(name)
        except Exception:
            pass

    return web.Response(
        text=json.dumps({"closed": closed}),
        content_type="application/json",
        headers=CORS_HEADERS,
    )


async def handle_post_score(request: web.Request) -> web.Response:
    game_type = request.match_info["game_type"]
    if game_type not in VALID_GAME_TYPES:
        return web.Response(status=404, text="Unknown game type")
    try:
        body = await request.json()
        name = str(body["name"]).strip()[:20]
        score = int(body["score"])
    except Exception:
        return web.Response(status=400, text="Invalid body")
    if not name:
        return web.Response(status=400, text="Name required")
    if not is_high_score(score, game_type):
        return web.json_response(load_scores(game_type))
    updated = add_score(name, score, game_type)
    print(f"[score] {game_type}  {name}={score}")
    return web.json_response(updated)


def _check_admin_auth(request: web.Request) -> bool:
    """Constant-time check of the Authorization: Bearer header against ADMIN_PASSWORD."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return False
    presented = header[len("Bearer "):]
    return hmac.compare_digest(presented, ADMIN_PASSWORD)


async def handle_admin_vitals(request: web.Request) -> web.Response:
    """Admin endpoint to get project vitals (health/stats).

    Requires header: Authorization: Bearer <ADMIN_PASSWORD>
    Returns JSON with test results, git info, server status, etc.
    """
    if not _check_admin_auth(request):
        return web.Response(
            status=401,
            text="Unauthorized",
            headers=ADMIN_CORS_HEADERS,
        )
    
    # Gather vitals
    uptime_seconds = time.time() - _server_start_time
    uptime_hours = uptime_seconds / 3600
    
    # Active multiplayer stats
    active_players = len(_players)
    active_games = len(_active_games)
    pending_challenges = len(_pending_challenges)
    
    # Score database stats
    score_stats = {}
    for game_type in VALID_GAME_TYPES:
        scores = load_scores(game_type)
        score_stats[game_type] = {
            "count": len(scores),
            "top_score": scores[0]["score"] if scores else 0,
            "top_player": scores[0]["name"] if scores else None,
        }
    
    # Git info (if available)
    git_info = {}
    try:
        git_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(Path(__file__).parent.parent),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        git_info["commit"] = git_hash
    except Exception:
        git_info["commit"] = "unknown"
    
    try:
        git_branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(Path(__file__).parent.parent),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        git_info["branch"] = git_branch
    except Exception:
        git_info["branch"] = "unknown"
    
    # Build timestamp
    version_file = Path(__file__).parent.parent / "build" / "version.txt"
    build_time = None
    try:
        with open(version_file) as f:
            build_time = f.read().strip()
    except Exception:
        build_time = "unknown"
    
    vitals = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "server": {
            "uptime_seconds": round(uptime_seconds, 2),
            "uptime_hours": round(uptime_hours, 2),
            "host": HOST,
            "port": PORT,
        },
        "multiplayer": {
            "active_players": active_players,
            "active_games": active_games,
            "pending_challenges": pending_challenges,
        },
        "scores": score_stats,
        "build": {
            "timestamp": build_time,
            "static_dir": str(STATIC_DIR),
        },
        "git": git_info,
    }
    
    return web.json_response(vitals, headers=ADMIN_CORS_HEADERS)


async def handle_admin_options(_request: web.Request) -> web.Response:
    """CORS preflight for /api/admin/vitals."""
    return web.Response(status=204, headers=ADMIN_CORS_HEADERS)


_ADMIN_PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>TYP0 admin</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  :root { color-scheme: dark; }
  body {
    margin: 0; padding: 2rem; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    background: #0e0e12; color: #e6e6e6;
  }
  h1 { margin: 0 0 1.5rem; font-size: 1.4rem; color: #7ad7ff; }
  h2 { font-size: 1rem; margin: 1.5rem 0 .5rem; color: #b4f0a8; text-transform: uppercase; letter-spacing: .08em; }
  .card { background: #16161d; border: 1px solid #2a2a35; border-radius: 6px; padding: 1rem 1.25rem; max-width: 720px; }
  .row { display: flex; justify-content: space-between; padding: .25rem 0; border-bottom: 1px dashed #2a2a35; }
  .row:last-child { border-bottom: none; }
  .row span:first-child { color: #9aa0a6; }
  table { width: 100%; border-collapse: collapse; font-size: .9rem; }
  th, td { text-align: left; padding: .35rem .5rem; border-bottom: 1px solid #2a2a35; }
  th { color: #9aa0a6; font-weight: normal; }
  form { display: flex; gap: .5rem; max-width: 420px; }
  input[type=password] {
    flex: 1; padding: .5rem .75rem; background: #16161d; color: #e6e6e6;
    border: 1px solid #2a2a35; border-radius: 4px; font: inherit;
  }
  button {
    padding: .5rem 1rem; background: #2d6cdf; color: white; border: 0;
    border-radius: 4px; font: inherit; cursor: pointer;
  }
  button:hover { background: #3b7ce8; }
  .err { color: #ff7373; margin-top: .75rem; }
  .muted { color: #9aa0a6; font-size: .85rem; margin-top: 1rem; }
</style>
</head>
<body>
<h1>TYP0 admin</h1>
<div id="login" class="card">
  <form id="login-form">
    <input type="password" id="pw" placeholder="admin password" autocomplete="current-password" autofocus>
    <button type="submit">Sign in</button>
  </form>
  <div id="err" class="err" hidden></div>
</div>
<div id="dash" hidden></div>

<script>
const $ = (id) => document.getElementById(id);
let token = null;
let timer = null;

async function fetchVitals() {
  const res = await fetch('/api/admin/vitals', {
    headers: { 'Authorization': 'Bearer ' + token },
    cache: 'no-store',
  });
  if (res.status === 401) throw new Error('unauthorized');
  if (!res.ok) throw new Error('http ' + res.status);
  return res.json();
}

function renderRow(label, value) {
  return `<div class="row"><span>${label}</span><span>${value ?? '—'}</span></div>`;
}

function render(v) {
  const s = v.server, m = v.multiplayer, sc = v.scores, b = v.build, g = v.git;
  const rows = (game) => `
    <tr>
      <td>${game}</td>
      <td>${sc[game].count}</td>
      <td>${sc[game].top_score}</td>
      <td>${sc[game].top_player ?? '—'}</td>
    </tr>`;
  $('dash').innerHTML = `
    <h2>Server</h2>
    <div class="card">
      ${renderRow('Uptime', s.uptime_hours + ' h (' + s.uptime_seconds + ' s)')}
      ${renderRow('Host', s.host + ':' + s.port)}
      ${renderRow('Timestamp', v.timestamp)}
    </div>
    <h2>Multiplayer</h2>
    <div class="card">
      ${renderRow('Active players', m.active_players)}
      ${renderRow('Active games', m.active_games)}
      ${renderRow('Pending challenges', m.pending_challenges)}
    </div>
    <h2>Scores</h2>
    <div class="card">
      <table>
        <thead><tr><th>Game</th><th>Count</th><th>Top</th><th>Player</th></tr></thead>
        <tbody>${Object.keys(sc).map(rows).join('')}</tbody>
      </table>
    </div>
    <h2>Build / Git</h2>
    <div class="card">
      ${renderRow('Build timestamp', b.timestamp)}
      ${renderRow('Static dir', b.static_dir)}
      ${renderRow('Git commit', g.commit)}
      ${renderRow('Git branch', g.branch)}
    </div>
    <p class="muted">Auto-refresh every 10 s. <a href="#" id="logout" style="color:#7ad7ff">Sign out</a></p>
  `;
  $('logout').onclick = (e) => { e.preventDefault(); signOut(); };
}

async function refresh() {
  try {
    render(await fetchVitals());
  } catch (e) {
    if (e.message === 'unauthorized') signOut('Session rejected — sign in again.');
    else $('dash').innerHTML = '<p class="err">Refresh failed: ' + e.message + '</p>';
  }
}

function signOut(msg) {
  token = null;
  if (timer) { clearInterval(timer); timer = null; }
  $('dash').hidden = true;
  $('dash').innerHTML = '';
  $('login').hidden = false;
  $('pw').value = '';
  $('pw').focus();
  if (msg) { $('err').textContent = msg; $('err').hidden = false; }
}

$('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  $('err').hidden = true;
  token = $('pw').value;
  try {
    const v = await fetchVitals();
    $('login').hidden = true;
    $('dash').hidden = false;
    render(v);
    timer = setInterval(refresh, 10000);
  } catch (err) {
    token = null;
    $('err').textContent = err.message === 'unauthorized'
      ? 'Wrong password.' : 'Error: ' + err.message;
    $('err').hidden = false;
  }
});
</script>
</body>
</html>
"""


async def handle_admin_page(_request: web.Request) -> web.Response:
    return web.Response(text=_ADMIN_PAGE_HTML, content_type="text/html")


def build_app() -> web.Application:
    app = web.Application()

    # Dynamic routes first so they win over the static catch-all.
    app.router.add_get("/ws", ws_handler)
    app.router.add_get("/scores/{game_type}", handle_get_scores)
    app.router.add_post("/scores/{game_type}", handle_post_score)
    app.router.add_get("/api/admin/vitals", handle_admin_vitals)
    app.router.add_route("OPTIONS", "/api/admin/vitals", handle_admin_options)
    app.router.add_get("/admin", handle_admin_page)

    # Pygbag build (game). aiohttp's add_static doesn't serve index.html
    # automatically, so wire up a root handler that returns it explicitly.
    # show_index stays False — we don't want directory listings exposed.
    static_path = Path(STATIC_DIR)
    if static_path.is_dir():
        index_file = static_path / "index.html"

        async def serve_index(_request: web.Request) -> web.FileResponse:
            return web.FileResponse(index_file)

        app.router.add_get("/", serve_index)
        app.router.add_static("/", path=str(static_path), show_index=False)
    else:
        print(f"[warn] STATIC_DIR {static_path} not found — static serving disabled")

    return app


def main() -> None:
    print(f"TYP0 unified server  http://{HOST}:{PORT}")
    print(f"  static dir : {STATIC_DIR}")
    print(f"  websocket  : /ws")
    print(f"  score api  : /scores/{{game_type}}")
    print(f"  admin api  : /api/admin/vitals  (header: Authorization: Bearer <ADMIN_PASSWORD>)")
    print(f"  admin gui  : /admin")
    web.run_app(build_app(), host=HOST, port=PORT, print=None)


if __name__ == "__main__":
    main()
