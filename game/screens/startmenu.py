import pygame
import asyncio
from game.utils import animation_utils
from game.screens.menu import MenuOverlay
from game.utils.button import Button

class StartMenu:
    def __init__(self, screen):
        self.screen = screen
        self.gradient_top = (25, 25, 112)  # Midnight blue
        self.gradient_bottom = (48, 25, 52)  # Dark purple
        self.running = True
        self.font_large = pygame.font.Font(None, 96)
        self.font_small = pygame.font.Font(None, 36)
        self.start_time = pygame.time.get_ticks()
        self.hovered = None  # track which button is hovered
        self.menu_overlay = MenuOverlay(screen)
        self.font_btn = pygame.font.Font(None, 36)

    async def run(self):
        clock = pygame.time.Clock()
        W = self.screen.get_width()
        H = self.screen.get_height()
        cx = W // 2
        btn_w, btn_h = 400, 75
        btn_x = cx - btn_w // 2

        self.simon_rect = pygame.Rect(btn_x, H // 2 + 10, btn_w, btn_h)
        self.bopit_rect = pygame.Rect(btn_x, H // 2 + 110, btn_w, btn_h)
        self.settings_rect = pygame.Rect(btn_x, H // 2 + 210, btn_w, btn_h)
        self.btn_simon    = Button(self.simon_rect,    "Simon Mode", self.font_btn)
        self.btn_bopit    = Button(self.bopit_rect,    "Bop It Mode", self.font_btn)
        self.btn_settings = Button(self.settings_rect, "Settings",   self.font_btn)

        while self.running:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                # Forward events to menu overlay when it's open
                if self.menu_overlay.open or self.menu_overlay.active_submenu is not None:
                    self.menu_overlay.handle_event(event)
                    continue

                for btn, result in [
                    (self.btn_simon, "start_simon"),
                    (self.btn_bopit, "start_bopit"),
                    (self.btn_settings, None)
                ]:
                    if btn.handle_event(event):
                        if result:
                            animation_utils.stop_music()
                            return result
                        else:
                            self.menu_overlay.open = True

                

            # Draw gradient background
            animation_utils.draw_gradient(self.screen, self.gradient_top, self.gradient_bottom)
            menu_text = self.font_large.render("Welcome to TYP0!", True, (255, 255, 255))
            self.screen.blit(menu_text, menu_text.get_rect(center=(cx, H // 2 - 50)))

            # Simon mode button
            self.btn_simon.draw(self.screen)

            # Bop It mode button
            self.btn_bopit.draw(self.screen)

            # Settings button
            self.btn_settings.draw(self.screen)

            # Draw menu overlay on top if open
            if self.menu_overlay.open or self.menu_overlay.active_submenu is not None:
                self.menu_overlay.draw()

            keys = pygame.key.get_pressed()
            if keys[pygame.K_w] and not self.menu_overlay.open and self.menu_overlay.active_submenu is None:
                animation_utils.stop_music()
                return "start_simon"

            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)  # Required for pygbag

        return "quit"
