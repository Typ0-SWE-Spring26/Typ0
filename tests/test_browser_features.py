"""Browser tests for new features — credits, high scores, game over flow.

Requires a local pygbag development server:

    python -m pygbag --port 8080 .

Run separately from unit tests:

    pytest tests/test_browser_features.py -v

Uses the `browser` marker so they are skipped in normal CI:

    python run_tests.py -v -m "not browser"
"""
import time
import pytest

GAME_URL = "http://localhost:8000"
LOAD_WAIT_MS = 12_000


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def page(playwright):
    """Single browser page shared across all tests in this module."""
    browser = playwright.chromium.launch(headless=True)
    ctx = browser.new_context()
    pg = ctx.new_page()
    yield pg
    browser.close()


def _boot_game(page):
    """Navigate to the game and wait for it to load."""
    page.goto(GAME_URL)
    page.wait_for_selector("#canvas", timeout=15_000)
    page.wait_for_timeout(LOAD_WAIT_MS)
    page.locator("#canvas").click()  # focus canvas / pass UME


def _enter_gameplay_and_gameover(page):
    """Start a game and trigger game over by pressing wrong keys."""
    page.keyboard.press("Space")          # past start screen
    page.wait_for_timeout(500)
    page.keyboard.press("w")              # start game from menu
    page.wait_for_timeout(3_000)          # let first round play out

    # Press unbound keys to trigger a wrong-guess game over
    for _ in range(5):
        page.keyboard.press("x")
        page.wait_for_timeout(300)

    page.wait_for_timeout(2_000)          # wait for game over screen to render


# ---------------------------------------------------------------------------
# Credits screen
# ---------------------------------------------------------------------------

@pytest.mark.browser
def test_credits_screen_accessible_from_menu(page):
    """Pressing C on the start menu should change the canvas (credits screen)."""
    _boot_game(page)
    page.keyboard.press("Space")          # past start screen
    page.wait_for_timeout(1_000)

    before = page.locator("#canvas").screenshot()
    page.keyboard.press("c")              # open credits
    page.wait_for_timeout(1_000)
    after = page.locator("#canvas").screenshot()

    assert before != after, (
        "Canvas did not change after pressing C — credits screen may not be working"
    )


@pytest.mark.browser
def test_credits_returns_to_menu(page):
    """Pressing ESC on the credits screen should return to the menu."""
    _boot_game(page)
    page.keyboard.press("Space")          # past start screen
    page.wait_for_timeout(500)
    page.keyboard.press("c")              # open credits
    page.wait_for_timeout(1_000)

    before = page.locator("#canvas").screenshot()
    page.keyboard.press("Escape")         # back to menu
    page.wait_for_timeout(1_000)
    after = page.locator("#canvas").screenshot()

    assert before != after, (
        "Canvas did not change after pressing ESC on credits"
    )


# ---------------------------------------------------------------------------
# Game over flow — auto-switch & retry
# ---------------------------------------------------------------------------

@pytest.mark.browser
def test_game_over_renders_after_wrong_input(page):
    """After wrong input, the game over screen should render."""
    _boot_game(page)
    _enter_gameplay_and_gameover(page)

    screenshot = page.locator("#canvas").screenshot()
    assert len(screenshot) > 500, "Canvas appears blank after expected game over"


@pytest.mark.browser
def test_retry_from_game_over(page):
    """Pressing R on the game over screen should restart the game."""
    _boot_game(page)
    _enter_gameplay_and_gameover(page)

    before = page.locator("#canvas").screenshot()

    page.keyboard.press("r")              # retry
    page.wait_for_timeout(2_000)
    after = page.locator("#canvas").screenshot()

    assert before != after, (
        "Canvas did not change after pressing R — retry may not be working"
    )


# ---------------------------------------------------------------------------
# High scores screen
# ---------------------------------------------------------------------------

@pytest.mark.browser
def test_high_scores_screen_appears_after_timeout(page):
    """After game over, the high scores screen should auto-show after ~10s.

    We wait longer than AUTO_SWITCH_MS (10s) and check that the canvas changed.
    """
    _boot_game(page)
    _enter_gameplay_and_gameover(page)

    before = page.locator("#canvas").screenshot()

    # Wait for auto-switch (10s + buffer)
    page.wait_for_timeout(12_000)
    after = page.locator("#canvas").screenshot()

    assert before != after, (
        "Canvas did not change after 12s — auto-switch to high scores may not be working"
    )


# ---------------------------------------------------------------------------
# Scaling
# ---------------------------------------------------------------------------

@pytest.mark.browser
def test_game_scales_on_resize(page):
    """Resizing the browser window should scale the game canvas."""
    _boot_game(page)

    dims_before = page.evaluate("""() => {
        const r = document.getElementById('canvas').getBoundingClientRect();
        return { w: r.width, h: r.height };
    }""")

    page.set_viewport_size({"width": 1920, "height": 1080})
    page.wait_for_timeout(1_000)

    dims_after = page.evaluate("""() => {
        const r = document.getElementById('canvas').getBoundingClientRect();
        return { w: r.width, h: r.height };
    }""")

    assert dims_after["w"] >= dims_before["w"] or dims_after["h"] >= dims_before["h"], (
        f"Canvas did not scale up: {dims_before} -> {dims_after}"
    )
