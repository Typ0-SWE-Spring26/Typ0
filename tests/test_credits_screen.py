"""Tests for the keyboard-keycap redesign of the credits screen.

Complements the exit/navigation tests in test_new_features.py. These cover:
  - CREDITS data integrity (roles, names)
  - Keycap sizing math (_keycap_size)
  - Name row wrapping (_draw_name_keys) — all names drawn, in order,
    including narrow-wrap, single-name, empty, and oversize-name cases
  - Title keycaps (_draw_title_keys) — one keycap per character
  - Palette sanity — hover brighter, base darker than face, text contrast
  - Click edge cases — wrong button, click outside back_rect
  - Draw-loop smoke test — multiple frames don't crash under full mocks
"""
import asyncio
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

sys.modules["pygame"] = MagicMock()


def run_async(coro):
    """Run a coroutine, handling the case where a loop is already running."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


def _make_font_manager(char_w=10, line_h=14):
    """Mock FontManager whose render_text returns surfaces with deterministic sizes.

    width = char_w * len(text), height = line_h
    """
    def _render(text, color=None, size=18):
        surf = Mock()
        surf.get_width.return_value = char_w * len(text)
        surf.get_height.return_value = line_h
        surf.get_rect.return_value = Mock()
        return surf

    fm = Mock()
    fm.render_text.side_effect = _render
    return fm


@pytest.fixture
def creds_ctx():
    """Patched credits module ready for instantiation.

    Yields (credits_module, mock_pygame, mock_screen, mock_font_manager).
    """
    import game.screens.credits as creds_mod

    mock_pg = MagicMock()
    mock_pg.QUIT = 256
    mock_pg.KEYDOWN = 768
    mock_pg.MOUSEBUTTONDOWN = 1025
    mock_pg.K_ESCAPE = 27
    mock_pg.K_q = 113
    mock_pg.time.Clock.return_value = Mock()
    mock_pg.mouse.get_pos.return_value = (0, 0)

    mock_screen = Mock()
    mock_screen.get_width.return_value = 800
    mock_screen.get_height.return_value = 600

    fm = _make_font_manager()
    mock_anim = MagicMock()

    with patch.object(creds_mod, "pygame", mock_pg), \
         patch.object(creds_mod, "animation_utils", mock_anim), \
         patch.object(creds_mod, "FontManager", return_value=fm):
        yield creds_mod, mock_pg, mock_screen, fm


# ── Data integrity ──────────────────────────────────────────────────────────

class TestCreditsDataIntegrity:
    def test_every_name_is_a_nonempty_string(self):
        from game.screens.credits import CREDITS
        for role, names in CREDITS:
            for name in names:
                assert isinstance(name, str), f"non-string name in role {role!r}: {name!r}"
                assert name.strip(), f"empty/whitespace name in role {role!r}"

    def test_every_role_label_is_a_nonempty_string(self):
        from game.screens.credits import CREDITS
        for role, _ in CREDITS:
            assert isinstance(role, str)
            assert role.strip()

    def test_roles_are_unique(self):
        from game.screens.credits import CREDITS
        roles = [r for r, _ in CREDITS]
        assert len(roles) == len(set(roles)), f"duplicate role in CREDITS: {roles}"


# ── Keycap sizing math ──────────────────────────────────────────────────────

class TestKeycapSizing:
    def test_keycap_adds_padding_to_text_size(self, creds_ctx):
        creds_mod, _, mock_screen, _ = creds_ctx
        screen = creds_mod.CreditsScreen(mock_screen)
        w, h = screen._keycap_size("A", font_size=18, pad_x=10, pad_y=5)
        # mocked render_text: width = 10*len(text), height = 14
        assert w == 10 + 2 * 10
        assert h == 14 + 2 * 5

    def test_keycap_width_scales_with_text_length(self, creds_ctx):
        creds_mod, _, mock_screen, _ = creds_ctx
        screen = creds_mod.CreditsScreen(mock_screen)
        w1, _ = screen._keycap_size("A", font_size=18, pad_x=10, pad_y=5)
        w2, _ = screen._keycap_size("Austin", font_size=18, pad_x=10, pad_y=5)
        assert w2 > w1

    def test_keycap_height_same_for_same_font_size(self, creds_ctx):
        creds_mod, _, mock_screen, _ = creds_ctx
        screen = creds_mod.CreditsScreen(mock_screen)
        _, h1 = screen._keycap_size("A", font_size=18, pad_x=10, pad_y=5)
        _, h2 = screen._keycap_size("Charlie", font_size=18, pad_x=10, pad_y=5)
        assert h1 == h2


# ── Name-row wrapping ───────────────────────────────────────────────────────

class TestNameRowWrapping:
    def _spy_keycaps(self, screen):
        """Patch _draw_keycap to record each text arg it receives."""
        drawn = []

        def _record(text, *_a, **_kw):
            drawn.append(text)
            return Mock()

        return drawn, patch.object(screen, "_draw_keycap", side_effect=_record)

    def test_wide_max_width_draws_all_names(self, creds_ctx):
        creds_mod, _, mock_screen, _ = creds_ctx
        screen = creds_mod.CreditsScreen(mock_screen)
        drawn, spy = self._spy_keycaps(screen)
        with spy:
            used = screen._draw_name_keys(
                ["Austin", "Ben", "Charlie"], center_x=400, top_y=100,
                max_width=10_000, font_size=18, pad_x=10, pad_y=5, gap=7, row_gap=6,
            )
        assert drawn == ["Austin", "Ben", "Charlie"]
        assert used > 0  # something was laid out

    def test_narrow_max_width_wraps_without_losing_names(self, creds_ctx):
        """All 9 contributor names must survive the wrap, in original order."""
        creds_mod, _, mock_screen, _ = creds_ctx
        screen = creds_mod.CreditsScreen(mock_screen)
        drawn, spy = self._spy_keycaps(screen)
        names = ["Austin", "Ben", "Charlie", "Dipen", "Gabi",
                 "Jude", "Joel", "Kregg", "Oriye"]
        with spy:
            screen._draw_name_keys(
                names, center_x=400, top_y=100,
                max_width=150,  # narrow — guarantees >=2 rows
                font_size=18, pad_x=10, pad_y=5, gap=7, row_gap=6,
            )
        assert drawn == names

    def test_single_name_draws_one_keycap(self, creds_ctx):
        creds_mod, _, mock_screen, _ = creds_ctx
        screen = creds_mod.CreditsScreen(mock_screen)
        drawn, spy = self._spy_keycaps(screen)
        with spy:
            screen._draw_name_keys(
                ["Ben"], center_x=400, top_y=100, max_width=300,
                font_size=18, pad_x=10, pad_y=5, gap=7, row_gap=6,
            )
        assert drawn == ["Ben"]

    def test_empty_list_draws_nothing(self, creds_ctx):
        creds_mod, _, mock_screen, _ = creds_ctx
        screen = creds_mod.CreditsScreen(mock_screen)
        drawn, spy = self._spy_keycaps(screen)
        with spy:
            used = screen._draw_name_keys(
                [], center_x=400, top_y=100, max_width=300,
                font_size=18, pad_x=10, pad_y=5, gap=7, row_gap=6,
            )
        assert drawn == []
        assert used == 0

    def test_name_wider_than_max_width_still_renders(self, creds_ctx):
        """A single name wider than max_width must NOT infinite-loop or be dropped.

        It should still get its own keycap (overflowing slightly is acceptable).
        """
        creds_mod, _, mock_screen, _ = creds_ctx
        screen = creds_mod.CreditsScreen(mock_screen)
        drawn, spy = self._spy_keycaps(screen)
        with spy:
            screen._draw_name_keys(
                ["VeryLongContributorName", "Ben"], center_x=400, top_y=100,
                max_width=50,  # tiny
                font_size=18, pad_x=10, pad_y=5, gap=7, row_gap=6,
            )
        assert drawn == ["VeryLongContributorName", "Ben"]


# ── Title keycaps ───────────────────────────────────────────────────────────

class TestTitleKeys:
    def test_draws_one_keycap_per_character(self, creds_ctx):
        creds_mod, _, mock_screen, _ = creds_ctx
        screen = creds_mod.CreditsScreen(mock_screen)
        drawn = []

        def _record(text, *_a, **_kw):
            drawn.append(text)
            return Mock()

        with patch.object(screen, "_draw_keycap", side_effect=_record):
            screen._draw_title_keys("CREDITS", center_x=400, top_y=40)
        assert drawn == list("CREDITS")
        assert len(drawn) == 7

    def test_empty_title_draws_no_keycaps(self, creds_ctx):
        """Defensive: empty title string shouldn't crash or draw anything."""
        creds_mod, _, mock_screen, _ = creds_ctx
        screen = creds_mod.CreditsScreen(mock_screen)
        drawn = []

        def _record(text, *_a, **_kw):
            drawn.append(text)
            return Mock()

        with patch.object(screen, "_draw_keycap", side_effect=_record):
            screen._draw_title_keys("", center_x=400, top_y=40)
        assert drawn == []


