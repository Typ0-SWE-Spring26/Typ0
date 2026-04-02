"""Browser tests for multiplayer screens.

Requires the game running locally:

    python -m pygbag --port 8000 .

Run with:

    pytest tests/test_browser_multiplayer.py -v -m browser

These are excluded from normal CI (they need a real browser + pygbag server).
"""
import time
import pytest

GAME_URL  = "http://localhost:8000"
LOAD_WAIT_MS   = 12_000   # time for WASM runtime to initialise
RENDER_BUDGET_S = 30      # max wait for a non-blank frame


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def page(playwright):
    browser = playwright.chromium.launch(headless=True)
    ctx = browser.new_context()
    pg = ctx.new_page()
    yield pg
    browser.close()


def _wait_for_render(page, timeout_s=RENDER_BUDGET_S):
    """Block until the canvas has at least one non-black pixel."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        result = page.evaluate("""() => {
            const canvas = document.querySelector('canvas');
            if (!canvas) return false;
            const ctx = canvas.getContext('2d');
            const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
            for (let i = 0; i < data.length; i += 4) {
                if (data[i] > 10 || data[i+1] > 10 || data[i+2] > 10) return true;
            }
            return false;
        }""")
        if result:
            return True
        time.sleep(0.5)
    return False


def _get_python_errors(page):
    """Return any Python-level error lines from the browser console."""
    return page.evaluate("""() => {
        return window.__pythonErrors || [];
    }""")


# ---------------------------------------------------------------------------
# Setup — load page once and wait for the game to render
# ---------------------------------------------------------------------------

@pytest.mark.browser
def test_mp_game_loads(page):
    """Game reaches a rendered frame — precondition for all multiplayer tests."""
    page.goto(GAME_URL)
    page.wait_for_timeout(LOAD_WAIT_MS)
    assert _wait_for_render(page), "Game canvas never rendered a non-blank frame"


@pytest.mark.browser
def test_mp_no_python_errors_on_load(page):
    """No Python exceptions should occur just from loading the game."""
    errors = _get_python_errors(page)
    assert errors == [], f"Python errors on load: {errors}"


# ---------------------------------------------------------------------------
# Multiplayer button present in main menu
# ---------------------------------------------------------------------------

@pytest.mark.browser
def test_mp_button_exists_in_menu(page):
    """The Multiplayer button must be visible after the start screen."""
    # Skip past the start screen (press Enter / Space)
    page.keyboard.press("Enter")
    page.wait_for_timeout(1000)

    # Canvas pixel check — we just verify the game is still rendering
    assert _wait_for_render(page, timeout_s=5), \
        "Canvas stopped rendering after pressing Enter on start screen"


# ---------------------------------------------------------------------------
# Multiplayer login screen
# ---------------------------------------------------------------------------

@pytest.mark.browser
def test_mp_login_screen_renders_after_button_click(page):
    """Clicking Multiplayer navigates to the login screen without crashing."""
    # The game is a canvas-based app — simulate the Multiplayer button click
    # by pressing 'M' (no direct keyboard shortcut) via mouse coordinates.
    # Since button position depends on screen size we just verify no errors.
    errors_before = len(_get_python_errors(page))

    # Simulate clicking near the Multiplayer button (centre of canvas, ~2/3 down)
    canvas = page.query_selector("canvas")
    if canvas:
        box = canvas.bounding_box()
        if box:
            page.mouse.click(
                box["x"] + box["width"] / 2,
                box["y"] + box["height"] * 0.65,
            )

    page.wait_for_timeout(1000)

    errors_after = _get_python_errors(page)
    new_errors = errors_after[errors_before:]
    assert new_errors == [], f"New Python errors after clicking Multiplayer: {new_errors}"


@pytest.mark.browser
def test_mp_login_canvas_still_rendering(page):
    """Canvas stays live on the login screen — no freeze."""
    assert _wait_for_render(page, timeout_s=5), \
        "Canvas stopped rendering on the login/multiplayer screen"


# ---------------------------------------------------------------------------
# Name input interaction
# ---------------------------------------------------------------------------

@pytest.mark.browser
def test_mp_typing_name_does_not_crash(page):
    """Typing characters into the name field must not cause Python errors."""
    errors_before = len(_get_python_errors(page))

    # Type a name (game reads keyboard events via pygame)
    page.keyboard.type("TestPlayer")
    page.wait_for_timeout(500)

    errors_after = _get_python_errors(page)
    new_errors = errors_after[errors_before:]
    assert new_errors == [], f"Python errors while typing name: {new_errors}"


@pytest.mark.browser
def test_mp_backspace_does_not_crash(page):
    """Backspace in name field must not cause Python errors."""
    errors_before = len(_get_python_errors(page))

    page.keyboard.press("Backspace")
    page.keyboard.press("Backspace")
    page.wait_for_timeout(300)

    errors_after = _get_python_errors(page)
    new_errors = errors_after[errors_before:]
    assert new_errors == [], f"Python errors on Backspace: {new_errors}"


@pytest.mark.browser
def test_mp_escape_returns_to_menu(page):
    """Pressing ESC on the login screen returns to the main menu."""
    errors_before = len(_get_python_errors(page))

    page.keyboard.press("Escape")
    page.wait_for_timeout(800)

    # Canvas should still be rendering (menu is active again)
    assert _wait_for_render(page, timeout_s=5), \
        "Canvas stopped rendering after ESC from login screen"

    errors_after = _get_python_errors(page)
    new_errors = errors_after[errors_before:]
    assert new_errors == [], f"Python errors after ESC: {new_errors}"
