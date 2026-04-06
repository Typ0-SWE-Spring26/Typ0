import pygame
import asyncio
from game.utils import animation_utils
from game.utils.button import Button


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

    # Highlighted difficulty button colours
    SEL_COLOR       = (80, 120, 200)
    SEL_HOVER_COLOR = (100, 145, 225)

    def __init__(self, screen, game_mode: str):
        self.screen    = screen
        self.game_mode = game_mode   # "simon" or "bopit"

        self.inverted   = False
        self.difficulty = "Normal"   # default

        self.font_title  = pygame.font.Font(None, 72)
        self.font_label  = pygame.font.Font(None, 42)
        self.font_btn    = pygame.font.Font(None, 36)
        self.font_sub    = pygame.font.Font(None, 30)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_diff_buttons(self, W, H):
        """Build the three difficulty toggle buttons centered on screen."""
        btn_w, btn_h = 160, 60
        gap          = 16
        total_w      = 3 * btn_w + 2 * gap
        start_x      = W // 2 - total_w // 2
        y            = H // 2 + 10

        buttons = {}
        for i, label in enumerate(DIFFICULTIES):
            rect = pygame.Rect(start_x + i * (btn_w + gap), y, btn_w, btn_h)
            is_sel = (label == self.difficulty)
            color       = self.SEL_COLOR       if is_sel else None
            hover_color = self.SEL_HOVER_COLOR if is_sel else None
            buttons[label] = Button(rect, label, self.font_btn, color=color, hover_color=hover_color)
        return buttons

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def run(self):
        clock = pygame.time.Clock()
        W = self.screen.get_width()
        H = self.screen.get_height()
        cx = W // 2

        # --- Layout constants ---
        btn_w, btn_h = 340, 60

        # Inverted controls toggle button (single wide button)
        invert_y   = H // 2 - 90
        invert_rect = pygame.Rect(cx - btn_w // 2, invert_y, btn_w, btn_h)

        # Bottom action buttons
        action_y   = H - 90
        back_rect  = pygame.Rect(cx - btn_w - 10, action_y, btn_w, btn_h)
        start_rect = pygame.Rect(cx + 10,          action_y, btn_w, btn_h)

        btn_back  = Button(back_rect,  "Back",       self.font_btn)
        btn_start = Button(start_rect, "Start Game", self.font_btn)

        while True:
            # Rebuild diff buttons each frame so selection highlight updates
            btn_invert = self._make_invert_button(invert_rect)
            diff_btns  = self._make_diff_buttons(W, H)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                # Inverted toggle
                if btn_invert.handle_event(event):
                    self.inverted = not self.inverted

                # Difficulty selector
                for label, btn in diff_btns.items():
                    if btn.handle_event(event):
                        self.difficulty = label

                # Action buttons
                if btn_back.handle_event(event):
                    return "back"
                if btn_start.handle_event(event):
                    return {
                        "inverted":   self.inverted,
                        "difficulty": self.difficulty.lower(),
                    }

                # Keyboard shortcut: Enter/Space → start
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        return {
                            "inverted":   self.inverted,
                            "difficulty": self.difficulty.lower(),
                        }
                    if event.key == pygame.K_ESCAPE:
                        return "back"

            # --- Draw ---
            animation_utils.draw_gradient(
                self.screen, self.GRADIENT_TOP, self.GRADIENT_BOTTOM
            )

            # Title
            mode_label = "Simon Mode" if self.game_mode == "simon" else "Bop It Mode"
            title_surf = self.font_title.render("Game Options", True, (255, 255, 255))
            self.screen.blit(title_surf, title_surf.get_rect(center=(cx, H // 6)))

            sub_surf = self.font_sub.render(mode_label, True, (180, 180, 220))
            self.screen.blit(sub_surf, sub_surf.get_rect(center=(cx, H // 6 + 48)))

            # Section: Inverted Controls
            sec1_surf = self.font_label.render("Controls", True, (200, 200, 240))
            self.screen.blit(sec1_surf, sec1_surf.get_rect(center=(cx, invert_y - 30)))
            btn_invert.draw(self.screen)

            # Section: Difficulty
            diff_y = H // 2 + 10
            sec2_surf = self.font_label.render("Difficulty", True, (200, 200, 240))
            self.screen.blit(sec2_surf, sec2_surf.get_rect(center=(cx, diff_y - 36)))
            for btn in diff_btns.values():
                btn.draw(self.screen)

            # Difficulty description hint
            hints = {
                "Easy":   "Slower pacing — great for beginners",
                "Normal": "Balanced speed and challenge",
                "Hard":   "Fast pace — for experienced players",
            }
            hint_surf = self.font_sub.render(hints[self.difficulty], True, (160, 160, 200))
            self.screen.blit(hint_surf, hint_surf.get_rect(center=(cx, diff_y + 80)))

            # Action buttons
            btn_back.draw(self.screen)
            btn_start.draw(self.screen)

            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)

    def _make_invert_button(self, rect):
        label = f"Inverted Controls:  {'ON ' if self.inverted else 'OFF'}"
        color       = self.SEL_COLOR       if self.inverted else None
        hover_color = self.SEL_HOVER_COLOR if self.inverted else None
        return Button(rect, label, self.font_btn, color=color, hover_color=hover_color)
