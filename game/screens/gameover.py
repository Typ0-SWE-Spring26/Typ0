# Screen when the player loses the game
# takes an argument of the score & reasons for the loss
# testing option - ctrl + e to jump to this screen

import pygame
import asyncio
from game.utils import animation_utils

AUTO_SWITCH_MS = 5000  # Auto-switch to high scores after 5 seconds


class GameOverScreen:
    def __init__(self, screen, score, reason):
        self.screen = screen
        self.score = score
        self.reason = reason
        self.gradient_top = (80, 10, 10)     # Dark red
        self.gradient_bottom = (20, 0, 0)    # Near black
        self.running = True
        self.start_time = None
        self.font_timer = pygame.font.Font(None, 28)
        self.close_rect = pygame.Rect(0, 0, 0, 0)
        # Make sure any previously-playing track is fully stopped so the ending
        # riff plays cleanly — blob-URL tracks can linger past stopMusic() in
        # some browsers, so calling it twice is a cheap belt-and-braces.
        animation_utils.stop_music()
        animation_utils.play_music("assets/Typ0__Ending_Riff.ogg", loops=0)
        # Prevent the music menu from overriding the riff until we leave.
        animation_utils.set_music_menu_locked(True)

    async def run(self):
        clock = pygame.time.Clock()
        self.start_time = pygame.time.get_ticks()

        while self.running:
            self.close_rect = pygame.Rect(
                self.screen.get_width() - 52,
                16,
                36,
                36,
            )
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    animation_utils.set_music_menu_locked(False)
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        animation_utils.set_music_menu_locked(False)
                        return "retry"
                    if event.key == pygame.K_c:
                        animation_utils.set_music_menu_locked(False)
                        return "credits"
                    if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                        animation_utils.set_music_menu_locked(False)
                        return "menu"
                    if event.key == pygame.K_h:
                        animation_utils.set_music_menu_locked(False)
                        return "high_scores"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.close_rect.collidepoint(event.pos):
                        animation_utils.set_music_menu_locked(False)
                        return "menu"

            # Auto-switch to high scores after timeout
            elapsed = pygame.time.get_ticks() - self.start_time
            if elapsed >= AUTO_SWITCH_MS:
                animation_utils.set_music_menu_locked(False)
                return "high_scores"

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

            # High scores countdown — make it obvious the board exists
            remaining_ms = max(0, AUTO_SWITCH_MS - elapsed)
            seconds_left = (remaining_ms + 999) // 1000
            countdown_surf = self.font_timer.render(
                f"High Scores in {seconds_left}...  (press H now)",
                True,
                (255, 215, 0),
            )
            cx = self.screen.get_width() // 2
            self.screen.blit(
                countdown_surf,
                countdown_surf.get_rect(center=(cx, self.screen.get_height() - 120)),
            )

            # Flashing prompt text
            animation_utils.flashing_text(
                self.screen,
                "R  Retry   |   H  High Scores   |   Q / ESC  Main Menu",
                (self.screen.get_width() // 2, self.screen.get_height() - 70),
                font_size=28,
            )

            # Close button (top-right)
            hovered = self.close_rect.collidepoint(pygame.mouse.get_pos())
            close_color = (140, 70, 80) if hovered else (110, 55, 65)
            pygame.draw.rect(self.screen, (10, 10, 20), self.close_rect.move(0, 2), border_radius=8)
            pygame.draw.rect(self.screen, close_color, self.close_rect, border_radius=8)
            pygame.draw.rect(self.screen, (200, 170, 180), self.close_rect, width=2, border_radius=8)
            close_text = pygame.font.Font(None, 24).render("X", True, (255, 235, 235))
            self.screen.blit(close_text, close_text.get_rect(center=self.close_rect.center))

            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)  # Required for pygbag

        return "quit"
