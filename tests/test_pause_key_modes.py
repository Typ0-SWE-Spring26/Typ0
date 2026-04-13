import asyncio
import sys
from unittest.mock import Mock, MagicMock, patch

sys.modules["pygame"] = MagicMock()

from game.core.event_bus import EventBus
from game.screens.gameplay.bopit_controller import BopItController
from game.screens.multiplayer.game import MultiplayerGameScreen


def _make_key_event(pg, key):
    ev = Mock()
    ev.type = pg.KEYDOWN
    ev.key = key
    return ev


def _make_quit_event(pg):
    ev = Mock()
    ev.type = pg.QUIT
    return ev


def test_bopit_p_pause_persists_with_closed_menu_overlay():
    with patch("game.screens.gameplay.bopit_controller.pygame") as pg, \
         patch("game.screens.gameplay.bopit_controller.animation_utils") as audio:
        pg.QUIT = 256
        pg.KEYDOWN = 768
        pg.MOUSEBUTTONDOWN = 1025
        pg.K_p = 112
        pg.K_e = 101
        pg.KMOD_CTRL = 64
        pg.time.get_ticks.return_value = 10000
        pg.time.Clock.return_value = Mock()
        pg.key.get_mods.return_value = 0

        model = Mock()
        model.reset = Mock()
        model.state = "adding"
        model.update.return_value = False
        model.flash_end = 999999

        view = Mock()
        view.button_rects = {}

        screen = Mock()
        screen.present = Mock()

        keybinds = Mock()
        keybinds.button_keys = {}

        menu_overlay = Mock()
        menu_overlay.open = False
        menu_overlay.active_submenu = None
        menu_overlay.handle_event.return_value = None

        ctrl = BopItController(
            screen,
            model,
            view,
            EventBus(),
            keybinds,
            menu_overlay=menu_overlay,
        )

        p_event = _make_key_event(pg, pg.K_p)
        quit_event = _make_quit_event(pg)
        pg.event.get.side_effect = [[p_event], [quit_event]]

        audio.get_user_music_selection.return_value = "assets/Techno.ogg"

        result = asyncio.run(ctrl.run())

        assert result == "quit"
        assert ctrl.paused is True


def test_multiplayer_p_toggles_pause_and_emits_bus_events():
    with patch("game.screens.multiplayer.game.pygame") as pg, \
         patch("game.screens.multiplayer.game.animation_utils") as audio, \
         patch("game.screens.multiplayer.game.GameView") as view_cls:
        pg.QUIT = 256
        pg.KEYDOWN = 768
        pg.MOUSEBUTTONDOWN = 1025
        pg.K_p = 112
        pg.time.get_ticks.return_value = 10000
        pg.time.Clock.return_value = Mock()
        pg.font.Font.return_value = Mock()

        screen = Mock()
        screen.get_width.return_value = 800
        screen.get_height.return_value = 600
        screen.present = Mock()

        view = Mock()
        view.button_rects = {}
        view_cls.return_value = view

        client = Mock()
        client.poll.return_value = None

        keybinds = Mock()
        keybinds.key_labels = {}
        keybinds.button_keys = {}

        game = MultiplayerGameScreen(
            screen,
            client,
            my_name="A",
            opponent_name="B",
            seed=123,
            settings=0,
            keybinds=keybinds,
        )

        paused_events = []
        resumed_events = []
        game._bus.subscribe("game_paused", lambda data: paused_events.append(data))
        game._bus.subscribe("game_resumed", lambda data: resumed_events.append(data))

        p_event = _make_key_event(pg, pg.K_p)
        quit_event = _make_quit_event(pg)
        pg.event.get.side_effect = [[p_event], [quit_event]]

        result = asyncio.run(game.run())

        assert result == "quit"
        assert game._paused is True
        assert len(paused_events) == 1
        assert len(resumed_events) == 0
        audio.pause_music.assert_called_once()
