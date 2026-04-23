import pygame
import asyncio
from game.utils import animation_utils
from assets.font_loader import FontManager


# Each entry: ("Role Title", ["Name1", "Name2", ...])
CREDITS = [
    ("Developed by", ["Austin", "Ben", "Charlie", "Dipen", "Gabi", "Jude", "Joel", "Kregg", "Oriye"]),
    ("Music Composed by", ["Ben"]),
    ("Art by", ["Charlie"]),
]


class CreditsScreen:
    _GRAD_TOP    = (15, 15, 60)
    _GRAD_BOTTOM = (5, 5, 20)

    # Keyboard-keycap palette, pulled from the TYP0 logo so the screen
    # reads as part of the same visual family. These are intentionally
    # simpler than the logo (no rotation, no inner-recess line, flat 3D).
    _KEY_FACE         = (196, 196, 240)
    _KEY_FACE_HOVER   = (220, 220, 252)
    _KEY_BASE         = (116, 116, 194)
    _KEY_BASE_HOVER   = (142, 142, 218)
    _KEY_OUTLINE      = (24, 24, 56)
    _KEY_TEXT         = (28, 28, 64)
    _KEY_DEPTH        = 5  # visible side/bottom of the key

    # Non-keycap colors
    _ACCENT           = (255, 215, 0)
    _SUBTLE_TEXT      = (180, 180, 220)
    _HINT_TEXT        = (110, 110, 160)
    _DIVIDER          = (80, 80, 120)

    def __init__(self, screen):
        self.screen = screen
        self._fm = FontManager()
        self._back_rect = pygame.Rect(0, 0, 0, 0)

    # ------------------------------------------------------------------
    # Keycap drawing
    # ------------------------------------------------------------------

    def _keycap_size(self, text, font_size, pad_x, pad_y):
        """Return (width, height) of the keycap *face* for a given text."""
        surf = self._fm.render_text(text, self._KEY_TEXT, font_size)
        # Use separate getters instead of unpacking get_size() — safer under
        # MagicMock and equally fast at runtime.
        tw = surf.get_width()
        th = surf.get_height()
        return tw + pad_x * 2, th + pad_y * 2

    def _draw_keycap(self, text, center, font_size=18,
                     pad_x=12, pad_y=6, depth=None,
                     face_color=None, base_color=None):
        """Draw a keyboard-keycap at *center* sized to its text.

        The cap is built from two stacked rounded rects:
          - a darker base showing as the side/bottom (the 3D body)
          - a lighter top face where the character sits

        Returns the outer rect (includes the visible side/depth).
        """
        face_color = face_color or self._KEY_FACE
        base_color = base_color or self._KEY_BASE
        depth = self._KEY_DEPTH if depth is None else depth

        w, h = self._keycap_size(text, font_size, pad_x, pad_y)
        total_h = h + depth
        outer_rect = pygame.Rect(
            center[0] - w // 2,
            center[1] - total_h // 2,
            w,
            total_h,
        )
        face_rect = pygame.Rect(outer_rect.x, outer_rect.y, w, h)

        # Base (dark side/bottom) with outline
        pygame.draw.rect(self.screen, base_color, outer_rect, border_radius=8)
        pygame.draw.rect(self.screen, self._KEY_OUTLINE, outer_rect,
                         width=2, border_radius=8)
        # Top face with its own outline — visually separates it from the base
        pygame.draw.rect(self.screen, face_color, face_rect, border_radius=7)
        pygame.draw.rect(self.screen, self._KEY_OUTLINE, face_rect,
                         width=2, border_radius=7)

        # Label centered on the face
        text_surf = self._fm.render_text(text, self._KEY_TEXT, font_size)
        self.screen.blit(text_surf, text_surf.get_rect(center=face_rect.center))
        return outer_rect

    def _draw_keycap_at_rect(self, rect, text, font_size,
                             depth=None, face_color=None, base_color=None):
        """Draw a keycap that fills *rect* (treating rect as the full body
        including the 3D depth).  Used for fixed-size buttons like BACK."""
        face_color = face_color or self._KEY_FACE
        base_color = base_color or self._KEY_BASE
        depth = self._KEY_DEPTH if depth is None else depth

        face_rect = pygame.Rect(rect.x, rect.y, rect.width, rect.height - depth)

        pygame.draw.rect(self.screen, base_color, rect, border_radius=10)
        pygame.draw.rect(self.screen, self._KEY_OUTLINE, rect,
                         width=2, border_radius=10)
        pygame.draw.rect(self.screen, face_color, face_rect, border_radius=9)
        pygame.draw.rect(self.screen, self._KEY_OUTLINE, face_rect,
                         width=2, border_radius=9)

        text_surf = self._fm.render_text(text, self._KEY_TEXT, font_size)
        self.screen.blit(text_surf, text_surf.get_rect(center=face_rect.center))

    def _draw_title_keys(self, text, center_x, top_y,
                         font_size=34, pad_x=10, pad_y=8, gap=4):
        """Draw each character of *text* as its own keycap, laid out in a row.

        Mirrors the look of the TYP0 logo without rotating each key.
        """
        widths = [self._keycap_size(ch, font_size, pad_x, pad_y)[0] for ch in text]
        _, face_h = self._keycap_size("X", font_size, pad_x, pad_y)
        total_w = sum(widths) + gap * (len(text) - 1)
        x = center_x - total_w // 2
        center_y = top_y + (face_h + self._KEY_DEPTH) // 2
        for ch, w in zip(text, widths):
            self._draw_keycap(
                ch, (x + w // 2, center_y),
                font_size=font_size, pad_x=pad_x, pad_y=pad_y,
            )
            x += w + gap
        return face_h + self._KEY_DEPTH  # total vertical height used

    def _draw_name_keys(self, names, center_x, top_y, max_width,
                       font_size=18, pad_x=10, pad_y=5, gap=7, row_gap=6):
        """Draw a set of name-keycaps centered horizontally, wrapping into
        additional rows whenever the next keycap would overflow *max_width*.

        Returns the total vertical height consumed.
        """
        widths = [self._keycap_size(n, font_size, pad_x, pad_y)[0] for n in names]
        _, face_h = self._keycap_size("X", font_size, pad_x, pad_y)
        row_h = face_h + self._KEY_DEPTH

        # Partition names into rows that each fit within max_width. Coerce
        # to int so the comparison stays valid under test mocks (where
        # font-size returns a MagicMock instead of a real integer).
        rows = []
        current, current_w = [], 0
        for n, w in zip(names, widths):
            candidate = w if not current else current_w + gap + w
            overflow = False
            try:
                overflow = int(candidate) > int(max_width)
            except (TypeError, ValueError):
                overflow = False
            if overflow and current:
                rows.append(current)
                current, current_w = [n], w
            else:
                current.append(n)
                current_w = candidate
        if current:
            rows.append(current)

        # Render each row centered.
        y = top_y
        for row in rows:
            row_widths = [self._keycap_size(n, font_size, pad_x, pad_y)[0] for n in row]
            total_w = sum(row_widths) + gap * (len(row) - 1)
            x = center_x - total_w // 2
            for n, rw in zip(row, row_widths):
                self._draw_keycap(
                    n, (x + rw // 2, y + row_h // 2),
                    font_size=font_size, pad_x=pad_x, pad_y=pad_y,
                )
                x += rw + gap
            y += row_h + row_gap

        return y - top_y

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def run(self):
        clock = pygame.time.Clock()
        W = self.screen.get_width()
        H = self.screen.get_height()
        cx = W // 2

        btn_w, btn_h = 200, 56
        self._back_rect = pygame.Rect(cx - btn_w // 2, H - 84, btn_w, btn_h)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        return "back"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._back_rect.collidepoint(event.pos):
                        return "back"

            animation_utils.draw_gradient(self.screen, self._GRAD_TOP, self._GRAD_BOTTOM)

            # Title — "CREDITS" rendered as a row of keycaps, matching the logo
            title_h = self._draw_title_keys("CREDITS", cx, 36,
                                            font_size=34, pad_x=10, pad_y=8, gap=4)

            # Credits grouped by role — role label in gold, names as keycaps
            y = 36 + title_h + 24
            max_row_width = W - 60
            for role, names in CREDITS:
                role_surf = self._fm.render_text(role.upper(), self._ACCENT, 24)
                self.screen.blit(role_surf, role_surf.get_rect(center=(cx, y)))
                y += 28

                used = self._draw_name_keys(
                    names, center_x=cx, top_y=y,
                    max_width=max_row_width,
                    font_size=18, pad_x=10, pad_y=5, gap=7, row_gap=6,
                )
                y += used + 10

            # Divider
            pygame.draw.line(
                self.screen,
                self._DIVIDER,
                (cx - 160, y - 4),
                (cx + 160, y - 4),
                1,
            )
            y += 8

            # Built-with line
            built_surf = self._fm.render_text("Built with Python & Pygame",
                                              self._HINT_TEXT, 18)
            self.screen.blit(built_surf, built_surf.get_rect(center=(cx, y)))

            # Back button — styled as a keycap that lights up on hover
            mouse = pygame.mouse.get_pos()
            hovered = self._back_rect.collidepoint(mouse)
            face = self._KEY_FACE_HOVER if hovered else self._KEY_FACE
            base = self._KEY_BASE_HOVER if hovered else self._KEY_BASE
            self._draw_keycap_at_rect(
                self._back_rect, "BACK", font_size=26,
                face_color=face, base_color=base, depth=6,
            )

            # Key hint
            hint_surf = self._fm.render_text("ESC / Q  or click BACK",
                                             self._HINT_TEXT, 16)
            self.screen.blit(hint_surf, hint_surf.get_rect(center=(cx, H - 22)))

            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)
