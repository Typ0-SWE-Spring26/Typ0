"""When/Then steps for input-timer scenarios."""
from behave import when, then


@when('the timer expires')
def step_timer_expires(ctx):
    ctx.model.on_timer_expired({'now': 0})


@then('the gameover reason should be "{reason}"')
def step_assert_gameover_reason(ctx, reason):
    assert ctx.model.gameover_reason == reason, (
        f'Expected gameover reason "{reason}", got "{ctx.model.gameover_reason}"'
    )
