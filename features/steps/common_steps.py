"""Shared Given steps and common Then steps used across all feature files."""
from behave import given, then


# ──────────────────────────────────────────────
# Given — model setup
# ──────────────────────────────────────────────

@given('a fresh game model')
def step_fresh_model(ctx):
    bus = ctx.EventBus()
    ctx.model = ctx.GameModel(bus)
    ctx.bus = bus
    ctx.paused = False


@given('the sequence is "{buttons}"')
def step_set_sequence(ctx, buttons):
    """Accept a single button name or comma-separated list, e.g. "left,right"."""
    ctx.model.sequence = [b.strip() for b in buttons.split(',')]
    ctx.model.player_index = 0


@given('the game is in {state} state')
def step_set_state(ctx, state):
    ctx.model.state = state


@given('the score is {n:d}')
def step_set_score(ctx, n):
    ctx.model.score = n


@given('all buttons have been shown')
def step_all_buttons_shown(ctx):
    ctx.model._show_index = len(ctx.model.sequence)


@given('the next action time has passed')
def step_next_time_passed(ctx):
    ctx.model._next_time = 0


# ──────────────────────────────────────────────
# Then — shared assertions
# ──────────────────────────────────────────────

@then('the game state should be "{state}"')
def step_assert_state(ctx, state):
    assert ctx.model.state == state, (
        f'Expected state "{state}", got "{ctx.model.state}"'
    )


@then('the player index should be {n:d}')
def step_assert_player_index(ctx, n):
    assert ctx.model.player_index == n, (
        f'Expected player_index {n}, got {ctx.model.player_index}'
    )


@then('the flash button should be "{button}"')
def step_assert_flash_button(ctx, button):
    assert ctx.model.flash_button == button, (
        f'Expected flash_button "{button}", got "{ctx.model.flash_button}"'
    )


@then('the flash button should be unset')
def step_assert_flash_unset(ctx):
    assert ctx.model.flash_button is None, (
        f'Expected flash_button to be None, got "{ctx.model.flash_button}"'
    )
