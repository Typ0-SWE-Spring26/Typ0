"""Comprehensive tests for GameScreen MVC modules."""
import sys
import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, call, AsyncMock

# Mock pygame and other dependencies before importing
sys.modules['pygame'] = MagicMock()

from game.screens.gameplay.display import GameScreen
from game.core.game_model import GameModel, BUTTON_NAMES
from game.screens.gameplay.view import GameView
from game.screens.gameplay.controller import GameController
from game.core.keybinds import KeybindManager


@pytest.fixture
def mock_pygame():
    """Mock pygame modules and functions."""
    with patch('game.screens.gameplay.view.pygame') as mock_view_pg, \
         patch('game.screens.gameplay.controller.pygame') as mock_ctrl_pg:
        # Mock screen
        mock_screen = Mock()
        mock_screen.get_width.return_value = 800
        mock_screen.get_height.return_value = 600

        # Mock image loading
        mock_image = Mock()
        mock_image.convert_alpha.return_value = Mock()
        mock_view_pg.image.load.return_value = mock_image

        # Mock font
        mock_font = Mock()
        mock_font.render.return_value = Mock()
        mock_view_pg.font.SysFont.return_value = mock_font

        # Mock key names (needed for display.py facade)
        mock_ctrl_pg.key.name.side_effect = lambda k: {
            mock_ctrl_pg.K_a: 'a',
            mock_ctrl_pg.K_d: 'd',
            mock_ctrl_pg.K_w: 'w',
            mock_ctrl_pg.K_s: 's',
            mock_ctrl_pg.K_SPACE: 'space'
        }.get(k, 'unknown')

        # Mock transform
        mock_view_pg.transform.smoothscale.side_effect = lambda _surf, _size: _surf

        # Mock Rect
        mock_view_pg.Rect = Mock(side_effect=lambda *_args: Mock(
            width=_args[2] if len(_args) > 2 else 0,
            height=_args[3] if len(_args) > 3 else 0,
            center=Mock()))

        # Mock time
        mock_ctrl_pg.time.Clock.return_value = Mock()
        mock_ctrl_pg.time.get_ticks.return_value = 0

        # Mock events
        mock_ctrl_pg.event.get.return_value = []

        # Event types
        mock_ctrl_pg.QUIT = 256
        mock_ctrl_pg.KEYDOWN = 768
        mock_ctrl_pg.MOUSEBUTTONDOWN = 1025

        # Keys
        mock_ctrl_pg.K_p = 112
        mock_ctrl_pg.K_e = 101
        mock_ctrl_pg.K_a = 97
        mock_ctrl_pg.K_d = 100
        mock_ctrl_pg.K_w = 119
        mock_ctrl_pg.K_s = 115
        mock_ctrl_pg.K_SPACE = 32
        mock_ctrl_pg.KMOD_CTRL = 64

        yield mock_view_pg, mock_ctrl_pg, mock_screen


@pytest.fixture
def mock_os_path():
    """Mock os.path.join for asset loading."""
    with patch('game.screens.gameplay.view.os.path.join') as mock_join:
        mock_join.side_effect = lambda *args: '/'.join(args)
        yield mock_join


@pytest.fixture
def mock_os_path_dirname():
    """Mock os.path.dirname."""
    with patch('game.screens.gameplay.view.os.path.dirname') as mock_dirname:
        mock_dirname.return_value = '/mock/game_screens'
        yield mock_dirname


@pytest.fixture
def mock_animation_utils():
    """Mock animation_utils module."""
    with patch('game.screens.gameplay.view.animation_utils') as mock_utils:
        yield mock_utils


@pytest.fixture
def event_bus():
    """Create a real EventBus for testing."""
    from game.core.event_bus import EventBus
    return EventBus()


@pytest.fixture
def model(event_bus):
    """Create a GameModel with a real EventBus."""
    return GameModel(event_bus)


