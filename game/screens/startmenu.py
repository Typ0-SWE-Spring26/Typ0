import pygame
import asyncio
from game.utils import animation_utils

class StartMenu:
    def __init__(self, screen):
        self.screen = screen
        self.gradient_top = (25, 25, 112)  # Midnight blue
        self.gradient_bottom = (48, 25, 52)  # Dark purple
        self.running = True
        self.font_large = pygame.font.Font(None, 96)
        self.font_small = pygame.font.Font(None, 36)
        self.start_time = pygame.time.get_ticks()


    async def run(self):
        clock = pygame.time.Clock()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

            # Draw gradient background
            animation_utils.draw_gradient(self.screen, self.gradient_top, self.gradient_bottom)
            menu_text = self.font_large.render("Welcome to TYP0!", True, (255, 255, 255))
            self.screen.blit(menu_text, menu_text.get_rect(
                center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 50)
            ))

            self.button_rect = pygame.Rect(self.screen.get_width() // 4, self.screen.get_height() // 2 +10, 400, 75)
            pygame.draw.rect(self.screen, (60, 60, 120), self.button_rect, border_radius=8)
            instruction_text = self.font_small.render("Press W to start regular mode", True, (200, 200, 200))
            self.screen.blit(instruction_text, instruction_text.get_rect(
                center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 50)
            ))

            self.button_rect = pygame.Rect(self.screen.get_width() // 4, self.screen.get_height() // 2+110, 400, 75)
            pygame.draw.rect(self.screen, (60, 60, 120), self.button_rect, border_radius=8)
            instruction_text = self.font_small.render("Settings", True, (200, 200, 200))
            self.screen.blit(instruction_text, instruction_text.get_rect(
                center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 150)
            ))

            self.credits_rect = pygame.Rect(self.screen.get_width() // 4, self.screen.get_height() // 2+210, 400, 75)
            pygame.draw.rect(self.screen, (60, 60, 120), self.credits_rect, border_radius=8)
            credits_text = self.font_small.render("Press C for Credits", True, (200, 200, 200))
            self.screen.blit(credits_text, credits_text.get_rect(
                center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 250)
            ))

            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:
                    return "start"
            if keys[pygame.K_c]:
                    return "credits"


            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)  # Required for pygbag

        return "quit"
