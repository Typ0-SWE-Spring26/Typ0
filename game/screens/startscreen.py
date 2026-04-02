import pygame
import asyncio
from game.utils import animation_utils

class StartScreen:
    def __init__(self, screen):
        self.screen = screen
        self.gradient_top = (25, 25, 112)  # Midnight blue
        self.gradient_bottom = (48, 25, 52)  # Dark purple
        self.running = True
        self.start_time = pygame.time.get_ticks()
        animation_utils.play_music("assets/Typ0__Intro_Theme.ogg")


    async def run(self):
        clock = pygame.time.Clock()
        load_time_ms = 4000

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    elapsed = pygame.time.get_ticks() - self.start_time
                    if elapsed >= load_time_ms:
                        return "menu"

            # Draw gradient background
            animation_utils.draw_gradient(self.screen, self.gradient_top, self.gradient_bottom)

            # Draw the wave title text
            animation_utils.wave_text(self.screen, "TYP0!", (self.screen.get_width() // 2, 200), font_size=128)

            # Draw loading bar and check if complete
            loading_complete = animation_utils.loading_bar(
                self.screen,
                self.start_time,
                load_time=load_time_ms,
            )
            # Draw flashing text
            if not loading_complete:
                animation_utils.flashing_text(self.screen, "Now Loading...", (self.screen.get_width() // 2, self.screen.get_height() - 100))
            else:
                animation_utils.flashing_text(self.screen, "Press Space to Start", (self.screen.get_width() // 2, self.screen.get_height() - 100))
                keys = pygame.key.get_pressed()
                if keys[pygame.K_SPACE]:
                    return "menu"


            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)  # Required for pygbag

        return "quit"
