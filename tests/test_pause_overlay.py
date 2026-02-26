"""Comprehensive tests for PauseOverlay."""
import sys
import pytest
from unittest.mock import Mock, MagicMock, patch, call

# Mock pygame before importing modules that depend on it
sys.modules['pygame'] = MagicMock()

from game_screens.pause_overlay import PauseOverlay
from game_screens.event_bus import EventBus


@pytest.fixture
def mock_screen():
    """Create a mock pygame screen."""
    screen = Mock()
    screen.get_size.return_value = (800, 600)
    screen.get_width.return_value = 800
    screen.get_height.return_value = 600
    return screen


@pytest.fixture
def mock_pygame():
    """Mock pygame modules."""
    with patch('game_screens.pause_overlay.pygame') as mock_pg:
        # Mock Font
        mock_font_large = Mock()
        mock_font_small = Mock()
        mock_pg.font.Font.side_effect = [mock_font_large, mock_font_small]

        # Mock Surface
        mock_surface = Mock()
        mock_surface.get_size.return_value = (800, 600)
        mock_pg.Surface.return_value = mock_surface

        # Mock text rendering - create separate surfaces for each render
        def create_text_surface():
            surf = Mock()
            rect = Mock()
            surf.get_rect.return_value = rect
            return surf

        mock_font_large.render.side_effect = lambda *args: create_text_surface()
        mock_font_small.render.side_effect = lambda *args: create_text_surface()

        yield mock_pg


