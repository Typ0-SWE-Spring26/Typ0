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
        # Restart the intro theme if music stopped (e.g. after the ending riff played on game over)
        if not animation_utils.is_music_playing():
            animation_utils.play_music("assets/Typ0__Intro_Theme.ogg")
        clock = pygame.time.Clock()
        W = self.screen.get_width()
        H = self.screen.get_height()
        cx = W // 2
        btn_w, btn_h = 400, 75
        btn_x = cx - btn_w // 2

        # Distribute 4 buttons evenly in the space below the title
        btn_gap   = 16
        block_h   = 4 * btn_h + 3 * btn_gap
        title_clearance = H // 4 + 60          # first pixel available below title
        btn_start = title_clearance + (H - 20 - title_clearance - block_h) // 2
        stride    = btn_h + btn_gap

        self.simon_rect    = pygame.Rect(btn_x, btn_start,              btn_w, btn_h)
        self.bopit_rect    = pygame.Rect(btn_x, btn_start + stride,     btn_w, btn_h)
        self.multi_rect    = pygame.Rect(btn_x, btn_start + stride * 2, btn_w, btn_h)
        self.settings_rect = pygame.Rect(btn_x, btn_start + stride * 3, btn_w, btn_h)
        self.btn_simon      = Button(self.simon_rect,    "Simon Mode",   self.font_btn)
        self.btn_bopit      = Button(self.bopit_rect,    "Bop It Mode",  self.font_btn)
        self.btn_multi      = Button(self.multi_rect,    "Multiplayer",  self.font_btn)
        self.btn_settings   = Button(self.settings_rect, "Settings",     self.font_btn)

        while self.running:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                # Forward events to menu overlay when it's open
                if self.menu_overlay.open or self.menu_overlay.active_submenu is not None:
                    action = self.menu_overlay.handle_event(event)
                    if action == "credits":
                        return "credits"
                    if action == "how_to_play":
                        return "how_to_play"
                    continue

                for btn, result in [
                    (self.btn_simon,    "start_simon"),
                    (self.btn_bopit,    "start_bopit"),
                    (self.btn_multi,    "multiplayer"),
                    (self.btn_settings, None),
                ]:
                    if btn.handle_event(event):
                        if result:
                            return result
                        else:
                            self.menu_overlay.open = True

                

            # Draw gradient background
            animation_utils.draw_gradient(self.screen, self.gradient_top, self.gradient_bottom)
            menu_text = self.font_large.render("Welcome to TYP0!", True, (255, 255, 255))
            self.screen.blit(menu_text, menu_text.get_rect(center=(cx, H // 4)))

            self.btn_simon.draw(self.screen)
            self.btn_bopit.draw(self.screen)
            self.btn_multi.draw(self.screen)
            self.btn_settings.draw(self.screen)

            # Hint that high-score leaderboards exist — shown after every game.
            hint_font = pygame.font.Font(None, 24)
            hint_surf = hint_font.render(
                "",
                True,
                (220, 200, 110),
            )
            self.screen.blit(hint_surf, hint_surf.get_rect(center=(cx, H - 30)))

            # Draw menu overlay on top if open
            if self.menu_overlay.open or self.menu_overlay.active_submenu is not None:
                self.menu_overlay.draw()

            keys = pygame.key.get_pressed()
            if keys[pygame.K_w] and not self.menu_overlay.open and self.menu_overlay.active_submenu is None:
                return "start_simon"

            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)  # Required for pygbag

        return "quit"