@pytest.fixture
def mock_keybinds():
    """Create a mock KeybindManager."""
    kb = Mock(spec=KeybindManager)
    kb.button_keys = {
        'left':  97,   # pygame.K_a
        'right': 100,  # pygame.K_d
        'up':    119,  # pygame.K_w
        'down':  115,  # pygame.K_s
        'space': 32,   # pygame.K_SPACE
    }
    kb.key_labels = {
        'left': 'A', 'right': 'D', 'up': 'W', 'down': 'S', 'space': 'SPACE',
    }
    kb.inverted = False
    return kb


@pytest.fixture
def game_screen(mock_pygame, mock_os_path, mock_os_path_dirname, mock_animation_utils, mock_keybinds):
    """Create a GameScreen instance with mocked dependencies."""
    _, mock_ctrl_pg, mock_screen = mock_pygame
    return GameScreen(mock_screen, mock_keybinds)


# ======================================================================
# Model tests
# ======================================================================

class TestGameModelReset:
    """Tests for GameModel.reset."""

    def test_reset_clears_sequence(self, model):
        model.sequence = ['left', 'right', 'up']
        model.reset()
        assert model.sequence == []

    def test_reset_zeros_player_index(self, model):
        model.player_index = 5
        model.reset()
        assert model.player_index == 0

    def test_reset_zeros_score(self, model):
        model.score = 100
        model.reset()
        assert model.score == 0

    def test_reset_clears_flash_state(self, model):
        model.flash_button = 'left'
        model.flash_state = 'pressed'
        model.reset()
        assert model.flash_button is None
        assert model.flash_state == 'normal'

    def test_reset_sets_state_to_adding(self, model):
        model.state = 'input'
        model.reset()
        assert model.state == 'adding'


class TestGameModelHandleInput:
    """Tests for GameModel.handle_input."""

    def test_correct_input_sets_flash(self, model):
        model.sequence = ['left', 'right']
        model.player_index = 0
        model.state = 'input'

        model.handle_input('left', 1000)

        assert model.flash_button == 'left'
        assert model.flash_state == 'pressed'
        assert model.flash_end == 1400

    def test_correct_input_advances_index(self, model):
        model.sequence = ['left', 'right']
        model.player_index = 0

        model.handle_input('left', 1000)

        assert model.player_index == 1

    def test_correct_input_returns_correct(self, model):
        model.sequence = ['left', 'right']
        model.player_index = 0

        result = model.handle_input('left', 1000)

        assert result == 'correct'

    def test_wrong_input_triggers_gameover(self, model):
        model.sequence = ['left', 'right']
        model.player_index = 0
        model.state = 'input'

        model.handle_input('right', 1500)

        assert model.state == 'gameover'

    def test_wrong_input_returns_wrong(self, model):
        model.sequence = ['left']
        model.player_index = 0

        result = model.handle_input('right', 1000)

        assert result == 'wrong'

    def test_complete_sequence_advances_round(self, model):
        model.sequence = ['left', 'right']
        model.player_index = 1
        model.state = 'input'
        model.score = 5

        model.handle_input('right', 1000)

        assert model.state == 'adding'
        assert model.score == 6

    def test_complete_sequence_returns_round_complete(self, model):
        model.sequence = ['left']
        model.player_index = 0

        result = model.handle_input('left', 1000)

        assert result == 'round_complete'

    def test_complete_sets_next_time(self, model):
        model.sequence = ['left']
        model.player_index = 0

        model.handle_input('left', 2000)

        assert model._next_time == 3000


