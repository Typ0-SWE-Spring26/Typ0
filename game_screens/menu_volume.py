import pygame

from game.utils.button import Button

class VolumeMenu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 40)
        self.small_font = pygame.font.SysFont(None, 30)

        self.volume = pygame.mixer.music.get_volume()
        self.dragging = False
        
        # These will be recalculated in draw() based on bg_rect
        self.slider_rect = None
        self.slider_hit_rect = None  # Larger hit area for easier clicking
        self.slider_width = 300  # Store this as instance variable
        self.knob_radius = 12
        self.back_rect = None
        self._font = pygame.font.SysFont(None, 40)
        self._back_btn = None

    def draw(self, bg_rect):
        # Title - positioned at top of brick background
        title = self.font.render("Volume Settings", True, (255, 255, 255))
        title_rect = title.get_rect(center=(bg_rect.centerx, bg_rect.y + 50))
        self.screen.blit(title, title_rect)

        # Slider - centered horizontally in brick background
        slider_height = 6
        
        self.slider_rect = pygame.Rect(
            bg_rect.centerx - self.slider_width // 2,
            bg_rect.centery - 20,
            self.slider_width,
            slider_height
        )
        # Larger invisible hit area for easier clicking/dragging
        self.slider_hit_rect = pygame.Rect(
            self.slider_rect.x - self.knob_radius,
            self.slider_rect.y - 20,
            self.slider_width + self.knob_radius * 2,
            40
        )

        pygame.draw.rect(self.screen, (180, 180, 180), self.slider_rect)

        # Volume percentage display
        volume_percent = int(self.volume * 100)
        vol_text = self.small_font.render(f"{volume_percent}%", True, (255, 255, 255))
        vol_rect = vol_text.get_rect(center=(bg_rect.centerx, self.slider_rect.y - 25))
        self.screen.blit(vol_text, vol_rect)

        # Knob
        knob_x = self.slider_rect.x + int(self.volume * self.slider_width)
        pygame.draw.circle(
            self.screen,
            (255, 255, 255),
            (knob_x, self.slider_rect.centery),
            self.knob_radius
        )

        # Draw a highlight if dragging (optional visual feedback)
        if self.dragging:
            pygame.draw.circle(
                self.screen,
                (200, 200, 255),
                (knob_x, self.slider_rect.centery),
                self.knob_radius + 2,
                2
            )

        # Back button - positioned at bottom of brick background
        button_width = 120
        button_height = 40
        
        self.back_rect = pygame.Rect(
            bg_rect.centerx - button_width // 2,
            bg_rect.bottom - 60,
            button_width,
            button_height
        )
        
        if self._back_btn is None or self._back_btn.rect != self.back_rect:
            self._back_btn = Button(self.back_rect, "Back", self._font)
        self._back_btn.draw(self.screen)

    def handle_event(self, event):
        # Check back button first using Button's handle_event
        if self._back_btn and self._back_btn.handle_event(event):
            return "Back"

        # Always check for mouse button UP first to stop dragging
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left mouse button
                self.dragging = False
            return None

        # Handle mouse motion for dragging
        if event.type == pygame.MOUSEMOTION:
            if self.dragging and self.slider_rect:
                # Constrain mouse position to slider bounds
                relative_x = event.pos[0] - self.slider_rect.x
                # Clamp between 0 and slider_width
                relative_x = max(0, min(self.slider_width, relative_x))
                self.volume = relative_x / self.slider_width
                pygame.mixer.music.set_volume(self.volume)
                return "volume_changed"  # Return something to indicate we handled it
            return None

        # Handle mouse button down
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check slider (use larger hit area)
            if self.slider_hit_rect and self.slider_hit_rect.collidepoint(event.pos):
                self.dragging = True
                # Also set volume immediately on click
                relative_x = event.pos[0] - self.slider_rect.x
                relative_x = max(0, min(self.slider_width, relative_x))
                self.volume = relative_x / self.slider_width
                pygame.mixer.music.set_volume(self.volume)
                return "volume_changed"

        return None