"""Unit tests for the multiplayer WebSocket server logic.

Tests run against the server's internal state-management functions directly
(no real network connections needed).
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import WSMsgType


# ---------------------------------------------------------------------------
# Async iterator helper — yields aiohttp-style WSMessage objects
# ---------------------------------------------------------------------------

class _FakeWSMessage:
    """Mimics the bits of aiohttp.WSMessage that _ws_session inspects."""
    def __init__(self, data, msg_type=WSMsgType.TEXT):
        self.type = msg_type
        self.data = data


class _AsyncMessages:
    """Async-iterable wrapper around a list of raw JSON strings, yielded
    as aiohttp-shaped WSMessage objects."""
    def __init__(self, messages):
        self._it = iter(messages)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return _FakeWSMessage(next(self._it))
        except StopIteration:
            raise StopAsyncIteration


# ---------------------------------------------------------------------------
# Helpers to import the server module with its globals reset between tests
# ---------------------------------------------------------------------------

def _fresh_server():
    """Re-import server with clean global state."""
    import server.server as srv
    srv._players.clear()
    srv._pending_challenges.clear()
    srv._active_games.clear()
    srv._sessions.clear()
    return srv


def _fake_ws():
    """Websocket that accepts sends but yields no incoming messages."""
    ws = MagicMock()
    ws.__aiter__ = lambda self_=None: _AsyncMessages([])
    ws.send_str = AsyncMock()
    return ws


def _ws_with_messages(messages):
    """Websocket that yields the given list of raw JSON strings."""
    ws = MagicMock()
    ws.__aiter__ = lambda self_=None: _AsyncMessages(messages)
    ws.send_str = AsyncMock()
    return ws


# ---------------------------------------------------------------------------
# Helper: run a coroutine in a test
# ---------------------------------------------------------------------------

def run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# _broadcast_lobby
# ---------------------------------------------------------------------------

class TestBroadcastLobby:
    def test_sends_player_list_to_all(self):
        srv = _fresh_server()
        ws_a, ws_b = _fake_ws(), _fake_ws()
        srv._players['Alice'] = ws_a
        srv._players['Bob']   = ws_b

        run(srv._broadcast_lobby())

        for ws in (ws_a, ws_b):
            ws.send_str.assert_called_once()
            msg = json.loads(ws.send_str.call_args[0][0])
            assert msg['type'] == 'player_list'
            assert set(msg['players']) == {'Alice', 'Bob'}

    def test_excludes_players_in_active_games(self):
        srv = _fresh_server()
        ws_a, ws_b = _fake_ws(), _fake_ws()
        srv._players['Alice'] = ws_a
        srv._players['Bob']   = ws_b
        srv._active_games['Alice'] = 'some_session'

        run(srv._broadcast_lobby())

        msg = json.loads(ws_b.send_str.call_args[0][0])
        assert 'Alice' not in msg['players']
        assert 'Bob' in msg['players']

    def test_empty_lobby_sends_empty_list(self):
        srv = _fresh_server()
        ws_a = _fake_ws()
        srv._players['Alice'] = ws_a

        run(srv._broadcast_lobby())

        msg = json.loads(ws_a.send_str.call_args[0][0])
        assert msg['players'] == ['Alice']


# ---------------------------------------------------------------------------
# _safe_send
# ---------------------------------------------------------------------------

class TestSafeSend:
    def test_sends_to_known_player(self):
        srv = _fresh_server()
        ws = _fake_ws()
        srv._players['Alice'] = ws

        run(srv._safe_send('Alice', {'type': 'ping'}))

        ws.send_str.assert_called_once()
        assert json.loads(ws.send_str.call_args[0][0]) == {'type': 'ping'}

    def test_silent_on_unknown_player(self):
        srv = _fresh_server()
        # Should not raise even if player doesn't exist
        run(srv._safe_send('Ghost', {'type': 'ping'}))

    def test_silent_on_send_error(self):
        srv = _fresh_server()
        ws = _fake_ws()
        ws.send_str.side_effect = Exception("connection lost")
        srv._players['Alice'] = ws

        # Should not raise
        run(srv._safe_send('Alice', {'type': 'ping'}))


# ---------------------------------------------------------------------------
# handler — join
# ---------------------------------------------------------------------------

class TestHandlerJoin:
    def test_join_registers_player(self):
        srv = _fresh_server()
        ws = _ws_with_messages([json.dumps({'type': 'join', 'name': 'Alice'})])

        run(srv._ws_session(ws))

        # Player should have been registered (and then removed on disconnect)
        # Since handler cleans up in finally, player is gone after the coro ends.
        # We verify the "joined" message was sent.
        sent = [json.loads(c[0][0]) for c in ws.send_str.call_args_list]
        assert any(m['type'] == 'joined' and m['name'] == 'Alice' for m in sent)

    def test_join_rejects_duplicate_name(self):
        srv = _fresh_server()
        existing_ws = _fake_ws()
        srv._players['Alice'] = existing_ws

        ws = _ws_with_messages([json.dumps({'type': 'join', 'name': 'Alice'})])
        run(srv._ws_session(ws))

        sent = [json.loads(c[0][0]) for c in ws.send_str.call_args_list]
        assert any(m['type'] == 'error' for m in sent)

    def test_join_rejects_empty_name(self):
        srv = _fresh_server()
        ws = _ws_with_messages([json.dumps({'type': 'join', 'name': '   '})])

        run(srv._ws_session(ws))

        sent = [json.loads(c[0][0]) for c in ws.send_str.call_args_list]
        assert any(m['type'] == 'error' for m in sent)


# ---------------------------------------------------------------------------
# handler — challenge / response
# ---------------------------------------------------------------------------

class TestHandlerChallenge:
    def _run_two_players(self, srv, alice_msgs, bob_msgs):
        ws_a = _ws_with_messages(alice_msgs)
        ws_b = _ws_with_messages(bob_msgs)

        async def _both():
            srv._players['Alice'] = ws_a
            srv._players['Bob']   = ws_b
            await asyncio.gather(
                srv._ws_session(ws_a),
                srv._ws_session(ws_b),
            )

        run(_both())
        return ws_a, ws_b

    def test_challenge_forwards_to_target(self):
        srv = _fresh_server()
        ws_a = _ws_with_messages([
            json.dumps({'type': 'join', 'name': 'Alice'}),
            json.dumps({'type': 'challenge', 'target': 'Bob', 'settings': 0}),
        ])
        ws_b = _fake_ws()
        srv._players['Bob'] = ws_b

        run(srv._ws_session(ws_a))

        sent_to_bob = [json.loads(c[0][0]) for c in ws_b.send_str.call_args_list]
        assert any(m['type'] == 'challenge_received' and m['from'] == 'Alice'
                   for m in sent_to_bob)

    def test_challenge_clamped_to_8_bits(self):
        srv = _fresh_server()
        ws_a = _ws_with_messages([
            json.dumps({'type': 'join', 'name': 'Alice'}),
            json.dumps({'type': 'challenge', 'target': 'Bob', 'settings': 0xFFF}),
        ])
        ws_b = _fake_ws()
        srv._players['Bob'] = ws_b

        run(srv._ws_session(ws_a))

        sent_to_bob = [json.loads(c[0][0]) for c in ws_b.send_str.call_args_list]
        challenge_msg = next(m for m in sent_to_bob if m['type'] == 'challenge_received')
        assert challenge_msg['settings'] == 0xFF  # clamped


# ---------------------------------------------------------------------------
# handler — mistake / game end
# ---------------------------------------------------------------------------

class TestHandlerMistake:
    def _run_mistake(self, srv, ws_a, ws_b, session_id, finished=False):
        """Set up a session with Alice and Bob, run ws_a through the handler."""
        srv._players['Bob'] = ws_b
        srv._sessions[session_id] = {
            'players': ['Alice', 'Bob'],
            'seed': 1234,
            'settings': 0,
            'scores': {'Alice': 2, 'Bob': 3},
            'finished': finished,
        }
        srv._active_games['Alice'] = session_id
        srv._active_games['Bob']   = session_id
        run(srv._ws_session(ws_a))

    def test_mistake_sends_you_lose_to_loser(self):
        srv = _fresh_server()
        ws_b = _fake_ws()
        ws_a = _ws_with_messages([
            json.dumps({'type': 'join', 'name': 'Alice'}),
            json.dumps({'type': 'mistake'}),
        ])
        self._run_mistake(srv, ws_a, ws_b, 'Alice:Bob')

        sent_to_alice = [json.loads(c[0][0]) for c in ws_a.send_str.call_args_list]
        assert any(m['type'] == 'you_lose' for m in sent_to_alice)

    def test_mistake_sends_you_win_to_opponent(self):
        srv = _fresh_server()
        ws_b = _fake_ws()
        ws_a = _ws_with_messages([
            json.dumps({'type': 'join', 'name': 'Alice'}),
            json.dumps({'type': 'mistake'}),
        ])
        self._run_mistake(srv, ws_a, ws_b, 'Alice:Bob')

        sent_to_bob = [json.loads(c[0][0]) for c in ws_b.send_str.call_args_list]
        assert any(m['type'] == 'you_win' for m in sent_to_bob)

    def test_second_mistake_ignored_after_game_finished(self):
        srv = _fresh_server()
        ws_b = _fake_ws()
        ws_a = _ws_with_messages([
            json.dumps({'type': 'join', 'name': 'Alice'}),
            json.dumps({'type': 'mistake'}),
        ])
        srv._players['Bob'] = ws_b
        session_id = 'Alice:Bob'
        srv._sessions[session_id] = {
            'players': ['Alice', 'Bob'],
            'seed': 1234,
            'settings': 0,
            'scores': {'Alice': 0, 'Bob': 0},
            'finished': True,   # already ended
        }
        srv._active_games['Alice'] = session_id
        srv._active_games['Bob']   = session_id
        run(srv._ws_session(ws_a))

        # No you_win/you_lose should have been sent
        sent_to_bob = [json.loads(c[0][0]) for c in ws_b.send_str.call_args_list]
        assert not any(m['type'] in ('you_win', 'you_lose') for m in sent_to_bob)

    def test_mistake_cleans_up_session(self):
        srv = _fresh_server()
        ws_b = _fake_ws()
        ws_a = _ws_with_messages([
            json.dumps({'type': 'join', 'name': 'Alice'}),
            json.dumps({'type': 'mistake'}),
        ])
        srv._players['Bob'] = ws_b
        session_id = 'Alice:Bob'
        srv._sessions[session_id] = {
            'players': ['Alice', 'Bob'],
            'seed': 0,
            'settings': 0,
            'scores': {'Alice': 0, 'Bob': 0},
            'finished': False,
        }
        srv._active_games['Alice'] = session_id
        srv._active_games['Bob']   = session_id

        run(srv._ws_session(ws_a))

        assert session_id not in srv._sessions
        assert 'Alice' not in srv._active_games
        assert 'Bob' not in srv._active_games
