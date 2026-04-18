from game.core.event_bus import EventBus
from game.core.game_model import GameModel
from game.screens.menu import MenuOverlay
from game.utils import animation_utils
from .view import GameView
from .controller import GameController


class GameScreen:
    """Thin MVC facade — wires up Model, View, and Controller.

    Constructor: GameScreen(screen, keybinds, pause_overlay=None, difficulty='normal')
      keybinds   — a KeybindManager supplying button_keys and key_labels.
      difficulty — 'easy', 'normal', or 'hard' (default 'normal').
    """
    
    def __init__(self, screen, keybinds, pause_overlay=None, difficulty: str = 'normal'):
        self._bus = EventBus()
        self.model = GameModel(self._bus, difficulty=difficulty)
        self.keybinds = keybinds

        # Create menu overlay
        menu_overlay = MenuOverlay(screen)

        self.view = GameView(screen, keybinds.key_labels)
        self.controller = GameController(
            screen, self.model, self.view, self._bus, keybinds, pause_overlay, menu_overlay,
        )
        # Propagate difficulty-derived timer limit to the controller's timer
        self.controller.game_timer.TIME_LIMIT = self.model.timer_limit

    async def run(self):
        return await self.controller.run()
