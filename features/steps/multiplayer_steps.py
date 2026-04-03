"""Step definitions for multiplayer.feature."""
from behave import given, when, then
from game.core.event_bus import EventBus
from game.core.game_model import GameModel
from game.core import settings_flags


def _advance_adding(model, ticks):
    model.state = 'adding'
    model._next_time = 0
    model.update(ticks)


# ── Background ───────────────────────────────────────────────────────────────

@given('two players with the same seed')
def step_two_players_same_seed(ctx):
    ctx.p1 = GameModel(EventBus(), seed=42)
    ctx.p2 = GameModel(EventBus(), seed=42)


# ── Sequence sync ─────────────────────────────────────────────────────────────

@when('both players advance through {n:d} rounds')
def step_both_advance(ctx, n):
    for i in range(n):
        t = (i + 1) * 10_000
        _advance_adding(ctx.p1, t)
        _advance_adding(ctx.p2, t)


@then('both sequences are identical')
def step_sequences_identical(ctx):
    assert ctx.p1.sequence == ctx.p2.sequence, (
        f'Sequences differ: {ctx.p1.sequence} vs {ctx.p2.sequence}'
    )


# ── Input / outcome ───────────────────────────────────────────────────────────

@given('both players are in input state with sequence "{buttons}"')
def step_both_in_input(ctx, buttons):
    seq = [b.strip() for b in buttons.split(',')]
    for p in (ctx.p1, ctx.p2):
        p.sequence = seq[:]
        p.player_index = 0
        p.state = 'input'


@when('player one inputs "{button}"')
def step_p1_input(ctx, button):
    ctx.p1.handle_input(button, 1000)


@when('player two inputs "{button}"')
def step_p2_input(ctx, button):
    ctx.p2.handle_input(button, 1000)


@then('player one is in gameover state')
def step_p1_gameover(ctx):
    assert ctx.p1.state == 'gameover', f'Expected gameover, got {ctx.p1.state}'


@then('player two is still playing')
def step_p2_still_playing(ctx):
    assert ctx.p2.state != 'gameover', f'Expected not gameover, got {ctx.p2.state}'


@then('player one score is {n:d}')
def step_p1_score(ctx, n):
    assert ctx.p1.score == n, f'Expected score {n}, got {ctx.p1.score}'


@then('player two score is {n:d}')
def step_p2_score(ctx, n):
    assert ctx.p2.score == n, f'Expected score {n}, got {ctx.p2.score}'


# ── Settings flags ────────────────────────────────────────────────────────────

@given('a settings flag with inverted keys enabled')
def step_flags_inverted(ctx):
    ctx.flags = settings_flags.encode(inverted_keys=True)


@given('a settings flag with default settings')
def step_flags_default(ctx):
    ctx.flags = settings_flags.encode()


@then('the decoded settings show inverted keys is true')
def step_decoded_inverted_true(ctx):
    decoded = settings_flags.decode(ctx.flags)
    assert decoded['inverted_keys'] is True, f'Expected True, got {decoded}'


@then('the decoded settings show inverted keys is false')
def step_decoded_inverted_false(ctx):
    decoded = settings_flags.decode(ctx.flags)
    assert decoded['inverted_keys'] is False, f'Expected False, got {decoded}'
