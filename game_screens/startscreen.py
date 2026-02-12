import pygame
import asyncio
from . import animation_utils

class StartScreen:
    def __init__(self, screen):
        self.screen = screen
        self.gradient_top = (25, 25, 112)  # Midnight blue
        self.gradient_bottom = (0, 0, 0)  # Black
        self.font_large = pygame.font.Font(None, 72)
        self.title_text = self.font_large.render("TYP0!", True, (255, 255, 255))
        self.running = True
        self.start_time = pygame.time.get_ticks()


    async def run(self):
        clock = pygame.time.Clock()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

            # Draw gradient background
            animation_utils.draw_gradient(self.screen, self.gradient_top, self.gradient_bottom)

            # Draw the wave title text
            animation_utils.wave_text(self.screen, "TYP0!", (self.screen.get_width() // 2, 200), font_size=72)

            # Draw loading bar and check if complete
            loading_complete = animation_utils.loading_bar(self.screen, self.start_time)

            # Draw flashing text
            if not loading_complete:
                animation_utils.flashing_text(self.screen, "Now Loading...", (self.screen.get_width() // 2, self.screen.get_height() - 100))
            else:
                animation_utils.flashing_text(self.screen, "Press Space to Start", (self.screen.get_width() // 2, self.screen.get_height() - 100))
                keys = pygame.key.get_pressed()
                if keys[pygame.K_SPACE]:
                    return "start"

            pygame.display.flip()
            clock.tick(60)
            await asyncio.sleep(0)  # Required for pygbag

        return "quit"