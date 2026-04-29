import asyncio
import json
from unittest.mock import AsyncMock, patch


def _run(coro):
    return asyncio.run(coro)


class _FakeRequest:
    def __init__(self, game_type=None, body=None, name=None):
        self.match_info = {}
        if game_type is not None:
            self.match_info["game_type"] = game_type
        if name is not None:
            self.match_info["name"] = name
        self._body = body or {}

    async def json(self):
        return self._body


def _json_from_response(resp):
    if getattr(resp, "text", None):
        return json.loads(resp.text)
    return json.loads(resp.body.decode("utf-8"))


def test_keys_ninja_is_valid_game_type():
    from server.scores import VALID_GAME_TYPES
    assert "keys_ninja" in VALID_GAME_TYPES


def test_handle_get_scores_accepts_keys_ninja():
    import server.server as srv

    req = _FakeRequest("keys_ninja")
    with patch.object(srv, "load_scores", return_value=[{"name": "AAA", "score": 10}]) as mock_load:
        resp = _run(srv.handle_get_scores(req))

    assert resp.status == 200
    assert _json_from_response(resp) == [{"name": "AAA", "score": 10}]
    mock_load.assert_called_once_with("keys_ninja")


def test_handle_get_scores_accepts_simon_bopit_multiplayer():
    import server.server as srv

    for game_type in ("simon", "bopit", "multiplayer"):
        req = _FakeRequest(game_type)
        with patch.object(srv, "load_scores", return_value=[]):
            resp = _run(srv.handle_get_scores(req))
        assert resp.status == 200


def test_handle_get_scores_rejects_unknown_game_type():
    import server.server as srv

    req = _FakeRequest("unknown")
    resp = _run(srv.handle_get_scores(req))

    assert resp.status == 404


def test_handle_post_score_accepts_keys_ninja():
    import server.server as srv

    req = _FakeRequest("keys_ninja", body={"name": "AAA", "score": 42})
    with patch.object(srv, "is_high_score", return_value=True) as mock_high, \
         patch.object(srv, "add_score", return_value=[{"name": "AAA", "score": 42}]) as mock_add:
        resp = _run(srv.handle_post_score(req))

    assert resp.status == 200
    assert _json_from_response(resp) == [{"name": "AAA", "score": 42}]
    mock_high.assert_called_once_with(42, "keys_ninja")
    mock_add.assert_called_once_with("AAA", 42, "keys_ninja")


def test_handle_post_score_accepts_simon_bopit_multiplayer():
    import server.server as srv

    for game_type in ("simon", "bopit", "multiplayer"):
        req = _FakeRequest(game_type, body={"name": "AAA", "score": 7})
        with patch.object(srv, "is_high_score", return_value=True), \
             patch.object(srv, "add_score", return_value=[{"name": "AAA", "score": 7}]):
            resp = _run(srv.handle_post_score(req))
        assert resp.status == 200


def test_handle_post_score_rejects_unknown_game_type():
    import server.server as srv

    req = _FakeRequest("unknown", body={"name": "AAA", "score": 7})
    resp = _run(srv.handle_post_score(req))

    assert resp.status == 404


def test_handle_post_score_rejects_blank_name():
    import server.server as srv

    req = _FakeRequest("simon", body={"name": "   ", "score": 5})
    resp = _run(srv.handle_post_score(req))

    assert resp.status == 400


def test_handle_post_score_rejects_invalid_body():
    import server.server as srv

    req = _FakeRequest("simon", body={"name": "AAA"})
    resp = _run(srv.handle_post_score(req))

    assert resp.status == 400


def test_handle_post_score_trims_name_to_20_chars():
    import server.server as srv

    long_name = "A" * 30
    req = _FakeRequest("bopit", body={"name": long_name, "score": 5})
    with patch.object(srv, "is_high_score", return_value=True), \
         patch.object(srv, "add_score", return_value=[] ) as mock_add:
        resp = _run(srv.handle_post_score(req))

    assert resp.status == 200
    mock_add.assert_called_once_with("A" * 20, 5, "bopit")


def test_handle_post_score_returns_existing_when_not_high_score():
    import server.server as srv

    req = _FakeRequest("bopit", body={"name": "AAA", "score": 1})
    with patch.object(srv, "is_high_score", return_value=False), \
         patch.object(srv, "load_scores", return_value=[{"name": "BBB", "score": 9}]):
        resp = _run(srv.handle_post_score(req))

    assert resp.status == 200
    assert _json_from_response(resp) == [{"name": "BBB", "score": 9}]


def test_handle_close_connections_closes_all():
    import server.server as srv

    ws_a = AsyncMock()
    ws_b = AsyncMock()
    srv._players.clear()
    srv._players["Alice"] = ws_a
    srv._players["Bob"] = ws_b
    srv.CORS_HEADERS = {}

    req = _FakeRequest()
    resp = _run(srv.handle_close_connections(req))

    assert resp.status == 200
    body = _json_from_response(resp)
    assert set(body.get("closed", [])) == {"Alice", "Bob"}
    assert ws_a.close.called
    assert ws_b.close.called


def test_handle_close_connections_closes_named_player():
    import server.server as srv

    ws_a = AsyncMock()
    ws_b = AsyncMock()
    srv._players.clear()
    srv._players["Alice"] = ws_a
    srv._players["Bob"] = ws_b
    srv.CORS_HEADERS = {}

    req = _FakeRequest(name="Alice")
    resp = _run(srv.handle_close_connections(req))

    assert resp.status == 200
    body = _json_from_response(resp)
    assert body.get("closed", []) == ["Alice"]
    assert ws_a.close.called
    assert not ws_b.close.called


def test_handle_close_connections_ignores_unknown_player():
    import server.server as srv

    ws_a = AsyncMock()
    srv._players.clear()
    srv._players["Alice"] = ws_a
    srv.CORS_HEADERS = {}

    req = _FakeRequest(name="Ghost")
    resp = _run(srv.handle_close_connections(req))

    assert resp.status == 200
    body = _json_from_response(resp)
    assert body.get("closed", []) == []
    assert not ws_a.close.called
