"""Tests for KeysNinjaModel difficulty presets and ConfigScreen keys_ninja mode.

Difficulty changes the model's starting lives, spawn cadence, fall speed, and
when bombs start appearing. The ConfigScreen needs to accept the keys_ninja
mode and hide the inverted toggle for it.
"""
import sys
from unittest.mock import MagicMock, Mock, patch

sys.modules["pygame"] = MagicMock()

import pytest

from game.core.keys_ninja_model import (
    KeysNinjaModel,
    _DIFFICULTY_PRESETS,
)


def _make(difficulty: str) -> KeysNinjaModel:
    bus = Mock()
    bus.emit = Mock()
    return KeysNinjaModel(bus, difficulty=difficulty)


# ── Preset shape ──────────────────────────────────────────────────────────

class TestPresetShape:
    """Every preset must define every key the model reads at runtime."""

    REQUIRED_KEYS = {
        "starting_lives",
        "spawn_base",
        "spawn_floor",
        "spawn_step_score",
        "speed_cap",
        "speed_per_point",
        "bomb_start_score",
        "bomb_chance",
    }

    @pytest.mark.parametrize("difficulty", ["easy", "normal", "hard"])
    def test_preset_has_all_keys(self, difficulty):
        assert set(_DIFFICULTY_PRESETS[difficulty]) == self.REQUIRED_KEYS

    def test_all_three_difficulties_present(self):
        assert set(_DIFFICULTY_PRESETS) == {"easy", "normal", "hard"}


# ── Starting lives ───────────────────────────────────────────────────────

class TestStartingLives:
    def test_easy_starts_with_more_lives_than_normal(self):
        assert _make("easy").lives > _make("normal").lives

    def test_hard_starts_with_fewer_lives_than_normal(self):
        assert _make("hard").lives < _make("normal").lives

    def test_normal_default_matches_explicit_normal(self):
        bus = Mock()
        assert KeysNinjaModel(bus).lives == _make("normal").lives


# ── Spawn cadence ────────────────────────────────────────────────────────

class TestSpawnInterval:
    def test_easy_spawns_slower_than_hard_at_score_zero(self):
        easy, hard = _make("easy"), _make("hard")
        assert easy._get_spawn_interval() > hard._get_spawn_interval()

    def test_easy_floor_higher_than_hard_floor(self):
        """Even at very high scores, Easy stays slower than Hard."""
        easy, hard = _make("easy"), _make("hard")
        easy.score = hard.score = 10_000
        assert easy._get_spawn_interval() > hard._get_spawn_interval()

    def test_spawn_interval_never_drops_below_floor(self):
        for diff in ("easy", "normal", "hard"):
            m = _make(diff)
            m.score = 100_000
            assert m._get_spawn_interval() >= _DIFFICULTY_PRESETS[diff]["spawn_floor"]

    def test_spawn_interval_decreases_with_score(self):
        for diff in ("easy", "normal", "hard"):
            m = _make(diff)
            m.score = 0
            base = m._get_spawn_interval()
            m.score = 500
            assert m._get_spawn_interval() < base


# ── Speed multiplier ─────────────────────────────────────────────────────

class TestSpeedMultiplier:
    def test_speed_starts_at_one_regardless_of_difficulty(self):
        for diff in ("easy", "normal", "hard"):
            assert _make(diff)._get_speed_multiplier() == pytest.approx(1.0)

    def test_easy_speed_cap_lower_than_hard(self):
        easy, hard = _make("easy"), _make("hard")
        easy.score = hard.score = 1_000_000
        assert easy._get_speed_multiplier() < hard._get_speed_multiplier()

    def test_speed_never_exceeds_cap(self):
        for diff in ("easy", "normal", "hard"):
            m = _make(diff)
            m.score = 1_000_000
            assert m._get_speed_multiplier() <= _DIFFICULTY_PRESETS[diff]["speed_cap"]

    def test_hard_ramps_speed_faster_than_easy(self):
        easy, hard = _make("easy"), _make("hard")
        easy.score = hard.score = 200
        assert hard._get_speed_multiplier() > easy._get_speed_multiplier()


# ── Bomb behavior ────────────────────────────────────────────────────────

class TestBombChance:
    def test_no_bombs_at_score_zero(self):
        for diff in ("easy", "normal", "hard"):
            assert _make(diff)._get_bomb_chance() == 0.0

    def test_easy_delays_bombs_past_normal_threshold(self):
        """At score 100 (normal's threshold), Easy still has no bombs."""
        easy = _make("easy")
        easy.score = 100
        assert easy._get_bomb_chance() == 0.0

    def test_hard_starts_bombs_before_normal(self):
        """Hard's bomb threshold is lower than normal's."""
        hard = _make("hard")
        hard.score = 50
        assert hard._get_bomb_chance() > 0.0
        normal = _make("normal")
        normal.score = 50
        assert normal._get_bomb_chance() == 0.0

    def test_hard_has_higher_bomb_rate_than_easy_when_active(self):
        easy, hard = _make("easy"), _make("hard")
        easy.score = hard.score = 1000  # well past every threshold
        assert hard._get_bomb_chance() > easy._get_bomb_chance()


# ── Difficulty fallback ──────────────────────────────────────────────────

class TestDifficultyFallback:
    def test_unknown_difficulty_falls_back_to_normal(self):
        bus = Mock()
        m = KeysNinjaModel(bus, difficulty="impossible")
        assert m.lives == _DIFFICULTY_PRESETS["normal"]["starting_lives"]
        assert m.difficulty == "normal"

    def test_difficulty_attribute_records_selection(self):
        for diff in ("easy", "normal", "hard"):
            assert _make(diff).difficulty == diff


# ── Reset preserves difficulty ───────────────────────────────────────────

class TestResetPreservesDifficulty:
    """A model reset must keep the chosen difficulty's preset values."""

    def test_reset_keeps_easy_lives(self):
        m = _make("easy")
        m.lives = 1  # simulate damage
        m.score = 500
        m.reset()
        assert m.lives == _DIFFICULTY_PRESETS["easy"]["starting_lives"]

    def test_reset_keeps_hard_lives(self):
        m = _make("hard")
        m.lives = 0
        m.reset()
        assert m.lives == _DIFFICULTY_PRESETS["hard"]["starting_lives"]


# ── ConfigScreen accepts keys_ninja ──────────────────────────────────────

class TestConfigScreenKeysNinjaMode:
    """ConfigScreen used to raise on keys_ninja; it must now construct cleanly
    and hide the inverted toggle for that mode."""

    def _make_screen(self):
        screen = Mock()
        screen.get_width.return_value = 800
        screen.get_height.return_value = 600
        return screen

    def _config(self, mode):
        with patch("game.screens.config_screen.FontManager") as MockFM:
            MockFM.return_value.get_font.return_value = Mock()
            from game.screens.config_screen import ConfigScreen
            return ConfigScreen(self._make_screen(), mode)

    def test_construct_with_keys_ninja_does_not_raise(self):
        cfg = self._config("keys_ninja")
        assert cfg.game_mode == "keys_ninja"

    def test_keys_ninja_hides_inverted_toggle(self):
        assert self._config("keys_ninja")._show_inverted_toggle is False

    def test_simon_still_shows_inverted_toggle(self):
        assert self._config("simon")._show_inverted_toggle is True

    def test_bopit_still_shows_inverted_toggle(self):
        assert self._config("bopit")._show_inverted_toggle is True
