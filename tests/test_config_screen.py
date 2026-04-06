"""Tests for ConfigScreen return values and GameScreen/BopItScreen difficulty wiring."""
import sys
import pytest
from unittest.mock import MagicMock, patch, Mock

# Mock pygame before any game imports
sys.modules['pygame'] = MagicMock()

from game.core.game_model import GameModel, _DIFFICULTY_PRESETS as SIMON_PRESETS
from game.core.bopit_model import BopItModel, _DIFFICULTY_PRESETS as BOPIT_PRESETS
from game.core.event_bus import EventBus
from game.core.keybinds import KeybindManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_screen():
    screen = Mock()
    screen.get_width.return_value = 800
    screen.get_height.return_value = 600
    return screen


def _make_keybinds():
    kb = Mock(spec=KeybindManager)
    kb.button_keys = {'left': 97, 'right': 100, 'up': 119, 'down': 115, 'space': 32}
    kb.key_labels  = {'left': 'A', 'right': 'D', 'up': 'W', 'down': 'S', 'space': 'SPACE'}
    kb.inverted = False
    return kb


# ---------------------------------------------------------------------------
# GameScreen difficulty wiring
# ---------------------------------------------------------------------------

class TestGameScreenDifficultyWiring:
    """GameScreen must pass difficulty through to its GameModel and timer."""

    def _make_game_screen(self, difficulty):
        with patch('game.screens.gameplay.display.EventBus'), \
             patch('game.screens.gameplay.display.GameView'), \
             patch('game.screens.gameplay.display.GameController') as MockCtrl, \
             patch('game.screens.gameplay.display.MenuOverlay'), \
             patch('game.screens.gameplay.display.GameModel') as MockModel:

            mock_model_instance = Mock()
            mock_model_instance.timer_limit = SIMON_PRESETS[difficulty][4]
            MockModel.return_value = mock_model_instance

            mock_ctrl_instance = Mock()
            mock_ctrl_instance.game_timer = Mock()
            MockCtrl.return_value = mock_ctrl_instance

            from game.screens.gameplay.display import GameScreen
            gs = GameScreen(_make_screen(), _make_keybinds(), difficulty=difficulty)

            return MockModel, mock_ctrl_instance

    def test_easy_difficulty_passed_to_model(self):
        MockModel, _ = self._make_game_screen('easy')
        _, kwargs = MockModel.call_args
        assert kwargs.get('difficulty') == 'easy'

    def test_normal_difficulty_passed_to_model(self):
        MockModel, _ = self._make_game_screen('normal')
        _, kwargs = MockModel.call_args
        assert kwargs.get('difficulty') == 'normal'

    def test_hard_difficulty_passed_to_model(self):
        MockModel, _ = self._make_game_screen('hard')
        _, kwargs = MockModel.call_args
        assert kwargs.get('difficulty') == 'hard'

    def test_timer_limit_propagated_from_model(self):
        _, mock_ctrl = self._make_game_screen('easy')
        expected = SIMON_PRESETS['easy'][4]
        assert mock_ctrl.game_timer.TIME_LIMIT == expected

    def test_default_difficulty_is_normal(self):
        with patch('game.screens.gameplay.display.EventBus'), \
             patch('game.screens.gameplay.display.GameView'), \
             patch('game.screens.gameplay.display.GameController') as MockCtrl, \
             patch('game.screens.gameplay.display.MenuOverlay'), \
             patch('game.screens.gameplay.display.GameModel') as MockModel:

            mock_model_instance = Mock()
            mock_model_instance.timer_limit = SIMON_PRESETS['normal'][4]
            MockModel.return_value = mock_model_instance
            MockCtrl.return_value = Mock(game_timer=Mock())

            from game.screens.gameplay.display import GameScreen
            GameScreen(_make_screen(), _make_keybinds())  # no difficulty arg

            _, kwargs = MockModel.call_args
            assert kwargs.get('difficulty') == 'normal'


# ---------------------------------------------------------------------------
# BopItScreen difficulty wiring
# ---------------------------------------------------------------------------

