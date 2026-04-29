import pygame
import asyncio
from game.utils import animation_utils

class StartScreen:
    def __init__(self, screen):
        self.screen = screen
        self.gradient_top = (25, 25, 112)  # Midnight blue
        self.gradient_bottom = (48, 25, 52)  # Dark purple
        self.running = True
        self.start_time = pygame.time.get_ticks()
        animation_utils.play_music("assets/Typ0__Intro_Theme.ogg")


    async def run(self):
        clock = pygame.time.Clock()
        load_time_ms = 4000

        while self.running:
            for event in pygame.event.get():
                # Any pygame event means the user has interacted — unlock web audio.
                animation_utils.try_unlock_audio()
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    elapsed = pygame.time.get_ticks() - self.start_time
                    if elapsed >= load_time_ms:
                        return "menu"

            # Draw gradient background
            animation_utils.draw_gradient(self.screen, self.gradient_top, self.gradient_bottom)

            # Draw the wave title text
            #animation_utils.wave_text(self.screen, "TYP0!", (self.screen.get_width() // 2, 200), font_size=128)
            animation_utils.draw_gradient(self.screen, self.gradient_top, self.gradient_bottom)
            logo = pygame.image.load('assets/typoLogo.png').convert_alpha()
            oldw=logo.get_width()
            oldh=logo.get_height()
            logo=pygame.transform.smoothscale(logo,((oldw//1.3),(oldh//1.3)))
            logo_rect=logo.get_rect()
            logo_rect.center=(self.screen.get_width() // 2, 200)
            self.screen.blit(logo, logo_rect)
            # Draw loading bar and check if complete
            loading_complete = animation_utils.loading_bar(
                self.screen,
                self.start_time,
                load_time=load_time_ms,
            )
            # Draw flashing text
            if not loading_complete:
                animation_utils.flashing_text(self.screen, "something is loading. not that you'd care...", (self.screen.get_width() // 2, self.screen.get_height() - 100))
            else:
                animation_utils.flashing_text(self.screen, "press SPACE. or don't. nothing matters.", (self.screen.get_width() // 2, self.screen.get_height() - 100))
                keys = pygame.key.get_pressed()
                if keys[pygame.K_SPACE]:
                    return "menu"


            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)  # Required for pygbag

        return "quit"
