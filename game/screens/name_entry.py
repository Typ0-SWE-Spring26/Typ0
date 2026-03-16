# Arcade-style name entry screen for high scores

import pygame
import asyncio
from game.utils import animation_utils

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
MAX_NAME_LEN = 5


class NameEntryScreen:
    def __init__(self, screen, score):
        self.screen = screen
        self.score = score
        self.gradient_top = (10, 40, 10)
        self.gradient_bottom = (0, 10, 0)
        self.running = True

        self.name = ["A"] * MAX_NAME_LEN
        self.cursor = 0
        self.char_index = [0] * MAX_NAME_LEN

        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)

    async def run(self):
        clock = pygame.time.Clock()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        # Scroll letter up
                        self.char_index[self.cursor] = (
                            self.char_index[self.cursor] + 1
                        ) % len(ALPHABET)
                        self.name[self.cursor] = ALPHABET[self.char_index[self.cursor]]
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        # Scroll letter down
                        self.char_index[self.cursor] = (
                            self.char_index[self.cursor] - 1
                        ) % len(ALPHABET)
                        self.name[self.cursor] = ALPHABET[self.char_index[self.cursor]]
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.cursor = min(self.cursor + 1, MAX_NAME_LEN - 1)
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.cursor = max(self.cursor - 1, 0)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        # Confirm name
                        return "".join(self.name)

            animation_utils.draw_gradient(
                self.screen, self.gradient_top, self.gradient_bottom
            )

            cx = self.screen.get_width() // 2

            # Title
            animation_utils.wave_text(
                self.screen,
                "NEW HIGH SCORE!",
                (cx, 80),
                font_size=64,
                color=(255, 215, 0),
                bounce_height=8,
                wave_speed=0.3,
            )

            # Show the score
            score_surface = self.font_medium.render(
                f"Score: {self.score}", True, (255, 255, 255)
            )
            self.screen.blit(
                score_surface, score_surface.get_rect(center=(cx, 160))
            )

            # Instruction
            inst_surface = self.font_small.render(
                "Enter your name!", True, (200, 200, 200)
            )
            self.screen.blit(inst_surface, inst_surface.get_rect(center=(cx, 220)))

            # Draw the letter slots
            slot_spacing = 70
            start_x = cx - (MAX_NAME_LEN - 1) * slot_spacing // 2
            slot_y = 320

            for i in range(MAX_NAME_LEN):
                x = start_x + i * slot_spacing
                letter = self.name[i]

                # Highlight current slot
                is_active = i == self.cursor
                color = (255, 255, 0) if is_active else (200, 200, 200)

                # Draw up/down arrows for active slot
                if is_active:
                    arrow_up = self.font_small.render("^", True, (255, 255, 0))
                    self.screen.blit(
                        arrow_up, arrow_up.get_rect(center=(x, slot_y - 50))
                    )
                    arrow_down = self.font_small.render("v", True, (255, 255, 0))
                    self.screen.blit(
                        arrow_down, arrow_down.get_rect(center=(x, slot_y + 50))
                    )

                # Draw the letter
                letter_surface = self.font_large.render(letter, True, color)
                self.screen.blit(
                    letter_surface, letter_surface.get_rect(center=(x, slot_y))
                )

                # Underline
                underline_width = 40
                pygame.draw.line(
                    self.screen,
                    color,
                    (x - underline_width // 2, slot_y + 30),
                    (x + underline_width // 2, slot_y + 30),
                    3,
                )

            # Controls hint
            animation_utils.flashing_text(
                self.screen,
                "W/S to change  |  A/D to move  |  ENTER to confirm",
                (cx, self.screen.get_height() - 60),
            )

            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)

        return "quit"
