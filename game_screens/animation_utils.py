import pygame
import math


def draw_gradient(screen, gradient_top=(25, 25, 112), gradient_bottom=(0, 0, 0)):
    """Draw a vertical gradient from top to bottom"""
    height = screen.get_height()
    for y in range(height):
        # Calculate the color at this y position
        ratio = y / height
        r = int(gradient_top[0] * (1 - ratio) + gradient_bottom[0] * ratio)
        g = int(gradient_top[1] * (1 - ratio) + gradient_bottom[1] * ratio)
        b = int(gradient_top[2] * (1 - ratio) + gradient_bottom[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (screen.get_width(), y))


def wave_text(screen, text, position=None, font_size=72, color=(255, 255, 255), bounce_height=15, wave_speed=0.3):
    """Draw text with each letter bouncing in a wave pattern"""
    font = pygame.font.Font(None, font_size)
    if position is None:
        position = (screen.get_width() // 2, screen.get_height() // 2)

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
        screen.blit(char_surface, char_rect)

        current_x += char_width


def draw_animated_icons(screen, string="TYP0!", position=None, radius=100, font_size=48, color=(255, 255, 255), rotation_speed=2):
    """Draw animated icons around the title"""
    if position is None:
        position = (screen.get_width() // 2, 200)

    time = pygame.time.get_ticks() / 1000  # Time in seconds
    angle = time * rotation_speed  # Rotate based on rotation_speed
    for i in range(len(string)):
        icon_x = position[0] + radius * math.cos(angle + i * (2 * math.pi / len(string)))
        icon_y = position[1] + radius * math.sin(angle + i * (2 * math.pi / len(string)))
        # Draw a letter from the string as an icon
        icon_font = pygame.font.Font(None, font_size)
        icon_text = icon_font.render(string[i % len(string)], True, color)
        icon_rect = icon_text.get_rect(center=(icon_x, icon_y))
        screen.blit(icon_text, icon_rect)


def flashing_text(screen, text, position=None, font_size=36, color_on=(255, 255, 255), color_off=(100, 100, 100), flash_speed=500):
    """Draw flashing text at the bottom of the screen"""
    font = pygame.font.Font(None, font_size)
    flash = (pygame.time.get_ticks() // flash_speed) % 2 == 0
    color = color_on if flash else color_off
    text_surface = font.render(text, True, color)
    if position is None:
        position = (screen.get_width() // 2, screen.get_height() - 30)
    text_rect = text_surface.get_rect(center=position)
    screen.blit(text_surface, text_rect)


def loading_bar(screen, start_time, position=None, width=400, height=20, color=(255, 255, 255), load_time=5000):
    """Draw a loading bar at the bottom of the screen"""
    if position is None:
        position = (screen.get_width() // 2, screen.get_height() - 50)

    bar_x = position[0] - width // 2
    bar_y = position[1]

    pygame.draw.rect(screen, color, (bar_x, bar_y, width, height), 2)
    # Calculate progress based on elapsed time
    elapsed = pygame.time.get_ticks() - start_time
    progress = min(elapsed / load_time, 1.0)
    fill_width = progress * width
    pygame.draw.rect(screen, color, (bar_x, bar_y, fill_width, height))
    return progress >= 1.0  # Return True when bar is full

def play_music(file):
    """Play background music"""
    pygame.mixer.music.load(file)
    pygame.mixer.music.play(-1)  # Loop indefinitely
