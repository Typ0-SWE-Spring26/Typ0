import pygame

from game.utils.button import Button

class MusicMenu:

    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 40)

        # Song list
        self.songs = [
            ("Intro Theme", "assets/Typ0__Intro_Theme.ogg"),
            ("Main Theme", "assets/Typ0__Main_Theme.ogg"),
            ("Ending Riff", "assets/Typ0__Ending_Riff.ogg"),
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

        # Label below
        label = self.font.render("Music", True, (200,200,200))
        self.screen.blit(label, label.get_rect(center=(bg_rect.centerx, bg_rect.centery + 60)))


        # Left and right arrows for song selection
        self.left_rect  = pygame.Rect(bg_rect.centerx - 170, bg_rect.centery - 25, 50, 50)
        self.right_rect = pygame.Rect(bg_rect.centerx + 120, bg_rect.centery - 25, 50, 50)

        if self._left_btn is None:
            self._left_btn  = Button(self.left_rect,  "<", self._font_btn)
            self._right_btn = Button(self.right_rect, ">", self._font_btn)
            self._back_btn  = Button(self.back_rect,  "Back", self._font_btn)

        self._left_btn.draw(self.screen)
        self._right_btn.draw(self.screen)
        self._back_btn.draw(self.screen)
    
        # Back button
        self.back_rect = pygame.Rect(
            bg_rect.centerx - 80,
            bg_rect.bottom - 70,
            160,
            50
        )


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
        pygame.mixer.music.load(path)
        pygame.mixer.music.play(-1)