"""Tests for the Simon-mode emo flavor text shown during showing/adding phases.

The line index used to clamp at the last entry, so high rounds got stuck on
the final line. It now wraps modulo the number of lines.
"""
import sys
from unittest.mock import Mock, MagicMock, patch

sys.modules["pygame"] = MagicMock()


def _make_rect(x, y, w, h):
    rect = Mock()
    rect.x, rect.y, rect.width, rect.height = x, y, w, h
    rect.left, rect.top, rect.right, rect.bottom = x, y, x + w, y + h
    rect.center = (x + w // 2, y + h // 2)
    rect.move = lambda dx, dy: _make_rect(x + dx, y + dy, w, h)
    return rect


def _build_view():
    """Construct a GameView with pygame fully mocked out."""
    import game.screens.gameplay.view as view_mod

    mock_pg = MagicMock()
    mock_font = Mock()
    rendered_surf = Mock()
    rendered_surf.get_rect = Mock(return_value=_make_rect(0, 0, 10, 10))
    rendered_surf.set_alpha = Mock()
    mock_font.render.return_value = rendered_surf
    mock_pg.font.SysFont.return_value = mock_font

    mock_surface = Mock()
    mock_surface.copy.return_value = mock_surface
    mock_pg.image.load.return_value = Mock(convert_alpha=Mock(return_value=mock_surface))
    mock_pg.transform.smoothscale.return_value = mock_surface
    mock_pg.Surface.return_value = Mock(fill=Mock(), blit=Mock(), set_alpha=Mock())
    mock_pg.Rect.side_effect = _make_rect

    screen = Mock()
    screen.get_width.return_value = 800
    screen.get_height.return_value = 600

    keybind_labels = {"left": "A", "right": "D", "up": "W", "down": "S", "space": "SPACE"}

    with patch.object(view_mod, "pygame", mock_pg), \
         patch.object(view_mod, "animation_utils"):
        view = view_mod.GameView(screen, keybind_labels)

    return view, view_mod, mock_pg, mock_font


def _make_model(round_num, state="showing"):
    model = Mock()
    model.score = 0
    model.sequence = [0] * round_num
    model.player_index = 0
    model.state = state
    model.flash_button = None
    model.flash_state = "normal"
    return model


def _rendered_emo_text(view, mock_font, model):
    """Drive the view and pull the emo line out of the render call args.

    The view also renders SCORE / ROUND / button labels, so we filter to the
    text that actually appears in `view._emo_lines`.
    """
    mock_font.render.reset_mock()
    import game.screens.gameplay.view as view_mod
    mock_pg = sys.modules["pygame"]
    with patch.object(view_mod, "pygame", mock_pg), \
         patch.object(view_mod, "animation_utils"):
        view.draw(model, 1.0)

    rendered = [c.args[0] for c in mock_font.render.call_args_list if c.args]
    emo = [t for t in rendered if t in view._emo_lines]
    assert emo, f"no emo line was rendered; saw {rendered!r}"
    return emo[-1]


def test_first_round_uses_first_emo_line():
    view, _, _, mock_font = _build_view()
    text = _rendered_emo_text(view, mock_font, _make_model(round_num=1))
    assert text == view._emo_lines[0]


def test_last_indexed_round_uses_last_emo_line():
    view, _, _, mock_font = _build_view()
    n = len(view._emo_lines)
    text = _rendered_emo_text(view, mock_font, _make_model(round_num=n))
    assert text == view._emo_lines[n - 1]


def test_round_past_last_line_wraps_to_first():
    """Round n+1 used to clamp to the final line; it should wrap to line 0."""
    view, _, _, mock_font = _build_view()
    n = len(view._emo_lines)
    text = _rendered_emo_text(view, mock_font, _make_model(round_num=n + 1))
    assert text == view._emo_lines[0]


def test_round_far_past_last_line_keeps_wrapping():
    view, _, _, mock_font = _build_view()
    n = len(view._emo_lines)
    # Three full cycles plus 2 -> index (3n + 2 - 1) % n == 1
    round_num = 3 * n + 2
    text = _rendered_emo_text(view, mock_font, _make_model(round_num=round_num))
    expected_idx = (round_num - 1) % n
    assert text == view._emo_lines[expected_idx]


def test_emo_line_shown_in_adding_state_too():
    view, _, _, mock_font = _build_view()
    text = _rendered_emo_text(view, mock_font, _make_model(round_num=1, state="adding"))
    assert text == view._emo_lines[0]
