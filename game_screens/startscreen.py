import pygame
import asyncio
import math

class StartScreen:
    def __init__(self, screen):
        self.screen = screen
        self.gradient_top = (25, 25, 112)  # Midnight blue
        self.gradient_bottom = (0, 0, 0)  # Black
        self.font_large = pygame.font.Font(None, 72)
        self.font_small = pygame.font.Font(None, 36)
        self.title_text = self.font_large.render("TYP0!", True, (255, 255, 255))
        self.start_text = self.font_small.render("Press SPACE to Start", True, (200, 200, 200))
        self.running = True

    def draw_gradient(self):
        """Draw a vertical gradient from top to bottom"""
        height = self.screen.get_height()
        for y in range(height):
            # Calculate the color at this y position
            ratio = y / height
            r = int(self.gradient_top[0] * (1 - ratio) + self.gradient_bottom[0] * ratio)
            g = int(self.gradient_top[1] * (1 - ratio) + self.gradient_bottom[1] * ratio)
            b = int(self.gradient_top[2] * (1 - ratio) + self.gradient_bottom[2] * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.screen.get_width(), y))

    def draw_animated_icons(self):
        '''Draw animated icons around the title'''
        time = pygame.time.get_ticks() / 1000  # Time in seconds
        radius = 100
        angle = time * 2  # Rotate at 2 radians per second
        for i in range(5):
            icon_x = self.screen.get_width() // 2 + radius * math.cos(angle + i * (2 * math.pi / 5))
            icon_y = 200 + radius * math.sin(angle + i * (2 * math.pi / 5))
            pygame.draw.circle(self.screen, (255, 255, 255), (int(icon_x), int(icon_y)), 10)

    async def run(self):
        clock = pygame.time.Clock()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        return "start"

            # Draw gradient background
            self.draw_gradient()

            # Draw animated icons
            self.draw_animated_icons()

            # Draw title
            title_rect = self.title_text.get_rect(center=(self.screen.get_width() // 2, 200))
            self.screen.blit(self.title_text, title_rect)

            # Draw start prompt
            start_rect = self.start_text.get_rect(center=(self.screen.get_width() // 2, 400))
            self.screen.blit(self.start_text, start_rect)

            pygame.display.flip()
            clock.tick(60)
            await asyncio.sleep(0)  # Required for pygbag

        return "quit"