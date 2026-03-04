"""Browser smoke tests — verify the pygbag build runs in a real browser.

These tests require a local pygbag development server.  Start it first:

    python -m pygbag --port 8080 .

Then run the browser tests separately (they are excluded from normal CI):

    pytest tests/test_browser.py -v

The `browser` marker lets you skip them in unit-test runs:

    python run_tests.py -v -m "not browser"
"""
import pytest

GAME_URL = "http://localhost:8080"


@pytest.fixture(scope="module")
def page(playwright):
    """Single browser page shared across all smoke tests in this module."""
    browser = playwright.chromium.launch(headless=True)
    ctx = browser.new_context()
    pg = ctx.new_page()
    yield pg
    browser.close()


@pytest.mark.browser
def test_canvas_present(page):
    """The pygbag build must serve a page that contains a <canvas> element."""
    page.goto(GAME_URL)
    page.wait_for_selector("canvas", timeout=15_000)
    assert page.locator("canvas").count() == 1


@pytest.mark.browser
def test_no_js_errors_on_load(page):
    """No uncaught JavaScript errors should appear during startup."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(GAME_URL)
    page.wait_for_timeout(3_000)
    assert errors == [], f"Unexpected JS errors: {errors}"


@pytest.mark.browser
def test_keyboard_event_does_not_crash(page):
    """Sending a key press to the canvas should not crash the WASM runtime."""
    page.goto(GAME_URL)
    page.wait_for_selector("canvas", timeout=15_000)
    page.locator("canvas").click()        # give the canvas focus
    page.keyboard.press("ArrowLeft")
    page.wait_for_timeout(500)
    # If the runtime is still alive, the canvas will still be in the DOM.
    assert page.locator("canvas").count() == 1
