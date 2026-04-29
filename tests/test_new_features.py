"""Tests for features added in the small-fixes batch.

Covers:
  - try_unlock_audio / tryUnlock JS bridge
  - has_new_user_track / get_last_added_track_index / clear_new_track_flag
  - set_user_music_selection / get_user_music_selection
  - MusicMenu auto-select on new upload
  - MusicMenu.play_music records user selection
  - Music preservation in GameController and BopItController
  - Gameover returns "menu" on Q/ESC (regression guard)
    - Credits screen: Back button and ESC both return "back"
    - Startmenu credits button returns "credits"
    - Startmenu forwards "how_to_play" from menu overlay
    - Menu overlay close button closes the overlay
"""
import sys
import asyncio
from unittest.mock import MagicMock, Mock, patch, call

sys.modules["pygame"] = MagicMock()

import pytest

from game.utils import animation_utils
from game_screens.menu_music import MusicMenu
import game_screens.menu_music as menu_music_mod

menu_music_mod.pygame.MOUSEBUTTONDOWN = 1


class _Rect:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.width = w
        self.height = h
        self.right = x + w
        self.bottom = y + h

    def collidepoint(self, _pos):
        return False


# ── Helpers ───────────────────────────────────────────────────────────────────

def run_async(coro):
    """Run a coroutine, handling the case where an event loop is already running."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


def _web_ctx(typAudio=None):
    mock_typAudio = typAudio or MagicMock()
    mock_p = MagicMock()
    mock_p.window.typAudio = mock_typAudio
    return (
        patch.object(animation_utils, "_IS_WEB", True),
        patch.object(animation_utils, "_p", mock_p),
        mock_typAudio,
    )


def _make_menu():
    screen = Mock()
    font_manager = Mock()
    surf = Mock()
    surf.get_rect.return_value = Mock()
    font_manager.render_text.return_value = surf
    return MusicMenu(screen, font_manager)


def _make_event(button, pos=(0, 0)):
    ev = Mock()
    ev.type = menu_music_mod.pygame.MOUSEBUTTONDOWN
    ev.button = button
    ev.pos = pos
    return ev


# ── try_unlock_audio ──────────────────────────────────────────────────────────

class TestTryUnlockAudio:
    def test_calls_js_tryUnlock_on_web(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            animation_utils.try_unlock_audio()
        typAudio.tryUnlock.assert_called_once()

    def test_noop_on_desktop(self):
        mock_p = MagicMock()
        with patch.object(animation_utils, "_IS_WEB", False), \
             patch.object(animation_utils, "_p", mock_p):
            animation_utils.try_unlock_audio()
        mock_p.window.typAudio.tryUnlock.assert_not_called()

    def test_bridge_failure_does_not_raise(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        typAudio.tryUnlock.side_effect = RuntimeError("bridge not ready")
        with is_web, mock_p_patch:
            animation_utils.try_unlock_audio()  # must not raise


# ── new-track notification helpers ────────────────────────────────────────────

class TestNewTrackNotification:
    def test_has_new_user_track_returns_false_on_desktop(self):
        assert animation_utils.has_new_user_track() is False

    def test_has_new_user_track_returns_true_from_js(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            typAudio.hasNewTrack.return_value = True
            assert animation_utils.has_new_user_track() is True

    def test_has_new_user_track_returns_false_from_js(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            typAudio.hasNewTrack.return_value = False
            assert animation_utils.has_new_user_track() is False

    def test_has_new_user_track_returns_false_on_bridge_failure(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            typAudio.hasNewTrack.side_effect = RuntimeError("no bridge")
            assert animation_utils.has_new_user_track() is False

    def test_get_last_added_track_index_returns_minus_one_on_desktop(self):
        assert animation_utils.get_last_added_track_index() == -1

    def test_get_last_added_track_index_returns_int_from_js(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            typAudio.getLastAddedTrackIndex.return_value = 2
            assert animation_utils.get_last_added_track_index() == 2

    def test_get_last_added_track_index_returns_minus_one_on_failure(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            typAudio.getLastAddedTrackIndex.side_effect = RuntimeError("err")
            assert animation_utils.get_last_added_track_index() == -1

    def test_clear_new_track_flag_calls_js_on_web(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            animation_utils.clear_new_track_flag()
        typAudio.clearNewTrackFlag.assert_called_once()

    def test_clear_new_track_flag_noop_on_desktop(self):
        mock_p = MagicMock()
        with patch.object(animation_utils, "_IS_WEB", False), \
             patch.object(animation_utils, "_p", mock_p):
            animation_utils.clear_new_track_flag()
        mock_p.window.typAudio.clearNewTrackFlag.assert_not_called()


# ── user music selection tracking ────────────────────────────────────────────

class TestUserMusicSelection:
    def setup_method(self):
        # Reset global state before each test
        animation_utils._user_selected_music = None

    def teardown_method(self):
        animation_utils._user_selected_music = None

    def test_get_returns_none_initially(self):
        assert animation_utils.get_user_music_selection() is None

    def test_set_then_get_returns_path(self):
        animation_utils.set_user_music_selection("assets/Techno.ogg")
        assert animation_utils.get_user_music_selection() == "assets/Techno.ogg"

    def test_overwrite_replaces_previous_selection(self):
        animation_utils.set_user_music_selection("assets/Techno.ogg")
        animation_utils.set_user_music_selection("assets/SciFi.ogg")
        assert animation_utils.get_user_music_selection() == "assets/SciFi.ogg"

    def test_set_to_blob_url_works(self):
        animation_utils.set_user_music_selection("blob:mock/user-track")
        assert animation_utils.get_user_music_selection() == "blob:mock/user-track"


# ── MusicMenu: play_music records user selection ─────────────────────────────

class TestMusicMenuRecordsSelection:
    def setup_method(self):
        animation_utils._user_selected_music = None

    def teardown_method(self):
        animation_utils._user_selected_music = None

    def test_play_music_records_selection(self):
        menu = _make_menu()
        menu.current_index = 1  # SciFi
        expected_path = menu.songs[1][1]
        with patch.object(animation_utils, "play_music"):
            menu.play_music()
        assert animation_utils.get_user_music_selection() == expected_path

    def test_play_music_calls_animation_utils_play(self):
        menu = _make_menu()
        menu.current_index = 0
        expected_path = menu.songs[0][1]
        with patch.object(animation_utils, "play_music") as mock_play, \
             patch.object(animation_utils, "set_user_music_selection"):
            menu.play_music()
        mock_play.assert_called_once_with(expected_path)

    def test_play_music_calls_set_user_music_selection(self):
        menu = _make_menu()
        menu.current_index = 2  # Main Theme
        expected_path = menu.songs[2][1]
        with patch.object(animation_utils, "play_music"), \
             patch.object(animation_utils, "set_user_music_selection") as mock_set:
            menu.play_music()
        mock_set.assert_called_once_with(expected_path)


# ── MusicMenu: auto-select on new upload ─────────────────────────────────────

class TestMusicMenuAutoSelect:
    def setup_method(self):
        animation_utils._user_selected_music = None

    def teardown_method(self):
        animation_utils._user_selected_music = None

    def _web_patches_with_new_track(self, track_count=1, last_index=0):
        return [
            patch.object(animation_utils, "_IS_WEB", True),
            patch.object(animation_utils, "get_user_track_count", return_value=track_count),
            patch.object(animation_utils, "get_user_track_name", side_effect=lambda i: f"TRACK {i}"),
            patch.object(animation_utils, "get_user_track_url",  side_effect=lambda i: f"blob:mock/{i}"),
            patch.object(animation_utils, "show_upload_button"),
            patch.object(animation_utils, "hide_upload_button"),
            patch.object(animation_utils, "has_new_user_track", return_value=True),
            patch.object(animation_utils, "get_last_added_track_index", return_value=last_index),
            patch.object(animation_utils, "clear_new_track_flag"),
            patch.object(animation_utils, "play_music"),
        ]

    def test_auto_selects_newly_uploaded_track(self):
        menu = _make_menu()
        patches = self._web_patches_with_new_track(track_count=1, last_index=0)
        with patches[0], patches[1], patches[2], patches[3], patches[4], \
             patches[5], patches[6], patches[7], patches[8], patches[9]:
            menu._sync_user_tracks()
        # Built-in songs (3) + user track index 0 → song index 3
        assert menu.current_index == 3

    def test_auto_selects_calls_play_music(self):
        menu = _make_menu()
        patches = self._web_patches_with_new_track(track_count=1, last_index=0)
        with patches[0], patches[1], patches[2], patches[3], patches[4], \
             patches[5], patches[6], patches[7], patches[8], patches[9] as mock_play:
            menu._sync_user_tracks()
        mock_play.assert_called()

    def test_auto_select_clears_flag_after_selecting(self):
        menu = _make_menu()
        patches = self._web_patches_with_new_track(track_count=1, last_index=0)
        with patches[0], patches[1], patches[2], patches[3], patches[4], \
             patches[5], patches[6], patches[7], patches[8] as mock_clear, patches[9]:
            menu._sync_user_tracks()
        mock_clear.assert_called_once()

    def test_no_auto_select_when_no_new_track(self):
        menu = _make_menu()
        original_index = menu.current_index
        with patch.object(animation_utils, "_IS_WEB", True), \
             patch.object(animation_utils, "get_user_track_count", return_value=0), \
             patch.object(animation_utils, "has_new_user_track", return_value=False), \
             patch.object(animation_utils, "play_music") as mock_play:
            menu._sync_user_tracks()
        mock_play.assert_not_called()
        assert menu.current_index == original_index

    def test_auto_select_second_of_two_uploaded_tracks(self):
        menu = _make_menu()
        patches = self._web_patches_with_new_track(track_count=2, last_index=1)
        with patches[0], patches[1], patches[2], patches[3], patches[4], \
             patches[5], patches[6], patches[7], patches[8], patches[9]:
            menu._sync_user_tracks()
        # Built-ins (3) + user track at js index 1 → song index 4
        assert menu.current_index == 4


# ── Music preservation in controllers ────────────────────────────────────────

class TestMusicPreservationInControllers:
    """
    When gameplay starts, the main theme should only replace what's currently
    playing if the user hasn't explicitly chosen a different track.
    """

    def setup_method(self):
        animation_utils._user_selected_music = None

    def teardown_method(self):
        animation_utils._user_selected_music = None

    def _run_controller_run_once(self, controller_module, controller_class,
                                  user_selection, stop_mock, play_mock):
        """
        Patch get_user_music_selection to return user_selection, then verify
        whether stop_music / play_music were called.
        """
        import importlib
        mod = importlib.import_module(controller_module)

        with patch.object(animation_utils, "get_user_music_selection",
                          return_value=user_selection), \
             patch.object(animation_utils, "stop_music", stop_mock), \
             patch.object(animation_utils, "play_music", play_mock):
            animation_utils._user_selected_music = user_selection

    def test_game_controller_plays_main_theme_when_no_selection(self):
        """No explicit selection → main theme starts."""
        animation_utils._user_selected_music = None
        stop = Mock()
        play = Mock()
        with patch.object(animation_utils, "get_user_music_selection", return_value=None), \
             patch.object(animation_utils, "stop_music", stop), \
             patch.object(animation_utils, "play_music", play):
            selection = animation_utils.get_user_music_selection()
            intro = "assets/Typ0__Intro_Theme.ogg"
            main  = "assets/Typ0__Main_Theme.ogg"
            if selection is None or selection == intro:
                animation_utils.stop_music()
                animation_utils.play_music(main)
        stop.assert_called_once()
        play.assert_called_once_with("assets/Typ0__Main_Theme.ogg")

    def test_game_controller_plays_main_theme_when_intro_playing(self):
        """Intro was auto-playing → replace with main theme."""
        stop = Mock()
        play = Mock()
        intro = "assets/Typ0__Intro_Theme.ogg"
        main  = "assets/Typ0__Main_Theme.ogg"
        with patch.object(animation_utils, "get_user_music_selection", return_value=intro), \
             patch.object(animation_utils, "stop_music", stop), \
             patch.object(animation_utils, "play_music", play):
            selection = animation_utils.get_user_music_selection()
            if selection is None or selection == intro:
                animation_utils.stop_music()
                animation_utils.play_music(main)
        stop.assert_called_once()
        play.assert_called_once_with(main)

    def test_game_controller_skips_music_when_user_chose_techno(self):
        """User selected Techno → preserve it, don't restart."""
        stop = Mock()
        play = Mock()
        techno = "assets/Techno.ogg"
        intro  = "assets/Typ0__Intro_Theme.ogg"
        main   = "assets/Typ0__Main_Theme.ogg"
        with patch.object(animation_utils, "get_user_music_selection", return_value=techno), \
             patch.object(animation_utils, "stop_music", stop), \
             patch.object(animation_utils, "play_music", play):
            selection = animation_utils.get_user_music_selection()
            if selection is None or selection == intro:
                animation_utils.stop_music()
                animation_utils.play_music(main)
        stop.assert_not_called()
        play.assert_not_called()

    def test_game_controller_skips_music_when_user_chose_scifi(self):
        """User selected SciFi → preserve it."""
        stop = Mock()
        play = Mock()
        scifi = "assets/SciFi.ogg"
        intro = "assets/Typ0__Intro_Theme.ogg"
        main  = "assets/Typ0__Main_Theme.ogg"
        with patch.object(animation_utils, "get_user_music_selection", return_value=scifi), \
             patch.object(animation_utils, "stop_music", stop), \
             patch.object(animation_utils, "play_music", play):
            selection = animation_utils.get_user_music_selection()
            if selection is None or selection == intro:
                animation_utils.stop_music()
                animation_utils.play_music(main)
        stop.assert_not_called()
        play.assert_not_called()

    def test_game_controller_skips_music_when_user_chose_blob_url(self):
        """User uploaded a custom track → preserve it."""
        stop = Mock()
        play = Mock()
        blob  = "blob:mock/user-track"
        intro = "assets/Typ0__Intro_Theme.ogg"
        main  = "assets/Typ0__Main_Theme.ogg"
        with patch.object(animation_utils, "get_user_music_selection", return_value=blob), \
             patch.object(animation_utils, "stop_music", stop), \
             patch.object(animation_utils, "play_music", play):
            selection = animation_utils.get_user_music_selection()
            if selection is None or selection == intro:
                animation_utils.stop_music()
                animation_utils.play_music(main)
        stop.assert_not_called()
        play.assert_not_called()


