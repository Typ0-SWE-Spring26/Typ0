"""Steps for name entry screen feature scenarios."""
import asyncio
from behave import given, when, then
from unittest.mock import Mock, patch

# Imports deferred — pygame must be mocked first by environment.py


def _setup_name_pg(mock_pg):
    mock_pg.time.Clock.return_value = Mock()
    mock_pg.time.get_ticks.return_value = 0
    mock_pg.QUIT = 256
    mock_pg.KEYDOWN = 768
    mock_pg.K_UP = 273
    mock_pg.K_DOWN = 274
    mock_pg.K_LEFT = 276
    mock_pg.K_RIGHT = 275
    mock_pg.K_w = 119
    mock_pg.K_s = 115
    mock_pg.K_a = 97
    mock_pg.K_d = 100
    mock_pg.K_RETURN = 13
    mock_pg.K_SPACE = 32
    mock_font = Mock()
    mock_font.render.return_value = Mock(get_rect=Mock(return_value=Mock()))
    mock_pg.font.Font.return_value = mock_font
    mock_pg.draw = Mock()


def _make_key(pg, key):
    ev = Mock()
    ev.type = pg.KEYDOWN
    ev.key = key
    return ev


def _safe_stop(ctx, attr):
    patcher = getattr(ctx, attr, None)
    if patcher is None:
        return
    stop = getattr(patcher, "stop", None)
    if not callable(stop):
        return
    try:
        stop()
    except Exception:
        pass


@given('a name entry screen with score {score:d}')
def step_name_entry_screen(ctx, score):
    ctx._ne_pg_patch = patch('game.screens.name_entry.pygame')
    ctx._ne_anim_patch = patch('game.screens.name_entry.animation_utils')
    ctx.mock_pg = ctx._ne_pg_patch.start()
    ctx.mock_anim = ctx._ne_anim_patch.start()
    _setup_name_pg(ctx.mock_pg)

    ctx.mock_screen = Mock()
    ctx.mock_screen.get_width.return_value = 800
    ctx.mock_screen.get_height.return_value = 600

    ctx._pending_events = []

    from game.screens.name_entry import NameEntryScreen
    ctx.screen_obj = NameEntryScreen(ctx.mock_screen, score=score)


@when('the player confirms immediately')
def step_confirm(ctx):
    ctx._pending_events.append(_make_key(ctx.mock_pg, ctx.mock_pg.K_RETURN))


@when('the player scrolls up once')
def step_scroll_up(ctx):
    ctx._pending_events.append(_make_key(ctx.mock_pg, ctx.mock_pg.K_w))


@when('the player scrolls down once')
def step_scroll_down(ctx):
    ctx._pending_events.append(_make_key(ctx.mock_pg, ctx.mock_pg.K_s))


@when('the player moves cursor right')
def step_move_right(ctx):
    ctx._pending_events.append(_make_key(ctx.mock_pg, ctx.mock_pg.K_d))


@when('the player moves cursor left')
def step_move_left(ctx):
    ctx._pending_events.append(_make_key(ctx.mock_pg, ctx.mock_pg.K_a))


@when('the player moves cursor right {n:d} times')
def step_move_right_n(ctx, n):
    for _ in range(n):
        ctx._pending_events.append(_make_key(ctx.mock_pg, ctx.mock_pg.K_d))


def _run_pending(ctx):
    """Execute pending events one at a time then confirm."""
    events = list(ctx._pending_events)
    call_count = [0]

    def get_events():
        call_count[0] += 1
        if call_count[0] <= len(events):
            return [events[call_count[0] - 1]]
        return [_make_key(ctx.mock_pg, ctx.mock_pg.K_RETURN)]

    ctx.mock_pg.event.get.side_effect = get_events
    try:
        ctx.screen_result = asyncio.run(ctx.screen_obj.run())
    finally:
        _safe_stop(ctx, '_ne_pg_patch')
        _safe_stop(ctx, '_ne_anim_patch')


@then('the returned name should be "{name}"')
def step_returned_name(ctx, name):
    _run_pending(ctx)
    assert ctx.screen_result == name, f'Expected "{name}", got "{ctx.screen_result}"'


@then('the first letter should be "{letter}"')
def step_first_letter(ctx, letter):
    if not hasattr(ctx, 'screen_result'):
        _run_pending(ctx)
    assert ctx.screen_result[0] == letter, (
        f'Expected first letter "{letter}", got "{ctx.screen_result[0]}" in "{ctx.screen_result}"'
    )


@then('the second letter should be "{letter}"')
def step_second_letter(ctx, letter):
    if not hasattr(ctx, 'screen_result'):
        _run_pending(ctx)
    assert ctx.screen_result[1] == letter, (
        f'Expected second letter "{letter}", got "{ctx.screen_result[1]}" in "{ctx.screen_result}"'
    )


@then('the last letter should be "{letter}"')
def step_last_letter(ctx, letter):
    if not hasattr(ctx, 'screen_result'):
        _run_pending(ctx)
    assert ctx.screen_result[-1] == letter, (
        f'Expected last letter "{letter}", got "{ctx.screen_result[-1]}" in "{ctx.screen_result}"'
    )


@then('the name entry should return "{value}"')
def step_name_entry_returns(ctx, value):
    ev = Mock()
    ev.type = ctx.mock_pg.QUIT
    ctx.mock_pg.event.get.return_value = [ev]
    try:
        ctx.screen_result = asyncio.run(ctx.screen_obj.run())
        assert ctx.screen_result == value
    finally:
        _safe_stop(ctx, '_ne_pg_patch')
        _safe_stop(ctx, '_ne_anim_patch')
