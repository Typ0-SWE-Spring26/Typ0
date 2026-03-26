import pygame
import os 
from game_screens.menu_volume import VolumeMenu
from game_screens.menu_music import MusicMenu
from game_screens.menu_about import AboutMenu
from assets.font_loader import FontManager

class MenuOverlay:
    
    def __init__(self, screen):
        self.screen = screen
        self.font_manager = FontManager()
        self.open = False

        W = screen.get_width()
        H = screen.get_height()
        # MENU button stays bottom-left
        self.button_rect = pygame.Rect(20, H - 70, 150, 60)
        
        # LOAD BACKGROUND IMAGE
        bg_path = os.path.join("assets", "menu_bg.png")
        self.bg_image = pygame.image.load(bg_path).convert_alpha()
        
        # Scale the original image
        self.bg_image = pygame.transform.smoothscale(self.bg_image, (500, 400))
        
        # Create a DARKER version of just the brick background
        self.bg_image_dark = self.bg_image.copy()
        dark_overlay = pygame.Surface(self.bg_image.get_size(), pygame.SRCALPHA)
        dark_overlay.fill((0, 0, 0, 200))  # Adjust this value to control darkness (0-255)
        self.bg_image_dark.blit(dark_overlay, (0, 0))

        # Center it
        self.bg_rect = self.bg_image.get_rect(center=(W // 2, H // 2))

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
        
        # Initialize submenus
        self.volume_menu = VolumeMenu(screen, self.font_manager)
        self.music_menu = MusicMenu(screen, self.font_manager)
        self.about_menu = AboutMenu(screen, self.font_manager)
        self.active_submenu = None

    def draw(self):
        # Draw MENU button
        button_color = (80, 80, 80)
        if self.button_rect.collidepoint(pygame.mouse.get_pos()):
            button_color = (120, 120, 120)
        
        pygame.draw.rect(self.screen, button_color, self.button_rect, border_radius=10)
        pygame.draw.rect(self.screen, (200, 200, 200), self.button_rect, 3, border_radius=10)
        
        menu_text = self.font_manager.render_text("MENU", (255, 255, 255), 32)
        text_rect = menu_text.get_rect(center=self.button_rect.center)
        self.screen.blit(menu_text, text_rect)
        
        # Draw dark overlay and background if menu is open
        if self.open or self.active_submenu is not None:
            # Dark transparent overlay behind popup (only behind, not on brick)
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))
            
            # Draw DARKENED brick background (only the brick area is darkened)
            self.screen.blit(self.bg_image_dark, self.bg_rect)

        # Draw submenus
        if self.active_submenu == "volume":
            self.volume_menu.draw(self.bg_rect)
        elif self.active_submenu == "music":
            self.music_menu.draw(self.bg_rect)
        elif self.active_submenu == "about":
            self.about_menu.draw(self.bg_rect)
        elif self.open:
            # Draw menu buttons
            for rect, label in [
                (self.volume_rect, "VOLUME"),
                (self.music_rect, "MUSIC"),
                (self.about_rect, "ABOUT")
            ]:
                hover = rect.collidepoint(pygame.mouse.get_pos())
                button_color = (120, 120, 120) if hover else (80, 80, 80)
                
                pygame.draw.rect(self.screen, button_color, rect, border_radius=12)
                pygame.draw.rect(self.screen, (200, 200, 200), rect, 3, border_radius=12)
                
                text_surf = self.font_manager.render_text(label, (255, 255, 255), 28)
                text_rect = text_surf.get_rect(center=rect.center)
                self.screen.blit(text_surf, text_rect)

    def _close(self):
        self.open = False
        self.active_submenu = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.open or self.active_submenu is not None:
                self._close()
                return None

        # Submenu handling
        if self.active_submenu == "volume":
            result = self.volume_menu.handle_event(event)
            if result == "Back":
                self.active_submenu = None
                self.open = True
            return None

        if self.active_submenu == "music":
            result = self.music_menu.handle_event(event)
            if result == "Back":
                self.active_submenu = None
                self.open = True
            return None
        
        if self.active_submenu == "about":
            result = self.about_menu.handle_event(event)
            if result == "Back":
                self.active_submenu = None
                self.open = True
            return None

        # Main menu clicks
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.button_rect.collidepoint(event.pos):
                self.open = not self.open
                return None

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
                    self.active_submenu = "about"
                    self.open = False
                    return None

        return None