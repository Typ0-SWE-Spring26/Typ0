"""Tests for MusicMenu — covers built-in tracks, user-track sync, navigation,
and upload-button show/hide lifecycle."""
import os
import sys
from unittest.mock import MagicMock, Mock, patch, call

sys.modules["pygame"] = MagicMock()

from game.utils import animation_utils
from game_screens.menu_music import MusicMenu


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_menu():
    """Return a MusicMenu with a minimal mock screen and font manager."""
    screen = Mock()
    font_manager = Mock()
    # render_text returns a surface-like mock with a get_rect method
    surf = Mock()
    surf.get_rect.return_value = Mock()
    font_manager.render_text.return_value = surf
    return MusicMenu(screen, font_manager)


def _web_patches(track_count=0, names=None, urls=None):
    """Return a list of patches that simulate a web build with N user tracks."""
    names = names or [f"TRACK {i}" for i in range(track_count)]
    urls  = urls  or [f"blob:mock/{i}" for i in range(track_count)]
    return [
        patch.object(animation_utils, "_IS_WEB", True),
        patch.object(animation_utils, "get_user_track_count", return_value=track_count),
        patch.object(animation_utils, "get_user_track_name", side_effect=lambda i: names[i]),
        patch.object(animation_utils, "get_user_track_url",  side_effect=lambda i: urls[i]),
        patch.object(animation_utils, "show_upload_button"),
        patch.object(animation_utils, "hide_upload_button"),
    ]


# ── Initialisation ────────────────────────────────────────────────────────────

class TestMusicMenuInit:
    def test_has_three_builtin_songs(self):
        menu = _make_menu()
        assert len(menu._builtin_songs) == 3

    def test_builtin_songs_have_name_and_path(self):
        menu = _make_menu()
        for name, path in menu._builtin_songs:
            assert isinstance(name, str) and name
            assert isinstance(path, str) and path

    def test_songs_equals_builtin_songs_on_desktop(self):
        menu = _make_menu()
        assert menu.songs == list(menu._builtin_songs)

    def test_current_index_starts_at_zero(self):
        menu = _make_menu()
        assert menu.current_index == 0

    def test_upload_button_not_visible_initially(self):
        menu = _make_menu()
        assert menu._upload_btn_visible is False

    def test_no_user_songs_initially(self):
        menu = _make_menu()
        assert menu._user_songs == []


# ── _sync_user_tracks ─────────────────────────────────────────────────────────

class TestSyncUserTracks:
    def test_noop_on_desktop(self):
        menu = _make_menu()
        with patch.object(animation_utils, "_IS_WEB", False):
            menu._sync_user_tracks()
        assert menu._user_songs == []
        assert len(menu.songs) == 3

    def test_appends_user_tracks_after_builtins(self):
        menu = _make_menu()
        patches = _web_patches(track_count=2)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            menu._sync_user_tracks()
        assert len(menu.songs) == 5
        assert menu.songs[3][0] == "TRACK 0"
        assert menu.songs[4][0] == "TRACK 1"

    def test_user_track_urls_stored_correctly(self):
        menu = _make_menu()
        patches = _web_patches(track_count=1, urls=["blob:mock/abc"])
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            menu._sync_user_tracks()
        assert menu.songs[3][1] == "blob:mock/abc"

    def test_skips_tracks_with_empty_url(self):
        menu = _make_menu()
        with patch.object(animation_utils, "_IS_WEB", True), \
             patch.object(animation_utils, "get_user_track_count", return_value=2), \
             patch.object(animation_utils, "get_user_track_name", side_effect=["GOOD", "BAD"]), \
             patch.object(animation_utils, "get_user_track_url", side_effect=lambda index: "blob:ok" if index == 0 else ""):
            menu._sync_user_tracks()
        assert len(menu.songs) == 4  # only "GOOD" appended

    def test_clamps_current_index_when_list_shrinks(self):
        menu = _make_menu()
        # Start with 2 user tracks, navigate to last one (index 4)
        patches = _web_patches(track_count=2)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            menu._sync_user_tracks()
        menu.current_index = 4

        # Now re-sync with only 1 user track — index must be clamped to 3
        patches2 = _web_patches(track_count=1)
        with patches2[0], patches2[1], patches2[2], patches2[3], patches2[4], patches2[5]:
            menu._sync_user_tracks()
        assert menu.current_index == 3

    def test_replaces_stale_user_songs_on_each_sync(self):
        menu = _make_menu()
        patches = _web_patches(track_count=1, names=["FIRST"], urls=["blob:first"])
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            menu._sync_user_tracks()
        assert menu.songs[3][0] == "FIRST"

        patches2 = _web_patches(track_count=1, names=["SECOND"], urls=["blob:second"])
        with patches2[0], patches2[1], patches2[2], patches2[3], patches2[4], patches2[5]:
            menu._sync_user_tracks()
        assert menu.songs[3][0] == "SECOND"
        assert len(menu.songs) == 4


# ── Navigation ────────────────────────────────────────────────────────────────

def _make_event(button, pos=(0, 0)):
    """Build a mock MOUSEBUTTONDOWN event."""
    import pygame
    ev = Mock()
    ev.type = pygame.MOUSEBUTTONDOWN
    ev.button = button
    ev.pos = pos
    return ev


