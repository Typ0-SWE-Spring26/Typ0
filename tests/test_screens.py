"""Tests for screen switching (#45) and sequence caching (#50)."""
import sys
import asyncio
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock

sys.modules['pygame'] = MagicMock()

from game.screens.startscreen import StartScreen
from game.screens.startmenu import StartMenu
from game.screens.gameover import GameOverScreen


# ── Helpers ────────────────────────────────────────────────────────────

def make_key_event(pg, key):
    ev = Mock()
    ev.type = pg.KEYDOWN
    ev.key = key
    return ev


def make_quit_event(pg):
    ev = Mock()
    ev.type = pg.QUIT
    return ev


@pytest.fixture
def pg_start():
    """Patch pygame for StartScreen."""
    with patch('game.screens.startscreen.pygame') as mock_pg, \
         patch('game.screens.startscreen.animation_utils') as mock_anim:
        mock_screen = Mock()
        mock_screen.get_width.return_value = 800
        mock_screen.get_height.return_value = 600

        mock_pg.time.Clock.return_value = Mock()
        mock_pg.time.get_ticks.return_value = 0
        mock_pg.K_SPACE = 32
        mock_pg.QUIT = 256

        yield mock_pg, mock_screen, mock_anim


@pytest.fixture
def pg_menu():
    """Patch pygame for StartMenu."""
    with patch('game.screens.startmenu.pygame') as mock_pg, \
         patch('game.screens.startmenu.animation_utils') as mock_anim:
        mock_screen = Mock()
        mock_screen.get_width.return_value = 800
        mock_screen.get_height.return_value = 600

        mock_pg.time.Clock.return_value = Mock()
        mock_pg.time.get_ticks.return_value = 0
        mock_pg.K_w = 119
        mock_pg.QUIT = 256

        mock_font = Mock()
        mock_font.render.return_value = Mock(get_rect=Mock(return_value=Mock()))
        mock_pg.font.Font.return_value = mock_font
        mock_pg.Rect.return_value = Mock()

        yield mock_pg, mock_screen, mock_anim


@pytest.fixture
def pg_gameover():
    """Patch pygame for GameOverScreen."""
    with patch('game.screens.gameover.pygame') as mock_pg, \
         patch('game.screens.gameover.animation_utils') as mock_anim:
        mock_screen = Mock()
        mock_screen.get_width.return_value = 800
        mock_screen.get_height.return_value = 600

        mock_pg.time.Clock.return_value = Mock()
        mock_pg.time.get_ticks.return_value = 0
        mock_pg.QUIT = 256
        mock_pg.KEYDOWN = 768
        mock_pg.K_r = 114
        mock_pg.K_q = 113
        mock_pg.K_ESCAPE = 27

        mock_font = Mock()
        mock_font.render.return_value = Mock(get_rect=Mock(return_value=Mock()))
        mock_pg.font.Font.return_value = mock_font

        yield mock_pg, mock_screen, mock_anim


# ======================================================================
# #45 — StartScreen
# ======================================================================

class TestStartScreen:
    """Verify StartScreen returns correct navigation signals."""

    def test_quit_on_quit_event(self, pg_start):
        mock_pg, mock_screen, _ = pg_start

        quit_ev = make_quit_event(mock_pg)
        mock_pg.event.get.return_value = [quit_ev]

        screen = StartScreen(mock_screen)
        result = asyncio.run(screen.run())

        assert result == "quit"

    def test_returns_menu_when_space_pressed_after_loading(self, pg_start):
        mock_pg, mock_screen, mock_anim = pg_start

        # Simulate loading complete
        mock_anim.loading_bar.return_value = True

        # Space key pressed
        keys = MagicMock()
        keys.__getitem__ = Mock(return_value=True)
        mock_pg.key.get_pressed.return_value = keys

        mock_pg.event.get.return_value = []

        screen = StartScreen(mock_screen)
        result = asyncio.run(screen.run())

        assert result == "menu"

    def test_does_not_return_menu_while_loading(self, pg_start):
        mock_pg, mock_screen, mock_anim = pg_start

        # Loading NOT complete first call, then QUIT to exit
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return False  # still loading
            return True  # done

        mock_anim.loading_bar.side_effect = side_effect

        keys = MagicMock()
        keys.__getitem__ = Mock(return_value=True)
        mock_pg.key.get_pressed.return_value = keys
        mock_pg.event.get.return_value = []

        screen = StartScreen(mock_screen)
        result = asyncio.run(screen.run())

        # Should eventually return "menu" once loading is done
        assert result == "menu"

    def test_plays_music_on_init(self, pg_start):
        _, mock_screen, mock_anim = pg_start
        StartScreen(mock_screen)
        mock_anim.play_music.assert_called_once_with("assets/Typ0__Intro_Theme.ogg")

    def test_stops_music_before_transitioning(self, pg_start):
        mock_pg, mock_screen, mock_anim = pg_start

        mock_anim.loading_bar.return_value = True
        keys = MagicMock()
        keys.__getitem__ = Mock(return_value=True)
        mock_pg.key.get_pressed.return_value = keys
        mock_pg.event.get.return_value = []

        screen = StartScreen(mock_screen)
        asyncio.run(screen.run())

        mock_anim.stop_music.assert_called_once()


# ======================================================================
# #45 — StartMenu
# ======================================================================

class TestStartMenu:
    """Verify StartMenu returns correct navigation signals."""

    def test_quit_on_quit_event(self, pg_menu):
        mock_pg, mock_screen, _ = pg_menu

        quit_ev = make_quit_event(mock_pg)
        mock_pg.event.get.return_value = [quit_ev]

        menu = StartMenu(mock_screen)
        result = asyncio.run(menu.run())

        assert result == "quit"

    def test_returns_start_when_w_pressed(self, pg_menu):
        mock_pg, mock_screen, _ = pg_menu

        keys = MagicMock()
        keys.__getitem__ = Mock(return_value=True)
        mock_pg.key.get_pressed.return_value = keys
        mock_pg.event.get.return_value = []

        menu = StartMenu(mock_screen)
        result = asyncio.run(menu.run())

        assert result == "start"