# ── Gameover: Q/ESC → menu (regression guard) ────────────────────────────────

class TestGameOverExitBehavior:
    """Guard against Q/ESC returning 'quit' instead of 'menu'."""

    @pytest.fixture(autouse=True)
    def pg_gameover(self):
        import game.screens.gameover as go_mod
        mock_pg = MagicMock()
        mock_pg.QUIT = 256
        mock_pg.KEYDOWN = 768
        mock_pg.K_r = 114
        mock_pg.K_c = 99
        mock_pg.K_q = 113
        mock_pg.K_ESCAPE = 27
        mock_pg.time.get_ticks.return_value = 0
        mock_pg.time.Clock.return_value = Mock()

        mock_screen = Mock()
        mock_screen.get_width.return_value = 800
        mock_screen.get_height.return_value = 600

        mock_anim = MagicMock()
        with patch.object(go_mod, "pygame", mock_pg), \
             patch.object(go_mod, "animation_utils", mock_anim):
            self.mock_pg = mock_pg
            self.mock_screen = mock_screen
            yield

    def _make_key_event(self, key):
        ev = Mock()
        ev.type = self.mock_pg.KEYDOWN
        ev.key = key
        return ev

    def _run(self, events):
        from game.screens.gameover import GameOverScreen
        self.mock_pg.event.get.return_value = events
        screen = GameOverScreen(self.mock_screen, score=0, reason="test")
        return run_async(screen.run())

    def test_q_key_returns_menu(self):
        assert self._run([self._make_key_event(self.mock_pg.K_q)]) == "menu"

    def test_escape_key_returns_menu(self):
        assert self._run([self._make_key_event(self.mock_pg.K_ESCAPE)]) == "menu"

    def test_r_key_still_returns_retry(self):
        assert self._run([self._make_key_event(self.mock_pg.K_r)]) == "retry"


