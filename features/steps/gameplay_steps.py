"""When/Then steps for gameplay state machine scenarios."""
from unittest.mock import patch
from behave import when, then


@when('the player inputs "{button}"')
def step_player_input(ctx, button):
    ctx.model.handle_input(button, 0)


@when('the game updates')
def step_game_updates(ctx):
    """Advance the model once, mocking _rng.choice to return 'left'."""
    with patch.object(ctx.model._rng, 'choice', return_value='left'):
        ctx.model.update(10_000)  # 10 s — well past any pending _next_time


@then('the sequence length should be {n:d}')
def step_assert_sequence_length(ctx, n):
    assert len(ctx.model.sequence) == n, (
        f'Expected sequence length {n}, got {len(ctx.model.sequence)}'
    )