class TestNavigation:
    def test_right_arrow_increments_index(self):
        menu = _make_menu()
        menu.right_rect = Mock()
        menu.right_rect.collidepoint.return_value = True
        menu.back_rect  = Mock(); menu.back_rect.collidepoint.return_value = False
        menu.left_rect  = Mock(); menu.left_rect.collidepoint.return_value = False
        with patch.object(animation_utils, "play_music"):
            menu.handle_event(_make_event(1))
        assert menu.current_index == 1

    def test_left_arrow_decrements_index(self):
        menu = _make_menu()
        menu.current_index = 1
        menu.left_rect  = Mock(); menu.left_rect.collidepoint.return_value = True
        menu.right_rect = Mock(); menu.right_rect.collidepoint.return_value = False
        menu.back_rect  = Mock(); menu.back_rect.collidepoint.return_value = False
        with patch.object(animation_utils, "play_music"):
            menu.handle_event(_make_event(1))
        assert menu.current_index == 0

    def test_right_arrow_wraps_from_last_to_first(self):
        menu = _make_menu()
        menu.current_index = 2  # last builtin
        menu.right_rect = Mock(); menu.right_rect.collidepoint.return_value = True
        menu.back_rect  = Mock(); menu.back_rect.collidepoint.return_value = False
        menu.left_rect  = Mock(); menu.left_rect.collidepoint.return_value = False
        with patch.object(animation_utils, "play_music"):
            menu.handle_event(_make_event(1))
        assert menu.current_index == 0

    def test_left_arrow_wraps_from_first_to_last(self):
        menu = _make_menu()
        menu.current_index = 0
        menu.left_rect  = Mock(); menu.left_rect.collidepoint.return_value = True
        menu.right_rect = Mock(); menu.right_rect.collidepoint.return_value = False
        menu.back_rect  = Mock(); menu.back_rect.collidepoint.return_value = False
        with patch.object(animation_utils, "play_music"):
            menu.handle_event(_make_event(1))
        assert menu.current_index == 2

    def test_arrow_press_calls_play_music_with_current_path(self):
        menu = _make_menu()
        menu.right_rect = Mock(); menu.right_rect.collidepoint.return_value = True
        menu.back_rect  = Mock(); menu.back_rect.collidepoint.return_value = False
        menu.left_rect  = Mock(); menu.left_rect.collidepoint.return_value = False
        with patch.object(animation_utils, "play_music") as mock_play:
            menu.handle_event(_make_event(1))
        expected_path = menu.songs[menu.current_index][1]
        mock_play.assert_called_once_with(expected_path)


# ── Back button / upload button lifecycle ────────────────────────────────────

class TestUploadButtonLifecycle:
    def test_back_returns_back_string(self):
        menu = _make_menu()
        menu.back_rect  = Mock(); menu.back_rect.collidepoint.return_value = True
        menu.left_rect  = Mock(); menu.left_rect.collidepoint.return_value = False
        menu.right_rect = Mock(); menu.right_rect.collidepoint.return_value = False
        result = menu.handle_event(_make_event(1))
        assert result == "Back"

    def test_back_hides_upload_button_on_web(self):
        menu = _make_menu()
        menu._upload_btn_visible = True
        menu.back_rect  = Mock(); menu.back_rect.collidepoint.return_value = True
        menu.left_rect  = Mock(); menu.left_rect.collidepoint.return_value = False
        menu.right_rect = Mock(); menu.right_rect.collidepoint.return_value = False
        with patch.object(animation_utils, "_IS_WEB", True), \
             patch.object(animation_utils, "hide_upload_button") as mock_hide:
            menu.handle_event(_make_event(1))
        mock_hide.assert_called_once()
        assert menu._upload_btn_visible is False

    def test_back_does_not_call_hide_if_button_not_visible(self):
        menu = _make_menu()
        menu._upload_btn_visible = False
        menu.back_rect  = Mock(); menu.back_rect.collidepoint.return_value = True
        menu.left_rect  = Mock(); menu.left_rect.collidepoint.return_value = False
        menu.right_rect = Mock(); menu.right_rect.collidepoint.return_value = False
        with patch.object(animation_utils, "hide_upload_button") as mock_hide:
            menu.handle_event(_make_event(1))
        mock_hide.assert_not_called()

    def test_draw_shows_upload_button_first_time_on_web(self):
        menu = _make_menu()
        with patch.object(animation_utils, "_IS_WEB", True), \
             patch.object(animation_utils, "show_upload_button") as mock_show, \
             patch.object(animation_utils, "get_user_track_count", return_value=0):
            bg = Mock(); bg.centerx = 400; bg.centery = 300
            bg.top = 100; bg.bottom = 500
            menu.draw(bg)
        mock_show.assert_called_once()
        assert menu._upload_btn_visible is True

    def test_draw_does_not_show_button_again_on_subsequent_frames(self):
        menu = _make_menu()
        menu._upload_btn_visible = True  # already shown
        with patch.object(animation_utils, "_IS_WEB", True), \
             patch.object(animation_utils, "show_upload_button") as mock_show, \
             patch.object(animation_utils, "get_user_track_count", return_value=0):
            bg = Mock(); bg.centerx = 400; bg.centery = 300
            bg.top = 100; bg.bottom = 500
            menu.draw(bg)
        mock_show.assert_not_called()

    def test_draw_does_not_show_button_on_desktop(self):
        menu = _make_menu()
        with patch.object(animation_utils, "_IS_WEB", False), \
             patch.object(animation_utils, "show_upload_button") as mock_show:
            bg = Mock(); bg.centerx = 400; bg.centery = 300
            bg.top = 100; bg.bottom = 500
            menu.draw(bg)
        mock_show.assert_not_called()
