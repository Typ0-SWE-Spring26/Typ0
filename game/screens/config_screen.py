import pygame
import asyncio
from game.utils import animation_utils
from game.utils.button import Button
from assets.font_loader import FontManager


DIFFICULTIES = ("Easy", "Normal", "Hard")


class ToggleSwitch:
    """Pill-shaped on/off toggle — draws its own label + state indicator."""

    TRACK_OFF    = (55, 55, 95)
    TRACK_ON     = (80, 170, 115)
    TRACK_BORDER = (110, 110, 180)
    KNOB_COLOR   = (230, 230, 250)
    KNOB_SHADOW  = (20, 20, 40)

    def __init__(self, rect, state: bool = False):
        self.rect  = pygame.Rect(rect)
        self.state = bool(state)
        self._pressing = False

    def draw(self, surface):
        track_color = self.TRACK_ON if self.state else self.TRACK_OFF
        radius = self.rect.height // 2

        shadow = self.rect.move(0, 3)
        pygame.draw.rect(surface, (20, 20, 40), shadow, border_radius=radius)
        pygame.draw.rect(surface, track_color, self.rect, border_radius=radius)
        pygame.draw.rect(surface, self.TRACK_BORDER, self.rect, width=1,
                         border_radius=radius)

        knob_r = radius - 4
        if self.state:
            knob_cx = self.rect.right - radius
        else:
            knob_cx = self.rect.left + radius
        knob_center = (knob_cx, self.rect.centery)

        pygame.draw.circle(surface, self.KNOB_SHADOW,
                           (knob_center[0], knob_center[1] + 2), knob_r)
        pygame.draw.circle(surface, self.KNOB_COLOR, knob_center, knob_r)

    def handle_event(self, event) -> bool:
        """Return True if the toggle was clicked (caller should flip state)."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._pressing = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._pressing and self.rect.collidepoint(event.pos):
                self._pressing = False
                self.state = not self.state
                return True
            self._pressing = False
        return False


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

    # Start button accent — makes it the clear focal point of the screen
    START_COLOR       = (60, 160,  90)
    START_HOVER_COLOR = (85, 195, 120)

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

    def _build_buttons(self, diff_rects, back_rect, start_rect):
        """Create the difficulty/back/start buttons reflecting current state."""
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
        btn_start = Button(start_rect, "Start Game", self.font_btn,
                           color=self.START_COLOR,
                           hover_color=self.START_HOVER_COLOR)
        return diff_btns, btn_back, btn_start

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def run(self):
        clock = pygame.time.Clock()
        W = self.screen.get_width()
        H = self.screen.get_height()
        cx = W // 2

        # --- Vertical layout (explicit y coordinates, no overlap) ---
        title_y    = 70
        mode_y     = 115
        controls_y = 170    # "Controls" label
        toggle_y   = 205    # toggle switch top
        diff_lbl_y = 295    # "Difficulty" label
        diff_y     = 325    # difficulty buttons top
        stars_y    = 405
        hint_y     = 432
        action_y   = H - 85

        # Toggle switch (pill) — centered below the Controls label
        tog_w, tog_h = 80, 40
        toggle_rect  = pygame.Rect(cx - tog_w // 2, toggle_y, tog_w, tog_h)
        toggle       = ToggleSwitch(toggle_rect, state=self.inverted)

        # Difficulty buttons — evenly spaced row
        diff_btn_w, diff_btn_h = 160, 60
        gap     = 16
        total_w = 3 * diff_btn_w + 2 * gap
        diff_rects = {
            label: pygame.Rect(cx - total_w // 2 + i * (diff_btn_w + gap),
                               diff_y, diff_btn_w, diff_btn_h)
            for i, label in enumerate(DIFFICULTIES)
        }

        # Back / Start buttons — Start is the focal point (green)
        btn_w, btn_h = 340, 60
        back_rect  = pygame.Rect(cx - btn_w - 10, action_y, btn_w, btn_h)
        start_rect = pygame.Rect(cx + 10,          action_y, btn_w, btn_h)

        diff_btns, btn_back, btn_start = self._build_buttons(
            diff_rects, back_rect, start_rect
        )

        if self.game_mode == "simon":
            hints = {
                "Easy":   "12s per round  -  slow flashes  -  for beginners",
                "Normal": "8s per round  -  balanced pacing",
                "Hard":   "4s per round  -  lightning flashes",
            }
        elif self.game_mode == "keys_ninja":
            hints = {
                "Easy":   "Slow spawn rate  -  gentle falling speed",
                "Normal": "Balanced spawn rate  -  moderate speed",
                "Hard":   "Fast spawn rate  -  rapid falling keys",
            }
        else:
            hints = {
                "Easy":   "Up to 7s per command  -  gentle speedup",
                "Normal": "Up to 5s per command  -  steady speedup",
                "Hard":   "Up to 3.5s per command  -  rapid speedup",
            }
        challenge_stars = {"Easy": "*", "Normal": "* *", "Hard": "* * *"}
        if self.game_mode == "simon":
            mode_label = "Simon Mode"
        elif self.game_mode == "bopit":
            mode_label = "Bop It Mode"
        else:
            mode_label = "Keys Ninja Mode"

        while True:
            changed = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                if toggle.handle_event(event):
                    self.inverted = toggle.state

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

            # Rebuild difficulty/action buttons only when the selected difficulty
            # changes (preserves the _pressing state of the other buttons).
            if changed:
                diff_btns, btn_back, btn_start = self._build_buttons(
                    diff_rects, back_rect, start_rect
                )

            # --- Draw ---
            animation_utils.draw_gradient(self.screen, self.GRADIENT_TOP, self.GRADIENT_BOTTOM)

            title_surf = self.font_title.render("Game Options", True, (255, 255, 255))
            self.screen.blit(title_surf, title_surf.get_rect(center=(cx, title_y)))

            sub_surf = self.font_sub.render(mode_label, True, (180, 180, 220))
            self.screen.blit(sub_surf, sub_surf.get_rect(center=(cx, mode_y)))

            # Controls section — label + toggle + ON/OFF text either side
            sec1_surf = self.font_label.render("Controls", True, (200, 200, 240))
            self.screen.blit(sec1_surf, sec1_surf.get_rect(center=(cx, controls_y)))

            inverted_lbl = self.font_sub.render("Inverted:", True, (200, 200, 240))
            self.screen.blit(
                inverted_lbl,
                inverted_lbl.get_rect(midright=(toggle_rect.left - 14,
                                                toggle_rect.centery)),
            )
            state_label  = "ON" if self.inverted else "OFF"
            state_color  = (130, 220, 160) if self.inverted else (160, 160, 190)
            state_surf   = self.font_sub.render(state_label, True, state_color)
            self.screen.blit(
                state_surf,
                state_surf.get_rect(midleft=(toggle_rect.right + 14,
                                             toggle_rect.centery)),
            )
            toggle.draw(self.screen)

            # Difficulty section
            sec2_surf = self.font_label.render("Difficulty", True, (200, 200, 240))
            self.screen.blit(sec2_surf, sec2_surf.get_rect(center=(cx, diff_lbl_y)))
            for btn in diff_btns.values():
                btn.draw(self.screen)

            star_color = self.DIFFICULTY_COLORS[self.difficulty][1]
            stars_surf = self.font_label.render(challenge_stars[self.difficulty], True, star_color)
            self.screen.blit(stars_surf, stars_surf.get_rect(center=(cx, stars_y)))

            hint_surf = self.font_sub.render(hints[self.difficulty], True, (180, 180, 220))
            self.screen.blit(hint_surf, hint_surf.get_rect(center=(cx, hint_y)))

            btn_back.draw(self.screen)
            btn_start.draw(self.screen)

            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)
