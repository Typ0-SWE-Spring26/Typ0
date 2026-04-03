#!/usr/bin/env python3
"""TYP0 Multiplayer WebSocket Server + Score API

Run with:
    pip install websockets aiohttp
    python server/server.py

WebSocket multiplayer:  ws://host:14023
Score HTTP API:         http://host:14024
  GET  /scores/{game_type}          -> JSON array of top 10
  POST /scores/{game_type}          -> body {"name":"..","score":0}, returns updated top 10
  Valid game_type values: simon, bopit, multiplayer
"""

import asyncio
import json
import random
import websockets
from websockets.exceptions import ConnectionClosed
from aiohttp import web

try:
    from scores import load_scores, add_score, is_high_score, VALID_GAME_TYPES
except ImportError:
    from server.scores import load_scores, add_score, is_high_score, VALID_GAME_TYPES

HOST = "0.0.0.0"
WS_PORT = 14023
HTTP_PORT = 14024

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}

# name -> websocket connection
_players: dict[str, websockets.ServerConnection] = {}

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
            await ws.send(msg)
        except Exception:
            pass


async def _safe_send(name: str, data: dict) -> None:
    """Send to a player by name, swallowing errors if they've disconnected."""
    ws = _players.get(name)
    if ws:
        try:
            await ws.send(json.dumps(data))
        except Exception:
            pass


async def handler(websocket) -> None:
    name: str | None = None
    try:
        async for raw in websocket:
            try:
                msg = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                continue

            t = msg.get("type", "")

            # ── JOIN ────────────────────────────────────────────────────
            if t == "join":
                requested = str(msg.get("name", "")).strip()[:20]
                if not requested:
                    await websocket.send(json.dumps(
                        {"type": "error", "message": "Name cannot be empty"}
                    ))
                    continue
                if requested in _players:
                    await websocket.send(json.dumps(
                        {"type": "error", "message": "Name already taken"}
                    ))
                    continue
                name = requested
                _players[name] = websocket
                await websocket.send(json.dumps({"type": "joined", "name": name}))
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
                    await websocket.send(json.dumps(
                        {"type": "error", "message": "Player not found"}
                    ))
                    continue
                if target in _active_games:
                    await websocket.send(json.dumps(
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

    except ConnectionClosed:
        pass
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

async def handle_options(request: web.Request) -> web.Response:
    """Handle CORS preflight requests."""
    return web.Response(headers=CORS_HEADERS)


async def handle_get_scores(request: web.Request) -> web.Response:
    game_type = request.match_info["game_type"]
    if game_type not in VALID_GAME_TYPES:
        return web.Response(status=404, text="Unknown game type",
                            headers=CORS_HEADERS)
    scores = load_scores(game_type)
    return web.Response(
        text=json.dumps(scores),
        content_type="application/json",
        headers=CORS_HEADERS,
    )


async def handle_post_score(request: web.Request) -> web.Response:
    game_type = request.match_info["game_type"]
    if game_type not in VALID_GAME_TYPES:
        return web.Response(status=404, text="Unknown game type",
                            headers=CORS_HEADERS)
    try:
        body = await request.json()
        name = str(body["name"]).strip()[:20]
        score = int(body["score"])
    except Exception:
        return web.Response(status=400, text="Invalid body",
                            headers=CORS_HEADERS)
    if not name:
        return web.Response(status=400, text="Name required",
                            headers=CORS_HEADERS)
    if not is_high_score(score, game_type):
        scores = load_scores(game_type)
        return web.Response(
            text=json.dumps(scores),
            content_type="application/json",
            headers=CORS_HEADERS,
        )
    updated = add_score(name, score, game_type)
    print(f"[score] {game_type}  {name}={score}")
    return web.Response(
        text=json.dumps(updated),
        content_type="application/json",
        headers=CORS_HEADERS,
    )


def _build_http_app() -> web.Application:
    app = web.Application()
    app.router.add_route("OPTIONS", "/scores/{game_type}", handle_options)
    app.router.add_get("/scores/{game_type}", handle_get_scores)
    app.router.add_post("/scores/{game_type}", handle_post_score)
    return app


async def main() -> None:
    print(f"TYP0 multiplayer server  ws://{HOST}:{WS_PORT}")
    print(f"TYP0 score API           http://{HOST}:{HTTP_PORT}")

    # HTTP score API
    app = _build_http_app()
    runner = web.AppRunner(app)
    await runner.setup()
    http_site = web.TCPSite(runner, HOST, HTTP_PORT)
    await http_site.start()

    # WebSocket multiplayer
    async with websockets.serve(handler, HOST, WS_PORT):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
