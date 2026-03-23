# High scores leaderboard display screen

import pygame
import asyncio
from game.utils import animation_utils
from game.core.high_scores import load_scores


class HighScoresScreen:
    def __init__(self, screen, highlight_name=None, highlight_score=None):
        self.screen = screen
        self.highlight_name = highlight_name
        self.highlight_score = highlight_score
        self.gradient_top = (10, 10, 50)
        self.gradient_bottom = (0, 0, 15)
        self.running = True
        self.scores = load_scores()

        self.font_rank = pygame.font.Font(None, 36)
        self.font_name = pygame.font.Font(None, 40)
        self.font_score = pygame.font.Font(None, 40)
        self.font_empty = pygame.font.Font(None, 30)

    async def run(self):
        clock = pygame.time.Clock()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        return "retry"
                    if (
                        event.key == pygame.K_ESCAPE
                        or event.key == pygame.K_q
                    ):
                        return "quit"

            animation_utils.draw_gradient(
                self.screen, self.gradient_top, self.gradient_bottom
            )

            cx = self.screen.get_width() // 2

            # Title
            animation_utils.wave_text(
                self.screen,
                "HIGH SCORES",
                (cx, 60),
                font_size=64,
                color=(255, 215, 0),
                bounce_height=6,
                wave_speed=0.3,
            )

            if not self.scores:
                empty_surface = self.font_empty.render(
                    "No scores yet! Be the first!", True, (150, 150, 150)
                )
                self.screen.blit(
                    empty_surface, empty_surface.get_rect(center=(cx, 300))
                )
            else:
                # Table header
                rank_x = cx - 180
                name_x = cx - 60
                score_x = cx + 160

                # Draw each score
                for i, entry in enumerate(self.scores):
                    y = 130 + i * 42
                    rank = f"{i + 1}."
                    name = entry["name"]
                    score = str(entry["score"])

                    # Highlight the just-entered score
                    is_highlight = (
                        self.highlight_name is not None
                        and name == self.highlight_name
                        and entry["score"] == self.highlight_score
                    )

                    if is_highlight:
                        # Flash effect
                        flash = (pygame.time.get_ticks() // 300) % 2 == 0
                        color = (255, 255, 0) if flash else (255, 180, 0)
                        # Clear highlight after first match so only one row highlights
                        self.highlight_score = None
                    else:
                        # Gold for top 3, white for rest
                        if i < 3:
                            color = (255, 200, 50)
                        else:
                            color = (200, 200, 220)

                    rank_surface = self.font_rank.render(rank, True, color)
                    self.screen.blit(rank_surface, rank_surface.get_rect(midright=(rank_x + 30, y)))

                    name_surface = self.font_name.render(name, True, color)
                    self.screen.blit(name_surface, name_surface.get_rect(midleft=(name_x, y)))

                    score_surface = self.font_score.render(score, True, color)
                    score_rect = score_surface.get_rect(midright=(score_x, y))
                    self.screen.blit(score_surface, score_rect)

                    # Dots between name and score — fill the gap dynamically
                    dot_start = name_x + name_surface.get_width() + 8
                    dot_end = score_rect.left - 8
                    dot_char_w = self.font_rank.size(".")[0]
                    if dot_end > dot_start and dot_char_w > 0:
                        num_dots = max(0, (dot_end - dot_start) // dot_char_w)
                        dots_surface = self.font_rank.render("." * num_dots, True, (60, 60, 80))
                        self.screen.blit(dots_surface, dots_surface.get_rect(midleft=(dot_start, y)))

            # Prompt
            animation_utils.flashing_text(
                self.screen,
                "Press R to Retry  |  ESC to Quit",
                (cx, self.screen.get_height() - 50),
            )

            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)

        return "back"
