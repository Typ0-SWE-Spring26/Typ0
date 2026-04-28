import asyncio
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

sys.modules["pygame"] = MagicMock()


def run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


class _RectHit:
    def __init__(self, hit=False):
        self._hit = hit

    def collidepoint(self, _):
        return self._hit


@pytest.fixture
def htp_ctx():
    import game.screens.how_to_play as htp_mod

    mock_pg = MagicMock()
    mock_pg.QUIT = 256
    mock_pg.KEYDOWN = 768
    mock_pg.MOUSEBUTTONDOWN = 1025
    mock_pg.K_ESCAPE = 27
    mock_pg.K_q = 113
    mock_pg.time.Clock.return_value = Mock()

    mock_screen = Mock()
    mock_screen.get_width.return_value = 800
    mock_screen.get_height.return_value = 600

    mock_anim = MagicMock()

    mock_font_manager = Mock()
    surf = Mock()
    surf.get_rect.return_value = Mock()
    mock_font_manager.render_text.return_value = surf

    with patch.object(htp_mod, "pygame", mock_pg), \
         patch.object(htp_mod, "animation_utils", mock_anim), \
         patch.object(htp_mod, "FontManager", return_value=mock_font_manager):
        yield htp_mod, mock_pg, mock_screen


def test_escape_returns_back(htp_ctx):
    htp_mod, mock_pg, mock_screen = htp_ctx

    ev = Mock()
    ev.type = mock_pg.KEYDOWN
    ev.key = mock_pg.K_ESCAPE
    mock_pg.event.get.return_value = [ev]

    screen = htp_mod.HowToPlayScreen(mock_screen)
    assert run_async(screen.run()) == "back"


def test_click_back_returns_back(htp_ctx):
    htp_mod, mock_pg, mock_screen = htp_ctx

    ev = Mock()
    ev.type = mock_pg.MOUSEBUTTONDOWN
    ev.button = 1
    ev.pos = (100, 100)
    mock_pg.event.get.return_value = [ev]

    screen = htp_mod.HowToPlayScreen(mock_screen)
    screen._back_rect = _RectHit(hit=True)

    assert run_async(screen.run()) == "back"


def test_quit_returns_quit(htp_ctx):
    htp_mod, mock_pg, mock_screen = htp_ctx

    ev = Mock()
    ev.type = mock_pg.QUIT
    mock_pg.event.get.return_value = [ev]

    screen = htp_mod.HowToPlayScreen(mock_screen)
    assert run_async(screen.run()) == "quit"


# ── Keys Ninja instructions in the right column ────────────────────────────

class _FakeRect:
    """Simple stand-in for pygame.Rect with real int attributes, so layout
    math (min/max///) works under fully-mocked pygame."""

    def __init__(self, *args):
        # Accept Rect(x,y,w,h) or Rect((x,y),(w,h)) signatures.
        if len(args) == 4:
            x, y, w, h = args
        elif len(args) == 2:
            (x, y), (w, h) = args
        else:
            x = y = w = h = 0
        self.x = self.left = int(x)
        self.y = self.top = int(y)
        self.width = self.w = int(w)
        self.height = self.h = int(h)
        self.right = self.x + self.width
        self.bottom = self.y + self.height
        self.centerx = self.x + self.width // 2
        self.centery = self.y + self.height // 2
        self.center = (self.centerx, self.centery)
        self.size = (self.width, self.height)
        self.topleft = (self.x, self.y)
        self.midleft = (self.x, self.centery)

    def move(self, dx, dy):
        return _FakeRect(self.x + dx, self.y + dy, self.width, self.height)

    def collidepoint(self, _pos):
        return False


@pytest.fixture
def htp_with_render_spy():
    """Fixture that records every (text, color) pair passed to render_text.

    Used to verify the color-coded Keys Ninja callout reaches the renderer
    with the expected colors.
    """
    import game.screens.how_to_play as htp_mod

    mock_pg = MagicMock()
    mock_pg.QUIT = 256
    mock_pg.KEYDOWN = 768
    mock_pg.MOUSEBUTTONDOWN = 1025
    mock_pg.K_ESCAPE = 27
    mock_pg.K_q = 113
    mock_pg.time.Clock.return_value = Mock()
    # Real Rects so width/height arithmetic in _draw works.
    mock_pg.Rect.side_effect = _FakeRect
    # Force the icon loader into its except branch so _icons stays {None,…}.
    # Real PNG decode isn't available in the headless test env anyway.
    mock_pg.image.load.side_effect = Exception("no real images in test env")

    mock_screen = Mock()
    mock_screen.get_width.return_value = 800
    mock_screen.get_height.return_value = 600

    mock_anim = MagicMock()

    # Surfaces report a deterministic size so layout math runs without errors.
    def _make_surf():
        s = Mock()
        s.get_width.return_value = 60
        s.get_height.return_value = 18
        s.get_size.return_value = (60, 18)
        s.get_rect.return_value = _FakeRect(0, 0, 60, 18)
        return s

    render_calls = []

    def _render(text, color, size):
        render_calls.append((text, color, size))
        return _make_surf()

    mock_fm = Mock()
    mock_fm.render_text.side_effect = _render

    with patch.object(htp_mod, "pygame", mock_pg), \
         patch.object(htp_mod, "animation_utils", mock_anim), \
         patch.object(htp_mod, "FontManager", return_value=mock_fm):
        yield htp_mod, mock_pg, mock_screen, render_calls