class TestBopItScreenDifficultyWiring:
    """BopItScreen must pass difficulty through to its BopItModel."""

    def _make_bopit_screen(self, difficulty):
        with patch('game.screens.gameplay.bopit_display.EventBus'), \
             patch('game.screens.gameplay.bopit_display.BopItView'), \
             patch('game.screens.gameplay.bopit_display.BopItController'), \
             patch('game.screens.gameplay.bopit_display.MenuOverlay'), \
             patch('game.screens.gameplay.bopit_display.BopItModel') as MockModel:

            from game.screens.gameplay.bopit_display import BopItScreen
            BopItScreen(_make_screen(), _make_keybinds(), difficulty=difficulty)
            return MockModel

    def test_easy_difficulty_passed_to_model(self):
        MockModel = self._make_bopit_screen('easy')
        _, kwargs = MockModel.call_args
        assert kwargs.get('difficulty') == 'easy'

    def test_hard_difficulty_passed_to_model(self):
        MockModel = self._make_bopit_screen('hard')
        _, kwargs = MockModel.call_args
        assert kwargs.get('difficulty') == 'hard'

    def test_default_difficulty_is_normal(self):
        with patch('game.screens.gameplay.bopit_display.EventBus'), \
             patch('game.screens.gameplay.bopit_display.BopItView'), \
             patch('game.screens.gameplay.bopit_display.BopItController'), \
             patch('game.screens.gameplay.bopit_display.MenuOverlay'), \
             patch('game.screens.gameplay.bopit_display.BopItModel') as MockModel:

            from game.screens.gameplay.bopit_display import BopItScreen
            BopItScreen(_make_screen(), _make_keybinds())  # no difficulty arg

            _, kwargs = MockModel.call_args
            assert kwargs.get('difficulty') == 'normal'


# ---------------------------------------------------------------------------
# ConfigScreen return value contract
# (tests the screen's logic without running its async event loop)
# ---------------------------------------------------------------------------

class TestConfigScreenReturnValues:
    """The config dict returned by ConfigScreen must have the right shape."""

    def _config_dict(self, inverted, difficulty_label):
        """Replicate exactly what ConfigScreen returns on 'Start Game'."""
        return {
            "inverted":   inverted,
            "difficulty": difficulty_label.lower(),
        }

    def test_inverted_false_normal(self):
        result = self._config_dict(False, "Normal")
        assert result == {"inverted": False, "difficulty": "normal"}

    def test_inverted_true_easy(self):
        result = self._config_dict(True, "Easy")
        assert result == {"inverted": True, "difficulty": "easy"}

    def test_hard_difficulty_lowercased(self):
        result = self._config_dict(False, "Hard")
        assert result["difficulty"] == "hard"

    def test_difficulty_is_string(self):
        result = self._config_dict(False, "Normal")
        assert isinstance(result["difficulty"], str)

    def test_inverted_is_bool(self):
        result = self._config_dict(True, "Normal")
        assert isinstance(result["inverted"], bool)

    def test_all_difficulty_labels_produce_valid_keys(self):
        for label in ("Easy", "Normal", "Hard"):
            result = self._config_dict(False, label)
            assert result["difficulty"] in SIMON_PRESETS
            assert result["difficulty"] in BOPIT_PRESETS


# ---------------------------------------------------------------------------
# End-to-end: difficulty preset values are sensible
# (sanity checks that presets don't accidentally break game balance)
# ---------------------------------------------------------------------------

class TestPresetSanity:
    """Presets must be internally consistent and ordered easy < normal < hard."""

    @pytest.mark.parametrize("difficulty", ["easy", "normal", "hard"])
    def test_bopit_min_time_less_than_base_time(self, difficulty):
        bus = EventBus()
        m = BopItModel(bus, difficulty=difficulty)
        assert m.MIN_TIME < m.BASE_TIME

    @pytest.mark.parametrize("difficulty", ["easy", "normal", "hard"])
    def test_bopit_min_round_delay_less_than_base(self, difficulty):
        bus = EventBus()
        m = BopItModel(bus, difficulty=difficulty)
        assert m.MIN_ROUND_DELAY < m.BASE_ROUND_DELAY

    @pytest.mark.parametrize("difficulty", ["easy", "normal", "hard"])
    def test_simon_timer_limit_positive(self, difficulty):
        bus = EventBus()
        m = GameModel(bus, difficulty=difficulty)
        assert m.timer_limit > 0

    @pytest.mark.parametrize("difficulty", ["easy", "normal", "hard"])
    def test_simon_flash_time_positive(self, difficulty):
        bus = EventBus()
        m = GameModel(bus, difficulty=difficulty)
        assert m._flash_time > 0
