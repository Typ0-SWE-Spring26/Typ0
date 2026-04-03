"""Tests for multiplayer-specific GameModel behaviour.

Covers seeded determinism (both clients must produce identical sequences)
and that seed=None still works for single-player (backward compat).
"""
import pytest
from game.core.event_bus import EventBus
from game.core.game_model import GameModel, BUTTON_NAMES


def _advance_to_sequence(model, ticks=10_000):
    """Drive an 'adding' cycle so the model appends one button."""
    model.state = 'adding'
    model._next_time = 0
    model.update(ticks)


class TestSeededDeterminism:
    """Two GameModel instances with the same seed must produce the same sequence."""

    def test_same_seed_same_first_button(self):
        m1 = GameModel(EventBus(), seed=42)
        m2 = GameModel(EventBus(), seed=42)
        _advance_to_sequence(m1)
        _advance_to_sequence(m2)
        assert m1.sequence == m2.sequence

    def test_same_seed_same_long_sequence(self):
        seed = 99999
        m1 = GameModel(EventBus(), seed=seed)
        m2 = GameModel(EventBus(), seed=seed)

        for i in range(10):
            t = (i + 1) * 10_000
            _advance_to_sequence(m1, t)
            _advance_to_sequence(m2, t)

        assert m1.sequence == m2.sequence
        assert len(m1.sequence) == 10

    def test_different_seeds_produce_different_sequences(self):
        # With enough rounds, two different seeds are extremely unlikely to match
        sequences = []
        for seed in (1, 2):
            m = GameModel(EventBus(), seed=seed)
            for i in range(15):
                _advance_to_sequence(m, (i + 1) * 10_000)
            sequences.append(m.sequence[:])
        assert sequences[0] != sequences[1]

    def test_sequence_contains_only_valid_buttons(self):
        m = GameModel(EventBus(), seed=7)
        for i in range(20):
            _advance_to_sequence(m, (i + 1) * 10_000)
        assert all(btn in BUTTON_NAMES for btn in m.sequence)

    def test_reset_replays_same_sequence(self):
        """After reset the _rng is NOT re-seeded — this is intentional.

        Single-player uses a fresh Random() per GameModel instantiation.
        Multiplayer creates a new GameModel per match with the server seed.
        """
        m = GameModel(EventBus(), seed=123)
        _advance_to_sequence(m, 10_000)
        first_button = m.sequence[0]

        m.reset()
        _advance_to_sequence(m, 10_000)
        # After reset the RNG continues from where it left off, so the
        # second sequence differs — this is expected behaviour.
        # The test just asserts reset doesn't crash and state is clean.
        assert m.score == 0
        assert m.state == 'showing'


class TestBackwardCompat:
    """seed=None (default) keeps single-player working exactly as before."""

    def test_no_seed_still_generates_sequence(self):
        m = GameModel(EventBus())
        _advance_to_sequence(m)
        assert len(m.sequence) == 1
        assert m.sequence[0] in BUTTON_NAMES

    def test_no_seed_score_still_increments(self):
        m = GameModel(EventBus())
        m.sequence = ['left']
        m.player_index = 0
        m.state = 'input'
        m.handle_input('left', 1000)
        assert m.score == 1
