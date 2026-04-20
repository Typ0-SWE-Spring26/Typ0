import sys
import pytest
from unittest.mock import MagicMock, Mock, patch

sys.modules['pygame'] = MagicMock()

from game.screens.menu import MenuOverlay


@pytest.fixture
def menu_overlay():
    with patch("game.screens.menu.pygame") as mock_pg, \
         patch("game_screens.menu_volume.pygame") as mock_vol_pg, \
         patch("game_screens.menu_music.pygame") as mock_music_pg, \
         patch("assets.font_loader.pygame") as mock_font_pg:
        
        screen = Mock()
        screen.get_width.return_value = 800
        screen.get_height.return_value = 600
        screen.get_size.return_value = (800, 600)

        mock_font = Mock()
        mock_font.render.return_value = Mock(get_rect=Mock(return_value=Mock()))
        
        # Setup font mocking for all modules
        for pg_mock in [mock_pg, mock_vol_pg, mock_music_pg, mock_font_pg]:
            pg_mock.font.SysFont.return_value = mock_font
            pg_mock.font.Font.return_value = mock_font

        bg_image = Mock()
        bg_image.get_rect.return_value = Mock(centerx=400, centery=300, right=650, top=100, bottom=500)
        bg_image.convert_alpha.return_value = bg_image
        bg_image.copy.return_value = bg_image
        bg_image.get_size.return_value = (500, 400)

        mock_pg.image.load.return_value = bg_image
        mock_pg.transform.smoothscale.return_value = bg_image
        
        # Mock Rect for all pygame modules
        def make_rect(x, y, w, h):
            return Mock(
                x=x,
                y=y,
                width=w,
                height=h,
                center=(x + w // 2, y + h // 2),
                centerx=x + w // 2,
                centery=y + h // 2,
                bottom=y + h,
                collidepoint=Mock(return_value=False),
            )
        
        for pg_mock in [mock_pg, mock_vol_pg, mock_music_pg]:
            pg_mock.Rect.side_effect = make_rect
            pg_mock.MOUSEBUTTONDOWN = 1
            pg_mock.MOUSEBUTTONUP = 2
            pg_mock.MOUSEMOTION = 3
            pg_mock.MOUSEWHEEL = 4
            pg_mock.KEYDOWN = 768
            pg_mock.K_ESCAPE = 27
            pg_mock.SRCALPHA = 1
            pg_mock.Surface.return_value = Mock()
            pg_mock.draw.rect = Mock()
            pg_mock.draw.circle = Mock()
            pg_mock.mouse.get_pos.return_value = (0, 0)
            
            # Mock mixer for volume and music menus
            pg_mock.mixer.get_init.return_value = True
            pg_mock.mixer.music.get_volume.return_value = 0.5
            pg_mock.mixer.music.set_volume = Mock()
            pg_mock.mixer.music.load = Mock()
            pg_mock.mixer.music.play = Mock()

        overlay = MenuOverlay(screen)
        yield overlay, mock_pg, screen


def _mouse_event(mock_pg, pos, button=1):
    event = Mock()
    event.type = mock_pg.MOUSEBUTTONDOWN
    event.button = button
    event.pos = pos
    return event


def test_menu_starts_closed(menu_overlay):
    overlay, _, _ = menu_overlay
    assert overlay.open is False


def test_click_menu_toggles_open(menu_overlay):
    overlay, mock_pg, _ = menu_overlay
    overlay.button_rect.collidepoint.return_value = True

    result = overlay.handle_event(_mouse_event(mock_pg, (30, 540)))

    assert result is None
    assert overlay.open is True


def test_click_menu_twice_toggles_closed(menu_overlay):
    overlay, mock_pg, _ = menu_overlay
    overlay.button_rect.collidepoint.return_value = True

    overlay.handle_event(_mouse_event(mock_pg, (30, 540)))
    overlay.handle_event(_mouse_event(mock_pg, (30, 540)))

    assert overlay.open is False


def test_click_volume_opens_submenu_when_open(menu_overlay):
    overlay, mock_pg, _ = menu_overlay
    overlay.open = True
    overlay.volume_rect.collidepoint.return_value = True

    result = overlay.handle_event(_mouse_event(mock_pg, overlay.volume_rect.center))

    assert result is None
    assert overlay.active_submenu == "volume"
    assert overlay.open is False


def test_click_music_opens_submenu_when_open(menu_overlay):
    overlay, mock_pg, _ = menu_overlay
    overlay.open = True
    overlay.music_rect.collidepoint.return_value = True

    result = overlay.handle_event(_mouse_event(mock_pg, overlay.music_rect.center))

    assert result is None
    assert overlay.active_submenu == "music"
    assert overlay.open is False


def test_click_about_routes_to_how_to_play_when_open(menu_overlay):
    overlay, mock_pg, _ = menu_overlay
    overlay.open = True
    overlay.about_rect.collidepoint.return_value = True

    result = overlay.handle_event(_mouse_event(mock_pg, overlay.about_rect.center))

    assert result == "how_to_play"
    assert overlay.active_submenu is None
    assert overlay.open is False


def test_click_option_when_closed_returns_none(menu_overlay):
    overlay, mock_pg, _ = menu_overlay
    overlay.open = False
    overlay.volume_rect.collidepoint.return_value = True

    result = overlay.handle_event(_mouse_event(mock_pg, overlay.volume_rect.center))

    assert result is None


def test_non_left_click_does_nothing(menu_overlay):
    overlay, mock_pg, _ = menu_overlay
    overlay.button_rect.collidepoint.return_value = True

    result = overlay.handle_event(_mouse_event(mock_pg, (30, 540), button=3))

    assert result is None
    assert overlay.open is False