# Arcade-style name entry screen for high scores

import pygame
import asyncio
from game.utils import animation_utils

MAX_NAME_LEN = 5


class NameEntryScreen:
    def __init__(self, screen, score):
        self.screen = screen
        self.score = score
        self.gradient_top = (10, 40, 10)
        self.gradient_bottom = (0, 10, 0)
        self.running = True

        self.name = [""] * MAX_NAME_LEN
        self.cursor = 0

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
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        # Confirm name
                        raw = "".join(self.name)
                        if not raw.strip():
                            raw = "A" * MAX_NAME_LEN
                        return raw[:MAX_NAME_LEN].ljust(MAX_NAME_LEN)
                    if event.key == pygame.K_LEFT:
                        self.cursor = (self.cursor - 1) % MAX_NAME_LEN
                        continue
                    if event.key == pygame.K_RIGHT:
                        self.cursor = (self.cursor + 1) % MAX_NAME_LEN
                        continue
                    if event.key == pygame.K_BACKSPACE:
                        if self.name[self.cursor]:
                            self.name[self.cursor] = ""
                        elif self.cursor > 0:
                            self.cursor -= 1
                            self.name[self.cursor] = ""
                    elif event.unicode and (event.unicode.isalnum() or event.unicode == " "):
                        self.name[self.cursor] = event.unicode.upper()
                        if self.cursor < MAX_NAME_LEN - 1:
                            self.cursor += 1

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
                "Type a 5-character name", True, (200, 200, 200)
            )
            self.screen.blit(inst_surface, inst_surface.get_rect(center=(cx, 220)))

            # Draw the letter slots
            slot_spacing = 70
            start_x = cx - (MAX_NAME_LEN - 1) * slot_spacing // 2
            slot_y = 320

            for i in range(MAX_NAME_LEN):
                x = start_x + i * slot_spacing
                letter = self.name[i] or "_"

                # Highlight current slot
                is_active = i == self.cursor
                color = (255, 255, 0) if is_active else (200, 200, 200)

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
                "Type A-Z/0-9/SPACE | ARROWS | BACKSPACE | ENTER",
                (cx, self.screen.get_height() - 60),
            )

            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)

        return "quit"
