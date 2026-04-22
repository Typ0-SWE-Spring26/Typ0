import asyncio
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

sys.modules["pygame"] = MagicMock()


def run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


class _RectHit:
    def __init__(self, hit=False):
        self._hit = hit

    def collidepoint(self, _):
        return self._hit


@pytest.fixture
def htp_ctx():
    import game.screens.how_to_play as htp_mod

    mock_pg = MagicMock()
    mock_pg.QUIT = 256
    mock_pg.KEYDOWN = 768
    mock_pg.MOUSEBUTTONDOWN = 1025
    mock_pg.K_ESCAPE = 27
    mock_pg.K_q = 113
    mock_pg.time.Clock.return_value = Mock()

    mock_screen = Mock()
    mock_screen.get_width.return_value = 800
    mock_screen.get_height.return_value = 600

    mock_anim = MagicMock()

    mock_font_manager = Mock()
    surf = Mock()
    surf.get_rect.return_value = Mock()
    mock_font_manager.render_text.return_value = surf

    with patch.object(htp_mod, "pygame", mock_pg), \
         patch.object(htp_mod, "animation_utils", mock_anim), \
         patch.object(htp_mod, "FontManager", return_value=mock_font_manager):
        yield htp_mod, mock_pg, mock_screen


def test_escape_returns_back(htp_ctx):
    htp_mod, mock_pg, mock_screen = htp_ctx

    ev = Mock()
    ev.type = mock_pg.KEYDOWN
    ev.key = mock_pg.K_ESCAPE
    mock_pg.event.get.return_value = [ev]

    screen = htp_mod.HowToPlayScreen(mock_screen)
    assert run_async(screen.run()) == "back"


def test_click_credits_returns_credits(htp_ctx):
    htp_mod, mock_pg, mock_screen = htp_ctx

    ev = Mock()
    ev.type = mock_pg.MOUSEBUTTONDOWN
    ev.button = 1
    ev.pos = (100, 100)
    mock_pg.event.get.return_value = [ev]

    screen = htp_mod.HowToPlayScreen(mock_screen)
    screen._back_rect = _RectHit(hit=False)
    screen._credits_rect = _RectHit(hit=True)

    assert run_async(screen.run()) == "credits"


def test_quit_returns_quit(htp_ctx):
    htp_mod, mock_pg, mock_screen = htp_ctx

    ev = Mock()
    ev.type = mock_pg.QUIT
    mock_pg.event.get.return_value = [ev]

    screen = htp_mod.HowToPlayScreen(mock_screen)
    assert run_async(screen.run()) == "quit"
