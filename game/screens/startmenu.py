import pygame
import asyncio
from game.utils import animation_utils
from game.screens.menu import MenuOverlay

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

        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            self.hovered = None
            for name, rect in [("simon", self.simon_rect), ("bopit", self.bopit_rect), ("settings", self.settings_rect)]:
                if rect.collidepoint(mouse_pos):
                    self.hovered = name

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                # Forward events to menu overlay when it's open
                if self.menu_overlay.open or self.menu_overlay.active_submenu is not None:
                    self.menu_overlay.handle_event(event)
                    continue

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.simon_rect.collidepoint(event.pos):
                        animation_utils.stop_music()
                        return "start_simon"
                    if self.bopit_rect.collidepoint(event.pos):
                        animation_utils.stop_music()
                        return "start_bopit"
                    if self.settings_rect.collidepoint(event.pos):
                        self.menu_overlay.open = True
                        continue

            # Draw gradient background
            animation_utils.draw_gradient(self.screen, self.gradient_top, self.gradient_bottom)
            menu_text = self.font_large.render("Welcome to TYP0!", True, (255, 255, 255))
            self.screen.blit(menu_text, menu_text.get_rect(center=(cx, H // 2 - 50)))

            # Simon mode button
            color = (80, 80, 160) if self.hovered == "simon" else (60, 60, 120)
            pygame.draw.rect(self.screen, color, self.simon_rect, border_radius=8)
            text = self.font_small.render("Simon Mode", True, (200, 200, 200))
            self.screen.blit(text, text.get_rect(center=self.simon_rect.center))

            # Bop It mode button
            color = (80, 80, 160) if self.hovered == "bopit" else (60, 60, 120)
            pygame.draw.rect(self.screen, color, self.bopit_rect, border_radius=8)
            text = self.font_small.render("Bop It Mode", True, (200, 200, 200))
            self.screen.blit(text, text.get_rect(center=self.bopit_rect.center))

            # Settings button
            color = (80, 80, 160) if self.hovered == "settings" else (60, 60, 120)
            pygame.draw.rect(self.screen, color, self.settings_rect, border_radius=8)
            text = self.font_small.render("Settings", True, (200, 200, 200))
            self.screen.blit(text, text.get_rect(center=self.settings_rect.center))

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
