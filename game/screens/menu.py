import pygame
import os 
from game_screens.menu_volume import VolumeMenu
from game_screens.menu_music import MusicMenu

class MenuOverlay:
    

    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 40)
        self.open = False

        W = screen.get_width()
        H = screen.get_height()
        # MENU button stays bottom-left
        self.button_rect = pygame.Rect(20, H - 70, 120, 50)
        # LOAD BACKGROUND IMAGE
        bg_path = os.path.join("assets", "menu_bg.png")
        self.bg_image = pygame.image.load(bg_path).convert_alpha()
        # Scale it smaller so it's a popup (not full screen)
        self.bg_image = pygame.transform.smoothscale(self.bg_image, (500, 400))

        # Center it
        self.bg_rect = self.bg_image.get_rect(center=(W // 2, H // 2))

        # X close button (top-right of popup)
        close_size = 36
        self.close_rect = pygame.Rect(
            self.bg_rect.right - close_size - 10,
            self.bg_rect.top + 10,
            close_size, close_size
        )
        self.close_font = pygame.font.SysFont(None, 32)

        # CENTERED MENU OPTIONS
        
        button_width = 250
        button_height = 50
        spacing = 70

        popup_center_x = self.bg_rect.centerx
        popup_center_y = self.bg_rect.centery

        self.volume_rect = pygame.Rect(
            popup_center_x - button_width // 2,
            popup_center_y - spacing,
            button_width,
            button_height
        )

        self.music_rect = pygame.Rect(
            popup_center_x - button_width // 2,
            popup_center_y,
            button_width,
            button_height
        )

        self.about_rect = pygame.Rect(
            popup_center_x - button_width // 2,
            popup_center_y + spacing,
            button_width,
            button_height
        )
        # volume subscreen
        self.volume_menu = VolumeMenu(screen)
        self.active_submenu = None  # None or "volume"

        #menuu subscreen
        self.music_menu = MusicMenu(screen)
 

    def draw(self):
        # Always draw MENU button
        pygame.draw.rect(self.screen, (60, 60, 90), self.button_rect, border_radius=8)
        text = self.font.render("MENU", True, (255, 255, 255))
        self.screen.blit(text, text.get_rect(center=self.button_rect.center))
        
        # Draw dark overlay and background if menu is open OR submenu is active
        if self.open or self.active_submenu is not None:
            # Dark transparent overlay behind popup
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))

            # Draw brick background centered
            self.screen.blit(self.bg_image, self.bg_rect)
        
            # Draw X close button
            pygame.draw.rect(self.screen, (150, 50, 50), self.close_rect, border_radius=6)
            x_text = self.close_font.render("X", True, (255, 255, 255))
            self.screen.blit(x_text, x_text.get_rect(center=self.close_rect.center))

        # Draw volume submenu if active (inside the brick background)
        if self.active_submenu == "volume":
            # We need to pass the bg_rect to VolumeMenu so it can position elements inside it
            self.volume_menu.draw(self.bg_rect)
        
        elif self.active_submenu == "music":
            self.music_menu.draw(self.bg_rect)
        
        # Draw menu options if menu is open (and no submenu is active)
        elif self.open:
            # Draw buttons on top of brick background
            for rect, label in [
                (self.volume_rect, "Volume"),
                (self.music_rect, "Music"),
                (self.about_rect, "About")
            ]:
                pygame.draw.rect(self.screen, (70, 70, 110), rect, border_radius=8)
                txt = self.font.render(label, True, (255, 255, 255))
                self.screen.blit(txt, txt.get_rect(center=rect.center))

    
    def _close(self):
        """Close the menu and any active submenu."""
        self.open = False
        self.active_submenu = None

    def handle_event(self, event):

        # ESC closes everything
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.open or self.active_submenu is not None:
                self._close()
                return None

        # 1️⃣ If volume submenu is open
        if self.active_submenu == "volume":
            result = self.volume_menu.handle_event(event)

            if result == "Back":
                self.active_submenu = None
                self.open = True

            return None


        # 2️⃣ If music submenu is open
        if self.active_submenu == "music":
            result = self.music_menu.handle_event(event)

            if result == "Back":
                self.active_submenu = None
                self.open = True

            return None


        # 3️⃣ Normal menu clicks
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            # X close button
            if (self.open or self.active_submenu is not None) and self.close_rect.collidepoint(event.pos):
                self._close()
                return None

            # MENU button
            if self.button_rect.collidepoint(event.pos):
                self.open = not self.open
                return None


            # Only allow menu buttons if menu is open
            if self.open:

                if self.volume_rect.collidepoint(event.pos):
                    self.active_submenu = "volume"
                    self.open = False
                    return None

                if self.music_rect.collidepoint(event.pos):
                    self.active_submenu = "music"
                    self.open = False
                    return None

                if self.about_rect.collidepoint(event.pos):
                    print("About clicked")
                    return "About"

        return None