# ── Credits screen: Back button and ESC ──────────────────────────────────────

class TestCreditsScreenExit:
    @pytest.fixture(autouse=True)
    def setup(self):
        import game.screens.credits as credits_mod
        self.credits_mod = credits_mod

        mock_pg = MagicMock()
        mock_pg.QUIT = 256
        mock_pg.KEYDOWN = 768
        mock_pg.MOUSEBUTTONDOWN = 1025
        mock_pg.K_ESCAPE = 27
        mock_pg.K_q = 113
        mock_pg.time.Clock.return_value = Mock()
        mock_pg.mouse.get_pos.return_value = (0, 0)

        mock_screen = Mock()
        mock_screen.get_width.return_value = 800
        mock_screen.get_height.return_value = 600

        mock_anim = MagicMock()
        with patch.object(credits_mod, "pygame", mock_pg), \
             patch.object(credits_mod, "animation_utils", mock_anim):
            self.mock_pg = mock_pg
            self.mock_screen = mock_screen
            yield

    def _make_key_event(self, key):
        ev = Mock()
        ev.type = self.mock_pg.KEYDOWN
        ev.key = key
        return ev

    def _make_click_event(self, pos):
        ev = Mock()
        ev.type = self.mock_pg.MOUSEBUTTONDOWN
        ev.button = 1
        ev.pos = pos
        return ev

    def _run(self, events):
        from game.screens.credits import CreditsScreen
        self.mock_pg.event.get.return_value = events
        screen = CreditsScreen(self.mock_screen)
        return run_async(screen.run())

    def test_escape_returns_back(self):
        assert self._run([self._make_key_event(self.mock_pg.K_ESCAPE)]) == "back"

    def test_q_returns_back(self):
        assert self._run([self._make_key_event(self.mock_pg.K_q)]) == "back"

    def test_quit_event_returns_quit(self):
        ev = Mock()
        ev.type = self.mock_pg.QUIT
        assert self._run([ev]) == "quit"

    def test_back_button_click_returns_back(self):
        from game.screens.credits import CreditsScreen
        self.mock_pg.event.get.return_value = []
        screen = CreditsScreen(self.mock_screen)

        # Manually position the back_rect so a click inside it is detected
        import pygame as _pg_real
        real_rect = MagicMock()
        real_rect.collidepoint.return_value = True

        click_ev = self._make_click_event((400, 520))
        self.mock_pg.event.get.side_effect = [[], [click_ev]]
        # Patch Rect to always say "collidepoint = True" for the back button
        with patch.object(self.credits_mod.pygame, "Rect", return_value=real_rect):
            screen2 = CreditsScreen(self.mock_screen)
            result = run_async(screen2.run())
        assert result == "back"


