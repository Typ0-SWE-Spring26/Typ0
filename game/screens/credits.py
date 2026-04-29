import pygame
import asyncio
from game.utils import animation_utils
from assets.font_loader import FontManager


# Standardized credits entry format: add one dict per person.
# Required keys: section, name, roles (list of strings).
CREDIT_ENTRIES = [
    {"section": "Core Team", "name": "Austin", "roles": ["Backend Development", "Scrum Master"]},
    {"section": "Core Team", "name": "Ben", "roles": ["Frontend Developer", "Music"]},
    {"section": "Core Team", "name": "Charlie", "roles": ["Frontend Developer", "Art"]},
    {"section": "Core Team", "name": "Dipen", "roles": ["NinjaKeys Developer"]},
    {"section": "Core Team", "name": "Gabi", "roles": ["Developer"]},
    {"section": "Core Team", "name": "Jude", "roles": ["Developer"]},
    {"section": "Core Team", "name": "Joel", "roles": ["Developer"]},
    {"section": "Core Team", "name": "Kregg", "roles": ["Developer"]},
    {"section": "Core Team", "name": "Oriye", "roles": ["Developer"]},
    {"section": "Music", "name": "Ben", "roles": ["Composer"]},
    {"section": "Art", "name": "Charlie", "roles": ["Artist"]},
]

TECH_STACK = [
    "Python",
    "pygame-ce",
    "pygbag",
    "aiohttp",
    "websockets",
    "Playwright",
    "pytest",
    "behave",
    "TypeScript",
]


def _normalize_roles(roles):
    if isinstance(roles, str):
        roles = [roles]
    if not isinstance(roles, (list, tuple)):
        return []
    return [r.strip() for r in roles if isinstance(r, str) and r.strip()]


def _format_entry(name, roles):
    roles = _normalize_roles(roles)
    if roles:
        return f"{name} — {', '.join(roles)}"
    return name


def _build_sections_from_entries(entries):
    grouped = []
    index = {}
    for entry in entries:
        section = entry.get("section", "").strip()
        name = entry.get("name", "").strip()
        roles = entry.get("roles", [])
        if not section or not name:
            continue
        if section not in index:
            index[section] = len(grouped)
            grouped.append((section, []))
        grouped[index[section]][1].append(_format_entry(name, roles))
    return grouped


# Each entry: ("Section Title", ["Name — Role1, Role2", ...])
CREDITS = _build_sections_from_entries(CREDIT_ENTRIES)


