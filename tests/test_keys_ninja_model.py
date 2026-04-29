import sys
from unittest.mock import Mock, patch

sys.modules["pygame"] = Mock()

from game.core.keys_ninja_model import KeyObject, KeysNinjaModel


def _make_model():
    bus = Mock()
    bus.emit = Mock()
    model = KeysNinjaModel(bus)
    return model, bus


def test_handle_input_correct_key_updates_score_combo():
    model, bus = _make_model()
    key = KeyObject("A", 100, 100, is_bomb=False)
    key.state = "falling"
    model.keys = [key]

    result = model.handle_input("A", now=1000)

    assert result == "correct"
    assert model.score == 10
    assert model.combo == 1
    assert model.max_combo == 1
    assert key.state == "hit"
    bus.emit.assert_called_once_with("input_result", {"result": "correct", "name": "A"})


def test_handle_input_bomb_ends_game():
    model, bus = _make_model()
    key = KeyObject("B", 120, 120, is_bomb=True)
    key.state = "rising"
    model.keys = [key]

    result = model.handle_input("B", now=1100)

    assert result == "wrong"
    assert model.state == "gameover"
    assert model.lives == 0
    assert model.gameover_reason == "Hit a bomb!"
    bus.emit.assert_called_once_with("input_result", {"result": "wrong", "name": "B"})


def test_handle_input_wrong_key_resets_combo_only():
    model, _ = _make_model()
    key = KeyObject("C", 140, 140, is_bomb=False)
    key.state = "falling"
    model.keys = [key]
    model.combo = 3

    result = model.handle_input("Z", now=1200)

    assert result == "wrong"
    assert model.combo == 0
    assert model.state == "playing"


def test_update_missed_key_reduces_life_and_triggers_gameover():
    model, _ = _make_model()
    model.lives = 1
    key = KeyObject("D", 200, 1000, is_bomb=False)
    key.state = "falling"
    model.keys = [key]

    model.update(now=2000, screen_width=800, screen_height=600)

    assert model.state == "gameover"
    assert model.gameover_reason == "Out of lives!"


def test_bomb_chance_thresholds():
    model, _ = _make_model()

    model.score = 0
    assert model._get_bomb_chance() == 0.0

    model.score = 150
    assert model._get_bomb_chance() == 0.15


def test_handle_input_ignored_when_not_playing():
    model, bus = _make_model()
    model.state = "gameover"

    result = model.handle_input("A", now=1300)

    assert result == "wrong"
    bus.emit.assert_not_called()


def test_get_keys_per_spawn_thresholds():
    model, _ = _make_model()

    model.score = 0
    assert model._get_keys_per_spawn() == 1

    model.score = 100
    with patch("game.core.keys_ninja_model.random.choices", return_value=[2]):
        assert model._get_keys_per_spawn() == 2

    model.score = 250
    with patch("game.core.keys_ninja_model.random.choice", return_value=3):
        assert model._get_keys_per_spawn() == 3


def test_spawn_interval_constant():
    model, _ = _make_model()
    assert model._get_spawn_interval() == 2500


def test_update_does_not_spawn_when_max_keys():
    model, _ = _make_model()
    model.last_spawn_time = 0
    model.keys = [KeyObject("A", 100, 200) for _ in range(8)]

    model.update(now=3000, screen_width=800, screen_height=600)

    assert len(model.keys) == 8


def test_update_clears_flash_after_end_time():
    model, _ = _make_model()
    model.flash_button = "A"
    model.flash_state = "pressed"
    model.flash_end = 100

    model.update(now=1000, screen_width=800, screen_height=600)

    assert model.flash_button is None
    assert model.flash_state == "normal"
