"""Steps for credits screen feature scenarios."""
from behave import given, then
from unittest.mock import Mock, patch

# Imports deferred — pygame must be mocked first by environment.py


def _setup_credits_pg(mock_pg):
    mock_pg.time.Clock.return_value = Mock()
    mock_pg.time.get_ticks.return_value = 0
    mock_pg.QUIT = 256
    mock_pg.KEYDOWN = 768
    mock_pg.K_ESCAPE = 27
    mock_pg.K_q = 113
    mock_font = Mock()
    mock_font.render.return_value = Mock(get_rect=Mock(return_value=Mock()))
    mock_pg.font.Font.return_value = mock_font


@given('the credits data is loaded')
def step_credits_loaded(ctx):
    from game.screens.credits import CREDITS
    ctx.credits = CREDITS


@then('there should be at least {n:d} role entry')
@then('there should be at least {n:d} role entries')
def step_role_count(ctx, n):
    assert len(ctx.credits) >= n


@then('every role should have at least {n:d} name')
@then('every role should have at least {n:d} names')
def step_every_role_has_names(ctx, n):
    for role, names in ctx.credits:
        assert len(names) >= n, f'Role "{role}" has {len(names)} names'


@given('a credits screen is running')
def step_credits_running(ctx):
    ctx._credits_pg_patch = patch('game.screens.credits.pygame')
    ctx._credits_anim_patch = patch('game.screens.credits.animation_utils')
    ctx.mock_pg = ctx._credits_pg_patch.start()
    ctx.mock_anim = ctx._credits_anim_patch.start()
    _setup_credits_pg(ctx.mock_pg)

    ctx.mock_screen = Mock()
    ctx.mock_screen.get_width.return_value = 800
    ctx.mock_screen.get_height.return_value = 600

    from game.screens.credits import CreditsScreen
    ctx.screen_obj = CreditsScreen(ctx.mock_screen)



@then('the credits screen should return "{value}"')
def step_credits_returns(ctx, value):
    assert ctx.screen_result == value, (
        f'Expected "{value}", got "{ctx.screen_result}"'
    )
    ctx._credits_pg_patch.stop()
    ctx._credits_anim_patch.stop()