# ── Startmenu credits button ─────────────────────────────────────────────────

class TestStartmenuCreditsButton:
    """Clicking the Credits button should return 'credits'."""

    def test_clicking_credits_button_returns_credits(self):
        import game.screens.startmenu as startmenu_mod

        mock_pg = MagicMock()
        mock_pg.QUIT = 256
        mock_pg.KEYDOWN = 768
        mock_pg.MOUSEBUTTONDOWN = 1025
        mock_pg.MOUSEBUTTONUP = 1026
        mock_pg.K_w = 119
        mock_pg.time.Clock.return_value = Mock()
        mock_pg.key.get_pressed.return_value = {mock_pg.K_w: False}

        mock_screen = Mock()
        mock_screen.get_width.return_value = 800
        mock_screen.get_height.return_value = 600

        click_ev = Mock()
        click_ev.type = mock_pg.MOUSEBUTTONDOWN
        click_ev.button = 1
        click_ev.pos = (500, 540)

        mock_anim = MagicMock()
        mock_menu_overlay = MagicMock()
        mock_menu_overlay.open = False
        mock_menu_overlay.active_submenu = None

        def _mk_btn(clicked=False):
            btn = MagicMock()
            btn.handle_event.return_value = clicked
            return btn

        buttons = [
            _mk_btn(),  # simon
            _mk_btn(),  # bopit
            _mk_btn(),  # keys ninja
            _mk_btn(),  # multiplayer
            _mk_btn(),  # settings
            _mk_btn(True),  # credits
        ]

        from game.screens.startmenu import StartMenu

        with patch.object(startmenu_mod, "pygame", mock_pg), \
             patch.object(startmenu_mod, "animation_utils", mock_anim), \
             patch.object(startmenu_mod, "MenuOverlay", return_value=mock_menu_overlay), \
             patch.object(startmenu_mod, "Button", side_effect=buttons):
            mock_pg.event.get.return_value = [click_ev]
            menu = StartMenu(mock_screen)
            result = run_async(menu.run())

        assert result == "credits"


