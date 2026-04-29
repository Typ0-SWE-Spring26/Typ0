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