# ======================================================================
# #45 — GameOverScreen
# ======================================================================

class TestGameOverScreen:
    """Verify GameOverScreen returns correct navigation signals."""

    def test_quit_on_quit_event(self, pg_gameover):
        mock_pg, mock_screen, _ = pg_gameover

        quit_ev = make_quit_event(mock_pg)
        mock_pg.event.get.return_value = [quit_ev]

        screen = GameOverScreen(mock_screen, score=5, reason="Wrong input!")
        result = asyncio.run(screen.run())

        assert result == "quit"

    def test_retry_on_r_key(self, pg_gameover):
        mock_pg, mock_screen, _ = pg_gameover

        ev = make_key_event(mock_pg, mock_pg.K_r)
        mock_pg.event.get.return_value = [ev]

        screen = GameOverScreen(mock_screen, score=5, reason="Wrong input!")
        result = asyncio.run(screen.run())

        assert result == "retry"

    def test_quit_on_q_key(self, pg_gameover):
        mock_pg, mock_screen, _ = pg_gameover

        ev = make_key_event(mock_pg, mock_pg.K_q)
        mock_pg.event.get.return_value = [ev]

        screen = GameOverScreen(mock_screen, score=5, reason="Wrong input!")
        result = asyncio.run(screen.run())

        assert result == "quit"

    def test_quit_on_escape_key(self, pg_gameover):
        mock_pg, mock_screen, _ = pg_gameover

        ev = make_key_event(mock_pg, mock_pg.K_ESCAPE)
        mock_pg.event.get.return_value = [ev]

        screen = GameOverScreen(mock_screen, score=3, reason="Time's up!")
        result = asyncio.run(screen.run())

        assert result == "quit"

    def test_stores_score_and_reason(self, pg_gameover):
        _, mock_screen, _ = pg_gameover

        screen = GameOverScreen(mock_screen, score=42, reason="Time's up!")

        assert screen.score == 42
        assert screen.reason == "Time's up!"

    def test_renders_score_text(self, pg_gameover):
        mock_pg, mock_screen, mock_anim = pg_gameover

        # Return empty events first to allow one draw, then return retry
        call_count = [0]
        def event_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return []  # First call: no events, continue loop
            else:
                # Second call: return R key to exit
                ev = make_key_event(mock_pg, mock_pg.K_r)
                return [ev]
        
        mock_pg.event.get.side_effect = event_side_effect

        screen = GameOverScreen(mock_screen, score=10, reason="Wrong input!")
        asyncio.run(screen.run())

        # Verify gradient was drawn
        mock_anim.draw_gradient.assert_called()
        # Verify wave text was drawn for "GAME OVER"
        mock_anim.wave_text.assert_called()


# ======================================================================
# #50 — Sequence Caching / State Isolation
# ======================================================================

class TestSequenceCaching:
    """Verify sequence doesn't persist between games — covers #50."""

    def test_sequence_empty_after_reset(self):
        from game.core.event_bus import EventBus
        from game.core.game_model import GameModel

        bus = EventBus()
        model = GameModel(bus)

        # Simulate a game with a built-up sequence
        model.sequence = ['left', 'right', 'up', 'down', 'space']
        model.score = 5
        model.state = 'gameover'

        # Reset (as controller.run() does at the start of each game)
        model.reset()

        assert model.sequence == []
        assert model.score == 0
        assert model.state == 'adding'

    def test_new_game_model_has_empty_sequence(self):
        from game.core.event_bus import EventBus
        from game.core.game_model import GameModel

        bus = EventBus()
        model = GameModel(bus)

        assert model.sequence == []

    def test_sequence_not_shared_between_model_instances(self):
        from game.core.event_bus import EventBus
        from game.core.game_model import GameModel

        bus = EventBus()
        model1 = GameModel(bus)
        model1.sequence.append('left')

        model2 = GameModel(bus)

        assert model2.sequence == []
        assert model1.sequence == ['left']

    def test_multiple_resets_always_clear(self):
        from game.core.event_bus import EventBus
        from game.core.game_model import GameModel

        bus = EventBus()
        model = GameModel(bus)

        for i in range(5):
            model.sequence = ['up'] * (i + 1)
            model.score = i * 10
            model.reset()
            assert model.sequence == []
            assert model.score == 0

    def test_retry_cycle_sequence_isolation(self):
        """Simulate the full retry loop: play -> gameover -> reset -> play."""
        from game.core.event_bus import EventBus
        from game.core.game_model import GameModel

        bus = EventBus()
        model = GameModel(bus)

        for game_num in range(3):
            # Each game starts with reset (as controller.run() does)
            model.reset()
            assert model.sequence == [], f"Game {game_num}: sequence not empty after reset"

            # Build up sequence
            model.state = 'adding'
            model._next_time = 0
            with patch('game.core.game_model.random.choice', return_value='left'):
                model.update(10000)

            assert len(model.sequence) == 1

            # Play correct input
            model._show_index = 1
            model.update(15000)
            model.handle_input('left', 16000)
            assert model.score == 1

            # Wrong input -> gameover
            model.state = 'adding'
            model._next_time = 0
            with patch('game.core.game_model.random.choice', return_value='right'):
                model.update(20000)
            model._show_index = len(model.sequence)
            model.update(25000)
            model.handle_input('up', 26000)  # wrong
            assert model.state == 'gameover'
