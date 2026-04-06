"""Tests for GameModel difficulty presets (Simon mode)."""
import pytest
from unittest.mock import patch
from game.core.game_model import GameModel, _DIFFICULTY_PRESETS
from game.core.event_bus import EventBus


@pytest.fixture
def bus():
    return EventBus()


# ---------------------------------------------------------------------------
# Preset values are applied on construction
# ---------------------------------------------------------------------------

class TestSimonDifficultyPresets:
    def test_normal_is_default(self, bus):
        model  = GameModel(bus)
        normal = GameModel(bus, difficulty='normal')
        assert model._flash_time       == normal._flash_time
        assert model._inter_gap        == normal._inter_gap
        assert model._pre_show_pause   == normal._pre_show_pause
        assert model._post_round_pause == normal._post_round_pause
        assert model.timer_limit       == normal.timer_limit

    def test_easy_has_longer_flash_time_than_normal(self, bus):
        easy   = GameModel(bus, difficulty='easy')
        normal = GameModel(bus, difficulty='normal')
        assert easy._flash_time > normal._flash_time

    def test_hard_has_shorter_flash_time_than_normal(self, bus):
        hard   = GameModel(bus, difficulty='hard')
        normal = GameModel(bus, difficulty='normal')
        assert hard._flash_time < normal._flash_time

    def test_easy_has_longer_timer_limit_than_hard(self, bus):
        easy = GameModel(bus, difficulty='easy')
        hard = GameModel(bus, difficulty='hard')
        assert easy.timer_limit > hard.timer_limit

    def test_difficulty_order_flash_time(self, bus):
        easy   = GameModel(bus, difficulty='easy')
        normal = GameModel(bus, difficulty='normal')
        hard   = GameModel(bus, difficulty='hard')
        assert easy._flash_time > normal._flash_time > hard._flash_time

    def test_difficulty_order_timer_limit(self, bus):
        easy   = GameModel(bus, difficulty='easy')
        normal = GameModel(bus, difficulty='normal')
        hard   = GameModel(bus, difficulty='hard')
        assert easy.timer_limit > normal.timer_limit > hard.timer_limit

    def test_all_presets_exist(self):
        for key in ('easy', 'normal', 'hard'):
            assert key in _DIFFICULTY_PRESETS

    def test_unknown_difficulty_falls_back_to_normal(self, bus):
        model  = GameModel(bus, difficulty='impossible')
        normal = GameModel(bus, difficulty='normal')
        assert model._flash_time == normal._flash_time
        assert model.timer_limit == normal.timer_limit

    def test_seed_still_works_with_difficulty(self, bus):
        """Seeded RNG should be unaffected by difficulty."""
        a = GameModel(bus, seed=42, difficulty='easy')
        b = GameModel(bus, seed=42, difficulty='hard')
        # Both should produce the same sequence from the same seed
        from game.core.game_model import BUTTON_NAMES
        choices_a = [a._rng.choice(list(BUTTON_NAMES)) for _ in range(10)]
        choices_b = [b._rng.choice(list(BUTTON_NAMES)) for _ in range(10)]
        assert choices_a == choices_b


# ---------------------------------------------------------------------------
# Timing constants are actually used during state transitions
# ---------------------------------------------------------------------------

class TestSimonDifficultyTimingInUpdate:
    def test_adding_uses_pre_show_pause(self, bus):
        model = GameModel(bus, difficulty='normal')
        model.state = 'adding'
        model._next_time = 0

        with patch.object(model._rng, 'choice', return_value='left'):
            model.update(500)

        # After adding, next time should be now + _pre_show_pause
        assert model._next_time == 500 + model._pre_show_pause

    def test_showing_uses_flash_time(self, bus):
        model = GameModel(bus, difficulty='normal')
        model.state = 'showing'
        model.sequence = ['left']
        model._show_index = 0
        model._showing_lit = False
        model._next_time = 0

        model.update(1000)

        assert model.flash_end == 1000 + model._flash_time

    def test_showing_uses_inter_gap(self, bus):
        model = GameModel(bus, difficulty='normal')
        model.state = 'showing'
        model.sequence = ['left', 'right']
        model._show_index = 0
        model._showing_lit = True
        model.flash_end = 0

        model.update(500)

        # After the lit period, next time should be now + _inter_gap
        assert model._next_time == 500 + model._inter_gap

    def test_round_complete_uses_post_round_pause(self, bus):
        model = GameModel(bus, difficulty='normal')
        model.sequence = ['left']
        model.player_index = 0

        model.handle_input('left', 3000)

        assert model._next_time == 3000 + model._post_round_pause

    def test_easy_post_round_pause_longer_than_hard(self, bus):
        easy = GameModel(bus, difficulty='easy')
        hard = GameModel(bus, difficulty='hard')
        assert easy._post_round_pause > hard._post_round_pause

    def test_easy_pre_show_pause_longer_than_hard(self, bus):
        easy = GameModel(bus, difficulty='easy')
        hard = GameModel(bus, difficulty='hard')
        assert easy._pre_show_pause > hard._pre_show_pause
