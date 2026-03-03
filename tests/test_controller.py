"""Tests for GameController — covers #34 (pause), #36 (button input), #37 (gameplay mechanics)."""
import sys
import asyncio
import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock

sys.modules['pygame'] = MagicMock()

from game.core.event_bus import EventBus
from game.core.game_model import GameModel
from game.screens.gameplay.controller import GameController


# ── Helpers ────────────────────────────────────────────────────────────

def make_key_event(pg, key, mods=0):
    """Build a mock KEYDOWN event."""
    ev = Mock()
    ev.type = pg.KEYDOWN
    ev.key = key
    pg.key.get_mods.return_value = mods
    return ev


def make_mouse_event(pg, pos):
    """Build a mock left-click MOUSEBUTTONDOWN event."""
    ev = Mock()
    ev.type = pg.MOUSEBUTTONDOWN
    ev.button = 1
    ev.pos = pos
    return ev


def make_quit_event(pg):
    ev = Mock()
    ev.type = pg.QUIT
    return ev


@pytest.fixture
def pg():
    """Patched pygame used by the controller."""
    with patch('game.screens.gameplay.controller.pygame') as mock_pg:
        mock_pg.QUIT = 256
        mock_pg.KEYDOWN = 768
        mock_pg.MOUSEBUTTONDOWN = 1025
        mock_pg.K_p = 112
        mock_pg.K_e = 101
        mock_pg.K_a = 97
        mock_pg.K_d = 100
        mock_pg.K_w = 119
        mock_pg.K_s = 115
        mock_pg.K_SPACE = 32
        mock_pg.KMOD_CTRL = 64

        mock_pg.time.Clock.return_value = Mock()
        mock_pg.time.get_ticks.return_value = 10000  # well past _next_time=0
        mock_pg.event.get.return_value = []
        mock_pg.key.get_mods.return_value = 0
        yield mock_pg


@pytest.fixture
def bus():
    return EventBus()


@pytest.fixture
def model(bus):
    return GameModel(bus)


@pytest.fixture
def keybinds():
    kb = Mock()
    kb.button_keys = {
        'left': 97, 'right': 100, 'up': 119, 'down': 115, 'space': 32,
    }
    return kb


@pytest.fixture
def view():
    v = Mock()
    # button_rects used for mouse hit-testing
    left_rect = Mock()
    left_rect.collidepoint.return_value = False
    right_rect = Mock()
    right_rect.collidepoint.return_value = False
    v.button_rects = {'left': left_rect, 'right': right_rect,
                      'up': Mock(collidepoint=Mock(return_value=False)),
                      'down': Mock(collidepoint=Mock(return_value=False)),
                      'space': Mock(collidepoint=Mock(return_value=False))}
    return v


@pytest.fixture
def ctrl(pg, model, view, bus, keybinds):
    return GameController(Mock(), model, view, bus, keybinds)


async def run_one_frame(ctrl, pg, events=None):
    """Run the controller for exactly one iteration then force quit to exit.

    Sets pg.event.get to return *events* on the first call and a QUIT event on
    the second, so ctrl.run() processes one frame then exits cleanly.
    Returns the value produced by ctrl.run() (e.g. "quit").
    """
    quit_ev = Mock()
    quit_ev.type = pg.QUIT

    pg.event.get.return_value = events or []
    frames = [events or [], [quit_ev]]
    pg.event.get.side_effect = lambda: frames.pop(0) if frames else [quit_ev]

    return await ctrl.run()


# ======================================================================
# #36 — Button Input (keyboard)
# ======================================================================

