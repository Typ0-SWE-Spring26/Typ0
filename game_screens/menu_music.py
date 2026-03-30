import os
import pygame

class MusicMenu:
    def __init__(self, screen, font_manager):
        self.screen = screen
        self.font_manager = font_manager
        
        # Check if assets directory exists, if not use fallback
        assets_dir = "assets"
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir, exist_ok=True)

        self.songs = [
            ("TECHNO THEME", os.path.join(assets_dir, "Techno.ogg")),
            ("SCIFI THEME", os.path.join(assets_dir, "SciFi.ogg")),
            ("MAIN THEME", os.path.join(assets_dir, "Typ0__Main_Theme.ogg")),
        ]

        self.current_index = 0
        self.left_rect = pygame.Rect(0, 0, 0, 0)
        self.right_rect = pygame.Rect(0, 0, 0, 0)
        self.back_rect = pygame.Rect(0, 0, 0, 0)

    def draw(self, bg_rect):
        # Title
        title = self.font_manager.render_text("MUSIC", (255, 255, 255), 36)
        self.screen.blit(title, title.get_rect(center=(bg_rect.centerx, bg_rect.top + 55)))

        # Current song
        name = self.songs[self.current_index][0]
        song_text = self.font_manager.render_text(name, (255, 255, 255), 28)
        self.screen.blit(song_text, song_text.get_rect(center=(bg_rect.centerx, bg_rect.centery - 20)))

        # Left arrow
        arrow_size = 70
        self.left_rect = pygame.Rect(bg_rect.centerx - 190, bg_rect.centery - 35, arrow_size, arrow_size)
        hover_left = self.left_rect.collidepoint(pygame.mouse.get_pos())
        button_color = (120, 120, 120) if hover_left else (80, 80, 80)
        pygame.draw.rect(self.screen, button_color, self.left_rect, border_radius=12)
        pygame.draw.rect(self.screen, (200, 200, 200), self.left_rect, 3, border_radius=12)
        left_txt = self.font_manager.render_text("<", (255, 255, 255), 48)
        self.screen.blit(left_txt, left_txt.get_rect(center=self.left_rect.center))

        # Right arrow
        self.right_rect = pygame.Rect(bg_rect.centerx + 120, bg_rect.centery - 35, arrow_size, arrow_size)
        hover_right = self.right_rect.collidepoint(pygame.mouse.get_pos())
        button_color = (120, 120, 120) if hover_right else (80, 80, 80)
        pygame.draw.rect(self.screen, button_color, self.right_rect, border_radius=12)
        pygame.draw.rect(self.screen, (200, 200, 200), self.right_rect, 3, border_radius=12)
        right_txt = self.font_manager.render_text(">", (255, 255, 255), 48)
        self.screen.blit(right_txt, right_txt.get_rect(center=self.right_rect.center))

        # Label
        label = self.font_manager.render_text("SELECT MUSIC", (200, 200, 200), 20)
        self.screen.blit(label, label.get_rect(center=(bg_rect.centerx, bg_rect.centery + 55)))

        # Back button
        self.back_rect = pygame.Rect(
            bg_rect.centerx - 100,
            bg_rect.bottom - 75,
            200,
            55
        )
        hover_back = self.back_rect.collidepoint(pygame.mouse.get_pos())
        button_color = (120, 120, 120) if hover_back else (80, 80, 80)
        pygame.draw.rect(self.screen, button_color, self.back_rect, border_radius=12)
        pygame.draw.rect(self.screen, (200, 200, 200), self.back_rect, 3, border_radius=12)
        back_txt = self.font_manager.render_text("BACK", (255, 255, 255), 28)
        self.screen.blit(back_txt, back_txt.get_rect(center=self.back_rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_rect.collidepoint(event.pos):
                return "Back"
            if self.left_rect.collidepoint(event.pos):
                self.current_index -= 1
                if self.current_index < 0:
                    self.current_index = len(self.songs) - 1
                self.play_music()
            if self.right_rect.collidepoint(event.pos):
                self.current_index += 1
                if self.current_index >= len(self.songs):
                    self.current_index = 0
                self.play_music()
        return None

    def play_music(self):
        path = self.songs[self.current_index][1]
        # Check if file exists before trying to play
        if not os.path.exists(path):
            print(f"[MusicMenu] missing file: {path}")
            return
        # Check if mixer is initialized
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except Exception as exc:
                print(f"[MusicMenu] mixer init failed: {exc}")
                return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1)
        except Exception as exc:
            print(f"[MusicMenu] failed to play {path}: {exc}")