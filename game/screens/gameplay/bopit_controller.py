import pygame
import asyncio
from game.core.game_timer import GameTimer


class BopItController:
    """Controller for Bop-It mode — dynamic timer that speeds up each round."""

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

    def _process_input_result(self, name: str, now: int) -> bool:
        result = self.model.handle_input(name, now)
        if result in ('wrong', 'round_complete'):
            self.game_timer.stop()
        return True

    async def run(self):
        self.model.reset()
        clock = pygame.time.Clock()

        while True:
            now = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                if self.menu_overlay:
                    self.menu_overlay.handle_event(event)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        self.paused = not self.paused
                        now_tick = pygame.time.get_ticks()
                        if self.paused:
                            self._bus.emit('game_paused', {'now': now_tick})
                        else:
                            self._bus.emit('game_resumed', {'now': now_tick})
                        continue

                    if event.key == pygame.K_e and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        return ("gameover", 0, "Testing - Ctrl+E shortcut")

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

            if self.model.state == 'gameover' and now >= self.model.flash_end:
                return ("gameover", self.model.score, self.model.gameover_reason)

            if not self.paused:
                entered_input = self.model.update(now)
                if entered_input:
                    # Set the timer's time limit based on current score
                    self.game_timer.TIME_LIMIT = self.model.time_limit
                    self.game_timer.start(now)
                if self.model.state == 'input':
                    self.game_timer.update(now)

            self.view.draw(self.model, self.game_timer.fraction)

            if self.pause_overlay:
                self.pause_overlay.draw()

            if self.menu_overlay:
                self.menu_overlay.draw()

            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)
