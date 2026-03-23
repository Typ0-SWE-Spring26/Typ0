import sys
import pytest
from unittest.mock import MagicMock, Mock, patch

sys.modules['pygame'] = MagicMock()

from game.screens.menu import MenuOverlay


@pytest.fixture
def menu_overlay():
    with patch("game.screens.menu.pygame") as mock_pg:
        screen = Mock()
        screen.get_width.return_value = 800
        screen.get_height.return_value = 600
        screen.get_size.return_value = (800, 600)

        mock_font = Mock()
        mock_font.render.return_value = Mock(get_rect=Mock(return_value=Mock()))
        mock_pg.font.SysFont.return_value = mock_font

        bg_image = Mock()
        bg_image.get_rect.return_value = Mock(
            centerx=400, centery=300,
            right=650, top=100, left=150, bottom=500,
        )
        bg_image.convert_alpha.return_value = bg_image

        mock_pg.image.load.return_value = bg_image
        mock_pg.transform.smoothscale.return_value = bg_image
        mock_pg.Rect.side_effect = lambda x, y, w, h: Mock(
            x=x,
            y=y,
            width=w,
            height=h,
            center=(x + w // 2, y + h // 2),
            collidepoint=Mock(return_value=False),
        )
        mock_pg.MOUSEBUTTONDOWN = 1
        mock_pg.SRCALPHA = 1
        mock_pg.Surface.return_value = Mock()

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


def test_click_about_returns_label_when_open(menu_overlay):
    overlay, mock_pg, _ = menu_overlay
    overlay.open = True
    overlay.about_rect.collidepoint.return_value = True

    result = overlay.handle_event(_mouse_event(mock_pg, overlay.about_rect.center))

    assert result == "credits"


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