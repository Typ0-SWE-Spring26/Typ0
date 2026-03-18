"""Steps for game over flow feature scenarios."""
import asyncio
from behave import given, when, then
from unittest.mock import Mock, patch

# Imports deferred — pygame must be mocked first by environment.py


def _setup_go_pg(mock_pg):
    mock_pg.time.Clock.return_value = Mock()
    mock_pg.time.get_ticks.return_value = 0
    mock_pg.QUIT = 256
    mock_pg.KEYDOWN = 768
    mock_pg.K_r = 114
    mock_pg.K_c = 99
    mock_pg.K_q = 113
    mock_pg.K_ESCAPE = 27
    mock_font = Mock()
    mock_font.render.return_value = Mock(get_rect=Mock(return_value=Mock()))
    mock_pg.font.Font.return_value = mock_font


def _make_key(pg, key):
    ev = Mock()
    ev.type = pg.KEYDOWN
    ev.key = key
    return ev


@given('a game over screen with score {score:d}')
def step_gameover_screen(ctx, score):
    ctx._go_pg_patch = patch('game.screens.gameover.pygame')
    ctx._go_anim_patch = patch('game.screens.gameover.animation_utils')
    ctx.mock_pg = ctx._go_pg_patch.start()
    ctx.mock_anim = ctx._go_anim_patch.start()
    _setup_go_pg(ctx.mock_pg)

    ctx.mock_screen = Mock()
    ctx.mock_screen.get_width.return_value = 800
    ctx.mock_screen.get_height.return_value = 600

    from game.screens.gameover import GameOverScreen
    ctx.screen_obj = GameOverScreen(ctx.mock_screen, score=score, reason="Wrong!")


@given('a high scores screen')
def step_hs_screen(ctx):
    ctx._hs_pg_patch = patch('game.screens.high_scores.pygame')
    ctx._hs_anim_patch = patch('game.screens.high_scores.animation_utils')
    ctx._hs_load_patch = patch('game.screens.high_scores.load_scores', return_value=[])
    ctx.mock_pg = ctx._hs_pg_patch.start()
    ctx.mock_anim = ctx._hs_anim_patch.start()
    ctx._hs_load_patch.start()
    _setup_go_pg(ctx.mock_pg)

    ctx.mock_screen = Mock()
    ctx.mock_screen.get_width.return_value = 800
    ctx.mock_screen.get_height.return_value = 600

    from game.screens.high_scores import HighScoresScreen
    ctx.screen_obj = HighScoresScreen(ctx.mock_screen)



@when('{n:d} seconds elapse with no input')
def step_time_elapses(ctx, n):
    ms = n * 1000
    tick_values = [0, ms + 1]
    call_count = [0]

    def get_ticks():
        if call_count[0] < len(tick_values):
            val = tick_values[call_count[0]]
            call_count[0] += 1
            return val
        return ms + 1

    ctx.mock_pg.time.get_ticks.side_effect = get_ticks
    ctx.mock_pg.event.get.return_value = []
    ctx.screen_result = asyncio.run(ctx.screen_obj.run())


@then('the game over screen should return "{value}"')
def step_gameover_returns(ctx, value):
    assert ctx.screen_result == value, (
        f'Expected "{value}", got "{ctx.screen_result}"'
    )


@then('the high scores screen should return "{value}"')
def step_hs_returns(ctx, value):
    assert ctx.screen_result == value, (
        f'Expected "{value}", got "{ctx.screen_result}"'
    )


@then('the auto-switch constant should be {n:d} milliseconds')
def step_auto_switch_constant(ctx, n):
    from game.screens.gameover import AUTO_SWITCH_MS
    assert AUTO_SWITCH_MS == n, f'Expected {n}, got {AUTO_SWITCH_MS}'
