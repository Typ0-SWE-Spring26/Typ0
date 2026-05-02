"""Tests for the per-mode emo flavor text shown during gameplay.

All three modes (Simon / Bop-It / Keys Ninja) need to:
  - cycle through every flavor line
  - wrap back to the first line once the last is reached
  - never get stuck on a single line

Simon used to clamp at the last entry; Keys Ninja keyed off `score` which
grows by 10 per key, so `score % 6` only ever landed on three of six lines.
"""
import sys
from unittest.mock import Mock, MagicMock, patch

sys.modules["pygame"] = MagicMock()


# ── Mock helpers ──────────────────────────────────────────────────────────

def _make_rect(x, y, w, h):
    rect = Mock()
    rect.x, rect.y, rect.width, rect.height = x, y, w, h
    rect.left, rect.top, rect.right, rect.bottom = x, y, x + w, y + h
    rect.center = (x + w // 2, y + h // 2)
    rect.move = lambda dx, dy: _make_rect(x + dx, y + dy, w, h)
    return rect


def _build_pygame_mock():
    mock_pg = MagicMock()
    mock_font = Mock()
    rendered_surf = Mock()
    rendered_surf.get_rect = Mock(return_value=_make_rect(0, 0, 10, 10))
    rendered_surf.set_alpha = Mock()
    mock_font.render.return_value = rendered_surf
    mock_pg.font.SysFont.return_value = mock_font
    mock_pg.font.Font.return_value = mock_font

    mock_surface = Mock()
    mock_surface.copy.return_value = mock_surface
    mock_surface.set_alpha = Mock()
    mock_pg.image.load.return_value = Mock(convert_alpha=Mock(return_value=mock_surface))
    mock_pg.transform.smoothscale.return_value = mock_surface
    mock_pg.Surface.return_value = Mock(fill=Mock(), blit=Mock(), set_alpha=Mock())
    mock_pg.transform.rotozoom.return_value = Mock(get_rect=Mock(return_value=Mock()))
    mock_pg.Rect.side_effect = _make_rect
    return mock_pg, mock_font


def _make_screen():
    screen = Mock()
    screen.get_width.return_value = 800
    screen.get_height.return_value = 600
    return screen


_KEY_LABELS = {"left": "A", "right": "D", "up": "W", "down": "S", "space": "SPACE"}


def _rendered_text_in(call_args_list, allowed):
    """Pull the most recent line from `allowed` that was passed to font.render."""
    for call in reversed(call_args_list):
        if call.args and call.args[0] in allowed:
            return call.args[0]
    return None


# ── Simon-mode (GameView) wrap ────────────────────────────────────────────

def _simon_view():
    import game.screens.gameplay.view as view_mod
    mock_pg, mock_font = _build_pygame_mock()
    with patch.object(view_mod, "pygame", mock_pg), \
         patch.object(view_mod, "animation_utils"):
        view = view_mod.GameView(_make_screen(), _KEY_LABELS)
    return view, view_mod, mock_pg, mock_font


def _simon_emo_for_round(view, view_mod, mock_pg, mock_font, round_num, state="showing"):
    model = Mock()
    model.score = 0
    model.sequence = [0] * round_num
    model.player_index = 0
    model.state = state
    model.flash_button = None
    model.flash_state = "normal"
    mock_font.render.reset_mock()
    with patch.object(view_mod, "pygame", mock_pg), \
         patch.object(view_mod, "animation_utils"):
        view.draw(model, 1.0)
    text = _rendered_text_in(mock_font.render.call_args_list, view._emo_lines)
    assert text is not None, f"no emo line rendered for round {round_num}"
    return text


def test_simon_first_round_uses_first_emo_line():
    view, view_mod, mock_pg, mock_font = _simon_view()
    text = _simon_emo_for_round(view, view_mod, mock_pg, mock_font, 1)
    assert text == view._emo_lines[0]


def test_simon_last_indexed_round_uses_last_emo_line():
    view, view_mod, mock_pg, mock_font = _simon_view()
    n = len(view._emo_lines)
    text = _simon_emo_for_round(view, view_mod, mock_pg, mock_font, n)
    assert text == view._emo_lines[n - 1]


def test_simon_round_past_last_line_wraps_to_first():
    view, view_mod, mock_pg, mock_font = _simon_view()
    n = len(view._emo_lines)
    text = _simon_emo_for_round(view, view_mod, mock_pg, mock_font, n + 1)
    assert text == view._emo_lines[0]


def test_simon_round_far_past_last_line_keeps_wrapping():
    view, view_mod, mock_pg, mock_font = _simon_view()
    n = len(view._emo_lines)
    round_num = 3 * n + 2
    text = _simon_emo_for_round(view, view_mod, mock_pg, mock_font, round_num)
    assert text == view._emo_lines[(round_num - 1) % n]


def test_simon_emo_line_shown_in_adding_state_too():
    view, view_mod, mock_pg, mock_font = _simon_view()
    text = _simon_emo_for_round(view, view_mod, mock_pg, mock_font, 1, state="adding")
    assert text == view._emo_lines[0]


def test_simon_visits_every_emo_line_across_a_run():
    """Driving rounds 1..n should produce each line at least once."""
    view, view_mod, mock_pg, mock_font = _simon_view()
    n = len(view._emo_lines)
    seen = {_simon_emo_for_round(view, view_mod, mock_pg, mock_font, r) for r in range(1, n + 1)}
    assert seen == set(view._emo_lines), f"missing lines: {set(view._emo_lines) - seen}"


# ── Bop-It mode wrap ──────────────────────────────────────────────────────

# The lines live inline inside BopItView.draw; mirror them here so tests don't
# break silently if someone reorders the list.
_BOPIT_EMO_LINES = [
    "do what you're told. like always.",
    "faster. you're not fast enough.",
    "react. that's all you're good for.",
    "keep going. it won't end well.",
    "your hands move. your heart doesn't.",
    "bop it. bury it. repeat.",
]


def _bopit_view():
    import game.screens.gameplay.bopit_view as view_mod
    mock_pg, mock_font = _build_pygame_mock()
    with patch.object(view_mod, "pygame", mock_pg), \
         patch("game.screens.gameplay.view.pygame", mock_pg), \
         patch("game.screens.gameplay.view.animation_utils"), \
         patch.object(view_mod, "animation_utils"):
        view = view_mod.BopItView(_make_screen(), _KEY_LABELS)
    return view, view_mod, mock_pg, mock_font


def _bopit_emo_for_score(view, view_mod, mock_pg, mock_font, score):
    model = Mock()
    model.score = score
    model.sequence = []
    model.player_index = 0
    model.state = "input"
    model.flash_button = None
    model.flash_state = "normal"
    model.current_command = None
    mock_font.render.reset_mock()
    with patch.object(view_mod, "pygame", mock_pg), \
         patch("game.screens.gameplay.view.pygame", mock_pg), \
         patch("game.screens.gameplay.view.animation_utils"), \
         patch.object(view_mod, "animation_utils"):
        view.draw(model, 1.0)
    text = _rendered_text_in(mock_font.render.call_args_list, _BOPIT_EMO_LINES)
    assert text is not None, f"no emo line rendered for score {score}"
    return text


def test_bopit_score_wraps_to_first_line():
    view, view_mod, mock_pg, mock_font = _bopit_view()
    n = len(_BOPIT_EMO_LINES)
    assert _bopit_emo_for_score(view, view_mod, mock_pg, mock_font, n) == _BOPIT_EMO_LINES[0]


def test_bopit_visits_every_emo_line_across_a_run():
    """Bopit awards +1 per command, so consecutive scores must exercise every line."""
    view, view_mod, mock_pg, mock_font = _bopit_view()
    n = len(_BOPIT_EMO_LINES)
    seen = {
        _bopit_emo_for_score(view, view_mod, mock_pg, mock_font, s)
        for s in range(n)
    }
    assert seen == set(_BOPIT_EMO_LINES), f"missing lines: {set(_BOPIT_EMO_LINES) - seen}"


# ── Keys Ninja mode wrap ──────────────────────────────────────────────────

_NINJA_EMO_LINES = [
    "they keep falling. so do you.",
    "type faster. feel nothing.",
    "the keys are falling oh no..",
    "hit them. miss them. it's all the same.",
    "gravity doesn't care about your feelings.",
    "dodge the bombs or dont",
]


def _ninja_view():
    import game.screens.gameplay.keys_ninja_view as view_mod
    mock_pg, mock_font = _build_pygame_mock()
    with patch.object(view_mod, "pygame", mock_pg), \
         patch("game.screens.gameplay.view.pygame", mock_pg), \
         patch("game.screens.gameplay.view.animation_utils"):
        view = view_mod.KeysNinjaView(_make_screen(), _KEY_LABELS)
    return view, view_mod, mock_pg, mock_font


def _ninja_emo_for_score(view, view_mod, mock_pg, mock_font, score):
    model = Mock()
    model.score = score
    model.lives = 3
    model.combo = 0
    model.max_combo = 0
    model.keys = []
    model.flash_button = None
    model.flash_state = "normal"
    model.state = "playing"
    mock_font.render.reset_mock()
    with patch.object(view_mod, "pygame", mock_pg), \
         patch("game.screens.gameplay.view.pygame", mock_pg), \
         patch("game.screens.gameplay.view.animation_utils"):
        view.draw(model, 1.0)
    text = _rendered_text_in(mock_font.render.call_args_list, _NINJA_EMO_LINES)
    assert text is not None, f"no emo line rendered for score {score}"
    return text


def test_ninja_score_wraps_to_first_line():
    """After 6 keys (60 points), the line should wrap back to line 0."""
    view, view_mod, mock_pg, mock_font = _ninja_view()
    n = len(_NINJA_EMO_LINES)
    assert _ninja_emo_for_score(view, view_mod, mock_pg, mock_font, n * 10) == _NINJA_EMO_LINES[0]


def test_ninja_visits_every_emo_line_across_a_run():
    """Each key adds +10. Score % 6 alone would skip half the lines —
    the divide-by-increment fix must make every line reachable."""
    view, view_mod, mock_pg, mock_font = _ninja_view()
    n = len(_NINJA_EMO_LINES)
    seen = {
        _ninja_emo_for_score(view, view_mod, mock_pg, mock_font, hits * 10)
        for hits in range(n)
    }
    assert seen == set(_NINJA_EMO_LINES), f"missing lines: {set(_NINJA_EMO_LINES) - seen}"


def test_ninja_keeps_wrapping_past_one_full_cycle():
    """Hits 6..11 should mirror lines 0..5 again."""
    view, view_mod, mock_pg, mock_font = _ninja_view()
    n = len(_NINJA_EMO_LINES)
    for hits in range(n):
        text = _ninja_emo_for_score(view, view_mod, mock_pg, mock_font, (n + hits) * 10)
        assert text == _NINJA_EMO_LINES[hits], f"hits={n + hits}: got {text!r}"
