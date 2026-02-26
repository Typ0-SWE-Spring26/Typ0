"""Comprehensive tests for GameScreen display module."""
import sys
import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, call, AsyncMock

# Mock pygame and other dependencies before importing
sys.modules['pygame'] = MagicMock()

from game_screens.display import GameScreen


@pytest.fixture
def mock_pygame():
    """Mock pygame modules and functions."""
    with patch('game_screens.display.pygame') as mock_pg:
        # Mock screen
        mock_screen = Mock()
        mock_screen.get_width.return_value = 800
        mock_screen.get_height.return_value = 600

        # Mock image loading
        mock_image = Mock()
        mock_image.convert_alpha.return_value = Mock()
        mock_pg.image.load.return_value = mock_image

        # Mock font
        mock_font = Mock()
        mock_font.render.return_value = Mock()
        mock_pg.font.SysFont.return_value = mock_font

        # Mock key names
        mock_pg.key.name.side_effect = lambda k: {
            mock_pg.K_a: 'a',
            mock_pg.K_d: 'd',
            mock_pg.K_w: 'w',
            mock_pg.K_s: 's',
            mock_pg.K_SPACE: 'space'
        }.get(k, 'unknown')

        # Mock transform
        mock_pg.transform.smoothscale.side_effect = lambda surf, size: surf

        # Mock Rect
        mock_pg.Rect = Mock(side_effect=lambda *args: Mock(width=args[2] if len(args) > 2 else 0,
                                                           height=args[3] if len(args) > 3 else 0,
                                                           center=Mock()))

        # Mock time
        mock_pg.time.Clock.return_value = Mock()
        mock_pg.time.get_ticks.return_value = 0

        # Mock events
        mock_pg.event.get.return_value = []

        # Event types
        mock_pg.QUIT = 256
        mock_pg.KEYDOWN = 768
        mock_pg.MOUSEBUTTONDOWN = 1025

        # Keys
        mock_pg.K_p = 112
        mock_pg.K_e = 101
        mock_pg.K_a = 97
        mock_pg.K_d = 100
        mock_pg.K_w = 119
        mock_pg.K_s = 115
        mock_pg.K_SPACE = 32
        mock_pg.KMOD_CTRL = 64

        yield mock_pg, mock_screen


@pytest.fixture
def mock_os_path():
    """Mock os.path.join for asset loading."""
    with patch('game_screens.display.os.path.join') as mock_join:
        mock_join.side_effect = lambda *args: '/'.join(args)
        yield mock_join


@pytest.fixture
def mock_os_path_dirname():
    """Mock os.path.dirname."""
    with patch('game_screens.display.os.path.dirname') as mock_dirname:
        mock_dirname.return_value = '/mock/game_screens'
        yield mock_dirname


@pytest.fixture
def mock_animation_utils():
    """Mock animation_utils module."""
    with patch('game_screens.display.animation_utils') as mock_utils:
        yield mock_utils


@pytest.fixture
def game_screen(mock_pygame, mock_os_path, mock_os_path_dirname, mock_animation_utils):
    """Create a GameScreen instance with mocked dependencies."""
    mock_pg, mock_screen = mock_pygame
    return GameScreen(mock_screen)


