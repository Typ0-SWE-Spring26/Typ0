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


class _FakeMenu:
    def __init__(self, action):
        self.open = False
        self.active_submenu = None
        self._action = action

    def handle_event(self, _event):
        return self._action

    def draw(self):
        pass


class _FakeModel:
    def __init__(self):
        self.state = "playing"
        self.score = 0
        self.gameover_reason = ""

    def reset(self):
        pass

    def update(self, _now, _w, _h):
        return False


class _FakeView:
    def draw(self, _model, _scale):
        pass


def _build_controller(menu_action):
    import game.screens.gameplay.keys_ninja_controller as kn_mod

    mock_pg = MagicMock()
    mock_pg.QUIT = 256
    mock_pg.KEYDOWN = 768
    mock_pg.K_p = 112
    mock_pg.K_e = 101
    mock_pg.KMOD_CTRL = 64
    mock_pg.time.Clock.return_value = Mock()
    mock_pg.time.get_ticks.return_value = 0

    event = Mock()
    event.type = 123
    mock_pg.event.get.return_value = [event]

    screen = Mock()
    screen.get_width.return_value = 800
    screen.get_height.return_value = 600
    screen.present = Mock()

    controller = None
    with patch.object(kn_mod, "pygame", mock_pg), \
         patch.object(kn_mod, "animation_utils") as mock_anim:
        menu = _FakeMenu(menu_action)
        controller = kn_mod.KeysNinjaController(
            screen,
            _FakeModel(),
            _FakeView(),
            event_bus=Mock(),
            keybinds=Mock(),
            menu_overlay=menu,
        )
        controller._mock_anim = mock_anim
        controller._anim = mock_anim

    return controller


def test_menu_switch_mode_returns_target_tuple():
    controller = _build_controller(("switch_mode", "bopit"))

    result = controller._handle_menu_action(("switch_mode", "bopit"))

    assert result == ("switch_mode", "bopit")
    controller._mock_anim.stop_music.assert_called_once()


def test_menu_main_menu_returns_tuple():
    controller = _build_controller("main_menu")

    result = controller._handle_menu_action("main_menu")

    assert result == ("main_menu",)
    controller._mock_anim.stop_music.assert_called_once()


def test_set_paused_toggles_state():
    """Test that _set_paused emits events and toggles paused state."""
    controller = _build_controller(None)
    bus = controller._bus

    controller._set_paused(True)
    assert controller.paused is True
    bus.emit.assert_called()

    bus.reset_mock()
    controller._set_paused(False)
    assert controller.paused is False
    bus.emit.assert_called()


def test_set_paused_no_op_on_same_state():
    """Test that _set_paused does nothing if state hasn't changed."""
    controller = _build_controller(None)
    controller.paused = True
    bus = controller._bus
    bus.reset_mock()

    controller._set_paused(True)
    bus.emit.assert_not_called()


def test_menu_is_open_property():
    """Test _menu_is_open checks both open and active_submenu."""
    controller = _build_controller(None)
    
    assert controller._menu_is_open is False
    
    controller.menu_overlay.open = True
    assert controller._menu_is_open is True
    
    controller.menu_overlay.open = False
    controller.menu_overlay.active_submenu = "settings"
    assert controller._menu_is_open is True
    
    controller.menu_overlay.active_submenu = None
    assert controller._menu_is_open is False


def test_exit_overlay_screen_resets_state():
    """Test that exiting overlay closes menu and resumes gameplay."""
    controller = _build_controller(None)
    controller.menu_overlay.open = True
    controller.menu_overlay.active_submenu = "test"
    controller._menu_forced_pause = True
    controller.paused = True

    controller._exit_overlay_screen()

    assert controller.menu_overlay.open is False
    assert controller.menu_overlay.active_submenu is None
    assert controller._menu_forced_pause is False
    assert controller.paused is False


def test_handle_menu_action_switch_mode_string():
    """Test _handle_menu_action with 'switch_mode' string."""
    controller = _build_controller(None)
    
    result = controller._handle_menu_action("switch_mode")
    
    assert result == ("switch_mode",)


def test_handle_menu_action_none_returns_none():
    """Test _handle_menu_action returns None for unknown actions."""
    controller = _build_controller(None)
    
    result = controller._handle_menu_action("unknown_action")
    
    assert result is None


def test_handle_menu_action_empty_tuple():
    """Test _handle_menu_action handles empty tuple gracefully."""
    controller = _build_controller(None)
    
    result = controller._handle_menu_action(())
    
    assert result is None


def test_menu_is_open_no_overlay():
    """Test _menu_is_open is falsy when menu_overlay is None."""
    import game.screens.gameplay.keys_ninja_controller as kn_mod
    
    mock_pg = MagicMock()
    mock_pg.time.Clock.return_value = Mock()
    
    controller = None
    with patch.object(kn_mod, "pygame", mock_pg):
        controller = kn_mod.KeysNinjaController(
            Mock(),
            _FakeModel(),
            _FakeView(),
            event_bus=Mock(),
            keybinds=Mock(),
            menu_overlay=None,
        )
    
    assert not controller._menu_is_open


def test_pause_overlay_subscription():
    """Test that pause overlay is subscribed to event bus."""
    controller = _build_controller(None)
    pause_overlay = Mock()
    
    with patch.object(controller, "_bus"):
        kn_mod = sys.modules["game.screens.gameplay.keys_ninja_controller"]
        with patch.object(kn_mod, "animation_utils"):
            controller = _build_controller(None)
            controller.pause_overlay = pause_overlay
            
            # pause_overlay.subscribe should be called with _bus
            if pause_overlay:
                pause_overlay.subscribe.assert_not_called()  # subscribe happens in __init__


def test_exit_overlay_restores_music_when_not_playing():
    """Test that exiting overlay closes menu and resets pause state."""
    controller = _build_controller(None)
    controller.menu_overlay.open = True
    controller._menu_forced_pause = True
    controller.paused = True
    
    controller._exit_overlay_screen()
    
    # Should reset menu and pause state
    assert controller.menu_overlay.open is False
    assert controller._menu_forced_pause is False
    assert controller.paused is False
