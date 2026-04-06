"""Given/When/Then steps for difficulty.feature."""
from unittest.mock import patch
from behave import given, then


# ---------------------------------------------------------------------------
# Given — Simon model setup
# ---------------------------------------------------------------------------

@given('a fresh Simon game model with "{difficulty}" difficulty')
def step_fresh_simon_model(ctx, difficulty):
    bus = ctx.EventBus()
    ctx.model = ctx.GameModel(bus, difficulty=difficulty)
    ctx.bus = bus
    ctx.difficulty = difficulty


@given('a fresh Simon game model with "{difficulty}" difficulty as "{alias}"')
def step_fresh_simon_model_alias(ctx, difficulty, alias):
    bus = ctx.EventBus()
    setattr(ctx, alias, ctx.GameModel(bus, difficulty=difficulty))


# ---------------------------------------------------------------------------
# Given — Bop-It model setup
# ---------------------------------------------------------------------------

@given('a fresh Bop-It model with "{difficulty}" difficulty')
def step_fresh_bopit_model(ctx, difficulty):
    bus = ctx.EventBus()
    ctx.bopit_model = ctx.BopItModel(bus, difficulty=difficulty)
    ctx.difficulty = difficulty


@given('a fresh Bop-It model with "{difficulty}" difficulty as "{alias}"')
def step_fresh_bopit_model_alias(ctx, difficulty, alias):
    bus = ctx.EventBus()
    setattr(ctx, alias, ctx.BopItModel(bus, difficulty=difficulty))


@given('the Bop-It score is {n:d}')
def step_set_bopit_score(ctx, n):
    ctx.bopit_model.score = n


# ---------------------------------------------------------------------------
# Then — Simon difficulty assertions
# ---------------------------------------------------------------------------

@then('the Simon timer limit should equal the normal preset timer limit')
def step_simon_timer_equals_normal(ctx):
    from game.core.game_model import _DIFFICULTY_PRESETS
    expected = _DIFFICULTY_PRESETS['normal'][4]  # timer_limit index
    assert ctx.model.timer_limit == expected, (
        f'Expected timer_limit {expected}, got {ctx.model.timer_limit}'
    )


@then('the Simon flash time should equal the normal preset flash time')
def step_simon_flash_equals_normal(ctx):
    from game.core.game_model import _DIFFICULTY_PRESETS
    expected = _DIFFICULTY_PRESETS['normal'][0]  # flash_time index
    assert ctx.model._flash_time == expected, (
        f'Expected _flash_time {expected}, got {ctx.model._flash_time}'
    )


@then('the Simon easy timer limit should be greater than the normal timer limit')
def step_simon_easy_timer_gt_normal(ctx):
    assert ctx.model.timer_limit > ctx.normal_model.timer_limit, (
        f'Easy timer {ctx.model.timer_limit} not > Normal {ctx.normal_model.timer_limit}'
    )


@then('the Simon hard timer limit should be less than the normal timer limit')
def step_simon_hard_timer_lt_normal(ctx):
    assert ctx.model.timer_limit < ctx.normal_model.timer_limit, (
        f'Hard timer {ctx.model.timer_limit} not < Normal {ctx.normal_model.timer_limit}'
    )


@then('the Simon easy flash time should be greater than the hard flash time')
def step_simon_easy_flash_gt_hard(ctx):
    assert ctx.model._flash_time > ctx.hard_model._flash_time, (
        f'Easy flash {ctx.model._flash_time} not > Hard {ctx.hard_model._flash_time}'
    )


@then('the Simon easy post-round pause should be greater than the hard post-round pause')
def step_simon_easy_pause_gt_hard(ctx):
    assert ctx.model._post_round_pause > ctx.hard_model._post_round_pause, (
        f'Easy post-round {ctx.model._post_round_pause} not > Hard {ctx.hard_model._post_round_pause}'
    )


@then('the flash end time should match the "{difficulty}" flash time')
def step_flash_end_matches_difficulty(ctx, difficulty):
    from game.core.game_model import _DIFFICULTY_PRESETS
    flash_time = _DIFFICULTY_PRESETS[difficulty][0]
    # update() was called at t=10_000 (see gameplay_steps), flash_end = t + flash_time
    expected = 10_000 + flash_time
    assert ctx.model.flash_end == expected, (
        f'Expected flash_end {expected}, got {ctx.model.flash_end}'
    )


@then('the next action time should match the "{difficulty}" post-round pause')
def step_next_time_matches_post_round(ctx, difficulty):
    from game.core.game_model import _DIFFICULTY_PRESETS
    post_round = _DIFFICULTY_PRESETS[difficulty][3]
    # handle_input was called at t=0, _next_time = 0 + post_round
    expected = post_round
    assert ctx.model._next_time == expected, (
        f'Expected _next_time {expected}, got {ctx.model._next_time}'
    )


# ---------------------------------------------------------------------------
# Then — Bop-It difficulty assertions
# ---------------------------------------------------------------------------

@then('the Bop-It base time should equal the normal Bop-It preset base time')
def step_bopit_base_equals_normal(ctx):
    from game.core.bopit_model import _DIFFICULTY_PRESETS
    expected = _DIFFICULTY_PRESETS['normal'][0]  # BASE_TIME index
    assert ctx.bopit_model.BASE_TIME == expected, (
        f'Expected BASE_TIME {expected}, got {ctx.bopit_model.BASE_TIME}'
    )


@then('the Bop-It easy base time should be greater than the hard base time')
def step_bopit_easy_base_gt_hard(ctx):
    assert ctx.bopit_model.BASE_TIME > ctx.hard_bopit.BASE_TIME, (
        f'Easy BASE_TIME {ctx.bopit_model.BASE_TIME} not > Hard {ctx.hard_bopit.BASE_TIME}'
    )


@then('the Bop-It hard minimum time should be less than the easy minimum time')
def step_bopit_hard_min_lt_easy(ctx):
    assert ctx.hard_bopit.MIN_TIME < ctx.bopit_model.MIN_TIME, (
        f'Hard MIN_TIME {ctx.hard_bopit.MIN_TIME} not < Easy {ctx.bopit_model.MIN_TIME}'
    )


@then('the Bop-It time limit should be base minus 3 steps')
def step_bopit_time_limit_formula(ctx):
    m = ctx.bopit_model
    expected = m.BASE_TIME - 3 * m.TIME_STEP
    assert m.time_limit == expected, (
        f'Expected time_limit {expected}, got {m.time_limit}'
    )


@then('the Bop-It easy round delay should be greater than the hard round delay')
def step_bopit_easy_delay_gt_hard(ctx):
    easy_delay = ctx.bopit_model.round_delay
    hard_delay = ctx.hard_bopit.round_delay
    assert easy_delay > hard_delay, (
        f'Easy round_delay {easy_delay} not > Hard {hard_delay}'
    )