class TestGameScreenInit:
    """Tests for GameScreen initialization."""

    def test_init_stores_screen_reference(self, game_screen, mock_pygame):
        """Should store reference to the screen."""
        _, mock_screen = mock_pygame
        assert game_screen.screen == mock_screen

    def test_init_starts_unpaused(self, game_screen):
        """Should initialize with paused=False."""
        assert game_screen.paused is False

    def test_init_sets_default_score(self, game_screen):
        """Should initialize with score=0 by default."""
        assert game_screen.score == 0

    def test_init_accepts_custom_score(self, mock_pygame, mock_os_path,
                                       mock_os_path_dirname, mock_animation_utils):
        """Should accept and set custom initial score."""
        _, mock_screen = mock_pygame
        gs = GameScreen(mock_screen, score=42)
        assert gs.score == 42

    def test_init_creates_event_bus(self, game_screen):
        """Should create an EventBus instance."""
        assert game_screen._bus is not None

    def test_init_creates_game_timer(self, game_screen):
        """Should create a GameTimer instance."""
        assert game_screen.game_timer is not None

    def test_init_subscribes_to_timer_expired(self, game_screen):
        """Should subscribe to timer_expired event."""
        assert 'timer_expired' in game_screen._bus._listeners
        assert game_screen._on_timer_expired in game_screen._bus._listeners['timer_expired']

    def test_init_loads_button_sprites(self, game_screen):
        """Should load sprites for all buttons."""
        assert 'left' in game_screen.sprites
        assert 'right' in game_screen.sprites
        assert 'up' in game_screen.sprites
        assert 'down' in game_screen.sprites
        assert 'space' in game_screen.sprites

    def test_init_loads_three_states_per_button(self, game_screen):
        """Each button should have normal, indicated, and pressed states."""
        for button_name in ['left', 'right', 'up', 'down', 'space']:
            assert 'normal' in game_screen.sprites[button_name]
            assert 'indicated' in game_screen.sprites[button_name]
            assert 'pressed' in game_screen.sprites[button_name]

    def test_init_creates_button_rects(self, game_screen):
        """Should create rects for all buttons."""
        assert 'left' in game_screen.button_rects
        assert 'right' in game_screen.button_rects
        assert 'up' in game_screen.button_rects
        assert 'down' in game_screen.button_rects
        assert 'space' in game_screen.button_rects

    def test_init_creates_scaled_sprites(self, game_screen):
        """Should create scaled versions of sprites."""
        assert 'left' in game_screen.scaled
        assert len(game_screen.scaled['left']) == 3  # normal, indicated, pressed

    def test_init_with_pause_overlay_subscribes(self, mock_pygame, mock_os_path,
                                                mock_os_path_dirname, mock_animation_utils):
        """Should subscribe pause overlay to event bus if provided."""
        _, mock_screen = mock_pygame
        mock_overlay = Mock()
        gs = GameScreen(mock_screen, pause_overlay=mock_overlay)

        mock_overlay.subscribe.assert_called_once_with(gs._bus)

    def test_init_calls_reset(self, game_screen):
        """Should initialize game state via _reset."""
        assert game_screen.sequence == []
        assert game_screen.player_index == 0
        assert game_screen.state == 'adding'

    def test_button_keys_defined(self):
        """Should have all button key mappings defined."""
        assert 'left' in GameScreen.BUTTON_KEYS
        assert 'right' in GameScreen.BUTTON_KEYS
        assert 'up' in GameScreen.BUTTON_KEYS
        assert 'down' in GameScreen.BUTTON_KEYS
        assert 'space' in GameScreen.BUTTON_KEYS
        assert len(GameScreen.BUTTON_KEYS) == 5


class TestGameScreenReset:
    """Tests for _reset method."""

    def test_reset_clears_sequence(self, game_screen):
        """_reset should clear the sequence."""
        game_screen.sequence = ['left', 'right', 'up']
        game_screen._reset()
        assert game_screen.sequence == []

    def test_reset_zeros_player_index(self, game_screen):
        """_reset should set player_index to 0."""
        game_screen.player_index = 5
        game_screen._reset()
        assert game_screen.player_index == 0

    def test_reset_zeros_score(self, game_screen):
        """_reset should set score to 0."""
        game_screen.score = 100
        game_screen._reset()
        assert game_screen.score == 0

    def test_reset_clears_flash_state(self, game_screen):
        """_reset should clear flash button and state."""
        game_screen.flash_button = 'left'
        game_screen.flash_state = 'pressed'
        game_screen._reset()
        assert game_screen.flash_button is None
        assert game_screen.flash_state == 'normal'

    def test_reset_sets_state_to_adding(self, game_screen):
        """_reset should set state to 'adding'."""
        game_screen.state = 'input'
        game_screen._reset()
        assert game_screen.state == 'adding'


