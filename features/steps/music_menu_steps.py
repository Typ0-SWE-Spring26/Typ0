"""Steps for music menu feature scenarios."""
import sys
from behave import given, when, then
from unittest.mock import MagicMock, Mock, patch

sys.modules["pygame"] = MagicMock()

from game_screens.menu_music import MusicMenu


def _setup_music_pg(mock_pg):
    def make_rect(x, y, w, h):
        return Mock(
            x=x,
            y=y,
            width=w,
            height=h,
            center=(x + w // 2, y + h // 2),
            centerx=x + w // 2,
            centery=y + h // 2,
            top=y,
            bottom=y + h,
            collidepoint=Mock(return_value=False),
        )

    mock_pg.Rect.side_effect = make_rect
    mock_pg.MOUSEBUTTONDOWN = 1
    mock_pg.mouse.get_pos.return_value = (0, 0)
    mock_pg.draw.rect = Mock()


def _setup_music_context(ctx, is_web=False, uploaded_tracks=None):
    ctx._mm_pg_patch = patch("game_screens.menu_music.pygame")
    ctx._mm_anim_patch = patch("game_screens.menu_music.animation_utils")
    ctx.mock_pg = ctx._mm_pg_patch.start()
    ctx.mock_anim = ctx._mm_anim_patch.start()
    _setup_music_pg(ctx.mock_pg)

    ctx.mock_anim._IS_WEB = is_web
    ctx.uploaded_tracks = list(uploaded_tracks or [])
    ctx.mock_anim.get_user_track_count.side_effect = lambda: len(ctx.uploaded_tracks)
    ctx.mock_anim.get_user_track_name.side_effect = lambda index: ctx.uploaded_tracks[index]
    ctx.mock_anim.get_user_track_url.side_effect = lambda index: f"blob:music/{ctx.uploaded_tracks[index].lower().replace(' ', '-')}"
    ctx.mock_anim.show_upload_button = Mock()
    ctx.mock_anim.hide_upload_button = Mock()
    ctx.mock_anim.play_music = Mock()
    ctx.mock_anim.has_new_user_track.return_value = False
    ctx.mock_anim.get_last_added_track_index.return_value = -1

    ctx.screen = Mock()
    ctx.screen.blit = Mock()
    ctx.font_manager = Mock()
    rendered = Mock()
    rendered.get_rect.return_value = Mock()
    ctx.font_manager.render_text.return_value = rendered

    ctx.bg_rect = Mock(centerx=400, centery=300, top=100, bottom=500)
    ctx.menu = MusicMenu(ctx.screen, ctx.font_manager)


@given('a fresh music menu')
def step_fresh_music_menu(ctx):
    _setup_music_context(ctx, is_web=False)


@given('a web music menu')
def step_web_music_menu(ctx):
    _setup_music_context(ctx, is_web=True)


@given('a web music menu with uploaded tracks "{tracks}"')
def step_web_music_menu_with_tracks(ctx, tracks):
    uploaded_tracks = [track.strip() for track in tracks.split(',') if track.strip()]
    _setup_music_context(ctx, is_web=True, uploaded_tracks=uploaded_tracks)


@given('the current track index is {index:d}')
def step_current_track_index(ctx, index):
    ctx.menu.current_index = index


@given('the upload button is visible')
def step_upload_button_visible(ctx):
    ctx.menu._upload_btn_visible = True


@when('the music menu synchronizes uploaded tracks')
def step_sync_tracks(ctx):
    ctx.menu._sync_user_tracks()


@when('the uploaded tracks are replaced with "{tracks}"')
def step_replace_uploaded_tracks(ctx, tracks):
    ctx.uploaded_tracks = [track.strip() for track in tracks.split(',') if track.strip()]


@when('the music menu is drawn')
def step_draw_menu(ctx):
    ctx.menu.draw(ctx.bg_rect)


@when('the player clicks the back button')
def step_click_back(ctx):
    ctx.menu.back_rect.collidepoint.return_value = True
    ctx.menu.left_rect.collidepoint.return_value = False
    ctx.menu.right_rect.collidepoint.return_value = False
    event = Mock()
    event.type = ctx.mock_pg.MOUSEBUTTONDOWN
    event.button = 1
    event.pos = (0, 0)
    ctx.result = ctx.menu.handle_event(event)


@then('the menu should have {count:d} built-in tracks')
def step_builtin_count(ctx, count):
    assert len(ctx.menu._builtin_songs) == count, (
        f'Expected {count} built-in tracks, got {len(ctx.menu._builtin_songs)}'
    )


@then('the menu should have {count:d} tracks')
def step_track_count(ctx, count):
    assert len(ctx.menu.songs) == count, (
        f'Expected {count} tracks, got {len(ctx.menu.songs)}'
    )


@then('the current track should be "{name}"')
def step_current_track_name(ctx, name):
    assert ctx.menu.songs[ctx.menu.current_index][0] == name, (
        f'Expected current track "{name}", got "{ctx.menu.songs[ctx.menu.current_index][0]}"'
    )


@then('the track at position {position:d} should be "{name}"')
def step_track_name_at_position(ctx, position, name):
    assert ctx.menu.songs[position - 1][0] == name, (
        f'Expected track {position} to be "{name}", got "{ctx.menu.songs[position - 1][0]}"'
    )


@then('the current track index should be {index:d}')
def step_current_track_index_assert(ctx, index):
    assert ctx.menu.current_index == index, (
        f'Expected current track index {index}, got {ctx.menu.current_index}'
    )


@then('the upload button should be visible')
def step_upload_visible(ctx):
    assert ctx.menu._upload_btn_visible is True


@then('the upload button should be hidden')
def step_upload_hidden(ctx):
    assert ctx.menu._upload_btn_visible is False


@then('the music menu should return "{value}"')
def step_menu_return_value(ctx, value):
    assert ctx.result == value, f'Expected "{value}", got "{ctx.result}"'


@then('the upload helper should be called once')
def step_upload_helper_called(ctx):
    ctx.mock_anim.show_upload_button.assert_called_once()