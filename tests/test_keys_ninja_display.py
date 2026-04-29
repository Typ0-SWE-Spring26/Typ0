import sys
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch

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


def test_keys_ninja_display_wires_menu_for_mode():
    import game.screens.gameplay.keys_ninja_display as display_mod

    mock_screen = Mock()
    mock_screen.get_width.return_value = 800
    mock_screen.get_height.return_value = 600
    mock_keybinds = Mock(key_labels={})

    with patch.object(display_mod, "MenuOverlay") as mock_menu, \
         patch.object(display_mod, "KeysNinjaView") as mock_view:
        mock_view.return_value = Mock()
        display_mod.KeysNinjaScreen(mock_screen, mock_keybinds)

    mock_menu.assert_called_once()
    assert mock_menu.call_args[1].get("game_mode") == "keys_ninja"


def test_keys_ninja_display_run_returns_controller_result():
    import game.screens.gameplay.keys_ninja_display as display_mod

    mock_screen = Mock()
    mock_screen.get_width.return_value = 800
    mock_screen.get_height.return_value = 600
    mock_keybinds = Mock(key_labels={})

    with patch.object(display_mod, "KeysNinjaController") as mock_ctrl, \
         patch.object(display_mod, "KeysNinjaView") as mock_view, \
         patch.object(display_mod, "MenuOverlay") as mock_menu:
        mock_view.return_value = Mock()
        mock_ctrl.return_value.run = AsyncMock(return_value="quit")
        screen = display_mod.KeysNinjaScreen(mock_screen, mock_keybinds)
        result = run_async(screen.run())

    assert result == "quit"