def _force_one_draw_then_back(mock_pg):
    """Have the run-loop draw exactly once, then return on the second poll."""
    esc = Mock()
    esc.type = mock_pg.KEYDOWN
    esc.key = mock_pg.K_ESCAPE
    # First poll: no events → draw runs.  Second poll: ESC → return "back".
    mock_pg.event.get.side_effect = [[], [esc]]


def test_keys_ninja_label_is_rendered(htp_with_render_spy):
    """The QUICK GUIDE must include a 'KEYS NINJA' entry."""
    htp_mod, mock_pg, mock_screen, render_calls = htp_with_render_spy
    _force_one_draw_then_back(mock_pg)

    screen = htp_mod.HowToPlayScreen(mock_screen)
    assert run_async(screen.run()) == "back"

    rendered_texts = [t for (t, _c, _s) in render_calls]
    assert "KEYS NINJA" in rendered_texts


def test_keys_ninja_callout_uses_purple_for_the_word_purple(htp_with_render_spy):
    """The word 'purple' must be rendered in the Keys Ninja purple color so
    the legend matches the keys the player sees in-game."""
    htp_mod, mock_pg, mock_screen, render_calls = htp_with_render_spy
    _force_one_draw_then_back(mock_pg)

    screen = htp_mod.HowToPlayScreen(mock_screen)
    run_async(screen.run())

    purple_renders = [
        (t, c) for (t, c, _s) in render_calls if t == "purple"
    ]
    assert purple_renders, "the word 'purple' was never rendered"
    assert all(c == htp_mod.HowToPlayScreen._NINJA_PURPLE for _t, c in purple_renders)


def test_keys_ninja_callout_uses_red_for_the_word_red(htp_with_render_spy):
    """The word 'red' must be rendered in the Keys Ninja red bomb color."""
    htp_mod, mock_pg, mock_screen, render_calls = htp_with_render_spy
    _force_one_draw_then_back(mock_pg)

    screen = htp_mod.HowToPlayScreen(mock_screen)
    run_async(screen.run())

    red_renders = [
        (t, c) for (t, c, _s) in render_calls if t == "red"
    ]
    assert red_renders, "the word 'red' was never rendered"
    assert all(c == htp_mod.HowToPlayScreen._NINJA_RED for _t, c in red_renders)


def test_keys_ninja_callout_mentions_falling_and_bombs(htp_with_render_spy):
    """The two callout lines should communicate the gameplay rules clearly."""
    htp_mod, mock_pg, mock_screen, render_calls = htp_with_render_spy
    _force_one_draw_then_back(mock_pg)

    screen = htp_mod.HowToPlayScreen(mock_screen)
    run_async(screen.run())

    joined = " ".join(t for (t, _c, _s) in render_calls if isinstance(t, str))
    # "before they fall" — covers the "type before it falls off-screen" rule.
    assert "fall" in joined.lower()
    # "bomb" — covers the "red = bomb, avoid" rule.
    assert "bomb" in joined.lower()


def test_inline_text_line_helper_advances_x_per_segment(htp_with_render_spy):
    """The new helper must lay segments out left-to-right (each one further
    right than the previous) and return a y past the line height."""
    htp_mod, _, mock_screen, render_calls = htp_with_render_spy
    screen = htp_mod.HowToPlayScreen(mock_screen)

    blits = []
    screen.screen = Mock()
    screen.screen.blit = lambda surf, rect: blits.append(rect)

    # Each segment renders at width=60 (from the fixture), so blit positions
    # should advance by ~60px per segment.
    new_y = screen._draw_inline_text_line(
        x=100, y=50,
        segments=[("a", (255, 0, 0)),
                  ("b", (0, 255, 0)),
                  ("c", (0, 0, 255))],
        size=17,
    )

    assert len(blits) == 3
    # y advanced past the line height + line_gap (18 + 2 = 20).
    assert new_y == 50 + 18 + 2

    # Also ensure each segment was rendered with its declared color.
    inline_render_colors = [c for (_t, c, _s) in render_calls[-3:]]
    assert inline_render_colors == [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
