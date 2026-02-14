# Screen when the player loses the game
# takes an argument of the score & reasons for the loss
# testing option - ctrl + e to jump to this screen

import pygame
import asyncio
from . import animation_utils

class GameOverScreen:
    def __init__(self, screen, score, reason):
        self.screen = screen
        self.score = score
        self.reason = reason
        self.gradient_top = (80, 10, 10)     # Dark red
        self.gradient_bottom = (20, 0, 0)    # Near black
        self.running = True

    async def run(self):
        clock = pygame.time.Clock()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        return "retry"
                    if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                        return "quit"

            # Draw gradient background
            animation_utils.draw_gradient(self.screen, self.gradient_top, self.gradient_bottom)

            # Draw animated "GAME OVER" title with wave effect
            animation_utils.wave_text(
                self.screen,
                "GAME OVER",
                (self.screen.get_width() // 2, 150),
                font_size=96,
                color=(255, 50, 50),
                bounce_height=10,
                wave_speed=0.4,
            )

            # Display score
            score_font = pygame.font.Font(None, 56)
            score_surface = score_font.render(f"Score: {self.score}", True, (255, 255, 255))
            score_rect = score_surface.get_rect(center=(self.screen.get_width() // 2, 280))
            self.screen.blit(score_surface, score_rect)

            # Display reason for loss
            reason_font = pygame.font.Font(None, 36)
            reason_surface = reason_font.render(self.reason, True, (200, 200, 200))
            reason_rect = reason_surface.get_rect(center=(self.screen.get_width() // 2, 350))
            self.screen.blit(reason_surface, reason_rect)

            # Flashing prompt text
            animation_utils.flashing_text(
                self.screen,
                "Press R to Retry  |  Q to Quit",
                (self.screen.get_width() // 2, self.screen.get_height() - 80),
            )

            # audio
            animation_utils.play_music("assets/gameover_music.mp3")

            pygame.display.flip()
            clock.tick(60)
            await asyncio.sleep(0)  # Required for pygbag

        return "quit"
