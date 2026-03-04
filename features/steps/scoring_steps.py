"""When/Then steps for scoring scenarios."""
from behave import when, then


@when('the model is reset')
def step_model_reset(ctx):
    ctx.model.reset()


@then('the score should be {n:d}')
def step_assert_score(ctx, n):
    assert ctx.model.score == n, (
        f'Expected score {n}, got {ctx.model.score}'
    )