class CreditsScreen:
    _GRAD_TOP = (15, 15, 60)
    _GRAD_BOTTOM = (5, 5, 20)

    # Keyboard-keycap palette aligned with Keys Ninja styling.
    _KEY_FACE = (200, 150, 255)
    _KEY_FACE_HOVER = (225, 185, 255)
    _KEY_BASE = (120, 60, 200)
    _KEY_BASE_HOVER = (145, 90, 220)
    _KEY_OUTLINE = (40, 20, 80)
    _KEY_TEXT = (255, 255, 255)
    _KEY_DEPTH = 5  # visible side/bottom of the key

    # Non-keycap colors
    _ACCENT = (200, 150, 255)
    _HINT_TEXT = (150, 140, 200)
    _DIVIDER = (90, 70, 140)

    _SCROLL_SPEED = 60.0

    def __init__(self, screen):
        self.screen = screen
        self._fm = FontManager()
        self._back_rect = pygame.Rect(0, 0, 0, 0)
        self._scroll_y = None

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
        """Draw a keyboard-keycap at *center* sized to its text."""
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
        # Top face with its own outline
        pygame.draw.rect(self.screen, face_color, face_rect, border_radius=7)
        pygame.draw.rect(self.screen, self._KEY_OUTLINE, face_rect,
                         width=2, border_radius=7)

        # Label centered on the face
        text_surf = self._fm.render_text(text, self._KEY_TEXT, font_size)
        self.screen.blit(text_surf, text_surf.get_rect(center=face_rect.center))
        return outer_rect

    def _draw_keycap_at_rect(self, rect, text, font_size,
                             depth=None, face_color=None, base_color=None):
        """Draw a keycap that fills *rect* (treating rect as the full body)."""
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
        """Draw each character of *text* as its own keycap, laid out in a row."""
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
        return face_h + self._KEY_DEPTH

    def _title_height(self, font_size=34, pad_x=10, pad_y=8):
        _, face_h = self._keycap_size("X", font_size, pad_x, pad_y)
        return face_h + self._KEY_DEPTH

    def _draw_name_keys(self, names, center_x, top_y, max_width,
                        font_size=18, pad_x=10, pad_y=5, gap=7, row_gap=6,
                        draw=True):
        """Draw a set of name-keycaps centered horizontally, wrapping rows."""
        widths = [self._keycap_size(n, font_size, pad_x, pad_y)[0] for n in names]
        _, face_h = self._keycap_size("X", font_size, pad_x, pad_y)
        row_h = face_h + self._KEY_DEPTH

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

        y = top_y
        for row in rows:
            row_widths = [self._keycap_size(n, font_size, pad_x, pad_y)[0] for n in row]
            total_w = sum(row_widths) + gap * (len(row) - 1)
            x = center_x - total_w // 2
            for n, rw in zip(row, row_widths):
                if draw:
                    self._draw_keycap(
                        n, (x + rw // 2, y + row_h // 2),
                        font_size=font_size, pad_x=pad_x, pad_y=pad_y,
                    )
                x += rw + gap
            y += row_h + row_gap

        return y - top_y

    def _build_sections(self):
        sections = list(CREDITS)
        if TECH_STACK:
            sections.append(("Tech Stack", TECH_STACK))
        return sections

    def _measure_content(self, max_row_width):
        y = 0
        y += self._title_height(font_size=34, pad_x=10, pad_y=8) + 24
        for role, entries in self._build_sections():
            y += 28
            used = self._draw_name_keys(
                entries,
                center_x=0,
                top_y=0,
                max_width=max_row_width,
                font_size=18,
                pad_x=10,
                pad_y=5,
                gap=7,
                row_gap=6,
                draw=False,
            )
            y += used + 10
        y += 10
        return y

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

        scroll_top = 24
        scroll_bottom = H - 120
        scroll_rect = pygame.Rect(0, scroll_top, W, scroll_bottom - scroll_top)
        max_row_width = W - 60
        content_height = self._measure_content(max_row_width)

        if self._scroll_y is None:
            self._scroll_y = float(scroll_bottom)

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

            dt_ms = clock.tick(60)
            try:
                dt = float(dt_ms) / 1000.0
            except (TypeError, ValueError):
                dt = 0.0
            self._scroll_y -= self._SCROLL_SPEED * dt
            try:
                scroll_y_val = float(self._scroll_y)
                content_h_val = float(content_height)
                if scroll_y_val + content_h_val < scroll_top:
                    self._scroll_y = float(scroll_bottom)
            except (TypeError, ValueError):
                self._scroll_y = float(scroll_bottom)

            self.screen.set_clip(scroll_rect)

            y = int(self._scroll_y)
            title_h = self._draw_title_keys("CREDITS", cx, y,
                                            font_size=34, pad_x=10, pad_y=8, gap=4)

            y = y + title_h + 24
            for role, names in self._build_sections():
                role_surf = self._fm.render_text(role.upper(), self._ACCENT, 24)
                self.screen.blit(role_surf, role_surf.get_rect(center=(cx, y)))
                y += 28

                used = self._draw_name_keys(
                    names, center_x=cx, top_y=y,
                    max_width=max_row_width,
                    font_size=18, pad_x=10, pad_y=5, gap=7, row_gap=6,
                )
                y += used + 10

            self.screen.set_clip(None)

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
            await asyncio.sleep(0)
