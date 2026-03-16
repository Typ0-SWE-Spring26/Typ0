import pygame
import asyncio
from game.utils import animation_utils


# Each entry: ("Role Title", ["Name1", "Name2", ...])
CREDITS = [
    ("Developed by", ["Austin", "Ben", "Charlie", "Dipen", "Gabi", "Jude", "Joel", "Kregg", "Oriye"]),
    ("Music Composed by", ["Ben"]),
    ("Art by", ["Charlie"]),
]


class CreditsScreen:
    def __init__(self, screen):
        self.screen = screen
        self.gradient_top = (15, 15, 60)
        self.gradient_bottom = (5, 5, 20)
        self.running = True
        self.font_role = pygame.font.Font(None, 36)
        self.font_name = pygame.font.Font(None, 28)

    async def run(self):
        clock = pygame.time.Clock()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        return "back"

            animation_utils.draw_gradient(
                self.screen, self.gradient_top, self.gradient_bottom
            )

            # Title
            animation_utils.wave_text(
                self.screen,
                "CREDITS",
                (self.screen.get_width() // 2, 80),
                font_size=72,
                color=(255, 215, 0),
                bounce_height=6,
                wave_speed=0.3,
            )

            # Draw credits grouped by role
            cx = self.screen.get_width() // 2
            y = 160

            for role, names in CREDITS:
                # Role heading
                role_surface = self.font_role.render(role, True, (255, 215, 0))
                self.screen.blit(role_surface, role_surface.get_rect(center=(cx, y)))
                y += 30

                # Names as comma-separated line
                names_str = ", ".join(names)
                name_surface = self.font_name.render(names_str, True, (220, 220, 240))
                self.screen.blit(name_surface, name_surface.get_rect(center=(cx, y)))
                y += 50

            # Back prompt
            animation_utils.flashing_text(
                self.screen,
                "Press Q or ESC to go back",
                (self.screen.get_width() // 2, self.screen.get_height() - 60),
            )

            pygame.display.flip()
            clock.tick(60)
            await asyncio.sleep(0)

        return "back"
