#!/usr/bin/env python3
"""TYP0 unified server — game static files, multiplayer WebSocket, and Score API
all served from a single aiohttp app on one port.

Run with:
    pip install -r server/requirements.txt
    STATIC_DIR=build/web python server/server.py

Routes:
    GET  /ws                   -> multiplayer WebSocket
    GET  /scores/{game_type}   -> JSON array of top 10
    POST /scores/{game_type}   -> body {"name":"..","score":0}, returns top 10
    GET  /*                    -> pygbag build (STATIC_DIR)

Valid game_type values: simon, bopit, multiplayer
"""

import asyncio
import json
import os
import random
from pathlib import Path

from aiohttp import WSMsgType, web

try:
    from scores import load_scores, add_score, is_high_score, VALID_GAME_TYPES
except ImportError:
    from server.scores import load_scores, add_score, is_high_score, VALID_GAME_TYPES

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "15090"))
STATIC_DIR = os.environ.get(
    "STATIC_DIR",
    str(Path(__file__).resolve().parent.parent / "build" / "web"),
)

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

    return ws


# ── HTTP Score API ───────────────────────────────────────────────────────────

async def handle_get_scores(request: web.Request) -> web.Response:
    game_type = request.match_info["game_type"]
    if game_type not in VALID_GAME_TYPES:
        return web.Response(status=404, text="Unknown game type")
    return web.json_response(load_scores(game_type))


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


def build_app() -> web.Application:
    app = web.Application()

    # Dynamic routes first so they win over the static catch-all.
    app.router.add_get("/ws", ws_handler)
    app.router.add_get("/scores/{game_type}", handle_get_scores)
    app.router.add_post("/scores/{game_type}", handle_post_score)

    # Pygbag build (game). show_index=True so "/" serves index.html.
    static_path = Path(STATIC_DIR)
    if static_path.is_dir():
        app.router.add_static("/", path=str(static_path), show_index=True)
    else:
        print(f"[warn] STATIC_DIR {static_path} not found — static serving disabled")

    return app


def main() -> None:
    print(f"TYP0 unified server  http://{HOST}:{PORT}")
    print(f"  static dir : {STATIC_DIR}")
    print(f"  websocket  : /ws")
    print(f"  score api  : /scores/{{game_type}}")
    web.run_app(build_app(), host=HOST, port=PORT, print=None)


if __name__ == "__main__":
    main()
