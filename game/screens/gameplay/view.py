import pygame
import os
from game.utils import animation_utils


class GameView:
    """Renders the game — reads from GameModel, never mutates it."""

    # (normal, indicated, pressed) paths relative to assets/Typo-buttons/
    BUTTON_FILES = {
        'left':  ('left.png',  'button-indicated/leftIndicate.png',  'button-pressed/leftPress.png'),
        'right': ('right.png', 'button-indicated/rightIndicate.png', 'button-pressed/rightPress.png'),
        'up':    ('up.png',    'button-indicated/upIndicate.png',    'button-pressed/upPress.png'),
        'down':  ('down.png',  'button-indicated/downIndicate.png',  'button-pressed/downPress.png'),
        'space': ('space.png', 'button-indicated/spaceIndicate.png', 'button-pressed/spacePress.png'),
    }

    def __init__(self, screen, key_labels):

        self.screen = screen
        self.key_labels = key_labels
        W, H = screen.get_width(), screen.get_height()

        asset_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'assets', 'Typo-buttons')

        # Load all 3 sprite states per button
        self.sprites = {}
        for name, (normal_f, indicated_f, pressed_f) in self.BUTTON_FILES.items():
            self.sprites[name] = {
                'normal':    pygame.image.load(os.path.join(asset_dir, normal_f)).convert_alpha(),
                'indicated': pygame.image.load(os.path.join(asset_dir, indicated_f)).convert_alpha(),
                'pressed':   pygame.image.load(os.path.join(asset_dir, pressed_f)).convert_alpha(),
            }

        # Button layout — tight d-pad cross centered slightly above mid, space below
        cx, cy = W // 2, H // 2 - 40
        spah = 210; #height of space bar
        spaw = 305; #width of space bar
        self.button_rects = {
            'up':    pygame.Rect(0, H//8, W, cy-(spah//2)+20),
            'down':  pygame.Rect(0, cy +spah-10, W, cy-(spah//2)+20),
            'left':  pygame.Rect(0,H//8, cx-155, H-40),
            'right': pygame.Rect(cx+(spaw//2)-2, H//8, cx-155, H-40),
            'space': pygame.Rect(cx - 155, cy-10, spaw, spah),
        }

        # Pre-scale every state to its rect size once
        self.scaled = {}
        for name, rect in self.button_rects.items():
            size = (rect.width, rect.height)
            self.scaled[name] = {
                state: pygame.transform.smoothscale(surf, size)
                for state, surf in self.sprites[name].items()
            }

        self.font_small = pygame.font.SysFont(None, 32)
        self.font_label = pygame.font.SysFont(None, 50)
        self.font_emo   = pygame.font.SysFont(None, 28)

        # Emo flavor lines shown at game start (round 1 intro)
        self._emo_lines = [
            "nobody understands me... or this sequence",
            "watch the buttons. like they're the only ones left.",
            "memorize this pattern. it's all you have now.",
            "the sequence grows. just like the emptiness inside.",
            "you press the keys. but do the keys press back?",
            "another round begins. another chance to feel something.",
        ]

    def _draw_hud_panel(self):
        """Shared top HUD strip background — subclasses blit labels on top."""
        W = self.screen.get_width()
        hud_h = 50
        panel = pygame.Surface((W, hud_h), pygame.SRCALPHA)
        panel.fill((30, 30, 50, 190))
        self.screen.blit(panel, (0, 0))
        pygame.draw.line(self.screen, (80, 80, 120), (0, hud_h), (W, hud_h), 2)
        return hud_h

    def _draw_status_centered(self, text, color, y):
        """Draw status text centered at y — sits inside the HUD bar."""
        W = self.screen.get_width()
        surf = self.font_small.render(text, True, color)
        self.screen.blit(surf, surf.get_rect(center=(W // 2, y)))

    def _draw_timer_bar(self, fraction, gradient=True):
        """Prominent rounded timer bar, placed above the MENU button."""
        W = self.screen.get_width()
        H = self.screen.get_height()
        bar_x, bar_h = 20, 14
        bar_y = H - 95
        bar_w = W - 40
        track = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(self.screen, (35, 35, 55), track, border_radius=bar_h // 2)

        fill_w = max(0, int(fraction * bar_w))
        if fill_w > 0:
            if gradient:
                r = int(240 * (1 - fraction)) + 40
                g = int(200 * fraction) + 55
                color = (r, g, 90)
            else:
                color = (240, 90, 90)
            pygame.draw.rect(self.screen, color,
                             pygame.Rect(bar_x, bar_y, fill_w, bar_h),
                             border_radius=bar_h // 2)
        pygame.draw.rect(self.screen, (80, 80, 110), track, width=1,
                         border_radius=bar_h // 2)

    def draw(self, model, timer_fraction):
        """Render one frame based on current model state."""
        self.screen.fill((15, 15, 25))
        W = self.screen.get_width()

        hud_h = self._draw_hud_panel()
        score_surf = self.font_small.render(f"SCORE  {model.score}", True, (235, 235, 245))
        self.screen.blit(score_surf, score_surf.get_rect(midleft=(24, hud_h // 2)))

        round_surf = self.font_small.render(
            f"ROUND  {len(model.sequence)}", True, (185, 205, 255))
        self.screen.blit(round_surf, round_surf.get_rect(midright=(W - 24, hud_h // 2)))

        # Status message — centered inside the HUD bar, between SCORE and ROUND
        if model.state == 'showing':
            self._draw_status_centered("Watch carefully...", (170, 170, 255), hud_h // 2)
        elif model.state == 'input':
            remaining = len(model.sequence) - model.player_index
            self._draw_status_centered(
                f"Your turn  -  {remaining} left", (170, 255, 170), hud_h // 2)

        # Draw buttons
        for name, rect in self.button_rects.items():
            if name == model.flash_button:
                self.screen.blit(self.scaled[name][model.flash_state], rect)
            elif model.state in ('showing', 'adding', 'gameover'):
                surf = self.scaled[name]['normal'].copy()
                surf.set_alpha(80)
                self.screen.blit(surf, rect)
            else:
                self.screen.blit(self.scaled[name]['normal'], rect)

            animation_utils.draw_shadowed_text(
                self.screen, self.font_label, self.key_labels[name], rect.center
            )

        if model.state == 'input':
            self._draw_timer_bar(timer_fraction, gradient=True)
        # emo flavor text (shown during the showing/adding phase)
        if model.state in ('adding', 'showing'):
            round_num = len(model.sequence)
            line_idx = min(round_num, len(self._emo_lines) - 1)
            emo_text = self._emo_lines[line_idx]
            H = self.screen.get_height()
            emo_surf = self.font_emo.render(emo_text, True, (160, 130, 200))
            emo_surf.set_alpha(180)
            self.screen.blit(emo_surf, emo_surf.get_rect(center=(W // 2, H - 20)))
