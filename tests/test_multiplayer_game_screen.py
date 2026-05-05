"""Unit tests for MultiplayerGameScreen core logic."""
import sys
from unittest.mock import Mock, MagicMock, patch

sys.modules["pygame"] = MagicMock()

from game.core.event_bus import EventBus
from game.core.game_model import GameModel


class TestMultiplayerGameScreen:
    """Test the multiplayer game screen initialization and state management."""

    def test_init_creates_seeded_model(self):
        import game.screens.multiplayer.game as game_mod

        mock_pg = MagicMock()
        mock_pg.font.Font.return_value = Mock(render=Mock(return_value=Mock(get_rect=Mock(return_value=Mock()))))
        mock_pg.Surface.return_value = Mock()
        mock_pg.SRCALPHA = 65536

        mock_screen = Mock()
        mock_screen.get_width.return_value = 800
        mock_screen.get_height.return_value = 600

        mock_client = Mock()
        mock_keybinds = Mock()
        mock_keybinds.inverted = False
        mock_keybinds.key_labels = {}

        with patch.object(game_mod, "pygame", mock_pg), \
             patch.object(game_mod, "GameModel") as mock_model_class, \
             patch.object(game_mod, "GameView"), \
             patch.object(game_mod, "GameTimer"), \
             patch.object(game_mod, "EventBus") as mock_bus_class:

            mock_model_instance = Mock()
            mock_model_class.return_value = mock_model_instance
            mock_bus_instance = Mock()
            mock_bus_class.return_value = mock_bus_instance

            screen = game_mod.MultiplayerGameScreen(
                mock_screen,
                mock_client,
                "Player1",
                "Player2",
                seed=42,
                settings=0,
                keybinds=mock_keybinds,
            )

            # Verify GameModel was called with the seed
            mock_model_class.assert_called_once()
            call_kwargs = mock_model_class.call_args[1]
            assert call_kwargs.get("seed") == 42

    def test_set_paused_toggles_state(self):
        import game.screens.multiplayer.game as game_mod

        mock_pg = MagicMock()
        mock_pg.font.Font.return_value = Mock(render=Mock(return_value=Mock(get_rect=Mock(return_value=Mock()))))
        mock_pg.Surface.return_value = Mock()
        mock_pg.SRCALPHA = 65536
        mock_pg.time.get_ticks.return_value = 1000

        mock_screen = Mock()
        mock_screen.get_width.return_value = 800
        mock_screen.get_height.return_value = 600

        mock_client = Mock()
        mock_keybinds = Mock()
        mock_keybinds.inverted = False
        mock_keybinds.key_labels = {}

        with patch.object(game_mod, "pygame", mock_pg), \
             patch.object(game_mod, "GameModel"), \
             patch.object(game_mod, "GameView"), \
             patch.object(game_mod, "GameTimer"), \
             patch.object(game_mod, "animation_utils") as mock_anim:

            screen = game_mod.MultiplayerGameScreen(
                mock_screen,
                mock_client,
                "Player1",
                "Player2",
                seed=42,
                settings=0,
                keybinds=mock_keybinds,
            )

            assert screen._paused is False

            # Pause
            screen._set_paused(True)
            assert screen._paused is True
            mock_anim.pause_music.assert_called_once()

            # Resume
            mock_anim.reset_mock()
            screen._set_paused(False)
            assert screen._paused is False
            mock_anim.unpause_music.assert_called_once()

    def test_set_paused_no_op_on_same_state(self):
        """Test that set_paused does nothing if state doesn't change."""
        import game.screens.multiplayer.game as game_mod

        mock_pg = MagicMock()
        mock_pg.font.Font.return_value = Mock(render=Mock(return_value=Mock(get_rect=Mock(return_value=Mock()))))
        mock_pg.Surface.return_value = Mock()
        mock_pg.SRCALPHA = 65536
        mock_pg.time.get_ticks.return_value = 1000

        mock_screen = Mock()
        mock_screen.get_width.return_value = 800
        mock_screen.get_height.return_value = 600

        mock_client = Mock()
        mock_keybinds = Mock()
        mock_keybinds.inverted = False
        mock_keybinds.key_labels = {}

        with patch.object(game_mod, "pygame", mock_pg), \
             patch.object(game_mod, "GameModel"), \
             patch.object(game_mod, "GameView"), \
             patch.object(game_mod, "GameTimer"), \
             patch.object(game_mod, "animation_utils") as mock_anim:

            screen = game_mod.MultiplayerGameScreen(
                mock_screen,
                mock_client,
                "Player1",
                "Player2",
                seed=42,
                settings=0,
                keybinds=mock_keybinds,
            )

            screen._paused = True
            mock_anim.reset_mock()

            # Try to set to same state — should not call pause_music/unpause_music
            screen._set_paused(True)
            mock_anim.pause_music.assert_not_called()
            mock_anim.unpause_music.assert_not_called()


class TestMultiplayerGameScreenInit:
    """Test initialization with different game settings."""

    def test_inverted_settings_applied_to_keybinds(self):
        import game.screens.multiplayer.game as game_mod

        mock_pg = MagicMock()
        mock_pg.font.Font.return_value = Mock(render=Mock(return_value=Mock(get_rect=Mock(return_value=Mock()))))
        mock_pg.Surface.return_value = Mock()
        mock_pg.SRCALPHA = 65536

        mock_screen = Mock()
        mock_screen.get_width.return_value = 800
        mock_screen.get_height.return_value = 600

        mock_client = Mock()
        mock_keybinds = Mock()
        mock_keybinds.inverted = False
        mock_keybinds.key_labels = {}

        # Create settings with inverted keys flag (bit 0)
        settings_with_inverted = 1  # inverted flag is bit 0

        with patch.object(game_mod, "pygame", mock_pg), \
             patch.object(game_mod, "GameModel"), \
             patch.object(game_mod, "GameView"), \
             patch.object(game_mod, "GameTimer"), \
             patch.object(game_mod, "settings_flags") as mock_flags:

            # Simulate the decode function returning inverted=True
            mock_flags.decode.return_value = {"inverted_keys": True}

            screen = game_mod.MultiplayerGameScreen(
                mock_screen,
                mock_client,
                "Player1",
                "Player2",
                seed=42,
                settings=settings_with_inverted,
                keybinds=mock_keybinds,
            )

            # Verify decode was called
            mock_flags.decode.assert_called_once_with(settings_with_inverted)
            # Verify keybinds was updated
            assert mock_keybinds.inverted is True

    def test_opponent_score_initialized_to_zero(self):
        import game.screens.multiplayer.game as game_mod

        mock_pg = MagicMock()
        mock_pg.font.Font.return_value = Mock(render=Mock(return_value=Mock(get_rect=Mock(return_value=Mock()))))
        mock_pg.Surface.return_value = Mock()
        mock_pg.SRCALPHA = 65536

        mock_screen = Mock()
        mock_screen.get_width.return_value = 800
        mock_screen.get_height.return_value = 600

        mock_client = Mock()
        mock_keybinds = Mock()
        mock_keybinds.inverted = False
        mock_keybinds.key_labels = {}

        with patch.object(game_mod, "pygame", mock_pg), \
             patch.object(game_mod, "GameModel"), \
             patch.object(game_mod, "GameView"), \
             patch.object(game_mod, "GameTimer"):

            screen = game_mod.MultiplayerGameScreen(
                mock_screen,
                mock_client,
                "Player1",
                "Player2",
                seed=42,
                settings=0,
                keybinds=mock_keybinds,
            )

            assert screen.opponent_score == 0
            assert screen._mistake_sent is False
            assert screen._pending_score is None
