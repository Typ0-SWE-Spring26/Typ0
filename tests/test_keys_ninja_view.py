import sys
from unittest.mock import Mock, MagicMock, patch

sys.modules["pygame"] = MagicMock()


def test_keys_ninja_view_draws_without_error():
    import game.screens.gameplay.keys_ninja_view as view_mod

    mock_pg = MagicMock()
    mock_font = Mock()
    mock_font.render.return_value = Mock(get_rect=Mock(return_value=Mock()))
    mock_pg.font.SysFont.return_value = mock_font
    mock_pg.font.Font.return_value = mock_font
    mock_pg.draw = Mock()
    mock_surface = Mock()
    mock_surface.copy.return_value = mock_surface
    mock_surface.set_alpha = Mock()
    mock_pg.image.load.return_value = Mock(convert_alpha=Mock(return_value=mock_surface))
    mock_pg.transform.smoothscale.return_value = mock_surface
    mock_pg.Surface.return_value = Mock(fill=Mock())
    mock_pg.transform.rotozoom.return_value = Mock(get_rect=Mock(return_value=Mock()))
    mock_pg.Rect.side_effect = lambda x, y, w, h: Mock(
        x=x,
        y=y,
        width=w,
        height=h,
        move=lambda dx, dy: Mock(x=x + dx, y=y + dy, width=w, height=h),
    )

    screen = Mock()
    screen.get_width.return_value = 800
    screen.get_height.return_value = 600

    keybind_labels = {"left": "A", "right": "D", "up": "W", "down": "S", "space": "SPACE"}

    with patch.object(view_mod, "pygame", mock_pg), \
         patch("game.screens.gameplay.view.pygame", mock_pg), \
         patch("game.screens.gameplay.view.animation_utils") as mock_anim:
        view = view_mod.KeysNinjaView(screen, keybind_labels)
        model = Mock()
        model.score = 10
        model.lives = 3
        model.combo = 2
        model.max_combo = 4
        key_obj = Mock()
        key_obj.scale = 1.0
        key_obj.is_bomb = False
        key_obj.char = "A"
        key_obj.alpha = 255
        key_obj.rotation = 0
        key_obj.x = 200
        key_obj.y = 200
        model.keys = [key_obj]
        model.flash_button = None
        model.flash_state = "normal"
        model.flash_end = 0
        model.state = "playing"

        view.draw(model, 1.0)

    assert mock_pg.draw.rect.called
