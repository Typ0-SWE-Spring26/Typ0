from game.core.event_bus import EventBus
from game.core.game_model import GameModel
from .view import GameView
from .controller import GameController


class GameScreen:
    """Thin MVC facade — wires up Model, View, and Controller.

    Constructor: GameScreen(screen, keybinds, pause_overlay=None, mp_client=None)
      keybinds    — a KeybindManager supplying button_keys and key_labels.
      pause_overlay — optional overlay; subscribe() is called on it if provided.
      mp_client   — optional MultiplayerClient; enables multiplayer mode.
    """

    def __init__(self, screen, keybinds, pause_overlay=None, mp_client=None):
        self._bus = EventBus()
        self.model = GameModel(self._bus)
        self.keybinds = keybinds

        self.view = GameView(screen, keybinds.key_labels)
        self.controller = GameController(
            screen, self.model, self.view, self._bus, keybinds, pause_overlay,
            mp_client=mp_client,
        )

    async def run(self):
        return await self.controller.run()
