import asyncio
import os

import pygame

from assets.font_loader import FontManager
from game.utils import animation_utils


class HowToPlayScreen:
    """Dedicated full-screen guide for controls and game modes."""

    _GRAD_TOP = (18, 22, 60)
    _GRAD_BOTTOM = (6, 8, 24)

    _PANEL_BG = (14, 18, 40)
    _PANEL_BORDER = (76, 96, 170)
    _SECTION_BG = (20, 26, 54)
    _SECTION_BORDER = (64, 80, 140)

    _TEXT_MAIN = (236, 242, 255)
    _TEXT_MUTED = (170, 184, 222)
    _TEXT_ACCENT = (255, 214, 104)
    _TEXT_GOOD = (160, 238, 196)

    _ICON_FILES = {
        "up": "up.png",
        "down": "down.png",
        "left": "left.png",
        "right": "right.png",
        "space": "space.png",
    }

    _INPUT_ROWS = [
        ("up", ("W", "UP"), "Match UP prompts"),
        ("down", ("S", "DOWN"), "Match DOWN prompts"),
        ("left", ("A", "LEFT"), "Match LEFT prompts"),
        ("right", ("D", "RIGHT"), "Match RIGHT prompts"),
        ("space", ("SPACE",), "Match CENTER prompts"),
    ]

    def __init__(self, screen):
        self.screen = screen
        self._fm = FontManager()

        self._icons = {}
        self._scaled_icon_cache = {}
        self._load_icons()

        self._back_rect = pygame.Rect(0, 0, 0, 0)
        self._credits_rect = pygame.Rect(0, 0, 0, 0)

    # ------------------------------------------------------------------
    # Asset helpers
    # ------------------------------------------------------------------

    def _load_icons(self):
        base = os.path.join("assets", "Typo-buttons")
        for name, filename in self._ICON_FILES.items():
            try:
                path = os.path.join(base, filename)
                self._icons[name] = pygame.image.load(path).convert_alpha()
            except Exception:
                self._icons[name] = None

    def _get_scaled_icon(self, name, size):
        key = (name, int(size[0]), int(size[1]))
        if key in self._scaled_icon_cache:
            return self._scaled_icon_cache[key]

        src = self._icons.get(name)
        if src is None:
            return None

        src_w, src_h = src.get_size()
        if src_w <= 0 or src_h <= 0:
            return None

        scale = min(size[0] / src_w, size[1] / src_h)
        out_w = max(1, int(src_w * scale))
        out_h = max(1, int(src_h * scale))
        scaled = pygame.transform.smoothscale(src, (out_w, out_h))
        self._scaled_icon_cache[key] = scaled
        return scaled

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_key_chip(self, text, x, y, h=30):
        width = max(44, 18 + len(text) * 12)
        rect = pygame.Rect(x, y - h // 2, width, h)
        pygame.draw.rect(self.screen, (30, 36, 70), rect, border_radius=8)
        pygame.draw.rect(self.screen, (108, 122, 190), rect, width=2, border_radius=8)
        surf = self._fm.render_text(text, self._TEXT_MAIN, 18)
        self.screen.blit(surf, surf.get_rect(center=rect.center))
        return rect.right

    def _draw_backdrop_glow(self, w, h):
        glow = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 190, 90, 42), (int(w * 0.18), int(h * 0.24)), int(min(w, h) * 0.32))
        pygame.draw.circle(glow, (100, 170, 255, 32), (int(w * 0.84), int(h * 0.2)), int(min(w, h) * 0.24))
        pygame.draw.circle(glow, (92, 220, 180, 28), (int(w * 0.82), int(h * 0.78)), int(min(w, h) * 0.28))
        self.screen.blit(glow, (0, 0))

    def _draw_left_column(self, rect):
        pygame.draw.rect(self.screen, self._SECTION_BG, rect, border_radius=16)
        pygame.draw.rect(self.screen, self._SECTION_BORDER, rect, width=2, border_radius=16)

        heading = self._fm.render_text("INPUT MAP", self._TEXT_ACCENT, 28)
        self.screen.blit(heading, heading.get_rect(midleft=(rect.x + 16, rect.y + 22)))

        row_area_top = rect.y + 44
        row_area_h = rect.height - 54
        row_h = max(48, min(62, row_area_h // len(self._INPUT_ROWS)))

        for idx, (icon_name, key_labels, action_text) in enumerate(self._INPUT_ROWS):
            row_y = row_area_top + idx * row_h
            row_rect = pygame.Rect(rect.x + 10, row_y, rect.width - 20, row_h - 6)

            shade = (26, 32, 66) if idx % 2 == 0 else (24, 29, 60)
            pygame.draw.rect(self.screen, shade, row_rect, border_radius=10)

            icon_box = pygame.Rect(row_rect.x + 8, row_rect.y + 5, 82, row_rect.height - 10)
            icon = self._get_scaled_icon(icon_name, icon_box.size)
            if icon is not None:
                icon_rect = icon.get_rect(center=icon_box.center)
                self.screen.blit(icon, icon_rect)
            else:
                pygame.draw.rect(self.screen, (40, 44, 78), icon_box, border_radius=8)
                fallback = self._fm.render_text(icon_name.upper(), self._TEXT_MUTED, 16)
                self.screen.blit(fallback, fallback.get_rect(center=icon_box.center))

            x = icon_box.right + 14
            for i, label in enumerate(key_labels):
                x = self._draw_key_chip(label, x, row_rect.centery)
                if i < len(key_labels) - 1:
                    join = self._fm.render_text("/", self._TEXT_MUTED, 18)
                    self.screen.blit(join, join.get_rect(center=(x + 10, row_rect.centery)))
                    x += 20

            action = self._fm.render_text(action_text, self._TEXT_MAIN, 19)
            action_rect = action.get_rect(midleft=(x + 14, row_rect.centery))
            if action_rect.right > row_rect.right - 8:
                action_rect.right = row_rect.right - 8
            self.screen.blit(action, action_rect)

    def _draw_right_column(self, rect):
        pygame.draw.rect(self.screen, self._SECTION_BG, rect, border_radius=16)
        pygame.draw.rect(self.screen, self._SECTION_BORDER, rect, width=2, border_radius=16)

        x = rect.x + 14
        y = rect.y + 14

        guide_title = self._fm.render_text("QUICK GUIDE", self._TEXT_ACCENT, 25)
        self.screen.blit(guide_title, guide_title.get_rect(topleft=(x, y)))
        y += 34

        lines = [
            ("SIMON", "Repeat the full sequence in order."),
            ("BOP IT", "React to one command before time runs out."),
            ("MENU", "Open settings, music, and mode switching."),
        ]
        for label, desc in lines:
            label_surf = self._fm.render_text(label, self._TEXT_GOOD, 20)
            self.screen.blit(label_surf, label_surf.get_rect(topleft=(x, y)))
            y += 22
            desc_surf = self._fm.render_text(desc, self._TEXT_MAIN, 18)
            self.screen.blit(desc_surf, desc_surf.get_rect(topleft=(x + 10, y)))
            y += 30

        y += 8
        short_title = self._fm.render_text("SHORTCUTS", self._TEXT_ACCENT, 23)
        self.screen.blit(short_title, short_title.get_rect(topleft=(x, y)))
        y += 32

        y_center = y + 14
        chip_right = self._draw_key_chip("P", x, y_center, h=30)
        pause_text = self._fm.render_text("Pause / Resume", self._TEXT_MAIN, 18)
        self.screen.blit(pause_text, pause_text.get_rect(midleft=(chip_right + 10, y_center)))

        y += 36
        y_center = y + 14
        chip_right = self._draw_key_chip("ESC", x, y_center, h=30)
        esc_text = self._fm.render_text("Close menus / Back", self._TEXT_MAIN, 18)
        self.screen.blit(esc_text, esc_text.get_rect(midleft=(chip_right + 10, y_center)))

        y += 36
        y_center = y + 14
        chip_right = self._draw_key_chip("MOUSE", x, y_center, h=30)
        mouse_text = self._fm.render_text("Click on-screen prompts", self._TEXT_MAIN, 18)
        self.screen.blit(mouse_text, mouse_text.get_rect(midleft=(chip_right + 10, y_center)))

        tip = self._fm.render_text("Tip: switch mode from MENU anytime.", self._TEXT_MUTED, 16)
        self.screen.blit(tip, tip.get_rect(midleft=(x, rect.bottom - 24)))

    def _draw(self):
        w = self.screen.get_width()
        h = self.screen.get_height()

        animation_utils.draw_gradient(self.screen, self._GRAD_TOP, self._GRAD_BOTTOM)
        self._draw_backdrop_glow(w, h)

        margin_x = max(16, w // 35)
        panel = pygame.Rect(margin_x, 18, w - 2 * margin_x, h - 112)

        pygame.draw.rect(self.screen, (6, 9, 22), panel.move(0, 4), border_radius=20)
        pygame.draw.rect(self.screen, self._PANEL_BG, panel, border_radius=20)
        pygame.draw.rect(self.screen, self._PANEL_BORDER, panel, width=2, border_radius=20)

        title = self._fm.render_text("HOW TO PLAY", self._TEXT_ACCENT, 48)
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 36)))

        subtitle = self._fm.render_text(
            "Learn the controls fast, then jump right back in.",
            self._TEXT_MUTED,
            20,
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(panel.centerx, panel.y + 72)))

        content_top = panel.y + 94
        content_h = panel.height - 108
        left_w = int(panel.width * 0.64)
        left_rect = pygame.Rect(panel.x + 14, content_top, left_w, content_h)
        right_rect = pygame.Rect(
            left_rect.right + 14,
            content_top,
            panel.right - left_rect.right - 28,
            content_h,
        )

        self._draw_left_column(left_rect)
        self._draw_right_column(right_rect)

        button_y = h - 78
        button_w = 200
        button_h = 50
        gap = 20
        total = button_w * 2 + gap
        row_left = panel.centerx - total // 2

        self._back_rect = pygame.Rect(row_left, button_y, button_w, button_h)
        self._credits_rect = pygame.Rect(row_left + button_w + gap, button_y, button_w, button_h)

        mouse = pygame.mouse.get_pos()
        for rect, label in ((self._back_rect, "BACK"), (self._credits_rect, "CREDITS")):
            hover = rect.collidepoint(mouse)
            color = (104, 118, 190) if hover else (62, 76, 136)
            pygame.draw.rect(self.screen, (8, 10, 24), rect.move(0, 3), border_radius=12)
            pygame.draw.rect(self.screen, color, rect, border_radius=12)
            pygame.draw.rect(self.screen, (150, 165, 240), rect, width=2, border_radius=12)
            text = self._fm.render_text(label, self._TEXT_MAIN, 26)
            self.screen.blit(text, text.get_rect(center=rect.center))

        hint = self._fm.render_text("ESC / Q to go back", self._TEXT_MUTED, 16)
        self.screen.blit(hint, hint.get_rect(center=(panel.centerx, h - 24)))

    # ------------------------------------------------------------------
    # Public async entry point
    # Returns:
    #   "back"    - return to previous screen
    #   "credits" - open credits screen
    #   "quit"    - app/window closed
    # ------------------------------------------------------------------

    async def run(self):
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
                    return "back"

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._back_rect.collidepoint(event.pos):
                        return "back"
                    if self._credits_rect.collidepoint(event.pos):
                        return "credits"

            self._draw()
            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)
