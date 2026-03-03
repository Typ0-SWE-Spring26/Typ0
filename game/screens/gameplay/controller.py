import pygame
import asyncio
from game.core.game_timer import GameTimer


class GameController:
    """Orchestrates input, model updates, and view rendering."""

    def __init__(self, screen, model, view, event_bus, keybinds, pause_overlay=None, menu_overlay=None):
        self.screen = screen
        self.model = model
        self.view = view
        self._bus = event_bus
        self.keybinds = keybinds
        self.pause_overlay = pause_overlay
        self.menu_overlay = menu_overlay
        self.paused = False

        self.game_timer = GameTimer(self._bus)
        self._bus.subscribe('timer_expired', self.model.on_timer_expired)

        if pause_overlay is not None:
            pause_overlay.subscribe(self._bus)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _process_input_result(self, name: str, now: int) -> bool:
        """Call model.handle_input, stop the timer on terminal results.

        Returns True so callers can ``break`` after a matched input.
        """
        result = self.model.handle_input(name, now)
        if result in ('wrong', 'round_complete'):
            self.game_timer.stop()
        return True

    # ------------------------------------------------------------------
    # Public async entry point
    # Returns:
    #   ("gameover", score, reason)  — player lost
    #   "quit"                       — window was closed
    # ------------------------------------------------------------------

    async def run(self):
        self.model.reset()
        clock = pygame.time.Clock()

        while True:
            now = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                # Handle menu events
                if self.menu_overlay:
                    menu_action = self.menu_overlay.handle_event(event)
                    if menu_action == "Volume":
                        print("Volume clicked")
                    if menu_action == "Music":
                        print("Music clicked")
                    if menu_action == "About":
                        print("About clicked")

                if event.type == pygame.KEYDOWN:
                    # P always toggles pause regardless of game state
                    if event.key == pygame.K_p:
                        self.paused = not self.paused
                        now_tick = pygame.time.get_ticks()
                        if self.paused:
                            self._bus.emit('game_paused', {'now': now_tick})
                        else:
                            self._bus.emit('game_resumed', {'now': now_tick})
                        continue

                    # Ctrl+E jumps to game over (debug shortcut)
                    if event.key == pygame.K_e and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        return ("gameover", 0, "Testing - Ctrl+E shortcut")

                    # Game inputs are blocked while paused
                    if not self.paused and self.model.state == 'input':
                        for name, key in self.keybinds.button_keys.items():
                            if event.key == key:
                                self._process_input_result(name, now)
                                break

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not self.paused and self.model.state == 'input':
                        for name, rect in self.view.button_rects.items():
                            if rect.collidepoint(event.pos):
                                self._process_input_result(name, now)
                                break

            # After the wrong-input press-flash expires, hand off to game over
            if self.model.state == 'gameover' and now >= self.model.flash_end:
                return ("gameover", self.model.score, self.model.gameover_reason)

            if not self.paused:
                entered_input = self.model.update(now)
                if entered_input:
                    self.game_timer.start(now)
                # Let timer update during input phase
                if self.model.state == 'input':
                    self.game_timer.update(now)

            self.view.draw(self.model, self.game_timer.fraction)

            if self.pause_overlay:
                self.pause_overlay.draw()

            if self.menu_overlay:
                self.menu_overlay.draw()

            pygame.display.flip()
            clock.tick(60)
            await asyncio.sleep(0)  # Required for pygbag
