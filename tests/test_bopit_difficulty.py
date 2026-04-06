"""Tests for BopItModel difficulty presets."""
import pytest
from game.core.bopit_model import BopItModel, _DIFFICULTY_PRESETS
from game.core.event_bus import EventBus


@pytest.fixture
def bus():
    return EventBus()


# ---------------------------------------------------------------------------
# Preset values are applied on construction
# ---------------------------------------------------------------------------

class TestDifficultyPresets:
    def test_normal_is_default(self, bus):
        model = BopItModel(bus)
        normal = BopItModel(bus, difficulty='normal')
        assert model.BASE_TIME == normal.BASE_TIME
        assert model.TIME_STEP == normal.TIME_STEP

    def test_easy_has_longer_base_time_than_normal(self, bus):
        easy   = BopItModel(bus, difficulty='easy')
        normal = BopItModel(bus, difficulty='normal')
        assert easy.BASE_TIME > normal.BASE_TIME

    def test_hard_has_shorter_base_time_than_normal(self, bus):
        hard   = BopItModel(bus, difficulty='hard')
        normal = BopItModel(bus, difficulty='normal')
        assert hard.BASE_TIME < normal.BASE_TIME

    def test_easy_has_larger_min_time_than_hard(self, bus):
        easy = BopItModel(bus, difficulty='easy')
        hard = BopItModel(bus, difficulty='hard')
        assert easy.MIN_TIME > hard.MIN_TIME

    def test_hard_has_larger_time_step_than_easy(self, bus):
        easy = BopItModel(bus, difficulty='easy')
        hard = BopItModel(bus, difficulty='hard')
        assert hard.TIME_STEP > easy.TIME_STEP

    def test_unknown_difficulty_falls_back_to_normal(self, bus):
        model  = BopItModel(bus, difficulty='nightmare')
        normal = BopItModel(bus, difficulty='normal')
        assert model.BASE_TIME == normal.BASE_TIME

    def test_all_presets_exist(self):
        for key in ('easy', 'normal', 'hard'):
            assert key in _DIFFICULTY_PRESETS


# ---------------------------------------------------------------------------
# Timer scaling still works correctly per difficulty
# ---------------------------------------------------------------------------

class TestDifficultyTimerScaling:
    def test_easy_time_limit_at_score_0(self, bus):
        model = BopItModel(bus, difficulty='easy')
        model.score = 0
        assert model.time_limit == model.BASE_TIME

    def test_easy_time_limit_decreases_with_score(self, bus):
        model = BopItModel(bus, difficulty='easy')
        model.score = 3
        assert model.time_limit == model.BASE_TIME - 3 * model.TIME_STEP

    def test_easy_time_limit_clamps_at_min(self, bus):
        model = BopItModel(bus, difficulty='easy')
        model.score = 1000
        assert model.time_limit == model.MIN_TIME

    def test_hard_time_limit_starts_lower_than_easy(self, bus):
        easy = BopItModel(bus, difficulty='easy')
        hard = BopItModel(bus, difficulty='hard')
        easy.score = 0
        hard.score = 0
        assert hard.time_limit < easy.time_limit

    def test_hard_reaches_floor_sooner_than_easy(self, bus):
        """Hard difficulty should hit MIN_TIME at a lower score than Easy."""
        easy = BopItModel(bus, difficulty='easy')
        hard = BopItModel(bus, difficulty='hard')

        # Find the score where each hits its floor
        def rounds_to_floor(m):
            for s in range(500):
                m.score = s
                if m.time_limit == m.MIN_TIME:
                    return s
            return 500

        assert rounds_to_floor(hard) < rounds_to_floor(easy)

    def test_round_delay_and_flash_time_scale_with_difficulty(self, bus):
        easy = BopItModel(bus, difficulty='easy')
        hard = BopItModel(bus, difficulty='hard')
        easy.score = 0
        hard.score = 0
        assert easy.round_delay > hard.round_delay
        assert easy.flash_time > hard.flash_time
