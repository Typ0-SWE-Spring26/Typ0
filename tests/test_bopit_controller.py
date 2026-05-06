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
        self.state = "input"
        self.score = 0
        self.gameover_reason = ""
        self.flash_end = 0
        self.time_limit = 3000

    def reset(self):
        pass

    def update(self, _now):
        return True

    def handle_input(self, _name, _now):
        return "correct"

    def on_timer_expired(self, _data):
        pass


class _FakeView:
    def __init__(self):
        self.button_rects = {"left": Mock(collidepoint=Mock(return_value=False))}

    def draw(self, _model, _fraction):
        pass


def _build_controller(menu_action):
    import game.screens.gameplay.bopit_controller as bopit_mod

    mock_pg = MagicMock()
    mock_pg.QUIT = 256
    mock_pg.KEYDOWN = 768
    mock_pg.MOUSEBUTTONDOWN = 1025
    mock_pg.K_p = 112
    mock_pg.K_e = 101
    mock_pg.KMOD_CTRL = 64
    mock_pg.time.Clock.return_value = Mock()
    mock_pg.time.get_ticks.return_value = 0
    mock_pg.event.get.return_value = [Mock(type=123)]

    screen = Mock()
    screen.present = Mock()

    controller = None
    with patch.object(bopit_mod, "pygame", mock_pg), \
         patch.object(bopit_mod, "animation_utils") as mock_anim:
        menu = _FakeMenu(menu_action)
        controller = bopit_mod.BopItController(
            screen,
            _FakeModel(),
            _FakeView(),
            event_bus=Mock(),
            keybinds=Mock(button_keys={}),
            menu_overlay=menu,
        )
        controller._mock_anim = mock_anim
        controller._anim = mock_anim

    return controller


def test_bopit_switch_mode_returns_target_tuple():
    controller = _build_controller(("switch_mode", "keys_ninja"))

    result = controller._handle_menu_action(("switch_mode", "keys_ninja"))

    assert result == ("switch_mode", "keys_ninja")
    controller._mock_anim.stop_music.assert_called_once()


def test_bopit_main_menu_returns_tuple():
    controller = _build_controller("main_menu")

    result = controller._handle_menu_action("main_menu")

    assert result == ("main_menu",)
    controller._mock_anim.stop_music.assert_called_once()


def test_bopit_set_paused_toggles_state():
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


def test_bopit_set_paused_no_op_on_same_state():
    """Test that _set_paused does nothing if state hasn't changed."""
    controller = _build_controller(None)
    controller.paused = True
    bus = controller._bus
    bus.reset_mock()

    controller._set_paused(True)
    bus.emit.assert_not_called()


def test_bopit_menu_is_open_property():
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


def test_bopit_exit_overlay_screen_resets_state():
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


def test_bopit_process_input_result_correct():
    """Test _process_input_result returns True on input."""
    controller = _build_controller(None)
    
    result = controller._process_input_result("left", 0)
    
    assert result is True


def test_bopit_process_input_result_stops_timer_on_wrong():
    """Test _process_input_result stops timer when wrong input."""
    controller = _build_controller(None)
    controller.model.handle_input = Mock(return_value='wrong')
    controller.game_timer = Mock()

    result = controller._process_input_result("wrong_button", 0)

    assert result is True
    controller.game_timer.stop.assert_called_once()


def test_bopit_handle_menu_action_switch_mode_string():
    """Test _handle_menu_action with 'switch_mode' string."""
    controller = _build_controller(None)
    
    result = controller._handle_menu_action("switch_mode")
    
    assert result == ("switch_mode",)


def test_bopit_handle_menu_action_none_returns_none():
    """Test _handle_menu_action returns None for unknown actions."""
    controller = _build_controller(None)
    
    result = controller._handle_menu_action("unknown_action")
    
    assert result is None


def test_bopit_exit_overlay_restores_music_when_not_playing():
    """When music isn't playing on overlay exit, the controller restarts it."""
    import game.screens.gameplay.bopit_controller as bopit_mod

    controller = _build_controller(None)
    controller.menu_overlay.open = True
    controller._menu_forced_pause = True
    controller.paused = True

    # Re-patch animation_utils for the call: _build_controller's patch context
    # has already exited by the time we get here.
    with patch.object(bopit_mod, "animation_utils") as mock_anim:
        mock_anim.is_music_playing.return_value = False
        mock_anim.get_user_music_selection.return_value = "assets/Techno.ogg"
        controller._exit_overlay_screen()

    assert controller.menu_overlay.open is False
    assert controller._menu_forced_pause is False
    assert controller.paused is False
    mock_anim.play_music.assert_called_once_with("assets/Techno.ogg")


def test_bopit_process_input_result_round_complete_stops_timer():
    """`round_complete` result must stop the game timer."""
    controller = _build_controller(None)
    controller.model.handle_input = Mock(return_value='round_complete')
    controller.game_timer = Mock()

    result = controller._process_input_result("button", 0)

    assert result is True
    controller.game_timer.stop.assert_called_once()
