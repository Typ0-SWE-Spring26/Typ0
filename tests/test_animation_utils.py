import sys
from unittest.mock import MagicMock, Mock, patch

sys.modules['pygame'] = MagicMock()

from game.utils import animation_utils


def _mock_screen(width=800, height=600):
    screen = Mock()
    screen.get_size.return_value = (width, height)
    screen.get_width.return_value = width
    screen.get_height.return_value = height
    return screen


def test_draw_gradient_uses_cache_for_same_size_and_colors():
    animation_utils._gradient_cache.clear()
    screen = _mock_screen(4, 4)

    with patch("game.utils.animation_utils.pygame") as mock_pg:
        gradient_surface = Mock()
        mock_pg.Surface.return_value.convert.return_value = gradient_surface

        animation_utils.draw_gradient(screen, (10, 20, 30), (0, 0, 0))
        first_line_calls = mock_pg.draw.line.call_count

        animation_utils.draw_gradient(screen, (10, 20, 30), (0, 0, 0))
        second_line_calls = mock_pg.draw.line.call_count

        assert first_line_calls == 4
        assert second_line_calls == first_line_calls
        assert screen.blit.call_count == 2


def test_wave_text_renders_each_character_and_blits():
    screen = _mock_screen()
    font = Mock()
    font.size.side_effect = lambda c: (10 if c else 0, 20)
    glyph = Mock()
    glyph.get_rect.return_value = Mock()
    font.render.return_value = glyph

    with patch("game.utils.animation_utils.pygame") as mock_pg:
        mock_pg.time.get_ticks.return_value = 0

        animation_utils.wave_text(screen, "ABC", position=(100, 200), font=font)

    assert font.render.call_count == 3
    assert screen.blit.call_count == 3


def test_flashing_text_uses_on_color_when_phase_is_even():
    screen = _mock_screen()
    font = Mock()
    rendered = Mock()
    rendered.get_rect.return_value = Mock()
    font.render.return_value = rendered

    with patch("game.utils.animation_utils.pygame") as mock_pg:
        mock_pg.time.get_ticks.return_value = 1000
        animation_utils.flashing_text(
            screen,
            "Press Start",
            color_on=(255, 255, 255),
            color_off=(10, 10, 10),
            flash_speed=500,
            font=font,
        )

    font.render.assert_called_once_with("Press Start", True, (255, 255, 255))


def test_flashing_text_uses_off_color_when_phase_is_odd():
    screen = _mock_screen()
    font = Mock()
    rendered = Mock()
    rendered.get_rect.return_value = Mock()
    font.render.return_value = rendered

    with patch("game.utils.animation_utils.pygame") as mock_pg:
        mock_pg.time.get_ticks.return_value = 501
        animation_utils.flashing_text(
            screen,
            "Press Start",
            color_on=(255, 255, 255),
            color_off=(10, 10, 10),
            flash_speed=500,
            font=font,
        )

    font.render.assert_called_once_with("Press Start", True, (10, 10, 10))


def test_loading_bar_returns_false_before_complete():
    screen = _mock_screen()
    with patch("game.utils.animation_utils.pygame") as mock_pg:
        mock_pg.time.get_ticks.return_value = 1200
        done = animation_utils.loading_bar(screen, start_time=1000, width=200, load_time=1000)

    assert done is False
    assert mock_pg.draw.rect.call_count == 2


def test_loading_bar_returns_true_when_complete():
    screen = _mock_screen()
    with patch("game.utils.animation_utils.pygame") as mock_pg:
        mock_pg.time.get_ticks.return_value = 6000
        done = animation_utils.loading_bar(screen, start_time=1000, width=200, load_time=1000)

    assert done is True


def test_play_music_success_returns_true_and_loops():
    with patch("game.utils.animation_utils.pygame") as mock_pg:
        ok = animation_utils.play_music("assets/startscreen.ogg")

    assert ok is True
    mock_pg.mixer.music.load.assert_called_once_with("assets/startscreen.ogg")
    mock_pg.mixer.music.play.assert_called_once_with(-1)


def test_play_music_failure_returns_false():
    with patch("game.utils.animation_utils.pygame") as mock_pg:
        mock_pg.error = RuntimeError
        mock_pg.mixer.music.load.side_effect = RuntimeError("bad file")

        ok = animation_utils.play_music("missing.ogg")

    assert ok is False


def test_stop_music_calls_mixer_stop():
    with patch("game.utils.animation_utils.pygame") as mock_pg:
        animation_utils.stop_music()

    mock_pg.mixer.music.stop.assert_called_once()


def test_play_sound_success_plays_once():
    animation_utils._sound_cache.clear()
    with patch("game.utils.animation_utils.pygame") as mock_pg:
        sound = Mock()
        mock_pg.mixer.Sound.return_value = sound

        animation_utils.play_sound("assets/click.wav")

    mock_pg.mixer.Sound.assert_called_once_with("assets/click.wav")
    sound.play.assert_called_once()


def test_play_sound_reuses_cached_sound_on_repeat_calls():
    animation_utils._sound_cache.clear()
    with patch("game.utils.animation_utils.pygame") as mock_pg:
        sound = Mock()
        mock_pg.mixer.Sound.return_value = sound

        animation_utils.play_sound("assets/click.wav")
        animation_utils.play_sound("assets/click.wav")
        animation_utils.play_sound("assets/click.wav")

    mock_pg.mixer.Sound.assert_called_once_with("assets/click.wav")
    assert sound.play.call_count == 3


def test_play_sound_failure_is_swallowed():
    animation_utils._sound_cache.clear()
    with patch("game.utils.animation_utils.pygame") as mock_pg:
        mock_pg.error = RuntimeError
        mock_pg.mixer.Sound.side_effect = RuntimeError("cannot load")

        animation_utils.play_sound("missing.wav")

    # Explicitly document expected behavior: failures are swallowed.
    assert True
    # Failed loads must not be cached, so subsequent calls retry.
    assert "missing.wav" not in animation_utils._sound_cache