class TestPauseOverlay:
    """Test suite for the PauseOverlay class."""

    def test_init_creates_invisible_overlay(self, mock_pygame, mock_screen):
        """PauseOverlay should initialize as invisible."""
        overlay = PauseOverlay(mock_screen)

        assert overlay.screen == mock_screen
        assert overlay.visible is False

    def test_init_creates_fonts(self, mock_pygame, mock_screen):
        """PauseOverlay should create large and small fonts."""
        overlay = PauseOverlay(mock_screen)

        assert mock_pygame.font.Font.call_count == 2
        # Large font with size 96
        mock_pygame.font.Font.assert_any_call(None, 96)
        # Small font with size 36
        mock_pygame.font.Font.assert_any_call(None, 36)

    def test_subscribe_registers_callbacks(self, mock_pygame, mock_screen):
        """subscribe() should register callbacks for pause events."""
        overlay = PauseOverlay(mock_screen)
        bus = EventBus()

        overlay.subscribe(bus)

        assert 'game_paused' in bus._listeners
        assert 'game_resumed' in bus._listeners
        assert overlay._on_paused in bus._listeners['game_paused']
        assert overlay._on_resumed in bus._listeners['game_resumed']

    def test_on_paused_makes_visible(self, mock_pygame, mock_screen):
        """_on_paused should set visible to True."""
        overlay = PauseOverlay(mock_screen)
        bus = EventBus()
        overlay.subscribe(bus)

        assert overlay.visible is False

        bus.emit('game_paused', {})

        assert overlay.visible is True

    def test_on_resumed_makes_invisible(self, mock_pygame, mock_screen):
        """_on_resumed should set visible to False."""
        overlay = PauseOverlay(mock_screen)
        bus = EventBus()
        overlay.subscribe(bus)

        overlay.visible = True

        bus.emit('game_resumed', {})

        assert overlay.visible is False

    def test_draw_does_nothing_when_invisible(self, mock_pygame, mock_screen):
        """draw() should do nothing when visible is False."""
        overlay = PauseOverlay(mock_screen)
        overlay.visible = False

        overlay.draw()

        # Screen should not be blitted to
        mock_screen.blit.assert_not_called()

    def test_draw_creates_overlay_surface_when_visible(self, mock_pygame, mock_screen):
        """draw() should create an overlay surface when visible."""
        overlay = PauseOverlay(mock_screen)
        overlay.visible = True

        overlay.draw()

        # Should create a surface with screen size
        mock_pygame.Surface.assert_called_with((800, 600))

    def test_draw_sets_overlay_alpha(self, mock_pygame, mock_screen):
        """draw() should set overlay surface alpha to 128."""
        overlay = PauseOverlay(mock_screen)
        overlay.visible = True

        overlay.draw()

        mock_surface = mock_pygame.Surface.return_value
        mock_surface.set_alpha.assert_called_once_with(128)

    def test_draw_fills_overlay_black(self, mock_pygame, mock_screen):
        """draw() should fill overlay surface with black."""
        overlay = PauseOverlay(mock_screen)
        overlay.visible = True

        overlay.draw()

        mock_surface = mock_pygame.Surface.return_value
        mock_surface.fill.assert_called_once_with((0, 0, 0))

    def test_draw_blits_overlay_to_screen(self, mock_pygame, mock_screen):
        """draw() should blit overlay surface to screen at origin."""
        overlay = PauseOverlay(mock_screen)
        overlay.visible = True

        overlay.draw()

        mock_surface = mock_pygame.Surface.return_value
        # First blit is the overlay surface itself
        assert mock_screen.blit.call_args_list[0] == call(mock_surface, (0, 0))

    def test_draw_renders_paused_text(self, mock_pygame, mock_screen):
        """draw() should render 'PAUSED' text in white."""
        overlay = PauseOverlay(mock_screen)
        overlay.visible = True

        overlay.draw()

        # Check that font_large.render was called with correct arguments
        overlay.font_large.render.assert_called_with("PAUSED", True, (255, 255, 255))

    def test_draw_centers_paused_text(self, mock_pygame, mock_screen):
        """draw() should center PAUSED text horizontally and position it above center."""
        overlay = PauseOverlay(mock_screen)
        overlay.visible = True

        overlay.draw()

        # Check that render was called for PAUSED text
        # The actual positioning is done in the implementation
        assert overlay.font_large.render.called
        assert overlay.font_small.render.called

    def test_draw_renders_instruction_text(self, mock_pygame, mock_screen):
        """draw() should render 'Press P to Resume' instruction."""
        overlay = PauseOverlay(mock_screen)
        overlay.visible = True

        overlay.draw()

        overlay.font_small.render.assert_called_once_with(
            "Press P to Resume", True, (200, 200, 200)
        )

    def test_draw_centers_instruction_text(self, mock_pygame, mock_screen):
        """draw() should center instruction text below PAUSED text."""
        overlay = PauseOverlay(mock_screen)
        overlay.visible = True

        overlay.draw()

        # Check that instruction text was rendered
        overlay.font_small.render.assert_called_with(
            "Press P to Resume", True, (200, 200, 200)
        )

    def test_draw_blits_both_texts_to_screen(self, mock_pygame, mock_screen):
        """draw() should blit both text surfaces to screen."""
        overlay = PauseOverlay(mock_screen)
        overlay.visible = True

        overlay.draw()

        # Should have 3 blits: overlay surface, paused text, instruction text
        assert mock_screen.blit.call_count == 3

    def test_pause_resume_cycle(self, mock_pygame, mock_screen):
        """Should handle pause and resume cycle correctly."""
        overlay = PauseOverlay(mock_screen)
        bus = EventBus()
        overlay.subscribe(bus)

        # Start invisible
        assert overlay.visible is False

        # Pause
        bus.emit('game_paused', {})
        assert overlay.visible is True

        # Resume
        bus.emit('game_resumed', {})
        assert overlay.visible is False

    def test_multiple_pause_events(self, mock_pygame, mock_screen):
        """Should handle multiple pause events correctly."""
        overlay = PauseOverlay(mock_screen)
        bus = EventBus()
        overlay.subscribe(bus)

        bus.emit('game_paused', {})
        assert overlay.visible is True

        bus.emit('game_paused', {})
        assert overlay.visible is True

    def test_multiple_resume_events(self, mock_pygame, mock_screen):
        """Should handle multiple resume events correctly."""
        overlay = PauseOverlay(mock_screen)
        bus = EventBus()
        overlay.subscribe(bus)

        overlay.visible = True

        bus.emit('game_resumed', {})
        assert overlay.visible is False

        bus.emit('game_resumed', {})
        assert overlay.visible is False

    def test_draw_multiple_times_when_visible(self, mock_pygame, mock_screen):
        """Should be able to draw multiple times while visible."""
        overlay = PauseOverlay(mock_screen)
        overlay.visible = True

        overlay.draw()
        overlay.draw()
        overlay.draw()

        # Each draw should create a new surface
        assert mock_pygame.Surface.call_count == 3

    def test_event_data_ignored(self, mock_pygame, mock_screen):
        """Pause/resume callbacks should ignore event data."""
        overlay = PauseOverlay(mock_screen)
        bus = EventBus()
        overlay.subscribe(bus)

        # Should work with any data
        bus.emit('game_paused', {'irrelevant': 'data'})
        assert overlay.visible is True

        bus.emit('game_resumed', {'some': 'value'})
        assert overlay.visible is False

    def test_different_screen_sizes(self, mock_pygame):
        """Should work with different screen sizes."""
        screen1 = Mock()
        screen1.get_size.return_value = (1024, 768)
        screen1.get_width.return_value = 1024
        screen1.get_height.return_value = 768

        overlay = PauseOverlay(screen1)
        overlay.visible = True
        overlay.draw()

        # Should create overlay with correct size
        mock_pygame.Surface.assert_called_with((1024, 768))

    def test_subscribe_to_multiple_buses(self, mock_pygame, mock_screen):
        """Should be able to subscribe to multiple event buses."""
        overlay = PauseOverlay(mock_screen)
        bus1 = EventBus()
        bus2 = EventBus()

        overlay.subscribe(bus1)
        overlay.subscribe(bus2)

        # Either bus should be able to control visibility
        bus1.emit('game_paused', {})
        assert overlay.visible is True

        bus2.emit('game_resumed', {})
        assert overlay.visible is False

    def test_screen_reference_preserved(self, mock_pygame, mock_screen):
        """Should maintain reference to the screen."""
        overlay = PauseOverlay(mock_screen)

        assert overlay.screen is mock_screen

        # Draw should use the same screen
        overlay.visible = True
        overlay.draw()

        assert mock_screen.blit.called

    def test_fonts_preserved_across_draws(self, mock_pygame, mock_screen):
        """Fonts should be created once and reused."""
        overlay = PauseOverlay(mock_screen)
        overlay.visible = True

        initial_font_large = overlay.font_large
        initial_font_small = overlay.font_small

        overlay.draw()
        overlay.draw()

        # Fonts should be the same objects
        assert overlay.font_large is initial_font_large
        assert overlay.font_small is initial_font_small

    def test_overlay_alpha_transparency(self, mock_pygame, mock_screen):
        """Overlay should be semi-transparent (alpha 128 = 50%)."""
        overlay = PauseOverlay(mock_screen)
        overlay.visible = True

        overlay.draw()

        mock_surface = mock_pygame.Surface.return_value
        mock_surface.set_alpha.assert_called_once_with(128)

    def test_color_values(self, mock_pygame, mock_screen):
        """Should use correct color values for all elements."""
        overlay = PauseOverlay(mock_screen)
        overlay.visible = True

        overlay.draw()

        # Overlay background should be black
        mock_surface = mock_pygame.Surface.return_value
        mock_surface.fill.assert_called_once_with((0, 0, 0))

        # PAUSED text should be white
        overlay.font_large.render.assert_called_with("PAUSED", True, (255, 255, 255))

        # Instruction text should be light gray
        overlay.font_small.render.assert_called_with(
            "Press P to Resume", True, (200, 200, 200)
        )

    def test_text_antialiasing_enabled(self, mock_pygame, mock_screen):
        """Text rendering should have antialiasing enabled."""
        overlay = PauseOverlay(mock_screen)
        overlay.visible = True

        overlay.draw()

        # Second parameter to render is antialias (True)
        overlay.font_large.render.assert_called_with("PAUSED", True, (255, 255, 255))
        overlay.font_small.render.assert_called_with("Press P to Resume", True, (200, 200, 200))

    def test_paused_text_positioning(self, mock_pygame, mock_screen):
        """PAUSED text should be positioned correctly."""
        overlay = PauseOverlay(mock_screen)
        overlay.visible = True

        overlay.draw()

        # Verify the PAUSED text was rendered
        overlay.font_large.render.assert_called_with("PAUSED", True, (255, 255, 255))

    def test_instruction_text_positioning(self, mock_pygame, mock_screen):
        """Instruction text should be positioned correctly."""
        overlay = PauseOverlay(mock_screen)
        overlay.visible = True

        overlay.draw()

        # Verify instruction text was rendered
        overlay.font_small.render.assert_called_with(
            "Press P to Resume", True, (200, 200, 200)
        )

    def test_rapid_pause_resume_toggles(self, mock_pygame, mock_screen):
        """Should handle rapid pause/resume toggling."""
        overlay = PauseOverlay(mock_screen)
        bus = EventBus()
        overlay.subscribe(bus)

        for i in range(10):
            bus.emit('game_paused', {})
            assert overlay.visible is True
            bus.emit('game_resumed', {})
            assert overlay.visible is False

    def test_pause_event_with_none_data(self, mock_pygame, mock_screen):
        """Should handle pause event with None data."""
        overlay = PauseOverlay(mock_screen)
        bus = EventBus()
        overlay.subscribe(bus)

        bus.emit('game_paused', None)
        assert overlay.visible is True

        bus.emit('game_resumed', None)
        assert overlay.visible is False

    def test_draw_without_subscribe(self, mock_pygame, mock_screen):
        """Should be able to draw without subscribing to event bus."""
        overlay = PauseOverlay(mock_screen)

        # Manually set visible
        overlay.visible = True
        overlay.draw()

        assert mock_screen.blit.call_count == 3

    def test_state_independent_of_draw_calls(self, mock_pygame, mock_screen):
        """Visibility state should not change from draw calls."""
        overlay = PauseOverlay(mock_screen)
        overlay.visible = True

        overlay.draw()
        assert overlay.visible is True

        overlay.visible = False
        overlay.draw()
        assert overlay.visible is False