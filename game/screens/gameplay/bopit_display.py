from game.core.event_bus import EventBus
from game.core.bopit_model import BopItModel
from game.screens.menu import MenuOverlay
from .bopit_view import BopItView
from .bopit_controller import BopItController


class BopItScreen:
    """MVC facade for Bop-It mode."""

    def __init__(self, screen, keybinds, pause_overlay=None, difficulty: str = 'normal'):
        self._bus = EventBus()
        self.model = BopItModel(self._bus, difficulty=difficulty)
        self.keybinds = keybinds

        menu_overlay = MenuOverlay(screen, game_mode="bopit")

        self.view = BopItView(screen, keybinds.key_labels)
        self.controller = BopItController(
            screen, self.model, self.view, self._bus, keybinds, pause_overlay, menu_overlay
        )

    async def run(self):
        return await self.controller.run()