class TestGameModelUpdate:
    """Tests for GameModel.update."""

    def test_adding_state_adds_to_sequence(self, model):
        model.state = 'adding'
        model._next_time = 1000
        model.sequence = []

        with patch('game.core.game_model.random.choice', return_value='left'):
            model.update(1000)

        assert 'left' in model.sequence

    def test_adding_state_transitions_to_showing(self, model):
        model.state = 'adding'
        model._next_time = 1000

        with patch('game.core.game_model.random.choice', return_value='up'):
            model.update(1000)

        assert model.state == 'showing'

    def test_adding_before_time_does_nothing(self, model):
        model.state = 'adding'
        model._next_time = 2000
        model.sequence = []

        model.update(1000)

        assert len(model.sequence) == 0
        assert model.state == 'adding'

    def test_showing_lights_button(self, model):
        model.state = 'showing'
        model.sequence = ['left', 'right']
        model._show_index = 0
        model._showing_lit = False
        model._next_time = 1000

        model.update(1000)

        assert model.flash_button == 'left'
        assert model.flash_state == 'indicated'
        assert model._showing_lit is True

    def test_showing_advances_after_lit_period(self, model):
        model.state = 'showing'
        model.sequence = ['left', 'right']
        model._show_index = 0
        model._showing_lit = True
        model.flash_end = 1000

        model.update(1000)

        assert model._show_index == 1
        assert model._showing_lit is False

    def test_showing_complete_transitions_to_input(self, model):
        model.state = 'showing'
        model.sequence = ['left', 'right']
        model._show_index = 2

        model.update(1000)

        assert model.state == 'input'

    def test_showing_complete_returns_true(self, model):
        """update() returns True when entering input state (signals timer start)."""
        model.state = 'showing'
        model.sequence = ['left']
        model._show_index = 1

        result = model.update(2000)

        assert result is True

    def test_input_expires_flash(self, model):
        model.state = 'input'
        model.flash_button = 'left'
        model.flash_state = 'pressed'
        model.flash_end = 1000

        model.update(1001)

        assert model.flash_button is None
        assert model.flash_state == 'normal'


class TestGameModelOnTimerExpired:
    """Tests for GameModel.on_timer_expired."""

    def test_sets_gameover(self, model):
        model.state = 'input'
        model.on_timer_expired({'now': 5000})
        assert model.state == 'gameover'

    def test_sets_reason(self, model):
        model.state = 'input'
        model.on_timer_expired({'now': 5000})
        assert model.gameover_reason == "Time's up!"

    def test_sets_flash_end(self, model):
        model.state = 'input'
        model.on_timer_expired({'now': 7500})
        assert model.flash_end == 7500

    def test_only_in_input_state(self, model):
        model.state = 'showing'
        model.on_timer_expired({'now': 5000})
        assert model.state == 'showing'


# ======================================================================
# View tests
# ======================================================================

class TestGameViewDraw:
    """Tests for GameView.draw."""

    def test_draw_fills_screen(self, game_screen):
        view = game_screen.view
        model = game_screen.model
        view.draw(model, 1.0)
        view.screen.fill.assert_called_once_with((15, 15, 25))

    def test_draw_renders_score(self, game_screen):
        view = game_screen.view
        model = game_screen.model
        model.score = 42
        view.draw(model, 1.0)

        calls = [str(c) for c in view.font_small.render.call_args_list]
        assert any('Score: 42' in c for c in calls)

    def test_draw_renders_round_number(self, game_screen):
        view = game_screen.view
        model = game_screen.model
        model.sequence = ['left', 'right', 'up']
        view.draw(model, 1.0)

        calls = [str(c) for c in view.font_small.render.call_args_list]
        assert any('Round 3' in c for c in calls)

    def test_draw_showing_state_status(self, game_screen):
        view = game_screen.view
        model = game_screen.model
        model.state = 'showing'
        view.draw(model, 1.0)

        calls = [str(c) for c in view.font_small.render.call_args_list]
        assert any('Watch carefully' in c for c in calls)

    def test_draw_input_state_status(self, game_screen):
        view = game_screen.view
        model = game_screen.model
        model.state = 'input'
        model.sequence = ['left', 'right']
        model.player_index = 0
        view.draw(model, 1.0)

        calls = [str(c) for c in view.font_small.render.call_args_list]
        assert any('Your turn' in c for c in calls)

    def test_draw_blits_buttons(self, game_screen):
        view = game_screen.view
        model = game_screen.model
        view.draw(model, 1.0)
        assert view.screen.blit.call_count >= 5


# ======================================================================
# Facade / integration tests
# ======================================================================

