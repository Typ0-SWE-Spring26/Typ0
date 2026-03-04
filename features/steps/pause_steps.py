"""Given/When steps for pause-behaviour scenarios."""
from behave import given, when


@given('the game is paused')
def step_game_paused(ctx):
    ctx.paused = True


@given('the game is not paused')
def step_game_not_paused(ctx):
    ctx.paused = False


@when('the player tries to input "{button}" while respecting the pause state')
def step_input_with_pause_guard(ctx, button):
    """Simulate the controller's guard: only forward input when not paused."""
    if not ctx.paused and ctx.model.state == 'input':
        ctx.model.handle_input(button, 0)
