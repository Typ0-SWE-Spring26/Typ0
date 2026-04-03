"""Browser-side WebSocket protocol tests.

Spins up the real multiplayer server as a subprocess, then uses Playwright
to exercise the WebSocket API from inside a real browser context — the same
JS runtime that pygbag uses at runtime.

No running game/pygbag server is required; only the multiplayer WS server.

Run with:
    pytest tests/test_browser_ws.py -v -m browser
"""
import json
import socket
import subprocess
import sys
import time

import pytest

WS_PORT = 14023
WS_URL  = f"ws://localhost:{WS_PORT}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _wait_for_port(port, host="127.0.0.1", timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


@pytest.fixture(scope="module")
def ws_server():
    """Start the multiplayer WS server; tear it down after the module."""
    proc = subprocess.Popen(
        [sys.executable, "server/server.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if not _wait_for_port(WS_PORT):
        proc.kill()
        pytest.skip(f"WS server did not start on port {WS_PORT} in time")
    yield proc
    proc.kill()
    proc.wait()


@pytest.fixture(scope="module")
def ws_page(playwright, ws_server):
    """A bare browser page — no game needed, just JS WebSocket access."""
    browser = playwright.chromium.launch(headless=True)
    ctx = browser.new_context()
    pg = ctx.new_page()
    pg.goto("about:blank")
    yield pg
    browser.close()


# ---------------------------------------------------------------------------
# JS helpers
# ---------------------------------------------------------------------------

def _single_session(page, messages, collect_ms=1500):
    """
    Open one WS from the browser, send *messages*, collect responses for
    *collect_ms* milliseconds, close, return the list of received dicts.
    """
    return page.evaluate(
        f"""async () => {{
            const ws = new WebSocket("{WS_URL}");
            const received = [];
            const msgs = {json.dumps(messages)};
            await new Promise(resolve => {{
                ws.onopen    = () => {{ msgs.forEach(m => ws.send(JSON.stringify(m))); }};
                ws.onmessage = e  => received.push(JSON.parse(e.data));
                ws.onerror   = ()  => resolve();
                setTimeout(() => {{ ws.close(); resolve(); }}, {collect_ms});
            }});
            return received;
        }}"""
    )


def _two_sessions(page, alice_msgs, bob_msgs, collect_ms=1500):
    """
    Open two WS connections simultaneously.  Alice and Bob connect in
    parallel; each sends their own message list after open.
    Returns {{ aliceReceived: [...], bobReceived: [...] }}.
    """
    return page.evaluate(
        f"""async () => {{
            function session(msgs) {{
                const ws = new WebSocket("{WS_URL}");
                const received = [];
                const openP = new Promise(r => ws.onopen = r);
                ws.onmessage = e => received.push(JSON.parse(e.data));
                return {{ ws, received, openP }};
            }}

            const a = session([]);
            const b = session([]);
            await Promise.all([a.openP, b.openP]);

            {json.dumps(alice_msgs)}.forEach(m => a.ws.send(JSON.stringify(m)));
            {json.dumps(bob_msgs)}.forEach(m => b.ws.send(JSON.stringify(m)));

            await new Promise(r => setTimeout(r, {collect_ms}));
            a.ws.close();
            b.ws.close();
            return {{ aliceReceived: a.received, bobReceived: b.received }};
        }}"""
    )


def _sequential_sessions(page, collect_ms=2000):
    """
    Alice joins first, then Bob joins, then Alice challenges Bob.
    Returns {{ aliceReceived: [...], bobReceived: [...] }}.
    """
    return page.evaluate(
        f"""async () => {{
            function openWS() {{
                const ws = new WebSocket("{WS_URL}");
                const received = [];
                ws.onmessage = e => received.push(JSON.parse(e.data));
                const openP = new Promise(r => ws.onopen = r);
                return {{ ws, received, openP }};
            }}

            const a = openWS();
            await a.openP;
            a.ws.send(JSON.stringify({{type: "join", name: "ChallengeAlice"}}));
            await new Promise(r => setTimeout(r, 150));

            const b = openWS();
            await b.openP;
            b.ws.send(JSON.stringify({{type: "join", name: "ChallengeBob"}}));
            await new Promise(r => setTimeout(r, 150));

            a.ws.send(JSON.stringify({{type: "challenge", target: "ChallengeBob", settings: 7}}));
            await new Promise(r => setTimeout(r, {collect_ms}));

            a.ws.close();
            b.ws.close();
            return {{ aliceReceived: a.received, bobReceived: b.received }};
        }}"""
    )


# ---------------------------------------------------------------------------
# Connection tests
# ---------------------------------------------------------------------------

@pytest.mark.browser
def test_ws_browser_can_connect(ws_page):
    """Browser JS WebSocket can open a connection to the server."""
    connected = ws_page.evaluate(
        f"""async () => {{
            const ws = new WebSocket("{WS_URL}");
            const ok = await new Promise(resolve => {{
                ws.onopen  = () => {{ ws.close(); resolve(true); }};
                ws.onerror = () => resolve(false);
                setTimeout(() => resolve(false), 3000);
            }});
            return ok;
        }}"""
    )
    assert connected, "Browser could not open a WebSocket connection to the server"


# ---------------------------------------------------------------------------
# Join protocol
# ---------------------------------------------------------------------------

@pytest.mark.browser
def test_ws_join_receives_joined_message(ws_page):
    """Sending {type: join} returns a {type: joined} confirmation."""
    msgs = _single_session(ws_page, [{"type": "join", "name": "BrowserUser1"}])
    types = [m["type"] for m in msgs]
    assert "joined" in types, f"Expected 'joined' in {types}"


@pytest.mark.browser
def test_ws_join_confirms_name(ws_page):
    """{type: joined} carries the player's chosen name."""
    msgs = _single_session(ws_page, [{"type": "join", "name": "BrowserUser2"}])
    joined = next((m for m in msgs if m["type"] == "joined"), None)
    assert joined is not None
    assert joined["name"] == "BrowserUser2"


@pytest.mark.browser
def test_ws_join_triggers_player_list(ws_page):
    """After joining, the client receives a player_list broadcast."""
    msgs = _single_session(ws_page, [{"type": "join", "name": "BrowserUser3"}])
    types = [m["type"] for m in msgs]
    assert "player_list" in types, f"Expected 'player_list' in {types}"


@pytest.mark.browser
def test_ws_player_list_includes_self(ws_page):
    """The player_list broadcast includes the newly joined player."""
    msgs = _single_session(ws_page, [{"type": "join", "name": "BrowserUser4"}])
    lists = [m for m in msgs if m["type"] == "player_list"]
    assert lists, "No player_list received"
    assert "BrowserUser4" in lists[-1]["players"]


@pytest.mark.browser
def test_ws_empty_name_returns_error(ws_page):
    """Sending an empty name must receive an error, not a joined message."""
    msgs = _single_session(ws_page, [{"type": "join", "name": "   "}])
    types = [m["type"] for m in msgs]
    assert "error" in types,  f"Expected 'error' in {types}"
    assert "joined" not in types


# ---------------------------------------------------------------------------
# Duplicate name
# ---------------------------------------------------------------------------

@pytest.mark.browser
def test_ws_duplicate_name_rejected(ws_page):
    """Two clients using the same name: second gets an error."""
    result = _two_sessions(
        ws_page,
        alice_msgs=[{"type": "join", "name": "DupeName"}],
        bob_msgs  =[{"type": "join", "name": "DupeName"}],
    )
    # Exactly one should receive 'joined'; the other should receive 'error'.
    alice_types = [m["type"] for m in result["aliceReceived"]]
    bob_types   = [m["type"] for m in result["bobReceived"]]
    joined_count = alice_types.count("joined") + bob_types.count("joined")
    error_count  = alice_types.count("error")  + bob_types.count("error")
    assert joined_count == 1, f"Expected exactly 1 joined; alice={alice_types} bob={bob_types}"
    assert error_count  >= 1, f"Expected at least 1 error;  alice={alice_types} bob={bob_types}"


# ---------------------------------------------------------------------------
# Two-player lobby
# ---------------------------------------------------------------------------

@pytest.mark.browser
def test_ws_two_players_see_each_other_in_lobby(ws_page):
    """Both players receive a player_list containing each other after joining."""
    result = _two_sessions(
        ws_page,
        alice_msgs=[{"type": "join", "name": "LobbyAlice"}],
        bob_msgs  =[{"type": "join", "name": "LobbyBob"}],
    )
    # Find the last player_list each client received
    alice_lists = [m for m in result["aliceReceived"] if m["type"] == "player_list"]
    bob_lists   = [m for m in result["bobReceived"]   if m["type"] == "player_list"]
    assert alice_lists, "Alice received no player_list"
    assert bob_lists,   "Bob received no player_list"
    # After both join, both names should appear in the final broadcast
    all_seen = set(alice_lists[-1]["players"]) | set(bob_lists[-1]["players"])
    assert "LobbyAlice" in all_seen
    assert "LobbyBob"   in all_seen


# ---------------------------------------------------------------------------
# Challenge protocol
# ---------------------------------------------------------------------------

@pytest.mark.browser
def test_ws_challenge_received_by_target(ws_page):
    """Bob receives {type: challenge_received} when Alice challenges him."""
    result = _sequential_sessions(ws_page)
    bob_types = [m["type"] for m in result["bobReceived"]]
    assert "challenge_received" in bob_types, (
        f"Bob never got challenge_received; bob msgs: {result['bobReceived']}"
    )


@pytest.mark.browser
def test_ws_challenge_carries_challenger_name(ws_page):
    """The challenge_received message identifies the challenger."""
    result = _sequential_sessions(ws_page)
    msg = next(
        (m for m in result["bobReceived"] if m["type"] == "challenge_received"),
        None,
    )
    assert msg is not None
    assert msg["from"] == "ChallengeAlice"


@pytest.mark.browser
def test_ws_challenge_settings_clamped_to_8_bits(ws_page):
    """Settings value > 0xFF is clamped to 8 bits before forwarding."""
    result = ws_page.evaluate(
        f"""async () => {{
            function openWS() {{
                const ws = new WebSocket("{WS_URL}");
                const received = [];
                ws.onmessage = e => received.push(JSON.parse(e.data));
                const openP = new Promise(r => ws.onopen = r);
                return {{ ws, received, openP }};
            }}

            const a = openWS();
            await a.openP;
            a.ws.send(JSON.stringify({{type: "join", name: "ClampAlice"}}));
            await new Promise(r => setTimeout(r, 150));

            const b = openWS();
            await b.openP;
            b.ws.send(JSON.stringify({{type: "join", name: "ClampBob"}}));
            await new Promise(r => setTimeout(r, 150));

            a.ws.send(JSON.stringify({{type: "challenge", target: "ClampBob", settings: 0xFFF}}));
            await new Promise(r => setTimeout(r, 1000));

            a.ws.close();
            b.ws.close();
            return b.received;
        }}"""
    )
    msg = next((m for m in result if m["type"] == "challenge_received"), None)
    assert msg is not None, f"ClampBob never received challenge_received: {result}"
    assert msg["settings"] == 0xFF, f"Expected settings=255, got {msg['settings']}"