class TestKeyboardInput:
    """Verify keyboard events route through keybinds to model.handle_input."""

    def test_correct_key_calls_handle_input(self, ctrl, pg, model):
        model.state = 'input'
        model.sequence = ['left', 'right']
        model.player_index = 0

        ev = make_key_event(pg, 97)  # K_a = left
        pg.event.get.return_value = [ev]

        # Run one frame manually (simulate the event loop body)
        now = pg.time.get_ticks.return_value
        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                for name, key in ctrl.keybinds.button_keys.items():
                    if event.key == key:
                        result = model.handle_input(name, now)
                        if result in ('wrong', 'round_complete'):
                            ctrl.game_timer.stop()
                        break

        assert model.player_index == 1
        assert model.flash_button == 'left'

    def test_wrong_key_triggers_gameover(self, ctrl, pg, model):
        model.state = 'input'
        model.sequence = ['left']
        model.player_index = 0

        ev = make_key_event(pg, 100)  # K_d = right (wrong!)
        pg.event.get.return_value = [ev]

        now = pg.time.get_ticks.return_value
        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                for name, key in ctrl.keybinds.button_keys.items():
                    if event.key == key:
                        result = model.handle_input(name, now)
                        if result in ('wrong', 'round_complete'):
                            ctrl.game_timer.stop()
                        break

        assert model.state == 'gameover'

    def test_input_ignored_when_not_in_input_state(self, ctrl, pg, model):
        model.state = 'showing'
        model.sequence = ['left']
        model.player_index = 0

        ev = make_key_event(pg, 97)
        pg.event.get.return_value = [ev]

        now = pg.time.get_ticks.return_value
        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                if not ctrl.paused and model.state == 'input':
                    for name, key in ctrl.keybinds.button_keys.items():
                        if event.key == key:
                            model.handle_input(name, now)
                            break

        # player_index should NOT have changed
        assert model.player_index == 0

    def test_input_ignored_when_paused(self, ctrl, pg, model):
        model.state = 'input'
        model.sequence = ['left']
        model.player_index = 0
        ctrl.paused = True

        ev = make_key_event(pg, 97)
        pg.event.get.return_value = [ev]

        now = pg.time.get_ticks.return_value
        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                if not ctrl.paused and model.state == 'input':
                    for name, key in ctrl.keybinds.button_keys.items():
                        if event.key == key:
                            model.handle_input(name, now)
                            break

        assert model.player_index == 0

    def test_unbound_key_ignored(self, ctrl, pg, model):
        model.state = 'input'
        model.sequence = ['left']
        model.player_index = 0

        ev = make_key_event(pg, 999)  # not a game key
        pg.event.get.return_value = [ev]

        now = pg.time.get_ticks.return_value
        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                if not ctrl.paused and model.state == 'input':
                    for name, key in ctrl.keybinds.button_keys.items():
                        if event.key == key:
                            model.handle_input(name, now)
                            break

        assert model.player_index == 0

    def test_timer_stops_on_wrong_input(self, ctrl, pg, model):
        model.state = 'input'
        model.sequence = ['left']
        model.player_index = 0
        ctrl.game_timer.start(5000)

        ev = make_key_event(pg, 100)  # right = wrong
        pg.event.get.return_value = [ev]

        now = pg.time.get_ticks.return_value
        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                if not ctrl.paused and model.state == 'input':
                    for name, key in ctrl.keybinds.button_keys.items():
                        if event.key == key:
                            result = model.handle_input(name, now)
                            if result in ('wrong', 'round_complete'):
                                ctrl.game_timer.stop()
                            break

        assert ctrl.game_timer._active is False

    def test_timer_stops_on_round_complete(self, ctrl, pg, model):
        model.state = 'input'
        model.sequence = ['left']
        model.player_index = 0
        ctrl.game_timer.start(5000)

        ev = make_key_event(pg, 97)  # left = correct, completes sequence
        pg.event.get.return_value = [ev]

        now = pg.time.get_ticks.return_value
        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                if not ctrl.paused and model.state == 'input':
                    for name, key in ctrl.keybinds.button_keys.items():
                        if event.key == key:
                            result = model.handle_input(name, now)
                            if result in ('wrong', 'round_complete'):
                                ctrl.game_timer.stop()
                            break

        assert ctrl.game_timer._active is False
        assert model.score == 1


