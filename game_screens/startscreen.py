import pygame
import asyncio
import math

class StartScreen:
    def __init__(self, screen):
        self.screen = screen
        self.gradient_top = (25, 25, 112)  # Midnight blue
        self.gradient_bottom = (0, 0, 0)  # Black
        self.font_large = pygame.font.Font(None, 72)
        self.title_text = self.font_large.render("TYP0!", True, (255, 255, 255))
        self.running = True
        self.start_time = pygame.time.get_ticks()

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


    def wave_text(self, text, position=None, font_size=72, color=(255, 255, 255), bounce_height=15, wave_speed=0.3):
        '''Draw text with each letter bouncing in a wave pattern'''
        font = pygame.font.Font(None, font_size)
        if position is None:
            position = (self.screen.get_width() // 2, self.screen.get_height() // 2)

        # Calculate total width of text to center it
        total_width = sum(font.size(char)[0] for char in text)
        current_x = position[0] - total_width // 2

        # Draw each letter with its own bounce offset
        for i, char in enumerate(text):
            # Each letter bounces with a time offset based on its position
            time_offset = i * wave_speed
            bounce = math.sin((pygame.time.get_ticks() / 500) + time_offset) * bounce_height

            char_surface = font.render(char, True, color)
            char_width = font.size(char)[0]
            char_rect = char_surface.get_rect(center=(current_x + char_width // 2, position[1] + bounce))
            self.screen.blit(char_surface, char_rect)

            current_x += char_width

    def draw_animated_icons(self, string="TYP0!", position=None, radius=100, font_size=48, color=(255, 255, 255), rotation_speed=2):
        '''Draw animated icons around the title'''
        if position is None:
            position = (self.screen.get_width() // 2, 200)

        time = pygame.time.get_ticks() / 1000  # Time in seconds
        angle = time * rotation_speed  # Rotate based on rotation_speed
        for i in range(len(string)):
            icon_x = position[0] + radius * math.cos(angle + i * (2 * math.pi / len(string)))
            icon_y = position[1] + radius * math.sin(angle + i * (2 * math.pi / len(string)))
            # Draw a letter from the string as an icon
            icon_font = pygame.font.Font(None, font_size)
            icon_text = icon_font.render(string[i % len(string)], True, color)
            icon_rect = icon_text.get_rect(center=(icon_x, icon_y))
            self.screen.blit(icon_text, icon_rect)

    def flashing_text(self, text, position=None, font_size=36, color_on=(255, 255, 255), color_off=(100, 100, 100), flash_speed=500):
        '''Draw flashing text at the bottom of the screen'''
        font = pygame.font.Font(None, font_size)
        flash = (pygame.time.get_ticks() // flash_speed) % 2 == 0
        color = color_on if flash else color_off
        text_surface = font.render(text, True, color)
        if position is None:
            position = (self.screen.get_width() // 2, self.screen.get_height() - 30)
        text_rect = text_surface.get_rect(center=position)
        self.screen.blit(text_surface, text_rect)
    
    def loading_bar(self, position=None, width=400, height=20, color=(255, 255, 255), load_time=5000):
        '''Draw a loading bar at the bottom of the screen'''
        if position is None:
            position = (self.screen.get_width() // 2, self.screen.get_height() - 50)

        bar_x = position[0] - width // 2
        bar_y = position[1]

        pygame.draw.rect(self.screen, color, (bar_x, bar_y, width, height), 2)
        # Calculate progress based on elapsed time
        elapsed = pygame.time.get_ticks() - self.start_time
        progress = min(elapsed / load_time, 1.0)
        fill_width = progress * width
        pygame.draw.rect(self.screen, color, (bar_x, bar_y, fill_width, height))
        return progress >= 1.0  # Return True when bar is full

    async def run(self):
        clock = pygame.time.Clock()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

            # Draw gradient background
            self.draw_gradient()

            # Draw the wave title text
            self.wave_text("TYP0!", (self.screen.get_width() // 2, 200), font_size=72)

            # Draw flashing text
            if not self.loading_bar():
                self.flashing_text("Now Loading...", (self.screen.get_width() // 2, self.screen.get_height() - 100))

            # Draw loading bar and check if complete
            # If complete, replace with "Press Space to Start"
            # Also hide the 'now loading' text when loading is complete
            if self.loading_bar():
                self.flashing_text("Press Space to Start", (self.screen.get_width() // 2, self.screen.get_height() - 100))
                keys = pygame.key.get_pressed()
                if keys[pygame.K_SPACE]:
                    return "start"

            pygame.display.flip()
            clock.tick(60)
            await asyncio.sleep(0)  # Required for pygbag

        return "quit"