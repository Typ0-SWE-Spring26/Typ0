"""Tests for Button utility class."""
import sys
from unittest.mock import Mock, MagicMock, patch

sys.modules["pygame"] = MagicMock()

from game.utils.button import Button


class _Rect:
    """Minimal Rect implementation for testing."""
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.width = w
        self.height = h
        self.left = x
        self.top = y
        self.right = x + w
        self.bottom = y + h
        self.centerx = x + w // 2
        self.centery = y + h // 2
        self.center = (self.centerx, self.centery)

    def collidepoint(self, pos):
        px, py = pos
        return self.left <= px <= self.right and self.top <= py <= self.bottom

    def move(self, dx, dy):
        return _Rect(self.x + dx, self.y + dy, self.width, self.height)


class TestButtonInit:
    """Test Button initialization."""

    def test_init_with_defaults(self):
        import game.utils.button as btn_mod

        mock_pg = MagicMock()
        # pygame.Rect can be called with either (x,y,w,h) or (rect_obj)
        mock_pg.Rect.side_effect = lambda *args, **kwargs: args[0] if len(args) == 1 and hasattr(args[0], 'x') else _Rect(*args)

        with patch.object(btn_mod, "pygame", mock_pg):
            rect = _Rect(10, 20, 100, 50)
            font = Mock()
            button = btn_mod.Button(rect, "Click Me", font)

            assert button.label == "Click Me"
            assert button.font is font
            assert button.color == btn_mod.Button.NORMAL_COLOR
            assert button.hover_color == btn_mod.Button.HOVER_COLOR
            assert button._pressing is False

    def test_init_with_custom_colors(self):
        import game.utils.button as btn_mod

        mock_pg = MagicMock()
        mock_pg.Rect.side_effect = lambda *args, **kwargs: args[0] if len(args) == 1 and hasattr(args[0], 'x') else _Rect(*args)

        with patch.object(btn_mod, "pygame", mock_pg):
            rect = _Rect(10, 20, 100, 50)
            font = Mock()
            custom_color = (100, 100, 100)
            hover_color = (150, 150, 150)
            
            button = btn_mod.Button(rect, "Test", font, color=custom_color, hover_color=hover_color)

            assert button.color == custom_color
            assert button.hover_color == hover_color


class TestButtonDraw:
    """Test Button rendering."""

    def test_draw_calls_pygame_functions(self):
        import game.utils.button as btn_mod

        mock_pg = MagicMock()
        mock_pg.Rect.side_effect = lambda *args, **kwargs: args[0] if len(args) == 1 and hasattr(args[0], 'x') else _Rect(*args)
        mock_pg.mouse.get_pos.return_value = (0, 0)
        mock_pg.draw.rect = Mock()
        mock_pg.MOUSEBUTTONDOWN = 1025

        with patch.object(btn_mod, "pygame", mock_pg):
            rect = _Rect(10, 20, 100, 50)
            font = Mock()
            font.render.return_value = Mock(get_rect=Mock(return_value=Mock()))

            button = btn_mod.Button(rect, "Click", font)
            surface = Mock()

            button.draw(surface)

            # Verify draw.rect was called multiple times (for shadow, button, border)
            assert mock_pg.draw.rect.call_count >= 2
            # Verify font.render was called
            font.render.assert_called()

    def test_draw_with_hover_applies_hover_color(self):
        import game.utils.button as btn_mod

        mock_pg = MagicMock()
        mock_pg.Rect.side_effect = lambda *args, **kwargs: args[0] if len(args) == 1 and hasattr(args[0], 'x') else _Rect(*args)
        mock_pg.draw.rect = Mock()

        with patch.object(btn_mod, "pygame", mock_pg):
            rect = _Rect(10, 20, 100, 50)
            font = Mock(render=Mock(return_value=Mock(get_rect=Mock(return_value=Mock()))))

            custom_hover = (200, 200, 200)
            button = btn_mod.Button(rect, "Click", font, hover_color=custom_hover)
            surface = Mock()

            # Hovered: mouse inside the button rect → second draw.rect uses hover_color
            mock_pg.mouse.get_pos.return_value = (60, 45)
            button.draw(surface)

            calls = mock_pg.draw.rect.call_args_list
            assert len(calls) >= 2
            # call(surface, color, rect, ...) — color is positional arg index 1
            assert calls[1].args[1] == custom_hover

            # Not hovered: mouse outside → second draw.rect uses normal color
            mock_pg.draw.rect.reset_mock()
            mock_pg.mouse.get_pos.return_value = (500, 500)
            button.draw(surface)

            calls = mock_pg.draw.rect.call_args_list
            assert len(calls) >= 2
            assert calls[1].args[1] == button.color


