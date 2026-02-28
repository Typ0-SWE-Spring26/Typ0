import pygame
import os 

class MenuOverlay:
    # def __init__(self, screen):
    #     self.screen = screen
    #     self.font = pygame.font.SysFont(None, 32)

    #     self.open = False

    #     W = screen.get_width()
    #     H = screen.get_height()

    #     # Bottom-left MENU button
    #     self.button_rect = pygame.Rect(20, H - 70, 120, 50)

    #     # volume
    #     self.volume_rect = pygame.Rect(20, H - 130, 200, 45)
    #     #change music 
    #     self.music_rect = pygame.Rect(20, self.volume_rect.y - 55, 200, 45)
    #     #about 
    #     self.about_rect = pygame.Rect(20,self.music_rect.y-55,200,45)

    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 40)

        self.open = False

        W = screen.get_width()
        H = screen.get_height()

        # MENU button stays bottom-left
        self.button_rect = pygame.Rect(20, H - 70, 120, 50)

        # ----------------------------
        # LOAD BACKGROUND IMAGE
        # ----------------------------
        bg_path = os.path.join("assets", "menu_bg.png")
        self.bg_image = pygame.image.load(bg_path).convert_alpha()

        # Scale it smaller so it's a popup (not full screen)
        self.bg_image = pygame.transform.smoothscale(self.bg_image, (500, 400))

        # Center it
        self.bg_rect = self.bg_image.get_rect(center=(W // 2, H // 2))

        # ----------------------------
        # CENTERED MENU OPTIONS
        # ----------------------------
        button_width = 250
        button_height = 50
        spacing = 70

        center_x = W // 2

        self.volume_rect = pygame.Rect(
            center_x - button_width // 2,
            H // 2 - spacing,
            button_width,
            button_height
        )

        self.music_rect = pygame.Rect(
            center_x - button_width // 2,
            H // 2,
            button_width,
            button_height
        )

        self.about_rect = pygame.Rect(
            center_x - button_width // 2,
            H // 2 + spacing,
            button_width,
            button_height
        )
   
    # def draw(self):

    #     # Draw MENU button
    #     pygame.draw.rect(self.screen, (60, 60, 90), self.button_rect, border_radius=8)

    #     text = self.font.render("MENU", True, (255, 255, 255))
    #     text_rect = text.get_rect(center=self.button_rect.center)
    #     self.screen.blit(text, text_rect)

    #     #  show Volume option
    #     if self.open:
    #         pygame.draw.rect(self.screen, (70, 70, 110), self.volume_rect, border_radius=6)

    #         volume_text = self.font.render("Volume", True, (255, 255, 255))
    #         volume_rect = volume_text.get_rect(center=self.volume_rect.center)
    #         self.screen.blit(volume_text, volume_rect)
        
    #         # Draw Music option
    #         pygame.draw.rect(self.screen, (70, 70, 110), self.music_rect, border_radius=6)

    #         music_text = self.font.render("Music", True, (255, 255, 255))
    #         music_text_rect = music_text.get_rect(center=self.music_rect.center)
    #         self.screen.blit(music_text, music_text_rect)

    #         # about option

    #         pygame.draw.rect(self.screen, (70,70,110),self.about_rect,border_radius=6)
    #         about_text = self.font.render("About", True,(255,255,255))
    #         about_text_rect = about_text.get_rect(center=self.about_rect.center)
    #         self.screen.blit(about_text, about_text_rect)

    def draw(self):

        # Always draw MENU button
        pygame.draw.rect(self.screen, (60, 60, 90), self.button_rect, border_radius=8)
        text = self.font.render("MENU", True, (255, 255, 255))
        self.screen.blit(text, text.get_rect(center=self.button_rect.center))

        # ----------------------------
        # IF MENU OPEN → draw popup
        # ----------------------------
        if self.open:

            # Dark transparent overlay behind popup
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))

            # Draw brick background centered
            self.screen.blit(self.bg_image, self.bg_rect)

            # Draw buttons on top
            for rect, label in [
                (self.volume_rect, "Volume"),
                (self.music_rect, "Music"),
                (self.about_rect, "About")
            ]:
                pygame.draw.rect(self.screen, (70, 70, 110), rect, border_radius=8)
                txt = self.font.render(label, True, (255, 255, 255))
                self.screen.blit(txt, txt.get_rect(center=rect.center))

    
    def handle_event(self, event):

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            # Click MENU button
            if self.button_rect.collidepoint(event.pos):
                self.open = not self.open
                return None

            # Click Volume (for now does nothing)
            if self.open and self.volume_rect.collidepoint(event.pos):
                print("Volume clicked")  # just to test
                return "Volume"
            
            if self.open and self.music_rect.collidepoint(event.pos): #music
                print("Music clicked")
                return "Music"
            
            if self.open and self.about_rect.collidepoint(event.pos):  # about
                print("About clicked")
                return "About"

        return None 