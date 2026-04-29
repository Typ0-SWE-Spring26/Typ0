from behave import given, when, then
from unittest.mock import Mock, MagicMock, patch


def _make_click(pg):
    ev = Mock()
    ev.type = pg.MOUSEBUTTONDOWN
    ev.button = 1
    ev.pos = (0, 0)
    return ev


def _make_key(pg, key):
    ev = Mock()
    ev.type = pg.KEYDOWN
    ev.key = key
    return ev


@given('an open menu overlay for "{mode}"')
def step_open_menu_overlay(ctx, mode):
    import game.screens.menu as menu_mod

    mock_pg = MagicMock()
    mock_pg.MOUSEBUTTONDOWN = 1025
    mock_pg.KEYDOWN = 768
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


@when("the player clicks the menu close button")
def step_click_close(ctx):
    ctx.menu.close_rect = Mock(collidepoint=Mock(return_value=True))
    ctx.menu.volume_rect = Mock(collidepoint=Mock(return_value=False))
    ctx.menu.music_rect = Mock(collidepoint=Mock(return_value=False))
    ctx.menu.about_rect = Mock(collidepoint=Mock(return_value=False))
    ctx.menu.switch_rects = []
    ctx.menu._switch_targets = []
    ctx.menu.main_menu_rect = None

    ctx.result = ctx.menu.handle_event(_make_click(ctx.mock_pg))


@when("the player presses Escape")
def step_press_escape(ctx):
    ctx.result = ctx.menu.handle_event(_make_key(ctx.mock_pg, ctx.mock_pg.K_ESCAPE))


@when("the player chooses main menu")
def step_choose_main_menu(ctx):
    ctx.menu.main_menu_rect = Mock(collidepoint=Mock(return_value=True))
    ctx.menu.close_rect = Mock(collidepoint=Mock(return_value=False))
    ctx.menu.volume_rect = Mock(collidepoint=Mock(return_value=False))
    ctx.menu.music_rect = Mock(collidepoint=Mock(return_value=False))
    ctx.menu.about_rect = Mock(collidepoint=Mock(return_value=False))
    ctx.menu.switch_rects = []
    ctx.menu._switch_targets = []

    ctx.result = ctx.menu.handle_event(_make_click(ctx.mock_pg))


@then("the menu overlay should be closed")
def step_assert_closed(ctx):
    assert ctx.menu.open is False
    assert ctx.menu.active_submenu is None


@then('the menu overlay should return "{result}"')
def step_assert_return(ctx, result):
    assert ctx.result == result