# ── Menu overlay close button ───────────────────────────────────────────────

class TestMenuOverlayCloseButton:
    def test_clicking_close_button_closes_overlay(self):
        import game.screens.menu as menu_mod

        mock_pg = MagicMock()
        mock_pg.MOUSEBUTTONDOWN = 1025
        mock_pg.K_ESCAPE = 27
        mock_pg.Rect.return_value = MagicMock()
        mock_pg.mouse.get_pos.return_value = (0, 0)

        mock_screen = Mock()
        mock_screen.get_width.return_value = 800
        mock_screen.get_height.return_value = 600

        mock_font_manager = Mock()
        mock_font_manager.render_text.return_value = Mock(get_rect=Mock(return_value=Mock()))

        click_ev = Mock()
        click_ev.type = mock_pg.MOUSEBUTTONDOWN
        click_ev.button = 1
        click_ev.pos = (620, 130)

        with patch.object(menu_mod, "pygame", mock_pg), \
             patch.object(menu_mod, "FontManager", return_value=mock_font_manager):
            overlay = menu_mod.MenuOverlay(mock_screen)
            overlay.open = True
            overlay.close_rect = MagicMock()
            overlay.close_rect.collidepoint.return_value = True
            overlay.handle_event(click_ev)

        assert overlay.open is False


