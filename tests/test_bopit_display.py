import sys
import asyncio
from unittest.mock import Mock, MagicMock, patch

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


def test_bopit_display_wires_menu_for_mode():
    import game.screens.gameplay.bopit_display as display_mod

    mock_screen = Mock()
    mock_keybinds = Mock(key_labels={})

    with patch.object(display_mod, "MenuOverlay") as mock_menu:
        display_mod.BopItScreen(mock_screen, mock_keybinds)

    mock_menu.assert_called_once()
    assert mock_menu.call_args[1].get("game_mode") == "bopit"


def test_bopit_display_run_returns_controller_result():
    import game.screens.gameplay.bopit_display as display_mod

    mock_screen = Mock()
    mock_keybinds = Mock(key_labels={})

    with patch.object(display_mod, "BopItController") as mock_ctrl:
        mock_ctrl.return_value.run = Mock(return_value="quit")
        screen = display_mod.BopItScreen(mock_screen, mock_keybinds)
        result = run_async(screen.run())

    assert result == "quit"
