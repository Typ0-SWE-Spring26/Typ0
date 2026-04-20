import pygame
import asyncio
from game.utils import animation_utils
from game.utils.button import Button
from assets.font_loader import FontManager


DIFFICULTIES = ("Easy", "Normal", "Hard")


class ConfigScreen:
    """Pre-game configuration screen: inverted controls + difficulty.

    Returns:
        {"inverted": bool, "difficulty": "easy"|"normal"|"hard"}
        "back"
        "quit"
    """

    GRADIENT_TOP    = (25, 25, 112)
    GRADIENT_BOTTOM = (48, 25, 52)

    # Per-difficulty button colours (shown when a level is selected)
    DIFFICULTY_COLORS = {
        "Easy":   ((60, 140,  90), (80, 170, 115)),
        "Normal": ((80, 120, 200), (100, 145, 225)),
        "Hard":   ((180, 70,  70), (210, 95,  95)),
    }

    # Fallback used for the inverted-controls toggle when selected
    SEL_COLOR       = (80, 120, 200)
    SEL_HOVER_COLOR = (100, 145, 225)

    def __init__(
        self,
        screen,
        game_mode: str,
        initial_inverted: bool = False,
        initial_difficulty: str = "normal",
    ):
        self.screen    = screen
        self.game_mode = game_mode   # "simon" or "bopit"

        self.inverted = bool(initial_inverted)

        difficulty_label = str(initial_difficulty).strip().capitalize()
        if difficulty_label not in DIFFICULTIES:
            difficulty_label = "Normal"
        self.difficulty = difficulty_label

        self._fm = FontManager()
        self.font_title  = self._fm.get_font(52)
        self.font_label  = self._fm.get_font(34)
        self.font_btn    = self._fm.get_font(28)
        self.font_sub    = self._fm.get_font(22)

    # ------------------------------------------------------------------
    # Button factory helpers — called once on init and after each change
    # ------------------------------------------------------------------

    def _build_buttons(self, invert_rect, diff_rects, back_rect, start_rect):
        """Create all interactive buttons reflecting current state."""
        invert_label = f"Inverted Controls:  {'ON' if self.inverted else 'OFF'}"
        inv_color       = self.SEL_COLOR       if self.inverted else None
        inv_hover_color = self.SEL_HOVER_COLOR if self.inverted else None
        btn_invert = Button(invert_rect, invert_label, self.font_btn,
                            color=inv_color, hover_color=inv_hover_color)

        diff_btns = {}
        for label, rect in diff_rects.items():
            is_sel = (label == self.difficulty)
            if is_sel:
                color, hover_color = self.DIFFICULTY_COLORS[label]
            else:
                color, hover_color = None, None
            diff_btns[label] = Button(rect, label, self.font_btn,
                                      color=color, hover_color=hover_color)

        btn_back  = Button(back_rect,  "Back",       self.font_btn)
        btn_start = Button(start_rect, "Start Game", self.font_btn)
        return btn_invert, diff_btns, btn_back, btn_start

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def run(self):
        clock = pygame.time.Clock()
        W = self.screen.get_width()
        H = self.screen.get_height()
        cx = W // 2

        # --- Compute rects once ---
        btn_w, btn_h = 340, 60
        invert_y    = H // 2 - 90
        invert_rect = pygame.Rect(cx - btn_w // 2, invert_y, btn_w, btn_h)

        diff_btn_w, diff_btn_h = 160, 60
        gap     = 16
        total_w = 3 * diff_btn_w + 2 * gap
        diff_y  = H // 2 + 10
        diff_rects = {
            label: pygame.Rect(cx - total_w // 2 + i * (diff_btn_w + gap),
                               diff_y, diff_btn_w, diff_btn_h)
            for i, label in enumerate(DIFFICULTIES)
        }

        action_y   = H - 90
        back_rect  = pygame.Rect(cx - btn_w - 10, action_y, btn_w, btn_h)
        start_rect = pygame.Rect(cx + 10,          action_y, btn_w, btn_h)

        # Build buttons once; rebuild only when selection changes
        btn_invert, diff_btns, btn_back, btn_start = self._build_buttons(
            invert_rect, diff_rects, back_rect, start_rect
        )

        if self.game_mode == "simon":
            hints = {
                "Easy":   "12s per round  -  slow flashes  -  for beginners",
                "Normal": "8s per round  -  balanced pacing",
                "Hard":   "4s per round  -  lightning flashes",
            }
        else:
            hints = {
                "Easy":   "Up to 7s per command  -  gentle speedup",
                "Normal": "Up to 5s per command  -  steady speedup",
                "Hard":   "Up to 3.5s per command  -  rapid speedup",
            }
        challenge_stars = {"Easy": "*", "Normal": "* *", "Hard": "* * *"}
        mode_label = "Simon Mode" if self.game_mode == "simon" else "Bop It Mode"

        while True:
            changed = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                if btn_invert.handle_event(event):
                    self.inverted = not self.inverted
                    changed = True

                for label, btn in diff_btns.items():
                    if btn.handle_event(event):
                        self.difficulty = label
                        changed = True

                if btn_back.handle_event(event):
                    return "back"
                if btn_start.handle_event(event):
                    return {"inverted": self.inverted, "difficulty": self.difficulty.lower()}

                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        return {"inverted": self.inverted, "difficulty": self.difficulty.lower()}
                    if event.key == pygame.K_ESCAPE:
                        return "back"

            # Rebuild buttons only when something changed (preserves _pressing state)
            if changed:
                btn_invert, diff_btns, btn_back, btn_start = self._build_buttons(
                    invert_rect, diff_rects, back_rect, start_rect
                )

            # --- Draw ---
            animation_utils.draw_gradient(self.screen, self.GRADIENT_TOP, self.GRADIENT_BOTTOM)

            title_surf = self.font_title.render("Game Options", True, (255, 255, 255))
            self.screen.blit(title_surf, title_surf.get_rect(center=(cx, H // 6)))

            sub_surf = self.font_sub.render(mode_label, True, (180, 180, 220))
            self.screen.blit(sub_surf, sub_surf.get_rect(center=(cx, H // 6 + 48)))

            sec1_surf = self.font_label.render("Controls", True, (200, 200, 240))
            self.screen.blit(sec1_surf, sec1_surf.get_rect(center=(cx, invert_y - 30)))
            btn_invert.draw(self.screen)

            sec2_surf = self.font_label.render("Difficulty", True, (200, 200, 240))
            self.screen.blit(sec2_surf, sec2_surf.get_rect(center=(cx, diff_y - 36)))
            for btn in diff_btns.values():
                btn.draw(self.screen)

            star_color = self.DIFFICULTY_COLORS[self.difficulty][1]
            stars_surf = self.font_label.render(challenge_stars[self.difficulty], True, star_color)
            self.screen.blit(stars_surf, stars_surf.get_rect(center=(cx, diff_y + 80)))

            hint_surf = self.font_sub.render(hints[self.difficulty], True, (180, 180, 220))
            self.screen.blit(hint_surf, hint_surf.get_rect(center=(cx, diff_y + 108)))

            btn_back.draw(self.screen)
            btn_start.draw(self.screen)

            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)