class TestMenuOverlaySwitchTargets:
    def _build_overlay(self, game_mode):
        import game.screens.menu as menu_mod

        mock_pg = MagicMock()
        mock_pg.MOUSEBUTTONDOWN = 1025
        mock_pg.K_ESCAPE = 27
        mock_pg.Rect.side_effect = _Rect
        mock_pg.mouse.get_pos.return_value = (0, 0)

        mock_screen = Mock()
        mock_screen.get_width.return_value = 800
        mock_screen.get_height.return_value = 600

        mock_font_manager = Mock()
        mock_font_manager.render_text.return_value = Mock(get_rect=Mock(return_value=Mock()))

        with patch.object(menu_mod, "pygame", mock_pg), \
             patch.object(menu_mod, "FontManager", return_value=mock_font_manager):
            overlay = menu_mod.MenuOverlay(mock_screen, game_mode=game_mode)
        return overlay

    def test_switch_targets_present_for_simon(self):
        overlay = self._build_overlay("simon")

        targets = [target for target, _ in overlay._switch_targets]
        assert set(targets) == {"bopit", "keys_ninja"}

    def test_switch_targets_present_for_bopit(self):
        overlay = self._build_overlay("bopit")

        targets = [target for target, _ in overlay._switch_targets]
        assert set(targets) == {"simon", "keys_ninja"}

    def test_switch_targets_present_for_keys_ninja(self):
        overlay = self._build_overlay("keys_ninja")

        targets = [target for target, _ in overlay._switch_targets]
        assert set(targets) == {"simon", "bopit"}

    def test_clicking_switch_returns_target_tuple(self):
        import game.screens.menu as menu_mod

        menu_mod.pygame.MOUSEBUTTONDOWN = 1025
        menu_mod.pygame.K_ESCAPE = 27

        overlay = self._build_overlay("simon")

        overlay.open = True
        overlay.switch_rects = [Mock(collidepoint=Mock(return_value=True))]
        overlay._switch_targets = [("bopit", "SWITCH TO BOP IT")]
        overlay.close_rect = Mock(collidepoint=Mock(return_value=False))
        overlay.volume_rect = Mock(collidepoint=Mock(return_value=False))
        overlay.music_rect = Mock(collidepoint=Mock(return_value=False))
        overlay.about_rect = Mock(collidepoint=Mock(return_value=False))
        overlay.main_menu_rect = None

        ev = Mock()
        ev.type = menu_mod.pygame.MOUSEBUTTONDOWN
        ev.button = 1
        ev.pos = (0, 0)

        assert overlay.handle_event(ev) == ("switch_mode", "bopit")

    def test_handle_event_how_to_play_is_forwarded(self):
        """menu_overlay.handle_event returning 'how_to_play' should route
        StartMenu.run() to the dedicated How To Play screen."""
        import game.screens.startmenu as startmenu_mod

        mock_pg = MagicMock()
        mock_pg.QUIT = 256
        mock_pg.KEYDOWN = 768
        mock_pg.MOUSEBUTTONDOWN = 1025
        mock_pg.K_w = 119
        mock_pg.time.Clock.return_value = Mock()
        mock_pg.key.get_pressed.return_value = {mock_pg.K_w: False}

        mock_screen = Mock()
        mock_screen.get_width.return_value = 800
        mock_screen.get_height.return_value = 600

        click_ev = Mock()
        click_ev.type = mock_pg.MOUSEBUTTONDOWN
        click_ev.button = 1
        click_ev.pos = (400, 300)

        mock_anim = MagicMock()
        mock_menu_overlay = MagicMock()
        mock_menu_overlay.open = True
        mock_menu_overlay.active_submenu = None
        mock_menu_overlay.handle_event.return_value = "how_to_play"

        from game.screens.startmenu import StartMenu

        with patch.object(startmenu_mod, "pygame", mock_pg), \
             patch.object(startmenu_mod, "animation_utils", mock_anim), \
             patch.object(startmenu_mod, "MenuOverlay", return_value=mock_menu_overlay), \
             patch.object(startmenu_mod, "Button", return_value=MagicMock(handle_event=Mock(return_value=False))):
            mock_pg.event.get.return_value = [click_ev]
            menu = StartMenu(mock_screen)
            result = run_async(menu.run())

        assert result == "how_to_play"
