"""Steps for browse_high_scores.feature."""
from unittest.mock import MagicMock, Mock, patch

from behave import given, when, then


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_screen():
    screen = Mock()
    screen.get_width.return_value = 800
    screen.get_height.return_value = 600
    screen.get_size.return_value = (800, 600)
    return screen


def _patched_pygame():
    """Build a pygame mock just rich enough for HighScoresScreen and MenuOverlay."""
    mock_pg = MagicMock()
    mock_pg.MOUSEBUTTONDOWN = 1
    mock_pg.KEYDOWN = 768
    mock_pg.K_ESCAPE = 27
    mock_pg.SRCALPHA = 1
    mock_pg.font.Font.return_value = Mock(
        render=Mock(return_value=Mock(get_rect=Mock(return_value=Mock())))
    )

    bg = Mock()
    bg.get_rect.return_value = Mock(centerx=400, centery=300,
                                    right=650, top=100, bottom=500)
    bg.convert_alpha.return_value = bg
    bg.copy.return_value = bg
    bg.get_size.return_value = (500, 400)
    mock_pg.image.load.return_value = bg
    mock_pg.transform.smoothscale.return_value = bg
    mock_pg.Surface.return_value = Mock()

    def make_rect(x, y, w, h):
        return Mock(
            x=x, y=y, width=w, height=h,
            center=(x + w // 2, y + h // 2),
            centerx=x + w // 2, centery=y + h // 2,
            bottom=y + h,
            collidepoint=Mock(return_value=False),
        )
    mock_pg.Rect.side_effect = make_rect
    return mock_pg


# ---------------------------------------------------------------------------
# Settings overlay setup
# ---------------------------------------------------------------------------

def _build_overlay(ctx, game_mode):
    mock_pg = _patched_pygame()
    ctx._bhs_pg_patch = patch("game.screens.menu.pygame", mock_pg)
    ctx._bhs_vol_patch = patch("game_screens.menu_volume.pygame")
    ctx._bhs_mus_patch = patch("game_screens.menu_music.pygame")
    ctx._bhs_fl_patch = patch("assets.font_loader.pygame")
    ctx._bhs_pg_patch.start()
    ctx._bhs_vol_patch.start()
    ctx._bhs_mus_patch.start()
    ctx._bhs_fl_patch.start()

    from game.screens.menu import MenuOverlay
    ctx.overlay = MenuOverlay(_mock_screen(), game_mode=game_mode)
    ctx.overlay_pg = mock_pg


@given('a Settings overlay opened from the start menu')
def step_overlay_start_menu(ctx):
    _build_overlay(ctx, game_mode=None)


@given('a Settings overlay opened during a "{mode}" run')
def step_overlay_in_game(ctx, mode):
    _build_overlay(ctx, game_mode=mode)


# ---------------------------------------------------------------------------
# Settings overlay assertions
# ---------------------------------------------------------------------------

@then('the overlay should have a high scores rect')
def step_has_hs_rect(ctx):
    assert getattr(ctx.overlay, "high_scores_rect", None) is not None


@when('the player clicks the HIGH SCORES button')
def step_click_hs(ctx):
    ctx.overlay.open = True
    ctx.overlay.high_scores_rect.collidepoint.return_value = True
    ev = Mock()
    ev.type = ctx.overlay_pg.MOUSEBUTTONDOWN
    ev.button = 1
    ev.pos = ctx.overlay.high_scores_rect.center
    ctx.overlay_action = ctx.overlay.handle_event(ev)


@then('the overlay should return "{action}"')
def step_overlay_returns(ctx, action):
    assert ctx.overlay_action == action, (
        f'Expected overlay action {action!r}, got {ctx.overlay_action!r}'
    )


@then('the overlay should be closed')
def step_overlay_closed(ctx):
    assert ctx.overlay.open is False, "overlay should be closed after the click"


# ---------------------------------------------------------------------------
# HighScoresScreen browse-mode setup
# ---------------------------------------------------------------------------

def _build_hs_screen(ctx, game_mode, difficulty="normal", browse_mode=False):
    mock_pg = _patched_pygame()
    ctx._bhs_hs_pg_patch = patch("game.screens.high_scores.pygame", mock_pg)
    ctx._bhs_hs_pg_patch.start()

    from game.screens.high_scores import HighScoresScreen
    ctx.hs_screen = HighScoresScreen(
        _mock_screen(),
        game_mode=game_mode,
        difficulty=difficulty,
        browse_mode=browse_mode,
    )
    ctx.hs_pg = mock_pg


@given('a high scores screen in browse mode for "{mode}"')
def step_hs_browse(ctx, mode):
    _build_hs_screen(ctx, game_mode=mode, browse_mode=True)


@given('a browse-mode high scores screen starting at "{mode}" "{difficulty}"')
def step_hs_browse_with_difficulty(ctx, mode, difficulty):
    _build_hs_screen(ctx, game_mode=mode, difficulty=difficulty, browse_mode=True)


@given('a high scores screen for "{mode}" "{difficulty}" after a run')
def step_hs_post_game(ctx, mode, difficulty):
    _build_hs_screen(ctx, game_mode=mode, difficulty=difficulty, browse_mode=False)


# ---------------------------------------------------------------------------
# HighScoresScreen browse-mode assertions
# ---------------------------------------------------------------------------

@then('the screen should expose a "{mode}" mode tab')
def step_screen_has_mode_tab(ctx, mode):
    tabs = ctx.hs_screen._build_mode_tabs()
    assert mode in tabs, f"expected {mode!r} mode tab, got {sorted(tabs)}"


@then('the screen should not expose a "{mode}" mode tab')
def step_screen_no_mode_tab(ctx, mode):
    tabs = ctx.hs_screen._build_mode_tabs()
    assert mode not in tabs, f"{mode!r} should not be a tab; got {sorted(tabs)}"


@then('the high scores screen should be in browse mode')
def step_screen_browse_mode_on(ctx):
    assert ctx.hs_screen.browse_mode is True


@then('the high scores screen should not be in browse mode')
def step_screen_browse_mode_off(ctx):
    assert ctx.hs_screen.browse_mode is False


@then('the resolved leaderboard ID should be "{expected}"')
def step_screen_leaderboard_id(ctx, expected):
    assert ctx.hs_screen.game_type == expected, (
        f'Expected leaderboard ID {expected!r}, got {ctx.hs_screen.game_type!r}'
    )
