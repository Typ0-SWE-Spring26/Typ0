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
    if not self.visible:
        return

    W, H = self.screen.get_width(), self.screen.get_height()
    cx, cy = W // 2, H // 2

    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    self.screen.blit(overlay, (0, 0))

    panel_w, panel_h = 340, 180
    panel_rect = pygame.Rect(cx - panel_w // 2, cy - panel_h // 2, panel_w, panel_h)
    pygame.draw.rect(self.screen, (30, 30, 55), panel_rect, border_radius=14)
    pygame.draw.rect(self.screen, (100, 100, 170), panel_rect, width=2, border_radius=14)

    shadow_surf = self.font_large.render("PAUSED", True, (20, 20, 40))
    self.screen.blit(shadow_surf, shadow_surf.get_rect(center=(cx + 2, cy - 32)))
    paused_surf = self.font_large.render("PAUSED", True, (200, 200, 255))
    self.screen.blit(paused_surf, paused_surf.get_rect(center=(cx, cy - 34)))

    inst_surf = self.font_small.render("Press P to Resume", True, (160, 160, 210))
    self.screen.blit(inst_surf, inst_surf.get_rect(center=(cx, cy + 34)))
