import sys
from unittest.mock import Mock, MagicMock, patch

sys.modules["pygame"] = MagicMock()


def test_keys_ninja_view_draws_without_error():
    import game.screens.gameplay.keys_ninja_view as view_mod

    mock_pg = MagicMock()
    mock_pg.font.Font.return_value = Mock(render=Mock(return_value=Mock(get_rect=Mock(return_value=Mock()))))
    mock_pg.draw = Mock()

    screen = Mock()
    screen.get_width.return_value = 800
    screen.get_height.return_value = 600

    keybind_labels = {"left": "A", "right": "D", "up": "W", "down": "S", "space": "SPACE"}

    with patch.object(view_mod, "pygame", mock_pg):
        view = view_mod.KeysNinjaView(screen, keybind_labels)
        model = Mock()
        model.score = 10
        model.lives = 3
        model.combo = 2
        model.max_combo = 4
        model.keys = []
        model.flash_button = None
        model.flash_state = "normal"
        model.flash_end = 0
        model.state = "playing"

        view.draw(model, 1.0)

    assert mock_pg.draw.rect.called
