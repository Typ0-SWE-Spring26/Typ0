"""Given/When/Then steps for difficulty.feature."""
from unittest.mock import patch
from behave import given, when, then


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


# ---------------------------------------------------------------------------
# Given/When — Keys Ninja model setup
# ---------------------------------------------------------------------------

@given('a fresh Keys Ninja model with "{difficulty}" difficulty')
def step_fresh_ninja_model(ctx, difficulty):
    from unittest.mock import Mock
    from game.core.keys_ninja_model import KeysNinjaModel
    bus = Mock()
    bus.emit = Mock()
    ctx.ninja_model = KeysNinjaModel(bus, difficulty=difficulty)
    ctx.difficulty = difficulty


@given('a fresh Keys Ninja model with "{difficulty}" difficulty as "{alias}"')
def step_fresh_ninja_model_alias(ctx, difficulty, alias):
    from unittest.mock import Mock
    from game.core.keys_ninja_model import KeysNinjaModel
    bus = Mock()
    bus.emit = Mock()
    setattr(ctx, alias, KeysNinjaModel(bus, difficulty=difficulty))


@given('the Keys Ninja score is {n:d}')
def step_set_ninja_score(ctx, n):
    ctx.ninja_model.score = n


@given('both Keys Ninja models have score {n:d}')
def step_both_ninja_models_score(ctx, n):
    ctx.ninja_model.score = n
    # Find whichever named alias exists in this scenario.
    for alias in ('normal_ninja', 'hard_ninja', 'easy_ninja'):
        other = getattr(ctx, alias, None)
        if other is not None:
            other.score = n


@when('the Keys Ninja model is damaged and reset')
def step_damage_and_reset_ninja(ctx):
    ctx.ninja_model.lives = 0
    ctx.ninja_model.score = 500
    ctx.ninja_model.reset()


# ---------------------------------------------------------------------------
# Then — Keys Ninja difficulty assertions
# ---------------------------------------------------------------------------

@then('the Keys Ninja difficulty attribute should equal "{expected}"')
def step_ninja_difficulty_attr(ctx, expected):
    actual = ctx.ninja_model.difficulty
    assert actual == expected, f'Expected difficulty {expected!r}, got {actual!r}'


@then('the Keys Ninja easy starting lives should be greater than the normal starting lives')
def step_ninja_easy_lives_gt_normal(ctx):
    assert ctx.ninja_model.lives > ctx.normal_ninja.lives, (
        f'Easy lives {ctx.ninja_model.lives} not > Normal {ctx.normal_ninja.lives}'
    )


@then('the Keys Ninja hard starting lives should be less than the normal starting lives')
def step_ninja_hard_lives_lt_normal(ctx):
    assert ctx.ninja_model.lives < ctx.normal_ninja.lives, (
        f'Hard lives {ctx.ninja_model.lives} not < Normal {ctx.normal_ninja.lives}'
    )


@then('the Keys Ninja easy spawn interval should be greater than the hard spawn interval')
def step_ninja_easy_spawn_gt_hard(ctx):
    easy_iv = ctx.ninja_model._get_spawn_interval()
    hard_iv = ctx.hard_ninja._get_spawn_interval()
    assert easy_iv > hard_iv, (
        f'Easy spawn interval {easy_iv} not > Hard {hard_iv}'
    )


@then('the Keys Ninja hard speed multiplier should be greater than the easy speed multiplier')
def step_ninja_hard_speed_gt_easy(ctx):
    easy_speed = ctx.ninja_model._get_speed_multiplier()
    hard_speed = ctx.hard_ninja._get_speed_multiplier()
    assert hard_speed > easy_speed, (
        f'Hard speed {hard_speed} not > Easy {easy_speed}'
    )


@then('the Keys Ninja bomb chance should be 0')
def step_ninja_bomb_chance_zero(ctx):
    chance = ctx.ninja_model._get_bomb_chance()
    assert chance == 0.0, f'Expected bomb chance 0, got {chance}'


@then('the Keys Ninja hard bomb chance should be greater than 0')
def step_ninja_hard_bomb_gt_zero(ctx):
    chance = ctx.ninja_model._get_bomb_chance()
    assert chance > 0.0, f'Expected hard bomb chance > 0 at this score, got {chance}'


@then('the Keys Ninja normal bomb chance should be 0')
def step_ninja_normal_bomb_zero(ctx):
    chance = ctx.normal_ninja._get_bomb_chance()
    assert chance == 0.0, (
        f'Expected normal bomb chance 0 at this score, got {chance}'
    )


@then('the Keys Ninja speed multiplier should not exceed the hard speed cap')
def step_ninja_speed_within_cap(ctx):
    from game.core.keys_ninja_model import _DIFFICULTY_PRESETS
    cap = _DIFFICULTY_PRESETS['hard']['speed_cap']
    actual = ctx.ninja_model._get_speed_multiplier()
    assert actual <= cap, f'Speed multiplier {actual} exceeded cap {cap}'


@then('the Keys Ninja starting lives should equal the normal starting lives')
def step_ninja_lives_eq_normal(ctx):
    assert ctx.ninja_model.lives == ctx.normal_ninja.lives, (
        f'Expected lives {ctx.normal_ninja.lives}, got {ctx.ninja_model.lives}'
    )


@then('the Keys Ninja starting lives should equal the easy starting lives')
def step_ninja_lives_eq_easy(ctx):
    from game.core.keys_ninja_model import _DIFFICULTY_PRESETS
    expected = _DIFFICULTY_PRESETS['easy']['starting_lives']
    assert ctx.ninja_model.lives == expected, (
        f'Expected easy lives {expected}, got {ctx.ninja_model.lives}'
    )
