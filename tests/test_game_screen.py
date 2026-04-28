import sys
from unittest.mock import Mock, patch

sys.modules["pygame"] = Mock()


def test_game_screen_wires_menu_overlay_with_simon_mode():
    import game.screens.gameplay.display as display_mod

    mock_screen = Mock()
    mock_keybinds = Mock(key_labels={}, button_keys={})

    with patch.object(display_mod, "MenuOverlay") as mock_menu:
        display_mod.GameScreen(mock_screen, mock_keybinds)

    mock_menu.assert_called_once()
    assert mock_menu.call_args[1].get("game_mode") == "simon"
