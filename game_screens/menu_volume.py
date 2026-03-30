import pygame

class VolumeMenu:
    def __init__(self, screen, font_manager):
        self.screen = screen
        self.font_manager = font_manager

        # Safely get volume
        try:
            if pygame.mixer.get_init():
                self.volume = pygame.mixer.music.get_volume()
            else:
                self.volume = 0.5
        except Exception:
            self.volume = 0.5

        self.dragging = False
        self.slider_width = 380
        self.knob_radius = 18
        self.back_rect = None
        self.slider_rect = None
        self.slider_hit_rect = None

    def draw(self, bg_rect):
        # Title with Courier font
        title_surf = self.font_manager.render_text("VOLUME", (255, 255, 255), 36)
        title_rect = title_surf.get_rect(center=(bg_rect.centerx, bg_rect.y + 55))
        self.screen.blit(title_surf, title_rect)

        # Slider
        slider_height = 10
        self.slider_rect = pygame.Rect(
            bg_rect.centerx - self.slider_width // 2,
            bg_rect.centery - 15,
            self.slider_width,
            slider_height
        )
        self.slider_hit_rect = pygame.Rect(
            self.slider_rect.x - self.knob_radius - 10,
            self.slider_rect.y - 30,
            self.slider_width + self.knob_radius * 2 + 20,
            70
        )

        pygame.draw.rect(self.screen, (150, 150, 150), self.slider_rect, border_radius=5)

        # Volume percentage
        volume_percent = int(self.volume * 100)
        vol_text = self.font_manager.render_text(f"{volume_percent}%", (255, 255, 255), 32)
        vol_rect = vol_text.get_rect(center=(bg_rect.centerx, self.slider_rect.y - 40))
        self.screen.blit(vol_text, vol_rect)

        # Knob
        knob_x = self.slider_rect.x + int(self.volume * self.slider_width)
        pygame.draw.circle(
            self.screen,
            (220, 220, 220),
            (knob_x, self.slider_rect.centery),
            self.knob_radius
        )
        
        pygame.draw.circle(
            self.screen,
            (100, 100, 100),
            (knob_x, self.slider_rect.centery),
            self.knob_radius + 2,
            2
        )

        if self.dragging:
            pygame.draw.circle(
                self.screen,
                (255, 255, 255),
                (knob_x, self.slider_rect.centery),
                self.knob_radius + 3,
                2
            )

        # Back button
        button_width = 160
        button_height = 50
        self.back_rect = pygame.Rect(
            bg_rect.centerx - button_width // 2,
            bg_rect.bottom - 70,
            button_width,
            button_height
        )
        
        hover = self.back_rect.collidepoint(pygame.mouse.get_pos())
        button_color = (120, 120, 120) if hover else (80, 80, 80)
        pygame.draw.rect(self.screen, button_color, self.back_rect, border_radius=12)
        pygame.draw.rect(self.screen, (200, 200, 200), self.back_rect, 3, border_radius=12)
        
        back_text = self.font_manager.render_text("BACK", (255, 255, 255), 28)
        self.screen.blit(back_text, back_text.get_rect(center=self.back_rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
            return None

        if event.type == pygame.MOUSEMOTION:
            if self.dragging and self.slider_rect:
                relative_x = event.pos[0] - self.slider_rect.x
                relative_x = max(0, min(self.slider_width, relative_x))
                self.volume = relative_x / self.slider_width
                # Only set volume if mixer is initialized
                if pygame.mixer.get_init():
                    pygame.mixer.music.set_volume(self.volume)
                return "volume_changed"
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_rect and self.back_rect.collidepoint(event.pos):
                return "Back"
            if self.slider_hit_rect and self.slider_hit_rect.collidepoint(event.pos):
                self.dragging = True
                relative_x = event.pos[0] - self.slider_rect.x
                relative_x = max(0, min(self.slider_width, relative_x))
                self.volume = relative_x / self.slider_width
                # Only set volume if mixer is initialized
                if pygame.mixer.get_init():
                    pygame.mixer.music.set_volume(self.volume)
                return "volume_changed"

        return None