class TestGameScreenHandleInput:
    """Tests for _handle_input method."""

    def test_handle_input_correct_sets_flash(self, game_screen):
        """Correct input should set flash button and state."""
        game_screen.sequence = ['left', 'right']
        game_screen.player_index = 0
        game_screen.state = 'input'

        game_screen._handle_input('left', 1000)

        assert game_screen.flash_button == 'left'
        assert game_screen.flash_state == 'pressed'
        assert game_screen.flash_end == 1400  # 1000 + 400

    def test_handle_input_correct_advances_index(self, game_screen):
        """Correct input should advance player_index."""
        game_screen.sequence = ['left', 'right']
        game_screen.player_index = 0

        game_screen._handle_input('left', 1000)

        assert game_screen.player_index == 1

    def test_handle_input_wrong_triggers_gameover(self, game_screen):
        """Wrong input should trigger game over."""
        game_screen.sequence = ['left', 'right']
        game_screen.player_index = 0
        game_screen.state = 'input'
        game_screen.game_timer.start(1000)

        game_screen._handle_input('right', 1500)  # Wrong!

        assert game_screen.state == 'gameover'

    def test_handle_input_wrong_stops_timer(self, game_screen):
        """Wrong input should stop the timer."""
        game_screen.sequence = ['left']
        game_screen.player_index = 0
        game_screen.state = 'input'
        game_screen.game_timer.start(1000)

        game_screen._handle_input('right', 1500)

        assert game_screen.game_timer._active is False

    def test_handle_input_complete_sequence_advances_round(self, game_screen):
        """Completing the sequence should advance to next round."""
        game_screen.sequence = ['left', 'right']
        game_screen.player_index = 1
        game_screen.state = 'input'
        game_screen.score = 5

        game_screen._handle_input('right', 1000)

        assert game_screen.state == 'adding'
        assert game_screen.score == 6

    def test_handle_input_complete_stops_timer(self, game_screen):
        """Completing sequence should stop timer."""
        game_screen.sequence = ['left']
        game_screen.player_index = 0
        game_screen.state = 'input'
        game_screen.game_timer.start(1000)

        game_screen._handle_input('left', 1500)

        assert game_screen.game_timer._active is False

    def test_handle_input_complete_sets_next_time(self, game_screen):
        """Completing sequence should set _next_time for pause."""
        game_screen.sequence = ['left']
        game_screen.player_index = 0

        game_screen._handle_input('left', 2000)

        assert game_screen._next_time == 3000  # 2000 + 1000


class TestGameScreenUpdate:
    """Tests for _update method."""

    def test_update_adding_state_adds_to_sequence(self, game_screen):
        """In 'adding' state, should add a button to sequence after delay."""
        game_screen.state = 'adding'
        game_screen._next_time = 1000
        game_screen.sequence = []

        with patch('game_screens.display.random.choice', return_value='left'):
            game_screen._update(1000)

        assert 'left' in game_screen.sequence

    def test_update_adding_state_transitions_to_showing(self, game_screen):
        """In 'adding' state, should transition to 'showing'."""
        game_screen.state = 'adding'
        game_screen._next_time = 1000

        with patch('game_screens.display.random.choice', return_value='up'):
            game_screen._update(1000)

        assert game_screen.state == 'showing'

    def test_update_adding_before_time_does_nothing(self, game_screen):
        """In 'adding' state before _next_time, should do nothing."""
        game_screen.state = 'adding'
        game_screen._next_time = 2000
        game_screen.sequence = []

        game_screen._update(1000)

        assert len(game_screen.sequence) == 0
        assert game_screen.state == 'adding'

    def test_update_showing_lights_button(self, game_screen):
        """In 'showing' state, should light up next button."""
        game_screen.state = 'showing'
        game_screen.sequence = ['left', 'right']
        game_screen._show_index = 0
        game_screen._showing_lit = False
        game_screen._next_time = 1000

        game_screen._update(1000)

        assert game_screen.flash_button == 'left'
        assert game_screen.flash_state == 'indicated'
        assert game_screen._showing_lit is True

    def test_update_showing_advances_after_lit_period(self, game_screen):
        """In 'showing' state, should advance to next button after lit period."""
        game_screen.state = 'showing'
        game_screen.sequence = ['left', 'right']
        game_screen._show_index = 0
        game_screen._showing_lit = True
        game_screen.flash_end = 1000

        game_screen._update(1000)

        assert game_screen._show_index == 1
        assert game_screen._showing_lit is False

    def test_update_showing_complete_transitions_to_input(self, game_screen):
        """In 'showing' state, after all shown, should transition to 'input'."""
        game_screen.state = 'showing'
        game_screen.sequence = ['left', 'right']
        game_screen._show_index = 2  # Past the end

        game_screen._update(1000)

        assert game_screen.state == 'input'

    def test_update_showing_complete_starts_timer(self, game_screen):
        """Transitioning to 'input' should start the timer."""
        game_screen.state = 'showing'
        game_screen.sequence = ['left']
        game_screen._show_index = 1

        game_screen._update(2000)

        assert game_screen.game_timer._active is True
        assert game_screen.game_timer._start_ticks == 2000

    def test_update_input_expires_flash(self, game_screen):
        """In 'input' state, should expire flash after timeout."""
        game_screen.state = 'input'
        game_screen.flash_button = 'left'
        game_screen.flash_state = 'pressed'
        game_screen.flash_end = 1000

        game_screen._update(1001)

        assert game_screen.flash_button is None
        assert game_screen.flash_state == 'normal'

    def test_update_input_calls_timer_update(self, game_screen):
        """In 'input' state, should update the timer."""
        game_screen.state = 'input'
        game_screen.game_timer.start(1000)

        game_screen._update(2000)

        # Timer should have updated and calculated remaining time
        assert game_screen.game_timer.fraction < 1.0


