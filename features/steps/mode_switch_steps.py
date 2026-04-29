from behave import given, when, then
from unittest.mock import Mock, MagicMock, patch


def _make_event(pg):
    ev = Mock()
    ev.type = pg.MOUSEBUTTONDOWN
    ev.button = 1
    ev.pos = (0, 0)
    return ev


@given('a menu overlay for "{mode}"')
def step_menu_overlay(ctx, mode):
    import game.screens.menu as menu_mod

    mock_pg = MagicMock()
    mock_pg.MOUSEBUTTONDOWN = 1025
    mock_pg.K_ESCAPE = 27
    mock_pg.Rect.return_value = Mock(collidepoint=Mock(return_value=False))
    mock_pg.mouse.get_pos.return_value = (0, 0)

    mock_screen = Mock()
    mock_screen.get_width.return_value = 800
    mock_screen.get_height.return_value = 600

    mock_font_manager = Mock()
    mock_font_manager.render_text.return_value = Mock(get_rect=Mock(return_value=Mock()))

    ctx._menu_pg_patch = patch.object(menu_mod, "pygame", mock_pg)
    ctx._menu_fm_patch = patch.object(menu_mod, "FontManager", return_value=mock_font_manager)

    ctx.mock_pg = ctx._menu_pg_patch.start()
    ctx._menu_fm_patch.start()

    ctx.menu = menu_mod.MenuOverlay(mock_screen, game_mode=mode)
    ctx.menu.open = True


@when('the player chooses to switch to "{target}"')
def step_choose_switch(ctx, target):
    ctx.menu.switch_rects = [Mock(collidepoint=Mock(return_value=True))]
    ctx.menu._switch_targets = [(target, "SWITCH")]
    ctx.menu.close_rect = Mock(collidepoint=Mock(return_value=False))
    ctx.menu.volume_rect = Mock(collidepoint=Mock(return_value=False))
    ctx.menu.music_rect = Mock(collidepoint=Mock(return_value=False))
    ctx.menu.about_rect = Mock(collidepoint=Mock(return_value=False))
    ctx.menu.main_menu_rect = None

    ev = _make_event(ctx.mock_pg)
    ctx.result = ctx.menu.handle_event(ev)


@then('the menu overlay should return switch result for "{target}"')
def step_assert_switch_result(ctx, target):
    assert ctx.result == ("switch_mode", target), (
        f"Expected ('switch_mode', '{target}'), got {ctx.result}"
    )
