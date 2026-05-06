"""Unit tests for MultiplayerLobbyScreen and NameEntryScreen."""
import sys
from contextlib import ExitStack
from unittest.mock import Mock, MagicMock, patch

import pytest

sys.modules["pygame"] = MagicMock()


class _Rect:
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

    def collidepoint(self, pos):
        px, py = pos
        return self.left <= px <= self.right and self.top <= py <= self.bottom


@pytest.fixture
def lobby_screen_factory():
    """Build a MultiplayerLobbyScreen plus the captured Button mock."""
    import game.screens.multiplayer.lobby as lobby_mod

    stack = ExitStack()

    def make(my_name="TestPlayer", custom_button=None):
        mock_pg = MagicMock()
        mock_pg.font.Font.return_value = Mock(render=Mock(return_value=Mock(get_rect=Mock(return_value=Mock()))))
        mock_pg.Rect.side_effect = lambda x, y, w, h: _Rect(x, y, w, h)

        mock_screen = Mock()
        mock_screen.get_width.return_value = 800
        mock_screen.get_height.return_value = 600

        mock_client = Mock()
        mock_button = custom_button if custom_button is not None else MagicMock()

        stack.enter_context(patch.object(lobby_mod, "pygame", mock_pg))
        stack.enter_context(patch.object(lobby_mod, "Button", mock_button))

        screen = lobby_mod.MultiplayerLobbyScreen(mock_screen, mock_client, my_name)
        return screen, mock_pg, mock_button, mock_screen, mock_client

    yield make
    stack.close()


class TestMultiplayerLobbyScreenInit:
    """Test lobby screen initialization."""

    def test_init_with_player_name(self, lobby_screen_factory):
        my_name = "TestPlayer"
        screen, _pg, _btn, _scr, _cli = lobby_screen_factory(my_name=my_name)

        assert screen.my_name == my_name
        assert screen.players == []
        assert screen._incoming_from is None
        assert screen._outgoing_to is None
        assert screen.status is not None

    def test_init_creates_buttons(self, lobby_screen_factory):
        button_mock = MagicMock()
        _screen, _pg, mock_button, _scr, _cli = lobby_screen_factory(
            my_name="Player", custom_button=button_mock,
        )
        assert mock_button.call_count > 0

    def test_button_rects_initialized_empty(self, lobby_screen_factory):
        screen, _pg, _btn, _scr, _cli = lobby_screen_factory(my_name="Player")
        assert screen._row_rects == {}


class TestNameEntryScreenInit:
    """Test name entry screen initialization."""

    def test_max_name_length_constant_exists(self):
        """Verify MAX_NAME_LEN constant is defined and positive."""
        import game.screens.name_entry as name_mod

        assert hasattr(name_mod, "MAX_NAME_LEN")
        assert isinstance(name_mod.MAX_NAME_LEN, int)
        assert name_mod.MAX_NAME_LEN > 0

    def test_max_name_length_is_reasonable(self):
        """Verify MAX_NAME_LEN is a reasonable value."""
        import game.screens.name_entry as name_mod

        # Typical max name length should be between 5 and 100
        assert 5 <= name_mod.MAX_NAME_LEN <= 100