class TestGameScreenOnTimerExpired:
    """Tests for _on_timer_expired callback."""

    def test_on_timer_expired_sets_gameover(self, game_screen):
        """Timer expiration should set state to 'gameover'."""
        game_screen.state = 'input'

        game_screen._on_timer_expired({'now': 5000})

        assert game_screen.state == 'gameover'

    def test_on_timer_expired_sets_reason(self, game_screen):
        """Timer expiration should set gameover reason."""
        game_screen.state = 'input'

        game_screen._on_timer_expired({'now': 5000})

        assert game_screen._gameover_reason == "Time's up!"

    def test_on_timer_expired_sets_flash_end(self, game_screen):
        """Timer expiration should set flash_end to current time."""
        game_screen.state = 'input'

        game_screen._on_timer_expired({'now': 7500})

        assert game_screen.flash_end == 7500

    def test_on_timer_expired_only_in_input_state(self, game_screen):
        """Timer expiration should only affect game in 'input' state."""
        game_screen.state = 'showing'
        original_state = game_screen.state

        game_screen._on_timer_expired({'now': 5000})

        # State should not change if not in 'input'
        assert game_screen.state == original_state


class TestGameScreenDraw:
    """Tests for _draw method."""

    def test_draw_fills_screen(self, game_screen):
        """_draw should fill screen with dark color."""
        game_screen._draw()
        game_screen.screen.fill.assert_called_once_with((15, 15, 25))

    def test_draw_renders_score(self, game_screen):
        """_draw should render current score."""
        game_screen.score = 42
        game_screen._draw()

        # Check that font render was called with score text
        calls = [str(call) for call in game_screen.font_small.render.call_args_list]
        assert any('Score: 42' in str(call) for call in calls)

    def test_draw_renders_round_number(self, game_screen):
        """_draw should render current round number."""
        game_screen.sequence = ['left', 'right', 'up']
        game_screen._draw()

        calls = [str(call) for call in game_screen.font_small.render.call_args_list]
        assert any('Round 3' in str(call) for call in calls)

    def test_draw_showing_state_status(self, game_screen):
        """_draw should show 'Watch carefully...' in showing state."""
        game_screen.state = 'showing'
        game_screen._draw()

        calls = [str(call) for call in game_screen.font_small.render.call_args_list]
        assert any('Watch carefully' in str(call) for call in calls)

    def test_draw_input_state_status(self, game_screen):
        """_draw should show 'Your turn!' in input state."""
        game_screen.state = 'input'
        game_screen.sequence = ['left', 'right']
        game_screen.player_index = 0
        game_screen._draw()

        calls = [str(call) for call in game_screen.font_small.render.call_args_list]
        assert any('Your turn' in str(call) for call in calls)

    def test_draw_blits_buttons(self, game_screen):
        """_draw should blit all button sprites."""
        game_screen._draw()

        # Should blit at least once per button (5 buttons)
        assert game_screen.screen.blit.call_count >= 5

    def test_draw_timer_bar_in_input_state(self, game_screen, mock_pygame):
        """_draw should render timer bar during input state."""
        mock_pg, _ = mock_pygame
        game_screen.state = 'input'
        game_screen.game_timer.fraction = 0.5

        game_screen._draw()

        # Should draw a rect for the timer bar
        assert mock_pg.draw.rect.called


class TestGameScreenIntegration:
    """Integration tests for GameScreen."""

    def test_full_game_cycle_single_round(self, game_screen):
        """Should handle a complete game cycle through one round."""
        # Start in adding state
        assert game_screen.state == 'adding'

        # Advance time to add button
        with patch('game_screens.display.random.choice', return_value='left'):
            game_screen._update(10000)

        assert game_screen.state == 'showing'
        assert len(game_screen.sequence) == 1

        # Fast-forward through showing
        game_screen._show_index = 1
        game_screen._update(20000)

        assert game_screen.state == 'input'

        # Provide correct input
        game_screen._handle_input('left', 21000)

        assert game_screen.state == 'adding'
        assert game_screen.score == 1

    def test_wrong_input_triggers_gameover(self, game_screen):
        """Wrong input should transition to game over state."""
        game_screen.sequence = ['left', 'right']
        game_screen.player_index = 0
        game_screen.state = 'input'

        game_screen._handle_input('up', 1000)  # Wrong button

        assert game_screen.state == 'gameover'

    def test_pause_stops_timer(self, game_screen, mock_pygame):
        """Pausing should freeze the timer."""
        mock_pg, _ = mock_pygame
        game_screen.state = 'input'
        game_screen.game_timer.start(1000)
        game_screen.game_timer.update(2000)  # 1 second elapsed

        fraction_before_pause = game_screen.game_timer.fraction

        game_screen._bus.emit('game_paused', {'now': 2000})

        # Timer should be inactive
        assert game_screen.game_timer._active is False
        assert game_screen.game_timer._paused_remaining is not None

    def test_sequence_grows_each_round(self, game_screen):
        """Sequence should grow by one button each round."""
        initial_length = len(game_screen.sequence)

        with patch('game_screens.display.random.choice', return_value='up'):
            game_screen.state = 'adding'
            game_screen._next_time = 0
            game_screen._update(1000)

        assert len(game_screen.sequence) == initial_length + 1

    def test_score_increments_on_completion(self, game_screen):
        """Score should increment when player completes a sequence."""
        game_screen.sequence = ['left']
        game_screen.player_index = 0
        game_screen.score = 5
        game_screen.state = 'input'

        game_screen._handle_input('left', 1000)

        assert game_screen.score == 6


