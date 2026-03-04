"""Browser smoke tests — verify the pygbag build runs in a real browser.

These tests require a local pygbag development server.  Start it first:

    python -m pygbag --port 8080 .

Then run the browser tests separately (they are excluded from normal CI):

    pytest tests/test_browser.py -v

The `browser` marker lets you skip them in unit-test runs:

    python run_tests.py -v -m "not browser"
"""
import time
import pytest

GAME_URL = "http://localhost:8000"
# pygbag downloads a WASM Python runtime from CDN — allow plenty of time
LOAD_WAIT_MS = 12_000
# Fail if the game hasn't produced a non-blank frame within this budget
RENDER_BUDGET_S = 30


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def page(playwright):
    """Single browser page shared across all smoke tests in this module."""
    browser = playwright.chromium.launch(headless=True)
    ctx = browser.new_context()
    pg = ctx.new_page()
    yield pg
    browser.close()


# ---------------------------------------------------------------------------
# Structural / DOM tests  (no game-start required)
# ---------------------------------------------------------------------------

@pytest.mark.browser
def test_page_title(page):
    """Page title should be the game name."""
    page.goto(GAME_URL)
    assert page.title() == "typ0"


@pytest.mark.browser
def test_canvas_is_focusable(page):
    """#canvas must have a tabindex attribute so keyboard events reach it."""
    page.goto(GAME_URL)
    page.wait_for_selector("#canvas", timeout=15_000)
    tabindex = page.get_attribute("#canvas", "tabindex")
    assert tabindex is not None, (
        "Canvas has no tabindex — keyboard events may never reach the game"
    )


@pytest.mark.browser
def test_game_bundle_loads(page):
    """The game APK bundle must be served without error.

    Uses expect_response() which registers the listener *before* goto() so
    fast/cached responses are not missed.  Accepts 200 (fresh) and 304
    (browser cache hit).  Timeout is 30s because the WASM runtime downloads
    first and the APK is only requested once Python starts running.
    """
    with page.expect_response(
        lambda r: "typ0.apk" in r.url, timeout=30_000
    ) as response_info:
        page.goto(GAME_URL)
    status = response_info.value.status
    assert status in (200, 304), f"typ0.apk returned unexpected HTTP {status}"


# ---------------------------------------------------------------------------
# Runtime / console tests
# ---------------------------------------------------------------------------

@pytest.mark.browser
def test_no_js_errors_on_load(page):
    """No uncaught JavaScript errors should appear during startup."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(GAME_URL)
    page.wait_for_timeout(LOAD_WAIT_MS)
    assert errors == [], f"Unexpected JS errors: {errors}"


@pytest.mark.browser
def test_no_python_exceptions_in_console(page):
    """No Python tracebacks should appear in the browser console.

    pygbag routes Python stdout/stderr to the JS console, so unhandled
    Python exceptions show up as messages starting with "Traceback".
    """
    python_errors = []

    def on_console(msg):
        if "Traceback" in msg.text:
            python_errors.append(msg.text)

    page.on("console", on_console)
    page.goto(GAME_URL)
    page.wait_for_selector("#canvas", timeout=15_000)
    page.wait_for_timeout(LOAD_WAIT_MS)
    assert not python_errors, f"Python exceptions in console: {python_errors}"


# ---------------------------------------------------------------------------
# Rendering / visual tests
# ---------------------------------------------------------------------------

@pytest.mark.browser
def test_game_renders_after_load(page):
    """Canvas must have non-trivial visual content once the game has loaded.

    We capture a PNG screenshot via Playwright's rendering pipeline.
    A blank or 1×1 canvas compresses to ~67 bytes; a rendered game screen
    is much larger even with PNG compression.
    """
    page.goto(GAME_URL)
    page.wait_for_selector("#canvas", timeout=15_000)
    page.wait_for_timeout(LOAD_WAIT_MS)

    canvas_bytes = page.locator("#canvas").screenshot()
    assert len(canvas_bytes) > 500, (
        f"Canvas screenshot is only {len(canvas_bytes)} bytes — "
        "the game loop may not have started"
    )


@pytest.mark.browser
def test_canvas_fills_viewport(page):
    """#canvas must be scaled up to fill the browser viewport once the game boots.

    pygbag uses CSS (width:100%; height:100%) to scale the canvas rather than
    updating canvas.width/canvas.height, so we check the rendered size via
    getBoundingClientRect instead of the DOM attribute.
    """
    page.goto(GAME_URL)
    page.wait_for_selector("#canvas", timeout=15_000)
    page.wait_for_timeout(LOAD_WAIT_MS)

    dims = page.evaluate("""() => {
        const r = document.getElementById('canvas').getBoundingClientRect();
        return { w: r.width, h: r.height };
    }""")
    assert dims["w"] > 1 and dims["h"] > 1, (
        f"Canvas rendered size is still tiny after {LOAD_WAIT_MS}ms — "
        f"got {dims['w']}×{dims['h']}"
    )


@pytest.mark.browser
def test_time_to_first_render(page):
    """Game must produce a non-blank canvas frame within RENDER_BUDGET_S seconds.

    Polls every 500ms after the UME click until the canvas screenshot
    exceeds 500 bytes (indicating real pixel content).  Reports elapsed
    time so regressions in startup speed are visible in test output.
    """
    page.goto(GAME_URL)
    page.wait_for_selector("#canvas", timeout=15_000)

    start = time.monotonic()
    elapsed = None
    while time.monotonic() - start < RENDER_BUDGET_S:
        canvas_bytes = page.locator("#canvas").screenshot()
        if len(canvas_bytes) > 500:
            elapsed = time.monotonic() - start
            break
        page.wait_for_timeout(500)

    if elapsed is None:
        pytest.fail(f"Game did not render within {RENDER_BUDGET_S}s")

    print(f"\n  Time to first render: {elapsed:.1f}s")


# ---------------------------------------------------------------------------
# Interaction tests
# ---------------------------------------------------------------------------

@pytest.mark.browser
def test_input_changes_display(page):
    """Pressing Enter on the start screen must visibly update the canvas.

    We take a screenshot before and after the keypress.  If the game
    received the input and re-rendered, the PNG bytes will differ.
    """
    page.goto(GAME_URL)
    page.wait_for_selector("#canvas", timeout=15_000)
    page.wait_for_timeout(LOAD_WAIT_MS)

    page.locator("#canvas").click()                  # give the canvas focus / pass UME
    before = page.locator("#canvas").screenshot()

    page.keyboard.press("Enter")                     # advance past the start menu
    page.wait_for_timeout(2_000)                     # wait for re-render

    after = page.locator("#canvas").screenshot()
    assert before != after, (
        "Canvas did not change after pressing Enter — "
        "input may not be reaching the game"
    )
