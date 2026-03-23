from unittest.mock import patch

from game.core.bopit_model import BopItModel
from game.core.event_bus import EventBus


def test_time_limit_decreases_with_score_and_clamps():
    model = BopItModel(EventBus())

    model.score = 0
    assert model.time_limit == model.BASE_TIME

    model.score = 3
    assert model.time_limit == model.BASE_TIME - 3 * model.TIME_STEP

    model.score = 100
    assert model.time_limit == model.MIN_TIME


def test_round_delay_decreases_with_score_and_clamps():
    model = BopItModel(EventBus())

    model.score = 0
    assert model.round_delay == model.BASE_ROUND_DELAY

    model.score = 5
    assert model.round_delay == model.BASE_ROUND_DELAY - 5 * model.ROUND_DELAY_STEP

    model.score = 100
    assert model.round_delay == model.MIN_ROUND_DELAY


def test_flash_time_decreases_with_score_and_clamps():
    model = BopItModel(EventBus())

    model.score = 0
    assert model.flash_time == model.BASE_FLASH_TIME

    model.score = 4
    assert model.flash_time == model.BASE_FLASH_TIME - 4 * model.FLASH_TIME_STEP

    model.score = 100
    assert model.flash_time == model.MIN_FLASH_TIME


def test_round_complete_sets_next_time_using_scaled_delay():
    model = BopItModel(EventBus())
    model.state = 'input'
    model.current_command = 'left'

    now = 1_000
    result = model.handle_input('left', now)

    assert result == 'round_complete'
    assert model.state == 'prompting'
    assert model.score == 1
    assert model._next_time == now + model.round_delay


def test_prompt_to_input_uses_scaled_flash_time():
    model = BopItModel(EventBus())
    model.state = 'prompting'
    model._next_time = 0
    model.score = 6

    with patch('game.core.bopit_model.random.choice', return_value='right'):
        entered_input = model.update(2_000)

    assert entered_input is True
    assert model.state == 'input'
    assert model.current_command == 'right'
    assert model.flash_end == 2_000 + model.flash_time
