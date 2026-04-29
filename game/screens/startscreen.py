import pygame
from game.utils import animation_utils

class StartScreen:
    def __init__(self, screen):
        self.screen = screen
        self.gradient_top = (25, 25, 112)  # Midnight blue
        self.gradient_bottom = (48, 25, 52)  # Dark purple
        self.running = True
        animation_utils.play_music("assets/Typ0__Intro_Theme.ogg")


    async def run(self):
        for event in pygame.event.get():
            # Any pygame event means the user has interacted — unlock web audio.
            animation_utils.try_unlock_audio()
            if event.type == pygame.QUIT:
                return "quit"

        return "menu"
