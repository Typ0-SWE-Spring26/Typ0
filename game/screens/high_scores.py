# High scores leaderboard display screen

import pygame
import asyncio
from game.utils import animation_utils
from game.utils.button import Button
from game.core.high_scores import load_scores_async


_DIFFICULTIES = ("easy", "normal", "hard")
# Color the active tab with the per-difficulty accent used by ConfigScreen
# so the leaderboard's identity matches the difficulty selector.
_TAB_COLORS = {
    "easy":   (60, 140, 90),
    "normal": (80, 120, 200),
    "hard":   (180, 70, 70),
}
_TAB_HOVER = {
    "easy":   (80, 170, 115),
    "normal": (100, 145, 225),
    "hard":   (210, 95, 95),
}

# Browseable single-player modes — multiplayer has a separate flow.
_BROWSE_MODES = ("simon", "bopit", "keys_ninja")
_MODE_LABELS = {
    "simon":      "Simon",
    "bopit":      "Bop It",
    "keys_ninja": "Keys Ninja",
}
_MODE_ACCENT = (200, 170, 90)
_MODE_ACCENT_HOVER = (230, 200, 110)


class HighScoresScreen:
    def __init__(
        self,
        screen,
        game_mode: str | None = None,
        difficulty: str = "normal",
        highlight_name=None,
        highlight_score=None,
        # Browse mode (default False) is what the start-menu Settings →
        # High Scores entry uses: shows mode tabs (Simon/Bop It/Keys Ninja),
        # disables the Retry shortcut, and never highlights a row.
        browse_mode: bool = False,
        # Back-compat: callers that still pass `game_type="simon"` (legacy
        # single-leaderboard usage) keep working — we treat the bare mode as
        # the user's current selection and default the tab to Normal.
        game_type: str | None = None,
    ):
        if game_mode is None:
            if game_type is None:
                raise TypeError("HighScoresScreen requires game_mode")
            game_mode = game_type
        self.screen = screen
        self.game_mode = game_mode
        self.difficulty = difficulty if difficulty in _DIFFICULTIES else "normal"
        # Multiplayer is shared across difficulties — no tabs, no composite key.
        self._has_difficulty_tabs = game_mode != "multiplayer"
        # Browse mode is only meaningful for single-player modes — multiplayer
        # has its own dedicated leaderboard with no mode picker.
        self.browse_mode = bool(browse_mode) and game_mode != "multiplayer"
        self.highlight_name = highlight_name
        self.highlight_score = highlight_score
        self.gradient_top = (10, 10, 50)
        self.gradient_bottom = (0, 0, 15)
        self.running = True
        self.scores = []  # loaded async at start of run() and on tab change

        self.font_rank = pygame.font.Font(None, 36)
        self.font_name = pygame.font.Font(None, 40)
        self.font_score = pygame.font.Font(None, 40)
        self.font_empty = pygame.font.Font(None, 30)
        self.font_tab = pygame.font.Font(None, 28)
        self.close_rect = pygame.Rect(0, 0, 0, 0)

    @property
    def game_type(self) -> str:
        """Composite leaderboard ID — '<mode>_<difficulty>' for single-player,
        bare 'multiplayer' for the multiplayer board."""
        if not self._has_difficulty_tabs:
            return self.game_mode
        return f"{self.game_mode}_{self.difficulty}"

    def _build_mode_tabs(self):
        """Lay out one tab per browseable mode just under the title."""
        cx = self.screen.get_width() // 2
        tab_w, tab_h = 140, 36
        gap = 12
        total_w = len(_BROWSE_MODES) * tab_w + (len(_BROWSE_MODES) - 1) * gap
        y = 105
        tabs = {}
        for i, mode in enumerate(_BROWSE_MODES):
            rect = pygame.Rect(
                cx - total_w // 2 + i * (tab_w + gap),
                y,
                tab_w,
                tab_h,
            )
            if mode == self.game_mode:
                color = _MODE_ACCENT
                hover = _MODE_ACCENT_HOVER
            else:
                color = None
                hover = None
            tabs[mode] = Button(rect, _MODE_LABELS[mode], self.font_tab,
                                color=color, hover_color=hover)
        return tabs

    def _build_difficulty_tabs(self):
        """Lay out one tab per difficulty below the title (or below the mode
        strip in browse mode)."""
        cx = self.screen.get_width() // 2
        tab_w, tab_h = 110, 36
        gap = 12
        total_w = len(_DIFFICULTIES) * tab_w + (len(_DIFFICULTIES) - 1) * gap
        y = 153 if self.browse_mode else 105
        tabs = {}
        for i, diff in enumerate(_DIFFICULTIES):
            rect = pygame.Rect(
                cx - total_w // 2 + i * (tab_w + gap),
                y,
                tab_w,
                tab_h,
            )
            if diff == self.difficulty:
                color = _TAB_COLORS[diff]
                hover = _TAB_HOVER[diff]
            else:
                color = None
                hover = None
            tabs[diff] = Button(rect, diff.capitalize(), self.font_tab,
                                color=color, hover_color=hover)
        return tabs

    async def run(self):
        self.scores = await load_scores_async(self.game_type)
        clock = pygame.time.Clock()
        diff_buttons = self._build_difficulty_tabs() if self._has_difficulty_tabs else {}
        mode_buttons = self._build_mode_tabs() if self.browse_mode else {}

        while self.running:
            self.close_rect = pygame.Rect(
                self.screen.get_width() - 52,
                16,
                36,
                36,
            )
            tab_changed = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    # Retry only makes sense after a real run — skip it in browse mode.
                    if event.key == pygame.K_r and not self.browse_mode:
                        return "retry"
                    if (
                        event.key == pygame.K_ESCAPE
                        or event.key == pygame.K_q
                    ):
                        return "menu"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.close_rect.collidepoint(event.pos):
                        return "menu"

                if self.browse_mode:
                    for mode, btn in mode_buttons.items():
                        if btn.handle_event(event) and mode != self.game_mode:
                            self.game_mode = mode
                            tab_changed = True

                if self._has_difficulty_tabs:
                    for diff, btn in diff_buttons.items():
                        if btn.handle_event(event) and diff != self.difficulty:
                            self.difficulty = diff
                            tab_changed = True

            if tab_changed:
                # Highlight a row only on the run that produced it; switching
                # tabs after that is a navigation action, not a celebration.
                self.highlight_score = None
                self.scores = await load_scores_async(self.game_type)
                diff_buttons = self._build_difficulty_tabs()
                if self.browse_mode:
                    mode_buttons = self._build_mode_tabs()

            animation_utils.draw_gradient(
                self.screen, self.gradient_top, self.gradient_bottom
            )

            cx = self.screen.get_width() // 2

            # Title
            animation_utils.wave_text(
                self.screen,
                "HIGH SCORES",
                (cx, 60),
                font_size=64,
                color=(255, 215, 0),
                bounce_height=6,
                wave_speed=0.3,
            )

            list_top_y = 130
            if self.browse_mode:
                for btn in mode_buttons.values():
                    btn.draw(self.screen)
            if self._has_difficulty_tabs:
                for btn in diff_buttons.values():
                    btn.draw(self.screen)
                list_top_y = 215 if self.browse_mode else 175
            # Tighter row pitch in browse mode keeps row 10 above the
            # bottom prompt now that the mode-tab strip eats vertical space.
            row_step = 32 if self.browse_mode else 36

            if not self.scores:
                empty_surface = self.font_empty.render(
                    "No scores yet! Be the first!", True, (150, 150, 150)
                )
                self.screen.blit(
                    empty_surface, empty_surface.get_rect(center=(cx, 320))
                )
            else:
                # Table header
                rank_x = cx - 180
                name_x = cx - 60
                score_x = cx + 160

                # Draw each score
                for i, entry in enumerate(self.scores):
                    y = list_top_y + i * row_step
                    rank = f"{i + 1}."
                    name = entry["name"]
                    score = str(entry["score"])

                    # Highlight the just-entered score
                    is_highlight = (
                        self.highlight_name is not None
                        and name == self.highlight_name
                        and entry["score"] == self.highlight_score
                    )

                    if is_highlight:
                        # Flash effect
                        flash = (pygame.time.get_ticks() // 300) % 2 == 0
                        color = (255, 255, 0) if flash else (255, 180, 0)
                        # Clear highlight after first match so only one row highlights
                        self.highlight_score = None
                    else:
                        # Gold for top 3, white for rest
                        if i < 3:
                            color = (255, 200, 50)
                        else:
                            color = (200, 200, 220)

                    rank_surface = self.font_rank.render(rank, True, color)
                    self.screen.blit(rank_surface, rank_surface.get_rect(midright=(rank_x + 30, y)))

                    name_surface = self.font_name.render(name, True, color)
                    self.screen.blit(name_surface, name_surface.get_rect(midleft=(name_x, y)))

                    score_surface = self.font_score.render(score, True, color)
                    score_rect = score_surface.get_rect(midright=(score_x, y))
                    self.screen.blit(score_surface, score_rect)

                    # Dots between name and score — fill the gap dynamically
                    dot_start = name_x + name_surface.get_width() + 8
                    dot_end = score_rect.left - 8
                    dot_char_w = self.font_rank.size(".")[0]
                    if dot_end > dot_start and dot_char_w > 0:
                        num_dots = max(0, (dot_end - dot_start) // dot_char_w)
                        dots_surface = self.font_rank.render("." * num_dots, True, (60, 60, 80))
                        self.screen.blit(dots_surface, dots_surface.get_rect(midleft=(dot_start, y)))

            # Prompt — Retry shortcut isn't shown in browse mode (no run to retry).
            prompt = "ESC  Main Menu" if self.browse_mode else "R  Retry  |  ESC  Main Menu"
            animation_utils.flashing_text(
                self.screen,
                prompt,
                (cx, self.screen.get_height() - 50),
            )

            # Close button (top-right)
            hovered = self.close_rect.collidepoint(pygame.mouse.get_pos())
            close_color = (140, 70, 80) if hovered else (110, 55, 65)
            pygame.draw.rect(self.screen, (10, 10, 20), self.close_rect.move(0, 2), border_radius=8)
            pygame.draw.rect(self.screen, close_color, self.close_rect, border_radius=8)
            pygame.draw.rect(self.screen, (200, 170, 180), self.close_rect, width=2, border_radius=8)
            close_text = pygame.font.Font(None, 24).render("X", True, (255, 235, 235))
            self.screen.blit(close_text, close_text.get_rect(center=self.close_rect.center))

            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)

        return "back"
