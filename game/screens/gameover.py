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

            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)  # Required for pygbag

        return "quit"
