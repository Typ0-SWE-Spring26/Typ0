import os
import pygame

class MusicMenu:

    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 40)

        # Song list (consistent with actual asset names in repository)
        self.songs = [
            ("Intro Theme", "assets/Typ0__Intro_Theme.ogg"),
            ("Techno Theme", "assets/Techno.ogg"),
            ("SciFi Theme", "assets/SciFi.ogg"),
            ("Main Theme", "assets/Typ0__Main_Theme.ogg"),
            ("Ending Riff", "assets/Typ0__Ending_Riff.ogg"),
# >>>>>>> origin/main
        ]

        self.current_index = 0
        self.left_rect = pygame.Rect(0, 0, 0, 0)
        self.right_rect = pygame.Rect(0, 0, 0, 0)
        self.back_rect = pygame.Rect(0, 0, 0, 0)

    def draw(self, bg_rect):

        # Title
        title = self.font.render("Music Settings", True, (255,255,255))
        self.screen.blit(title, title.get_rect(center=(bg_rect.centerx, bg_rect.top + 60)))

        # Current song name
        name = self.songs[self.current_index][0]
        song_text = self.font.render(name, True, (255,255,255))
        self.screen.blit(song_text, song_text.get_rect(center=(bg_rect.centerx, bg_rect.centery)))

        # Left arrow
        self.left_rect = pygame.Rect(bg_rect.centerx - 170, bg_rect.centery - 25, 50, 50)
        left_txt = self.font.render("<", True, (255,255,255))
        self.screen.blit(left_txt, left_txt.get_rect(center=self.left_rect.center))

        # Right arrow
        self.right_rect = pygame.Rect(bg_rect.centerx + 120, bg_rect.centery - 25, 50, 50)
        right_txt = self.font.render(">", True, (255,255,255))
        self.screen.blit(right_txt, right_txt.get_rect(center=self.right_rect.center))

        # Label below
        label = self.font.render("Music", True, (200,200,200))
        self.screen.blit(label, label.get_rect(center=(bg_rect.centerx, bg_rect.centery + 60)))

        # Back button
        self.back_rect = pygame.Rect(
            bg_rect.centerx - 80,
            bg_rect.bottom - 70,
            160,
            50
        )

        pygame.draw.rect(self.screen, (100, 150, 200), self.back_rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), self.back_rect, 2, border_radius=8)  # White border

        back_txt = self.font.render("Back", True, (255,255,255))
        self.screen.blit(back_txt, back_txt.get_rect(center=self.back_rect.center))


    def handle_event(self, event):

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            # Back
            if self.back_rect.collidepoint(event.pos):
                return "Back"

            # Left arrow
            if self.left_rect.collidepoint(event.pos):
                self.current_index -= 1
                if self.current_index < 0:
                    self.current_index = len(self.songs) - 1
                self.play_music()

            # Right arrow
            if self.right_rect.collidepoint(event.pos):
                self.current_index += 1
                if self.current_index >= len(self.songs):
                    self.current_index = 0
                self.play_music()

        return None


    def play_music(self):
        path = self.songs[self.current_index][1]

        if not os.path.exists(path):
            print(f"[MusicMenu] missing file: {path}")
            return

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