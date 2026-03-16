"""Shared When steps for screen-level key presses and window events."""
import asyncio
from behave import when
from unittest.mock import Mock


def _make_key(pg, key):
    ev = Mock()
    ev.type = pg.KEYDOWN
    ev.key = key
    return ev


@when('the player presses ESC')
def step_press_esc(ctx):
    ctx.mock_pg.event.get.return_value = [_make_key(ctx.mock_pg, ctx.mock_pg.K_ESCAPE)]
    ctx.screen_result = asyncio.run(ctx.screen_obj.run())


@when('the player presses Q')
def step_press_q(ctx):
    ctx.mock_pg.event.get.return_value = [_make_key(ctx.mock_pg, ctx.mock_pg.K_q)]
    ctx.screen_result = asyncio.run(ctx.screen_obj.run())


@when('the player presses R')
def step_press_r(ctx):
    ctx.mock_pg.event.get.return_value = [_make_key(ctx.mock_pg, ctx.mock_pg.K_r)]
    ctx.screen_result = asyncio.run(ctx.screen_obj.run())


@when('the player presses C')
def step_press_c(ctx):
    ctx.mock_pg.event.get.return_value = [_make_key(ctx.mock_pg, ctx.mock_pg.K_c)]
    ctx.screen_result = asyncio.run(ctx.screen_obj.run())


@when('the player closes the window')
def step_close_window(ctx):
    ev = Mock()
    ev.type = ctx.mock_pg.QUIT
    ctx.mock_pg.event.get.return_value = [ev]
    ctx.screen_result = asyncio.run(ctx.screen_obj.run())
