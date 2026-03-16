import pygame
import os 
from game_screens.menu_volume import VolumeMenu

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
 

    def draw(self):
        # Always draw MENU button
        pygame.draw.rect(self.screen, (60, 60, 90), self.button_rect, border_radius=8)
        text = self.font.render("MENU", True, (255, 255, 255))
        self.screen.blit(text, text.get_rect(center=self.button_rect.center))
        
        # Draw dark overlay and background if menu is open OR submenu is active
        if self.open or self.active_submenu == "volume":
            # Dark transparent overlay behind popup
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))

            # Draw brick background centered
            self.screen.blit(self.bg_image, self.bg_rect)
        
        # Draw volume submenu if active (inside the brick background)
        if self.active_submenu == "volume":
            # We need to pass the bg_rect to VolumeMenu so it can position elements inside it
            self.volume_menu.draw(self.bg_rect)
        
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

    
    def handle_event(self, event):

        # If volume screen active, forward events to it
        if self.active_submenu == "volume":
            result = self.volume_menu.handle_event(event)

            if result == "Back":
                self.active_submenu = None
                self.open = True  # Re-open the main menu when going back

            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            # Click MENU button
            if self.button_rect.collidepoint(event.pos):
                self.open = not self.open
                return None

            # Click Volume (for now does nothing)
            if self.open and self.volume_rect.collidepoint(event.pos):
                self.active_submenu = "volume"
                self.open= False
                return None
            
            if self.open and self.music_rect.collidepoint(event.pos): #music
                print("Music clicked")
                return "Music"
            
            if self.open and self.about_rect.collidepoint(event.pos):  # about
                print("About clicked")
                return "About"

        return None 
    