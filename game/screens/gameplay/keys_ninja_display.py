import asyncio
from game.core.event_bus import EventBus
from game.core.keys_ninja_model import KeysNinjaModel
from game.screens.gameplay.keys_ninja_view import KeysNinjaView
from game.screens.gameplay.keys_ninja_controller import KeysNinjaController
from game.screens.menu import MenuOverlay


class KeysNinjaScreen:
    """Entry point for Keys Ninja mode — wires model, view, and controller."""
    
    def __init__(self, screen, keybinds, pause_overlay=None, difficulty: str = 'normal'):
        self.screen = screen
        self.keybinds = keybinds
        self.difficulty = difficulty
        self.pause_overlay = pause_overlay
        
        # Build MVC stack
        self._bus = EventBus()
        self.model = KeysNinjaModel(self._bus, difficulty=difficulty)
        self.view = KeysNinjaView(screen, keybinds.key_labels)
        self.menu_overlay = MenuOverlay(screen, game_mode="keys_ninja")
        self.controller = KeysNinjaController(
            screen,
            self.model,
            self.view,
            self._bus,
            keybinds,
            pause_overlay=pause_overlay,
            menu_overlay=self.menu_overlay,
        )
    
    async def run(self):
        """Run the game loop and return the result."""
        return await self.controller.run()
