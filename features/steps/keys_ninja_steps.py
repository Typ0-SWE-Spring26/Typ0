from behave import given, when, then
from unittest.mock import Mock

from game.core.keys_ninja_model import KeyObject, KeysNinjaModel


@given('a keys ninja model')
def step_keys_ninja_model(ctx):
    bus = Mock()
    bus.emit = Mock()
    ctx.bus = bus
    ctx.model = KeysNinjaModel(bus)


@given('a keys ninja model with 1 life')
def step_keys_ninja_model_one_life(ctx):
    bus = Mock()
    bus.emit = Mock()
    ctx.bus = bus
    ctx.model = KeysNinjaModel(bus)
    ctx.model.lives = 1


@given('a normal key "{char}" is on screen')
def step_normal_key_on_screen(ctx, char):
    key = KeyObject(char, 100, 100, is_bomb=False)
    key.state = "falling"
    ctx.model.keys = [key]


@given('the keys ninja combo is {combo:d}')
def step_set_combo(ctx, combo):
    ctx.model.combo = combo


@given('a bomb key "{char}" is on screen')
def step_bomb_key_on_screen(ctx, char):
    key = KeyObject(char, 120, 120, is_bomb=True)
    key.state = "rising"
    ctx.model.keys = [key]


@given('a normal key "{char}" has fallen off screen')
def step_key_fallen_off(ctx, char):
    key = KeyObject(char, 200, 1000, is_bomb=False)
    key.state = "falling"
    ctx.model.keys = [key]


@when('the player hits key "{char}"')
def step_player_hits_key(ctx, char):
    ctx.result = ctx.model.handle_input(char, now=1000)


@when('the keys ninja model updates')
def step_model_updates(ctx):
    ctx.model.update(now=2000, screen_width=800, screen_height=600)


@then('the keys ninja score should be {score:d}')
def step_score_should_be(ctx, score):
    assert ctx.model.score == score, (
        f"Expected score {score}, got {ctx.model.score}"
    )


@then('the keys ninja combo should be {combo:d}')
def step_combo_should_be(ctx, combo):
    assert ctx.model.combo == combo, (
        f"Expected combo {combo}, got {ctx.model.combo}"
    )


@then('the keys ninja game should be over with reason "{reason}"')
def step_game_over_reason(ctx, reason):
    assert ctx.model.state == "gameover", (
        f"Expected gameover, got {ctx.model.state}"
    )
    assert ctx.model.gameover_reason == reason, (
        f"Expected reason '{reason}', got '{ctx.model.gameover_reason}'"
    )


@then('the keys ninja state should be "{state}"')
def step_state_should_be(ctx, state):
    assert ctx.model.state == state, (
        f"Expected state '{state}', got '{ctx.model.state}'"
    )
