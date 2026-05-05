"""Unit tests for MultiplayerLobbyScreen and NameEntryScreen."""
import sys
from unittest.mock import Mock, MagicMock, patch

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


class TestMultiplayerLobbyScreenInit:
    """Test lobby screen initialization."""

    def test_init_with_player_name(self):
        import game.screens.multiplayer.lobby as lobby_mod

        mock_pg = MagicMock()
        mock_pg.font.Font.return_value = Mock(render=Mock(return_value=Mock(get_rect=Mock(return_value=Mock()))))
        mock_pg.Rect.side_effect = lambda x, y, w, h: _Rect(x, y, w, h)

        mock_screen = Mock()
        mock_screen.get_width.return_value = 800
        mock_screen.get_height.return_value = 600

        mock_client = Mock()
        my_name = "TestPlayer"

        with patch.object(lobby_mod, "pygame", mock_pg), \
             patch.object(lobby_mod, "Button"):

            screen = lobby_mod.MultiplayerLobbyScreen(mock_screen, mock_client, my_name)

            assert screen.my_name == my_name
            assert screen.players == []
            assert screen._incoming_from is None
            assert screen._outgoing_to is None
            assert screen.status is not None

    def test_init_creates_buttons(self):
        import game.screens.multiplayer.lobby as lobby_mod

        mock_pg = MagicMock()
        mock_pg.font.Font.return_value = Mock(render=Mock(return_value=Mock(get_rect=Mock(return_value=Mock()))))
        mock_pg.Rect.side_effect = lambda x, y, w, h: _Rect(x, y, w, h)

        mock_screen = Mock()
        mock_screen.get_width.return_value = 800
        mock_screen.get_height.return_value = 600

        mock_client = Mock()
        mock_button_class = MagicMock()

        with patch.object(lobby_mod, "pygame", mock_pg), \
             patch.object(lobby_mod, "Button", mock_button_class):

            screen = lobby_mod.MultiplayerLobbyScreen(mock_screen, mock_client, "Player")

            # Verify Button was called multiple times (for each button)
            assert mock_button_class.call_count > 0

    def test_button_rects_initialized_empty(self):
        import game.screens.multiplayer.lobby as lobby_mod

        mock_pg = MagicMock()
        mock_pg.font.Font.return_value = Mock(render=Mock(return_value=Mock(get_rect=Mock(return_value=Mock()))))
        mock_pg.Rect.side_effect = lambda x, y, w, h: _Rect(x, y, w, h)

        mock_screen = Mock()
        mock_screen.get_width.return_value = 800
        mock_screen.get_height.return_value = 600

        mock_client = Mock()

        with patch.object(lobby_mod, "pygame", mock_pg), \
             patch.object(lobby_mod, "Button"):

            screen = lobby_mod.MultiplayerLobbyScreen(mock_screen, mock_client, "Player")

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
