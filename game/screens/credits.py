import pygame
import asyncio
from game.utils import animation_utils


CREDITS = [
    ("Austin", "Developer"),
    ("Ben", "Developer & Music Composer"),
]


class CreditsScreen:
    def __init__(self, screen):
        self.screen = screen
        self.gradient_top = (15, 15, 60)
        self.gradient_bottom = (5, 5, 20)
        self.running = True
        self.font_name = pygame.font.Font(None, 44)
        self.font_role = pygame.font.Font(None, 32)

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

            # Draw each credit entry
            start_y = 200
            spacing = 80

            for i, (name, role) in enumerate(CREDITS):
                y = start_y + i * spacing

                name_surface = self.font_name.render(name, True, (255, 255, 255))
                name_rect = name_surface.get_rect(
                    center=(self.screen.get_width() // 2, y)
                )
                self.screen.blit(name_surface, name_rect)

                role_surface = self.font_role.render(role, True, (180, 180, 220))
                role_rect = role_surface.get_rect(
                    center=(self.screen.get_width() // 2, y + 30)
                )
                self.screen.blit(role_surface, role_rect)

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
