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
