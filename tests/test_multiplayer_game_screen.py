"""Unit tests for MultiplayerGameScreen core logic."""
import sys
from contextlib import ExitStack
from unittest.mock import Mock, MagicMock, patch

import pytest

sys.modules["pygame"] = MagicMock()


def _build_mocks(extra_patches=None):
    """Build the standard mock_pg / screen / client / keybinds used by every test."""
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

    return mock_pg, mock_screen, mock_client, mock_keybinds


@pytest.fixture
def multiplayer_screen_factory():
    """Factory fixture that builds a MultiplayerGameScreen plus its mocks.

    Each test calls the factory with the patches it cares about (e.g. ``GameModel``,
    ``EventBus``, ``animation_utils``) and gets back the constructed screen plus the
    captured mocks. Patches stay active for the lifetime of the test.
    """
    import game.screens.multiplayer.game as game_mod

    stack = ExitStack()

    def make(*, extra_patches=(), seed=42, settings=0):
        mock_pg, mock_screen, mock_client, mock_keybinds = _build_mocks()

        captured = {"pygame": mock_pg}
        stack.enter_context(patch.object(game_mod, "pygame", mock_pg))
        stack.enter_context(patch.object(game_mod, "GameView"))
        stack.enter_context(patch.object(game_mod, "GameTimer"))
        for name in extra_patches:
            captured[name] = stack.enter_context(patch.object(game_mod, name))
        # Default GameModel patch when the test hasn't asked for its own.
        if "GameModel" not in captured:
            stack.enter_context(patch.object(game_mod, "GameModel"))

        screen = game_mod.MultiplayerGameScreen(
            mock_screen,
            mock_client,
            "Player1",
            "Player2",
            seed=seed,
            settings=settings,
            keybinds=mock_keybinds,
        )
        return screen, captured, mock_keybinds

    yield make
    stack.close()


class TestMultiplayerGameScreen:
    """Test the multiplayer game screen initialization and state management."""

    def test_init_creates_seeded_model(self, multiplayer_screen_factory):
        _screen, captured, _kb = multiplayer_screen_factory(
            extra_patches=("GameModel", "EventBus"),
            seed=42,
        )
        mock_model_class = captured["GameModel"]
        mock_model_class.assert_called_once()
        assert mock_model_class.call_args[1].get("seed") == 42

    def test_set_paused_toggles_state(self, multiplayer_screen_factory):
        screen, captured, _kb = multiplayer_screen_factory(
            extra_patches=("animation_utils",),
        )
        mock_anim = captured["animation_utils"]

        assert screen._paused is False

        screen._set_paused(True)
        assert screen._paused is True
        mock_anim.pause_music.assert_called_once()

        mock_anim.reset_mock()
        screen._set_paused(False)
        assert screen._paused is False
        mock_anim.unpause_music.assert_called_once()

    def test_set_paused_no_op_on_same_state(self, multiplayer_screen_factory):
        """Test that set_paused does nothing if state doesn't change."""
        screen, captured, _kb = multiplayer_screen_factory(
            extra_patches=("animation_utils",),
        )
        mock_anim = captured["animation_utils"]

        screen._paused = True
        mock_anim.reset_mock()

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