class TestGameScreenEdgeCases:
    """Edge case tests for GameScreen."""

    def test_empty_sequence_handling(self, game_screen):
        """Should handle empty sequence gracefully."""
        game_screen.sequence = []
        game_screen.state = 'showing'
        game_screen._show_index = 0

        game_screen._update(1000)

        # Should transition to input immediately
        assert game_screen.state == 'input'

    def test_rapid_input_handling(self, game_screen):
        """Should handle rapid consecutive inputs."""
        game_screen.sequence = ['left', 'right', 'up']
        game_screen.player_index = 0
        game_screen.state = 'input'

        game_screen._handle_input('left', 1000)
        game_screen._handle_input('right', 1100)
        game_screen._handle_input('up', 1200)

        assert game_screen.state == 'adding'
        assert game_screen.score == 1

    def test_flash_state_persistence(self, game_screen):
        """Flash state should persist until timeout."""
        game_screen.state = 'input'
        game_screen.flash_button = 'space'
        game_screen.flash_state = 'pressed'
        game_screen.flash_end = 2000

        game_screen._update(1500)
        assert game_screen.flash_button == 'space'

        game_screen._update(2001)
        assert game_screen.flash_button is None

    def test_timer_expiration_during_input(self, game_screen):
        """Timer expiring during input should trigger game over."""
        game_screen.state = 'input'
        game_screen._bus.emit('timer_expired', {'now': 5000})

        assert game_screen.state == 'gameover'
        assert game_screen._gameover_reason == "Time's up!"

    def test_multiple_pause_overlay_integration(self, mock_pygame, mock_os_path,
                                               mock_os_path_dirname, mock_animation_utils):
        """Should work with pause overlay subscribing to events."""
        _, mock_screen = mock_pygame
        mock_overlay = Mock()
        gs = GameScreen(mock_screen, pause_overlay=mock_overlay)

        # Emit pause event
        gs._bus.emit('game_paused', {'now': 1000})

        # Overlay should have been subscribed
        mock_overlay.subscribe.assert_called_once()

    def test_button_key_constants(self):
        """Button key constants should be properly defined."""
        assert 'left' in GameScreen.BUTTON_KEYS
        assert 'right' in GameScreen.BUTTON_KEYS
        assert 'up' in GameScreen.BUTTON_KEYS
        assert 'down' in GameScreen.BUTTON_KEYS
        assert 'space' in GameScreen.BUTTON_KEYS

    def test_button_files_constants(self):
        """Button file paths should be properly defined."""
        assert 'left' in GameScreen.BUTTON_FILES
        assert len(GameScreen.BUTTON_FILES['left']) == 3  # normal, indicated, pressed

    def test_state_machine_transitions(self, game_screen):
        """Should follow correct state machine transitions."""
        # adding -> showing
        game_screen.state = 'adding'
        game_screen._next_time = 0
        with patch('game_screens.display.random.choice', return_value='left'):
            game_screen._update(1000)
        assert game_screen.state == 'showing'

        # showing -> input
        game_screen._show_index = len(game_screen.sequence)
        game_screen._update(2000)
        assert game_screen.state == 'input'

        # input -> adding (on success)
        game_screen.sequence = ['left']
        game_screen.player_index = 0
        game_screen._handle_input('left', 3000)
        assert game_screen.state == 'adding'

    def test_player_index_boundary(self, game_screen):
        """Player index should not exceed sequence length."""
        game_screen.sequence = ['left', 'right']
        game_screen.player_index = 1
        game_screen.state = 'input'

        game_screen._handle_input('right', 1000)

        # After completing, state should change
        assert game_screen.state == 'adding'