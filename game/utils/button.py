import pygame

class Button:
    NORMAL_COLOR   = (55, 55, 95)
    HOVER_COLOR    = (85, 85, 140)
    PRESSED_COLOR  = (35, 35, 70)
    TEXT_COLOR     = (220, 220, 255)
    BORDER_COLOR   = (110, 110, 180)
    RADIUS         = 10

    def __init__(self, rect, label, font, color=None, hover_color=None):
        self.rect        = pygame.Rect(rect)
        self.label       = label
        self.font        = font
        self.color       = color       or self.NORMAL_COLOR
        self.hover_color = hover_color or self.HOVER_COLOR
        self._pressing   = False

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.rect.collidepoint(mouse_pos)

        if self._pressing and hovered:
            bg = self.PRESSED_COLOR
        elif hovered:
            bg = self.hover_color
        else:
            bg = self.color
        
        # shadow
        shadow = self.rect.move(0,3)
        pygame.draw.rect(surface, (20, 20, 40), shadow, border_radius=self.RADIUS)

        # button
        pygame.draw.rect(surface, bg, self.rect, border_radius=self.RADIUS)
        
        # Border
        pygame.draw.rect(surface, self.BORDER_COLOR, self.rect,
                         width=1, border_radius=self.RADIUS)
        
        # label
        text_surf = self.font.render(self.label, True, self.TEXT_COLOR)
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

    def handle_event(self, event):
        """Returns True if the button was clicked."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._pressing = True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._pressing and self.rect.collidepoint(event.pos):
                self._pressing = False
                return True
            self._pressing = False
        return False