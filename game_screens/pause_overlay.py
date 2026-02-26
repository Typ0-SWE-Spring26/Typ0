import pygame


class PauseOverlay:
    """Reusable pause overlay that can be drawn on any screen."""

    def __init__(self, screen):
        self.screen = screen
        self.visible = False
        self.font_large = pygame.font.Font(None, 96)
        self.font_small = pygame.font.Font(None, 36)

    def subscribe(self, event_bus) -> None:
        """Attach to an EventBus so visibility is driven by game_paused/game_resumed events."""
        event_bus.subscribe('game_paused',  self._on_paused)
        event_bus.subscribe('game_resumed', self._on_resumed)

    def _on_paused(self, _) -> None:
        self.visible = True

    def _on_resumed(self, _) -> None:
        self.visible = False

    def draw(self) -> None:
        """Draw the overlay if currently visible."""
        if not self.visible:
            return

        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        paused_text = self.font_large.render("PAUSED", True, (255, 255, 255))
        self.screen.blit(paused_text, paused_text.get_rect(
            center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 50)
        ))

        instruction_text = self.font_small.render("Press P to Resume", True, (200, 200, 200))
        self.screen.blit(instruction_text, instruction_text.get_rect(
            center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 50)
        ))
