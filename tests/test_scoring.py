"""Tests for scoring logic — covers #35 (Test Scoring)."""
import pytest
from unittest.mock import patch
from game.core.event_bus import EventBus
from game.core.game_model import GameModel


@pytest.fixture
def bus():
    return EventBus()


@pytest.fixture
def model(bus):
    return GameModel(bus)


class TestScoreIncrement:
    """Verify score increments correctly each round."""

    def test_score_starts_at_zero(self, model):
        assert model.score == 0

    def test_score_increments_on_correct_sequence(self, model):
        model.sequence = ['left']
        model.player_index = 0
        model.state = 'input'

        model.handle_input('left', 1000)

        assert model.score == 1

    def test_score_increments_each_round(self, model):
        """Play through 5 rounds and verify score tracks."""
        for round_num in range(1, 6):
            model.state = 'adding'
            model._next_time = 0

            with patch.object(model._rng, 'choice', return_value='up'):
                model.update(round_num * 10000)

            # Fast-forward through showing
            model._show_index = len(model.sequence)
            model.update(round_num * 10000 + 5000)

            assert model.state == 'input'

            # Play back the entire sequence correctly
            for i, button in enumerate(model.sequence):
                model.handle_input(button, round_num * 10000 + 6000 + i * 100)

            assert model.score == round_num

    def test_score_not_incremented_on_wrong_input(self, model):
        model.sequence = ['left']
        model.player_index = 0
        model.state = 'input'
        model.score = 3

        model.handle_input('right', 1000)

        assert model.score == 3  # unchanged

    def test_score_preserved_on_gameover(self, model):
        model.sequence = ['left', 'right']
        model.player_index = 0
        model.state = 'input'
        model.score = 10

        model.handle_input('down', 1000)  # wrong

        assert model.state == 'gameover'
        assert model.score == 10  # preserved for display

    def test_score_preserved_on_timer_expiry(self, model):
        model.state = 'input'
        model.score = 7

        model.on_timer_expired({'now': 5000})

        assert model.state == 'gameover'
        assert model.score == 7


class TestScoreReset:
    """Verify score resets properly between games."""

    def test_reset_clears_score(self, model):
        model.score = 42
        model.reset()
        assert model.score == 0

    def test_score_fresh_after_gameover_and_reset(self, model):
        """Simulate: play, gameover, reset, play again."""
        # Round 1
        model.sequence = ['left']
        model.player_index = 0
        model.state = 'input'
        model.handle_input('left', 1000)
        assert model.score == 1

        # Wrong input -> gameover
        model.state = 'adding'
        model._next_time = 0
        with patch.object(model._rng, 'choice', return_value='right'):
            model.update(5000)
        model._show_index = len(model.sequence)
        model.update(6000)
        # Sequence is now ['left', 'right'], player must input both
        # Give wrong input immediately
        model.handle_input('down', 7000)  # wrong — expected 'left' at index 0
        assert model.state == 'gameover'
        assert model.score == 1

        # Reset for retry
        model.reset()
        assert model.score == 0
        assert model.sequence == []

        # New game round 1
        model._next_time = 0
        with patch.object(model._rng, 'choice', return_value='up'):
            model.update(10000)
        model._show_index = 1
        model.update(15000)
        model.handle_input('up', 16000)
        assert model.score == 1


class TestScoreEvents:
    """Verify score-related events are emitted."""

    def test_round_complete_event_contains_score(self, model, bus):
        handler = mock_handler()
        bus.subscribe('round_complete', handler)

        model.sequence = ['left']
        model.player_index = 0
        model.state = 'input'

        model.handle_input('left', 1000)

        handler.assert_called_once()
        assert handler.call_args[0][0]['score'] == 1

    def test_round_complete_events_accumulate(self, model, bus):
        scores = []
        bus.subscribe('round_complete', lambda data: scores.append(data['score']))

        for round_num in range(1, 4):
            model.state = 'adding'
            model._next_time = 0
            with patch.object(model._rng, 'choice', return_value='left'):
                model.update(round_num * 10000)

            model._show_index = len(model.sequence)
            model.update(round_num * 10000 + 5000)

            for i, btn in enumerate(model.sequence):
                model.handle_input(btn, round_num * 10000 + 6000 + i * 100)

        assert scores == [1, 2, 3]


def mock_handler():
    from unittest.mock import Mock
    return Mock()