# ── Palette sanity ──────────────────────────────────────────────────────────

class TestPalette:
    def _cs(self):
        from game.screens.credits import CreditsScreen
        return CreditsScreen

    def test_all_palette_entries_are_valid_rgb_tuples(self):
        cs = self._cs()
        palette = [
            cs._KEY_FACE, cs._KEY_FACE_HOVER,
            cs._KEY_BASE, cs._KEY_BASE_HOVER,
            cs._KEY_OUTLINE, cs._KEY_TEXT,
            cs._ACCENT, cs._HINT_TEXT, cs._DIVIDER,
            cs._SUBTLE_TEXT, cs._GRAD_TOP, cs._GRAD_BOTTOM,
        ]
        for color in palette:
            assert isinstance(color, tuple)
            assert len(color) == 3
            for channel in color:
                assert isinstance(channel, int)
                assert 0 <= channel <= 255

    def test_hover_face_is_brighter_than_normal(self):
        cs = self._cs()
        # Hover state must give visible feedback — total channel brightness check.
        assert sum(cs._KEY_FACE_HOVER) > sum(cs._KEY_FACE)

    def test_hover_base_is_brighter_than_normal(self):
        cs = self._cs()
        assert sum(cs._KEY_BASE_HOVER) > sum(cs._KEY_BASE)

    def test_base_is_darker_than_face_for_3d_effect(self):
        """The stacked-rect 3D illusion depends on the base being darker."""
        cs = self._cs()
        assert sum(cs._KEY_BASE) < sum(cs._KEY_FACE)

    def test_keycap_depth_is_positive(self):
        cs = self._cs()
        assert cs._KEY_DEPTH > 0

    def test_text_is_readable_on_face(self):
        """Text must be dramatically darker than the face for legibility."""
        cs = self._cs()
        assert sum(cs._KEY_FACE) - sum(cs._KEY_TEXT) > 250


