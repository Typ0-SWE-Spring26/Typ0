"""TYP0 multiplayer WebSocket relay server.

Responsibilities:
  - Maintain a live registry of connected players (username → websocket).
  - Broker challenge/accept handshakes and start matches.
  - Relay in-game messages (sequence_add, input_result, game_over) between opponents.
  - Broadcast an updated player list to all clients whenever the registry changes.

Run locally:
    python server/server.py

Deploy to Railway / Render / Fly.io by pointing the start command at this file.
The PORT environment variable is respected so cloud platforms can assign a port.

Protocol — all messages are JSON objects with a "type" field.
See game/core/websocket.py for the full message reference.
"""
import asyncio
import json
import logging
import os
import websockets

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# username → websocket
_connected: dict[str, websockets.WebSocketServerProtocol] = {}

# username → opponent username (only set while a match is live)
_opponents: dict[str, str] = {}

# username → settings flags sent in their hello message
_settings: dict[str, int] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _send(ws: websockets.WebSocketServerProtocol, msg: dict) -> None:
    try:
        await ws.send(json.dumps(msg))
    except Exception:
        pass


async def _broadcast_player_list() -> None:
    """Send the current player list (excluding in-game players) to every client."""
    players = [
        {"username": u, "settings": _settings.get(u, 0)}
        for u in _connected
        if u not in _opponents        # hide players who are already in a match
    ]
    msg = {"type": "player_list", "players": players}
    for ws in list(_connected.values()):
        await _send(ws, msg)


def _username_for(ws: websockets.WebSocketServerProtocol) -> str | None:
    for u, w in _connected.items():
        if w is ws:
            return u
    return None


# ---------------------------------------------------------------------------
# Message handlers
# ---------------------------------------------------------------------------

async def _handle_hello(ws, data: dict) -> str | None:
    """Register the player. Returns the accepted username or None on error."""
    username = str(data.get("username", "")).strip()[:24]
    if not username:
        await _send(ws, {"type": "error", "message": "Username required."})
        return None
    if username in _connected:
        await _send(ws, {"type": "error", "message": "Username already taken."})
        return None

    _connected[username] = ws
    _settings[username] = int(data.get("settings", 0))
    log.info("+ %s joined", username)
    await _broadcast_player_list()
    return username


async def _handle_challenge(sender: str, data: dict) -> None:
    target = str(data.get("target", ""))
    if target not in _connected:
        await _send(_connected[sender], {"type": "error", "message": f"{target} is not online."})
        return
    if target in _opponents or sender in _opponents:
        await _send(_connected[sender], {"type": "error", "message": "Player is already in a match."})
        return
    await _send(_connected[target], {
        "type": "challenged",
        "from": sender,
        "settings": _settings.get(sender, 0),
    })


async def _handle_challenge_accept(sender: str, data: dict) -> None:
    host = str(data.get("from", ""))
    if host not in _connected:
        await _send(_connected[sender], {"type": "error", "message": f"{host} is no longer online."})
        return

    # Pair the two players
    _opponents[host]   = sender
    _opponents[sender] = host

    await _send(_connected[host], {
        "type": "game_start",
        "role": "host",
        "opponent": sender,
        "settings": _settings.get(sender, 0),
    })
    await _send(_connected[sender], {
        "type": "game_start",
        "role": "guest",
        "opponent": host,
        "settings": _settings.get(host, 0),
    })
    log.info("Match: %s (host) vs %s (guest)", host, sender)
    await _broadcast_player_list()


async def _handle_challenge_decline(sender: str, data: dict) -> None:
    host = str(data.get("from", ""))
    if host in _connected:
        await _send(_connected[host], {"type": "challenge_declined", "from": sender})


async def _relay_to_opponent(sender: str, msg: dict) -> None:
    """Forward *msg* to the sender's current opponent unchanged."""
    opponent = _opponents.get(sender)
    if opponent and opponent in _connected:
        await _send(_connected[opponent], msg)


# ---------------------------------------------------------------------------
# Per-connection handler
# ---------------------------------------------------------------------------

async def handler(ws: websockets.WebSocketServerProtocol) -> None:
    username: str | None = None
    try:
        async for raw in ws:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type", "")

            if msg_type == "hello":
                username = await _handle_hello(ws, data)

            elif username is None:
                # All other message types require the player to be registered
                await _send(ws, {"type": "error", "message": "Send hello first."})

            elif msg_type == "challenge":
                await _handle_challenge(username, data)

            elif msg_type == "challenge_accept":
                await _handle_challenge_accept(username, data)

            elif msg_type == "challenge_decline":
                await _handle_challenge_decline(username, data)

            elif msg_type in ("sequence_add", "input_result", "game_over"):
                # Relay in-game messages to the opponent
                await _relay_to_opponent(username, data)

            elif msg_type == "goodbye":
                break

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if username:
            _connected.pop(username, None)
            _settings.pop(username, None)
            opponent = _opponents.pop(username, None)
            if opponent:
                _opponents.pop(opponent, None)
                if opponent in _connected:
                    await _send(_connected[opponent], {"type": "opponent_disconnected"})
            log.info("- %s left", username)
            await _broadcast_player_list()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 8765))
    log.info("TYP0 relay server starting on ws://%s:%d", host, port)
    async with websockets.serve(handler, host, port):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
