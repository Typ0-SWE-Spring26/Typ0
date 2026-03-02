from .event_bus import EventBus
from .game_model import GameModel
from .game_view import GameView
from .game_controller import GameController


class GameScreen:
    """Thin MVC facade — wires up Model, View, and Controller.

    Preserves the same public API so main.py doesn't need to change.
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