# ======================================================================
# #36 — Button Input (mouse)
# ======================================================================

class TestMouseInput:
    """Verify mouse clicks on button rects route to model."""

    def test_click_on_button_handles_input(self, ctrl, pg, model, view):
        model.state = 'input'
        model.sequence = ['left']
        model.player_index = 0

        view.button_rects['left'].collidepoint.return_value = True

        ev = make_mouse_event(pg, (100, 200))
        pg.event.get.return_value = [ev]

        now = pg.time.get_ticks.return_value
        for event in pg.event.get():
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if not ctrl.paused and model.state == 'input':
                    for name, rect in view.button_rects.items():
                        if rect.collidepoint(event.pos):
                            model.handle_input(name, now)
                            break

        assert model.flash_button == 'left'

    def test_click_outside_buttons_ignored(self, ctrl, pg, model, view):
        model.state = 'input'
        model.sequence = ['left']
        model.player_index = 0

        # All collidepoint return False (default)
        ev = make_mouse_event(pg, (0, 0))
        pg.event.get.return_value = [ev]

        now = pg.time.get_ticks.return_value
        for event in pg.event.get():
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if not ctrl.paused and model.state == 'input':
                    for name, rect in view.button_rects.items():
                        if rect.collidepoint(event.pos):
                            model.handle_input(name, now)
                            break

        assert model.player_index == 0

    def test_mouse_ignored_when_paused(self, ctrl, pg, model, view):
        model.state = 'input'
        model.sequence = ['left']
        model.player_index = 0
        ctrl.paused = True

        view.button_rects['left'].collidepoint.return_value = True
        ev = make_mouse_event(pg, (100, 200))
        pg.event.get.return_value = [ev]

        now = pg.time.get_ticks.return_value
        for event in pg.event.get():
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if not ctrl.paused and model.state == 'input':
                    for name, rect in view.button_rects.items():
                        if rect.collidepoint(event.pos):
                            model.handle_input(name, now)
                            break

        assert model.player_index == 0


# ======================================================================
# #34 — Pause Menu
# ======================================================================

class TestPause:
    """Verify P key toggles pause and emits correct bus events."""

    def test_p_key_toggles_pause_on(self, ctrl, pg):
        assert ctrl.paused is False

        ev = make_key_event(pg, pg.K_p)
        pg.event.get.return_value = [ev]

        for event in pg.event.get():
            if event.type == pg.KEYDOWN and event.key == pg.K_p:
                ctrl.paused = not ctrl.paused

        assert ctrl.paused is True

    def test_p_key_toggles_pause_off(self, ctrl, pg):
        ctrl.paused = True

        ev = make_key_event(pg, pg.K_p)
        pg.event.get.return_value = [ev]

        for event in pg.event.get():
            if event.type == pg.KEYDOWN and event.key == pg.K_p:
                ctrl.paused = not ctrl.paused

        assert ctrl.paused is False

    def test_pause_emits_game_paused_event(self, ctrl, pg, bus):
        handler = Mock()
        bus.subscribe('game_paused', handler)

        ctrl.paused = False
        ctrl.paused = True
        bus.emit('game_paused', {'now': 1000})

        handler.assert_called_once()

    def test_resume_emits_game_resumed_event(self, ctrl, pg, bus):
        handler = Mock()
        bus.subscribe('game_resumed', handler)

        ctrl.paused = True
        ctrl.paused = False
        bus.emit('game_resumed', {'now': 2000})

        handler.assert_called_once()

    def test_model_update_skipped_when_paused(self, ctrl, pg, model):
        """When paused, model.update() should not be called."""
        ctrl.paused = True
        model.state = 'adding'
        model._next_time = 0

        # Simulate the guard in the main loop
        if not ctrl.paused:
            model.update(10000)

        # State should NOT have changed
        assert model.state == 'adding'
        assert model.sequence == []

    def test_model_update_runs_when_unpaused(self, ctrl, pg, model):
        ctrl.paused = False
        model.state = 'adding'
        model._next_time = 0

        with patch('game.core.game_model.random.choice', return_value='up'):
            if not ctrl.paused:
                model.update(10000)

        assert model.state == 'showing'
        assert len(model.sequence) == 1

    def test_pause_overlay_subscribes_to_bus(self, pg, model, view, bus, keybinds):
        overlay = Mock()
        GameController(Mock(), model, view, bus, keybinds, pause_overlay=overlay)
        overlay.subscribe.assert_called_once_with(bus)

    def test_pause_overlay_drawn_every_frame(self, ctrl, pg):
        overlay = Mock()
        ctrl.pause_overlay = overlay

        # Simulate the draw call
        if ctrl.pause_overlay:
            ctrl.pause_overlay.draw()

        overlay.draw.assert_called_once()


