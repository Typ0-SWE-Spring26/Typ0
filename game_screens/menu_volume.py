import pygame

class VolumeMenu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 40)

        self.volume = pygame.mixer.music.get_volume()
        self.dragging = False

        W, H = screen.get_size()

        # Slider
        self.slider_width = 300
        self.slider_height = 6
        self.slider_rect = pygame.Rect(
            W//2 - self.slider_width//2,
            H//2,
            self.slider_width,
            self.slider_height
        )

        self.knob_radius = 12

        # Back button
        self.back_rect = pygame.Rect(30, 30, 120, 50)

    def draw(self):
        self.screen.fill((20, 20, 40))

        title = self.font.render("Volume Settings", True, (255,255,255))
        self.screen.blit(title, title.get_rect(center=(self.screen.get_width()//2, 100)))

        # Slider
        pygame.draw.rect(self.screen, (180,180,180), self.slider_rect)

        knob_x = self.slider_rect.x + int(self.volume * self.slider_width)
        pygame.draw.circle(
            self.screen,
            (255,255,255),
            (knob_x, self.slider_rect.centery),
            self.knob_radius
        )

        # Back
        pygame.draw.rect(self.screen, (70,70,110), self.back_rect)
        back_txt = self.font.render("Back", True, (255,255,255))
        self.screen.blit(back_txt, back_txt.get_rect(center=self.back_rect.center))

    def handle_event(self, event):

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_rect.collidepoint(event.pos):
                return "Back"

            if self.slider_rect.collidepoint(event.pos):
                self.dragging = True

        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

        if event.type == pygame.MOUSEMOTION and self.dragging:
            relative_x = event.pos[0] - self.slider_rect.x
            self.volume = max(0, min(1, relative_x / self.slider_width))
            pygame.mixer.music.set_volume(self.volume)

        return None