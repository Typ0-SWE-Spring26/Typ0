"""Tests for the web-audio bridge in animation_utils.

The existing test_animation_utils.py covers the desktop (pygame.mixer) path.
These tests cover the web path (_IS_WEB=True) and the new functions added for
the JS bridge: pause_music, unpause_music, set_volume, get_volume, and the
user-upload helpers.
"""
import sys
from unittest.mock import MagicMock, Mock, patch, call

sys.modules["pygame"] = MagicMock()

from game.utils import animation_utils


# ── Helpers ───────────────────────────────────────────────────────────────────

def _web_ctx(typAudio=None):
    """Return a context manager that patches _IS_WEB=True and _p.window.typAudio."""
    mock_typAudio = typAudio or MagicMock()
    mock_p = MagicMock()
    mock_p.window.typAudio = mock_typAudio
    return (
        patch.object(animation_utils, "_IS_WEB", True),
        patch.object(animation_utils, "_p", mock_p),
        mock_typAudio,
    )


# ── _web_audio return-value contract ─────────────────────────────────────────

class TestWebAudioHelper:
    def test_returns_true_for_void_js_method(self):
        """void JS methods return Python None; _web_audio maps that to True."""
        mock_p = MagicMock()
        mock_p.window.typAudio.stopMusic.return_value = None
        with patch.object(animation_utils, "_p", mock_p):
            result = animation_utils._web_audio("stopMusic")
        assert result is True

    def test_returns_value_for_value_returning_js_method(self):
        mock_p = MagicMock()
        mock_p.window.typAudio.getVolume.return_value = 0.8
        with patch.object(animation_utils, "_p", mock_p):
            result = animation_utils._web_audio("getVolume")
        assert result == 0.8

    def test_returns_none_on_exception(self):
        mock_p = MagicMock()
        mock_p.window.typAudio.playMusic.side_effect = AttributeError("typAudio not ready")
        with patch.object(animation_utils, "_p", mock_p):
            result = animation_utils._web_audio("playMusic", "track.ogg", -1)
        assert result is None

    def test_passes_args_to_js_method(self):
        mock_p = MagicMock()
        mock_p.window.typAudio.playMusic.return_value = None
        with patch.object(animation_utils, "_p", mock_p):
            animation_utils._web_audio("playMusic", "theme.ogg", -1)
        mock_p.window.typAudio.playMusic.assert_called_once_with("theme.ogg", -1)


# ── play_music (web path) ─────────────────────────────────────────────────────

