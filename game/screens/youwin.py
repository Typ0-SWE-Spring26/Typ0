import pygame
import asyncio
from game.utils import animation_utils


class YouWinScreen:
    def __init__(self, screen, score, reason=""):
        self.screen = screen
        self.score  = score
        self.reason = reason
        self.gradient_top    = (10, 60, 20)   # Dark green
        self.gradient_bottom = (0,  20,  5)   # Near black

    async def run(self):
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        return "retry"
                    if event.key in (pygame.K_q, pygame.K_ESCAPE):
                        return "quit"

            animation_utils.draw_gradient(self.screen, self.gradient_top, self.gradient_bottom)

            animation_utils.wave_text(
                self.screen,
                "YOU WIN!",
                (self.screen.get_width() // 2, 150),
                font_size=96,
                color=(80, 255, 120),
                bounce_height=10,
                wave_speed=0.4,
            )

            score_font   = pygame.font.Font(None, 56)
            score_surf   = score_font.render(f"Score: {self.score}", True, (255, 255, 255))
            self.screen.blit(score_surf, score_surf.get_rect(center=(self.screen.get_width() // 2, 280)))

            if self.reason:
                reason_font = pygame.font.Font(None, 36)
                reason_surf = reason_font.render(self.reason, True, (180, 255, 180))
                self.screen.blit(reason_surf, reason_surf.get_rect(center=(self.screen.get_width() // 2, 350)))

            animation_utils.flashing_text(
                self.screen,
                "Press R to Play Again  |  Q to Quit",
                (self.screen.get_width() // 2, self.screen.get_height() - 80),
            )

            pygame.display.flip()
            clock.tick(60)
            await asyncio.sleep(0)
