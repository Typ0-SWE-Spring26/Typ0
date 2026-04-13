import pygame
import asyncio
from game.utils import animation_utils
from assets.font_loader import FontManager


# Each entry: ("Role Title", ["Name1", "Name2", ...])
CREDITS = [
    ("Developed by", ["Austin", "Ben", "Charlie", "Dipen", "Gabi", "Jude", "Joel", "Kregg", "Oriye"]),
    ("Music Composed by", ["Ben"]),
    ("Art by", ["Charlie"]),
]


class CreditsScreen:
    _GRAD_TOP    = (15, 15, 60)
    _GRAD_BOTTOM = (5, 5, 20)

    def __init__(self, screen):
        self.screen = screen
        self._fm = FontManager()
        self._back_rect = pygame.Rect(0, 0, 0, 0)

    async def run(self):
        clock = pygame.time.Clock()
        W = self.screen.get_width()
        H = self.screen.get_height()
        cx = W // 2

        btn_w, btn_h = 200, 52
        self._back_rect = pygame.Rect(cx - btn_w // 2, H - 80, btn_w, btn_h)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        return "back"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._back_rect.collidepoint(event.pos):
                        return "back"

            animation_utils.draw_gradient(self.screen, self._GRAD_TOP, self._GRAD_BOTTOM)

            # Title
            animation_utils.wave_text(
                self.screen,
                "CREDITS",
                (cx, 75),
                font_size=72,
                color=(255, 215, 0),
                bounce_height=6,
                wave_speed=0.3,
            )

            # Credits grouped by role
            y = 155
            for role, names in CREDITS:
                role_surf = self._fm.render_text(role.upper(), (255, 215, 0), 26)
                self.screen.blit(role_surf, role_surf.get_rect(center=(cx, y)))
                y += 32

                names_str = ",  ".join(names)
                name_surf = self._fm.render_text(names_str, (210, 210, 235), 20)
                self.screen.blit(name_surf, name_surf.get_rect(center=(cx, y)))
                y += 48

            # Divider
            pygame.draw.line(
                self.screen,
                (80, 80, 120),
                (cx - 160, y - 10),
                (cx + 160, y - 10),
                1,
            )
            y += 10

            # Built-with line
            built_surf = self._fm.render_text("Built with Python & Pygame", (120, 120, 170), 18)
            self.screen.blit(built_surf, built_surf.get_rect(center=(cx, y)))

            # Back button
            mouse = pygame.mouse.get_pos()
            btn_color = (100, 100, 160) if self._back_rect.collidepoint(mouse) else (55, 55, 95)
            pygame.draw.rect(self.screen, (20, 20, 40), self._back_rect.move(0, 3), border_radius=10)
            pygame.draw.rect(self.screen, btn_color, self._back_rect, border_radius=10)
            pygame.draw.rect(self.screen, (110, 110, 180), self._back_rect, 1, border_radius=10)
            back_surf = self._fm.render_text("BACK", (220, 220, 255), 26)
            self.screen.blit(back_surf, back_surf.get_rect(center=self._back_rect.center))

            # Key hint
            hint_surf = self._fm.render_text("ESC / Q  or click BACK", (80, 80, 110), 16)
            self.screen.blit(hint_surf, hint_surf.get_rect(center=(cx, H - 22)))

            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)
