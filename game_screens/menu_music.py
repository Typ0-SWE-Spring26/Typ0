import os
import pygame

from game.utils.button import Button
from game.utils import animation_utils

class MusicMenu:
    def __init__(self, screen, font_manager):
        self.screen = screen
        self.font_manager = font_manager

        assets_dir = "assets"
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir, exist_ok=True)

        # Built-in tracks are fixed; user tracks are appended at runtime (web only).
        self._builtin_songs = [
            ("TECHNO THEME", os.path.join(assets_dir, "Techno.ogg")),
            ("SCIFI THEME",  os.path.join(assets_dir, "SciFi.ogg")),
            ("MAIN THEME",   os.path.join(assets_dir, "Typ0__Main_Theme.ogg")),
        ]
        self._user_songs = []   # populated by _sync_user_tracks() in web builds
        self.songs = list(self._builtin_songs)

        self.current_index = 0
        self.left_rect  = pygame.Rect(0, 0, 0, 0)
        self.right_rect = pygame.Rect(0, 0, 0, 0)
        self.back_rect  = pygame.Rect(0, 0, 0, 0)

        # Tracks whether the HTML upload button is currently shown so we only
        # show/hide it on open/close rather than every frame.
        self._upload_btn_visible = False

    # ── User-track sync ───────────────────────────────────────────────────────

    def _sync_user_tracks(self):
        """Pull any newly uploaded tracks from the JS audio manager and append
        them to self.songs after the built-ins.  Safe to call every frame."""
        if not animation_utils._IS_WEB:
            return
        count = animation_utils.get_user_track_count()
        self._user_songs = [
            (animation_utils.get_user_track_name(i) or f"TRACK {i + 1}",
             animation_utils.get_user_track_url(i))
            for i in range(count)
            if animation_utils.get_user_track_url(i)
        ]
        self.songs = list(self._builtin_songs) + self._user_songs
        # Keep current_index in bounds after a new track may have been added.
        self.current_index = max(0, min(self.current_index, len(self.songs) - 1))

        # Auto-select and play the most recently uploaded track.
        if animation_utils.has_new_user_track():
            js_idx = animation_utils.get_last_added_track_index()
            if js_idx >= 0:
                song_idx = len(self._builtin_songs) + js_idx
                if 0 <= song_idx < len(self.songs):
                    self.current_index = song_idx
                    self.play_music()
            animation_utils.clear_new_track_flag()

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self, bg_rect):
        # Show the upload button the first time this menu is drawn (web only).
        if animation_utils._IS_WEB and not self._upload_btn_visible:
            self._upload_btn_visible = True
            animation_utils.show_upload_button()

        if animation_utils._IS_WEB:
            self._sync_user_tracks()

        # Title
        title = self.font_manager.render_text("MUSIC", (255, 255, 255), 36)
        self.screen.blit(title, title.get_rect(center=(bg_rect.centerx, bg_rect.top + 55)))

        # Current track name
        name = self.songs[self.current_index][0]
        song_text = self.font_manager.render_text(name, (255, 255, 255), 28)
        self.screen.blit(song_text, song_text.get_rect(center=(bg_rect.centerx, bg_rect.centery - 20)))

        # Left arrow
        arrow_size = 70
        self.left_rect = pygame.Rect(bg_rect.centerx - 190, bg_rect.centery - 35, arrow_size, arrow_size)
        hover_left = self.left_rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(self.screen, (120, 120, 120) if hover_left else (80, 80, 80), self.left_rect, border_radius=12)
        pygame.draw.rect(self.screen, (200, 200, 200), self.left_rect, 3, border_radius=12)
        self.screen.blit(
            self.font_manager.render_text("<", (255, 255, 255), 48),
            self.font_manager.render_text("<", (255, 255, 255), 48).get_rect(center=self.left_rect.center),
        )

        # Right arrow
        self.right_rect = pygame.Rect(bg_rect.centerx + 120, bg_rect.centery - 35, arrow_size, arrow_size)
        hover_right = self.right_rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(self.screen, (120, 120, 120) if hover_right else (80, 80, 80), self.right_rect, border_radius=12)
        pygame.draw.rect(self.screen, (200, 200, 200), self.right_rect, 3, border_radius=12)
        self.screen.blit(
            self.font_manager.render_text(">", (255, 255, 255), 48),
            self.font_manager.render_text(">", (255, 255, 255), 48).get_rect(center=self.right_rect.center),
        )

        # Sub-label: "YOUR MUSIC" for user uploads, "SELECT MUSIC" for built-ins
        is_user_track = self.current_index >= len(self._builtin_songs)
        sub_color = (160, 220, 160) if is_user_track else (200, 200, 200)
        sub_text  = "YOUR MUSIC" if is_user_track else "SELECT MUSIC"
        label = self.font_manager.render_text(sub_text, sub_color, 20)
        self.screen.blit(label, label.get_rect(center=(bg_rect.centerx, bg_rect.centery + 55)))

        # Web hint: nudge users toward the upload button
        if animation_utils._IS_WEB:
            hint = self.font_manager.render_text(
                "USE THE BUTTON BELOW TO UPLOAD YOUR OWN", (120, 120, 120), 14
            )
            self.screen.blit(hint, hint.get_rect(center=(bg_rect.centerx, bg_rect.bottom - 95)))

        # Back button
        self.back_rect = pygame.Rect(bg_rect.centerx - 100, bg_rect.bottom - 75, 200, 55)
        hover_back = self.back_rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(self.screen, (120, 120, 120) if hover_back else (80, 80, 80), self.back_rect, border_radius=12)
        pygame.draw.rect(self.screen, (200, 200, 200), self.back_rect, 3, border_radius=12)
        self.screen.blit(
            self.font_manager.render_text("BACK", (255, 255, 255), 28),
            self.font_manager.render_text("BACK", (255, 255, 255), 28).get_rect(center=self.back_rect.center),
        )

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_close(self):
        """Called by the parent menu when the music submenu is being dismissed
        (e.g. ESC) so it can tear down DOM-side overlays it owns."""
        if self._upload_btn_visible:
            self._upload_btn_visible = False
            animation_utils.hide_upload_button()

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_rect.collidepoint(event.pos):
                self.on_close()
                return "Back"

            if self.left_rect.collidepoint(event.pos):
                self._sync_user_tracks()
                self.current_index = (self.current_index - 1) % len(self.songs)
                self.play_music()

            if self.right_rect.collidepoint(event.pos):
                self._sync_user_tracks()
                self.current_index = (self.current_index + 1) % len(self.songs)
                self.play_music()

        return None

    # ── Playback ──────────────────────────────────────────────────────────────

    def play_music(self):
        path = self.songs[self.current_index][1]
        animation_utils.set_user_music_selection(path)
        # Don't start a new track while the music menu is locked (e.g. the
        # game-over riff must be allowed to play through uninterrupted).
        if animation_utils.is_music_menu_locked():
            return
        animation_utils.play_music(path)
