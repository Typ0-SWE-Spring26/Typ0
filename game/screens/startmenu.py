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
                center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 80)
            ))

            # Simon mode button
            simon_rect = pygame.Rect(self.screen.get_width() // 4, self.screen.get_height() // 2 - 20, 400, 75)
            pygame.draw.rect(self.screen, (60, 60, 120), simon_rect, border_radius=8)
            simon_text = self.font_small.render("Press W - Simon Mode", True, (200, 200, 200))
            self.screen.blit(simon_text, simon_text.get_rect(center=simon_rect.center))

            # Bop It mode button
            bopit_rect = pygame.Rect(self.screen.get_width() // 4, self.screen.get_height() // 2 + 80, 400, 75)
            pygame.draw.rect(self.screen, (120, 60, 60), bopit_rect, border_radius=8)
            bopit_text = self.font_small.render("Press E - Bop It Mode", True, (255, 200, 150))
            self.screen.blit(bopit_text, bopit_text.get_rect(center=bopit_rect.center))

            # Settings button
            settings_rect = pygame.Rect(self.screen.get_width() // 4, self.screen.get_height() // 2 + 180, 400, 75)
            pygame.draw.rect(self.screen, (60, 60, 120), settings_rect, border_radius=8)
            settings_text = self.font_small.render("Settings", True, (200, 200, 200))
            self.screen.blit(settings_text, settings_text.get_rect(center=settings_rect.center))

            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:
                    return "start_simon"
            if keys[pygame.K_e]:
                    return "start_bopit"

            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)  # Required for pygbag

        return "quit"
