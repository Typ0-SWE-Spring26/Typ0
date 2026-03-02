from game.core.event_bus import EventBus
from game.core.game_model import GameModel
from .view import GameView
from .controller import GameController


class GameScreen:
    """Thin MVC facade — wires up Model, View, and Controller.

    Constructor: GameScreen(screen, keybinds, pause_overlay=None)
      keybinds — a KeybindManager (or compatible object) supplying button_keys
                 and key_labels; main.py must pass this argument.
      pause_overlay — optional overlay object; subscribe() is called on it if provided.
    """

    def __init__(self, screen, keybinds, pause_overlay=None):
        self._bus = EventBus()
        self.model = GameModel(self._bus)
        self.keybinds = keybinds

        self.view = GameView(screen, keybinds.key_labels)
        self.controller = GameController(
            screen, self.model, self.view, self._bus, keybinds, pause_overlay,
        )

    async def run(self):
        return await self.controller.run()
