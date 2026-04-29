from behave import given, when, then
from unittest.mock import Mock

from game.core.bopit_model import BopItModel


@given('a bopit model in input with command "{command}"')
def step_bopit_model(ctx, command):
    bus = Mock()
    bus.emit = Mock()
    ctx.model = BopItModel(bus)
    ctx.model.state = "input"
    ctx.model.current_command = command


@when('the player presses bopit input "{command}"')
def step_bopit_input(ctx, command):
    ctx.result = ctx.model.handle_input(command, now=1000)


@then('the bopit game should be over')
def step_bopit_game_over(ctx):
    assert ctx.model.state == "gameover", (
        f"Expected gameover, got {ctx.model.state}"
    )


@then('the bopit score should be at least {score:d}')
def step_bopit_score(ctx, score):
    assert ctx.model.score >= score, (
        f"Expected score >= {score}, got {ctx.model.score}"
    )