# ── Click handling edge cases ───────────────────────────────────────────────

class TestClickEdgeCases:
    """The back button should only trigger on left-click inside its rect."""

    def _make_click(self, pg, button=1, pos=(400, 520)):
        ev = Mock()
        ev.type = pg.MOUSEBUTTONDOWN
        ev.button = button
        ev.pos = pos
        return ev

    def _make_esc(self, pg):
        ev = Mock()
        ev.type = pg.KEYDOWN
        ev.key = pg.K_ESCAPE
        return ev

    def test_right_click_on_back_does_not_dismiss(self, creds_ctx):
        """Right-click (button=3) in the back area must NOT return 'back'."""
        creds_mod, mock_pg, mock_screen, _ = creds_ctx
        fake_rect = MagicMock()
        fake_rect.collidepoint.return_value = True  # click IS inside

        right_click = self._make_click(mock_pg, button=3)
        esc = self._make_esc(mock_pg)
        # Frame 1: right-click (ignored). Frame 2: ESC → "back".
        mock_pg.event.get.side_effect = [[right_click], [esc]]

        with patch.object(mock_pg, "Rect", return_value=fake_rect):
            screen = creds_mod.CreditsScreen(mock_screen)
            result = run_async(screen.run())

        assert result == "back"
        # Two frames worth of event polls = the right-click was processed without exit.
        assert mock_pg.event.get.call_count == 2

    def test_middle_click_on_back_does_not_dismiss(self, creds_ctx):
        """Middle-click (button=2) must also be ignored."""
        creds_mod, mock_pg, mock_screen, _ = creds_ctx
        fake_rect = MagicMock()
        fake_rect.collidepoint.return_value = True

        middle_click = self._make_click(mock_pg, button=2)
        esc = self._make_esc(mock_pg)
        mock_pg.event.get.side_effect = [[middle_click], [esc]]

        with patch.object(mock_pg, "Rect", return_value=fake_rect):
            screen = creds_mod.CreditsScreen(mock_screen)
            result = run_async(screen.run())

        assert result == "back"
        assert mock_pg.event.get.call_count == 2

    def test_left_click_outside_back_rect_is_ignored(self, creds_ctx):
        """Left-click with collidepoint=False must not return 'back'."""
        creds_mod, mock_pg, mock_screen, _ = creds_ctx
        fake_rect = MagicMock()
        fake_rect.collidepoint.return_value = False  # outside the button

        click = self._make_click(mock_pg, button=1)
        esc = self._make_esc(mock_pg)
        mock_pg.event.get.side_effect = [[click], [esc]]

        with patch.object(mock_pg, "Rect", return_value=fake_rect):
            screen = creds_mod.CreditsScreen(mock_screen)
            result = run_async(screen.run())

        assert result == "back"
        assert mock_pg.event.get.call_count == 2

    def test_unrelated_keypress_is_ignored(self, creds_ctx):
        """A key other than ESC/Q must not dismiss the credits screen."""
        creds_mod, mock_pg, mock_screen, _ = creds_ctx
        # Pick a key value not used for back navigation.
        mock_pg.K_a = 97

        unrelated = Mock()
        unrelated.type = mock_pg.KEYDOWN
        unrelated.key = mock_pg.K_a

        esc = self._make_esc(mock_pg)
        mock_pg.event.get.side_effect = [[unrelated], [esc]]

        screen = creds_mod.CreditsScreen(mock_screen)
        result = run_async(screen.run())
        assert result == "back"
        assert mock_pg.event.get.call_count == 2


# ── Draw-loop smoke test ────────────────────────────────────────────────────

class TestDrawLoopSmoke:
    def test_many_empty_frames_then_quit_does_not_crash(self, creds_ctx):
        """Multiple draw iterations must complete without crashing under mocks.

        This is a regression guard against MagicMock arithmetic errors in new
        layout/helper code (we previously hit a `MagicMock > int` TypeError
        during row wrapping).
        """
        creds_mod, mock_pg, mock_screen, _ = creds_ctx
        quit_ev = Mock()
        quit_ev.type = mock_pg.QUIT
        mock_pg.event.get.side_effect = [[]] * 5 + [[quit_ev]]

        screen = creds_mod.CreditsScreen(mock_screen)
        assert run_async(screen.run()) == "quit"
        # 5 empty frames + 1 quit frame = 6 event.get() calls.
        assert mock_pg.event.get.call_count == 6