class TestPlayMusicWeb:
    def test_calls_js_playMusic_with_file_and_loops(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            typAudio.playMusic.return_value = None
            animation_utils.play_music("assets/theme.ogg", -1)
        typAudio.playMusic.assert_called_once_with("assets/theme.ogg", -1)

    def test_returns_true_on_success(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            typAudio.playMusic.return_value = None
            result = animation_utils.play_music("theme.ogg")
        assert result is True

    def test_returns_false_when_bridge_raises(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            typAudio.playMusic.side_effect = RuntimeError("bridge error")
            result = animation_utils.play_music("theme.ogg")
        assert result is False

    def test_uses_default_loops_minus_one(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            typAudio.playMusic.return_value = None
            animation_utils.play_music("theme.ogg")
        _, _, loops_arg = typAudio.playMusic.call_args[0] if len(typAudio.playMusic.call_args[0]) == 3 else (None, None, typAudio.playMusic.call_args[0][1])
        assert loops_arg == -1


# ── stop_music ────────────────────────────────────────────────────────────────

class TestStopMusic:
    def test_web_calls_js_stopMusic(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            animation_utils.stop_music()
        typAudio.stopMusic.assert_called_once()

    def test_desktop_skips_stop_when_mixer_not_init(self):
        with patch("game.utils.animation_utils.pygame") as mock_pg:
            mock_pg.mixer.get_init.return_value = False
            animation_utils.stop_music()
        mock_pg.mixer.music.stop.assert_not_called()

    def test_desktop_calls_stop_when_mixer_is_init(self):
        with patch("game.utils.animation_utils.pygame") as mock_pg:
            mock_pg.mixer.get_init.return_value = True
            animation_utils.stop_music()
        mock_pg.mixer.music.stop.assert_called_once()


# ── pause_music ───────────────────────────────────────────────────────────────

class TestPauseMusic:
    def test_web_calls_js_pauseMusic(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            animation_utils.pause_music()
        typAudio.pauseMusic.assert_called_once()

    def test_desktop_skips_pause_when_mixer_not_init(self):
        with patch("game.utils.animation_utils.pygame") as mock_pg:
            mock_pg.mixer.get_init.return_value = False
            animation_utils.pause_music()
        mock_pg.mixer.music.pause.assert_not_called()

    def test_desktop_calls_pause_when_mixer_is_init(self):
        with patch("game.utils.animation_utils.pygame") as mock_pg:
            mock_pg.mixer.get_init.return_value = True
            animation_utils.pause_music()
        mock_pg.mixer.music.pause.assert_called_once()


# ── unpause_music ─────────────────────────────────────────────────────────────

class TestUnpauseMusic:
    def test_web_calls_js_unpauseMusic(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            animation_utils.unpause_music()
        typAudio.unpauseMusic.assert_called_once()

    def test_desktop_skips_unpause_when_mixer_not_init(self):
        with patch("game.utils.animation_utils.pygame") as mock_pg:
            mock_pg.mixer.get_init.return_value = False
            animation_utils.unpause_music()
        mock_pg.mixer.music.unpause.assert_not_called()

    def test_desktop_calls_unpause_when_mixer_is_init(self):
        with patch("game.utils.animation_utils.pygame") as mock_pg:
            mock_pg.mixer.get_init.return_value = True
            animation_utils.unpause_music()
        mock_pg.mixer.music.unpause.assert_called_once()


# ── set_volume ────────────────────────────────────────────────────────────────

class TestSetVolume:
    def test_web_calls_js_setVolume(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            animation_utils.set_volume(0.6)
        typAudio.setVolume.assert_called_once_with(0.6)

    def test_desktop_skips_when_mixer_not_init(self):
        with patch("game.utils.animation_utils.pygame") as mock_pg:
            mock_pg.mixer.get_init.return_value = False
            animation_utils.set_volume(0.5)
        mock_pg.mixer.music.set_volume.assert_not_called()

    def test_desktop_calls_set_volume_when_mixer_is_init(self):
        with patch("game.utils.animation_utils.pygame") as mock_pg:
            mock_pg.mixer.get_init.return_value = True
            animation_utils.set_volume(0.5)
        mock_pg.mixer.music.set_volume.assert_called_once_with(0.5)


# ── get_volume ────────────────────────────────────────────────────────────────

class TestGetVolume:
    def test_web_returns_float_from_js(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            typAudio.getVolume.return_value = 0.75
            result = animation_utils.get_volume()
        assert result == 0.75
        assert isinstance(result, float)

    def test_web_falls_back_to_0_5_when_bridge_raises(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            typAudio.getVolume.side_effect = AttributeError("no typAudio")
            result = animation_utils.get_volume()
        assert result == 0.5

    def test_desktop_reads_from_mixer(self):
        with patch("game.utils.animation_utils.pygame") as mock_pg:
            mock_pg.mixer.get_init.return_value = True
            mock_pg.mixer.music.get_volume.return_value = 0.9
            result = animation_utils.get_volume()
        assert result == 0.9

    def test_desktop_falls_back_to_0_5_when_mixer_not_init(self):
        with patch("game.utils.animation_utils.pygame") as mock_pg:
            mock_pg.mixer.get_init.return_value = False
            result = animation_utils.get_volume()
        assert result == 0.5


# ── upload bridge helpers ─────────────────────────────────────────────────────

class TestUploadBridge:
    def test_show_upload_button_calls_js_on_web(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            animation_utils.show_upload_button()
        typAudio.showUploadButton.assert_called_once()

    def test_show_upload_button_is_noop_on_desktop(self):
        mock_p = MagicMock()
        with patch.object(animation_utils, "_IS_WEB", False), \
             patch.object(animation_utils, "_p", mock_p):
            animation_utils.show_upload_button()
        mock_p.window.typAudio.showUploadButton.assert_not_called()

    def test_hide_upload_button_calls_js_on_web(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            animation_utils.hide_upload_button()
        typAudio.hideUploadButton.assert_called_once()

    def test_get_user_track_count_returns_0_on_desktop(self):
        assert animation_utils.get_user_track_count() == 0

    def test_get_user_track_count_returns_int_from_js(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            typAudio.getUserTrackCount.return_value = 3
            result = animation_utils.get_user_track_count()
        assert result == 3

    def test_get_user_track_count_returns_0_on_bridge_failure(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            typAudio.getUserTrackCount.side_effect = RuntimeError("no bridge")
            result = animation_utils.get_user_track_count()
        assert result == 0

    def test_get_user_track_name_returns_empty_on_desktop(self):
        assert animation_utils.get_user_track_name(0) == ""

    def test_get_user_track_name_returns_string_from_js(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            typAudio.getUserTrackName.return_value = "MY TRACK"
            result = animation_utils.get_user_track_name(0)
        assert result == "MY TRACK"

    def test_get_user_track_url_returns_empty_on_desktop(self):
        assert animation_utils.get_user_track_url(0) == ""

    def test_get_user_track_url_returns_blob_url_from_js(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            typAudio.getUserTrackUrl.return_value = "blob:mock/abc"
            result = animation_utils.get_user_track_url(0)
        assert result == "blob:mock/abc"

    def test_get_user_track_url_passes_index_to_js(self):
        is_web, mock_p_patch, typAudio = _web_ctx()
        with is_web, mock_p_patch:
            typAudio.getUserTrackUrl.return_value = "blob:mock/2"
            animation_utils.get_user_track_url(2)
        typAudio.getUserTrackUrl.assert_called_once_with(2)