class TestGameScreenInit:
    """Tests for GameScreen facade initialization."""

    def test_init_creates_event_bus(self, game_screen):
        assert game_screen._bus is not None

    def test_init_creates_model(self, game_screen):
        assert game_screen.model is not None

    def test_init_creates_view(self, game_screen):
        assert game_screen.view is not None

    def test_init_creates_controller(self, game_screen):
        assert game_screen.controller is not None

    def test_init_model_starts_in_adding(self, game_screen):
        assert game_screen.model.state == 'adding'
        assert game_screen.model.sequence == []
        assert game_screen.model.player_index == 0

    def test_init_with_pause_overlay_subscribes(self, mock_pygame, mock_os_path,
                                                mock_os_path_dirname, mock_animation_utils,
                                                mock_keybinds):
        _, mock_ctrl_pg, mock_screen = mock_pygame
        mock_overlay = Mock()
        gs = GameScreen(mock_screen, mock_keybinds, pause_overlay=mock_overlay)
        mock_overlay.subscribe.assert_called_once_with(gs._bus)


class TestGameScreenIntegration:
    """Integration tests exercising model logic through a full cycle."""

    def test_full_game_cycle_single_round(self, model):
        assert model.state == 'adding'

        with patch('game.core.game_model.random.choice', return_value='left'):
            model.update(10000)

        assert model.state == 'showing'
        assert len(model.sequence) == 1

        model._show_index = 1
        model.update(20000)

        assert model.state == 'input'

        model.handle_input('left', 21000)

        assert model.state == 'adding'
        assert model.score == 1

    def test_wrong_input_triggers_gameover(self, model):
        model.sequence = ['left', 'right']
        model.player_index = 0
        model.state = 'input'

        model.handle_input('up', 1000)

        assert model.state == 'gameover'

    def test_sequence_grows_each_round(self, model):
        initial_length = len(model.sequence)

        with patch('game.core.game_model.random.choice', return_value='up'):
            model.state = 'adding'
            model._next_time = 0
            model.update(1000)

        assert len(model.sequence) == initial_length + 1

    def test_score_increments_on_completion(self, model):
        model.sequence = ['left']
        model.player_index = 0
        model.score = 5
        model.state = 'input'

        model.handle_input('left', 1000)

        assert model.score == 6

    def test_timer_expiration_during_input(self, model):
        model.state = 'input'
        model.on_timer_expired({'now': 5000})

        assert model.state == 'gameover'
        assert model.gameover_reason == "Time's up!"


class TestGameScreenEdgeCases:
    """Edge case tests."""

    def test_empty_sequence_handling(self, model):
        model.sequence = []
        model.state = 'showing'
        model._show_index = 0

        model.update(1000)

        assert model.state == 'input'

    def test_rapid_input_handling(self, model):
        model.sequence = ['left', 'right', 'up']
        model.player_index = 0
        model.state = 'input'

        model.handle_input('left', 1000)
        model.handle_input('right', 1100)
        model.handle_input('up', 1200)

        assert model.state == 'adding'
        assert model.score == 1

    def test_flash_state_persistence(self, model):
        model.state = 'input'
        model.flash_button = 'space'
        model.flash_state = 'pressed'
        model.flash_end = 2000

        model.update(1500)
        assert model.flash_button == 'space'

        model.update(2001)
        assert model.flash_button is None

    def test_state_machine_transitions(self, model):
        # adding -> showing
        model.state = 'adding'
        model._next_time = 0
        with patch('game.core.game_model.random.choice', return_value='left'):
            model.update(1000)
        assert model.state == 'showing'

        # showing -> input
        model._show_index = len(model.sequence)
        model.update(2000)
        assert model.state == 'input'

        # input -> adding (on success)
        model.sequence = ['left']
        model.player_index = 0
        model.handle_input('left', 3000)
        assert model.state == 'adding'

    def test_player_index_boundary(self, model):
        model.sequence = ['left', 'right']
        model.player_index = 1
        model.state = 'input'

        model.handle_input('right', 1000)

        assert model.state == 'adding'

    def test_button_names_constant(self):
        assert 'left' in BUTTON_NAMES
        assert 'right' in BUTTON_NAMES
        assert 'up' in BUTTON_NAMES
        assert 'down' in BUTTON_NAMES
        assert 'space' in BUTTON_NAMES