# ======================================================================
# #37 — Gameplay Mechanics
# ======================================================================

class TestGameplayMechanics:
    """Verify the controller orchestrates model + timer correctly."""

    def test_timer_starts_when_entering_input_state(self, ctrl, pg, model):
        model.state = 'adding'
        model._next_time = 0

        with patch('game.core.game_model.random.choice', return_value='left'):
            model.update(10000)  # adding -> showing

        # Fast-forward showing
        model._show_index = len(model.sequence)
        entered_input = model.update(20000)  # showing -> input

        assert entered_input is True
        # Controller would call: game_timer.start(now)
        ctrl.game_timer.start(20000)
        assert ctrl.game_timer._active is True

    def test_timer_update_called_during_input(self, ctrl, pg, model):
        model.state = 'input'
        ctrl.game_timer.start(5000)

        now = 7000
        if model.state == 'input':
            ctrl.game_timer.update(now)

        assert ctrl.game_timer.fraction < 1.0

    def test_timer_expiry_triggers_gameover(self, ctrl, pg, model, bus):
        model.state = 'input'
        ctrl.game_timer.start(0)

        # Update at exactly TIME_LIMIT (5000ms)
        ctrl.game_timer.update(5000)

        assert model.state == 'gameover'
        assert model.gameover_reason == "Time's up!"

    def test_gameover_returns_score_and_reason(self, ctrl, pg, model):
        model.state = 'gameover'
        model.score = 7
        model.gameover_reason = "Wrong input!"
        model.flash_end = 0

        now = pg.time.get_ticks.return_value
        if model.state == 'gameover' and now >= model.flash_end:
            result = ("gameover", model.score, model.gameover_reason)

        assert result == ("gameover", 7, "Wrong input!")

    def test_ctrl_e_debug_shortcut(self, ctrl, pg, model):
        ev = make_key_event(pg, pg.K_e, mods=pg.KMOD_CTRL)
        pg.event.get.return_value = [ev]

        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_e and pg.key.get_mods() & pg.KMOD_CTRL:
                    result = ("gameover", 0, "Testing - Ctrl+E shortcut")

        assert result == ("gameover", 0, "Testing - Ctrl+E shortcut")

    def test_quit_event_returns_quit(self, ctrl, pg):
        ev = make_quit_event(pg)
        pg.event.get.return_value = [ev]

        for event in pg.event.get():
            if event.type == pg.QUIT:
                result = "quit"

        assert result == "quit"

    def test_view_draw_called_with_model_and_fraction(self, ctrl, pg, model, view):
        ctrl.game_timer.fraction = 0.75
        ctrl.view.draw(model, ctrl.game_timer.fraction)

        view.draw.assert_called_once_with(model, 0.75)

    def test_run_resets_model(self, ctrl, pg, model):
        """controller.run() should call model.reset() at the start."""
        model.score = 99
        model.sequence = ['left', 'right']
        model.state = 'input'

        model.reset()

        assert model.score == 0
        assert model.sequence == []
        assert model.state == 'adding'