class TestButtonHandleEvent:
    """Test Button event handling."""

    def test_handle_event_click_inside_rect(self):
        import game.utils.button as btn_mod

        mock_pg = MagicMock()
        mock_pg.Rect.side_effect = lambda *args, **kwargs: args[0] if len(args) == 1 and hasattr(args[0], 'x') else _Rect(*args)
        mock_pg.MOUSEBUTTONDOWN = 1025
        mock_pg.MOUSEBUTTONUP = 1026

        with patch.object(btn_mod, "pygame", mock_pg):
            rect = _Rect(10, 20, 100, 50)
            font = Mock()
            button = btn_mod.Button(rect, "Click", font)

            # Simulate click down inside
            down_event = Mock()
            down_event.type = mock_pg.MOUSEBUTTONDOWN
            down_event.button = 1
            down_event.pos = (60, 45)  # Inside rect

            result = button.handle_event(down_event)
            assert result is False
            assert button._pressing is True

            # Simulate click up inside
            up_event = Mock()
            up_event.type = mock_pg.MOUSEBUTTONUP
            up_event.button = 1
            up_event.pos = (60, 45)

            result = button.handle_event(up_event)
            assert result is True
            assert button._pressing is False

    def test_handle_event_click_outside_rect(self):
        import game.utils.button as btn_mod

        mock_pg = MagicMock()
        mock_pg.Rect.side_effect = lambda *args, **kwargs: args[0] if len(args) == 1 and hasattr(args[0], 'x') else _Rect(*args)
        mock_pg.MOUSEBUTTONDOWN = 1025
        mock_pg.MOUSEBUTTONUP = 1026

        with patch.object(btn_mod, "pygame", mock_pg):
            rect = _Rect(10, 20, 100, 50)
            font = Mock()
            button = btn_mod.Button(rect, "Click", font)

            # Click down outside
            down_event = Mock()
            down_event.type = mock_pg.MOUSEBUTTONDOWN
            down_event.button = 1
            down_event.pos = (200, 200)  # Outside rect

            result = button.handle_event(down_event)
            assert result is False
            assert button._pressing is False

    def test_handle_event_press_inside_release_outside(self):
        import game.utils.button as btn_mod

        mock_pg = MagicMock()
        mock_pg.Rect.side_effect = lambda *args, **kwargs: args[0] if len(args) == 1 and hasattr(args[0], 'x') else _Rect(*args)
        mock_pg.MOUSEBUTTONDOWN = 1025
        mock_pg.MOUSEBUTTONUP = 1026

        with patch.object(btn_mod, "pygame", mock_pg):
            rect = _Rect(10, 20, 100, 50)
            font = Mock()
            button = btn_mod.Button(rect, "Click", font)

            # Press inside
            down_event = Mock()
            down_event.type = mock_pg.MOUSEBUTTONDOWN
            down_event.button = 1
            down_event.pos = (60, 45)
            button.handle_event(down_event)
            assert button._pressing is True

            # Release outside
            up_event = Mock()
            up_event.type = mock_pg.MOUSEBUTTONUP
            up_event.button = 1
            up_event.pos = (200, 200)  # Outside

            result = button.handle_event(up_event)
            assert result is False
            assert button._pressing is False

    def test_handle_event_ignores_other_buttons(self):
        import game.utils.button as btn_mod

        mock_pg = MagicMock()
        mock_pg.Rect.side_effect = lambda *args, **kwargs: args[0] if len(args) == 1 and hasattr(args[0], 'x') else _Rect(*args)
        mock_pg.MOUSEBUTTONDOWN = 1025

        with patch.object(btn_mod, "pygame", mock_pg):
            rect = _Rect(10, 20, 100, 50)
            font = Mock()
            button = btn_mod.Button(rect, "Click", font)

            # Right-click inside (button=3)
            event = Mock()
            event.type = mock_pg.MOUSEBUTTONDOWN
            event.button = 3
            event.pos = (60, 45)

            result = button.handle_event(event)
            assert result is False
            assert button._pressing is False

    def test_handle_event_ignores_other_event_types(self):
        import game.utils.button as btn_mod

        mock_pg = MagicMock()
        mock_pg.Rect.side_effect = lambda *args, **kwargs: args[0] if len(args) == 1 and hasattr(args[0], 'x') else _Rect(*args)
        mock_pg.KEYDOWN = 768

        with patch.object(btn_mod, "pygame", mock_pg):
            rect = _Rect(10, 20, 100, 50)
            font = Mock()
            button = btn_mod.Button(rect, "Click", font)

            # Key press event
            event = Mock()
            event.type = mock_pg.KEYDOWN

            result = button.handle_event(event)
            assert result is False
