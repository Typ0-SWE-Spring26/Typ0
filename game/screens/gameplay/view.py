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

        # Cache the static HUD background — recreating an SRCALPHA surface every
        # frame leaks memory in pygbag/WASM and can stall the browser tab.
        self._hud_h = 50
        self._hud_panel = pygame.Surface((W, self._hud_h), pygame.SRCALPHA)
        self._hud_panel.fill((30, 30, 50, 190))

    def _draw_hud_panel(self):
        """Shared top HUD strip background — subclasses blit labels on top."""
        W = self.screen.get_width()
        self.screen.blit(self._hud_panel, (0, 0))
        pygame.draw.line(self.screen, (80, 80, 120), (0, self._hud_h), (W, self._hud_h), 2)
        return self._hud_h

    def _draw_status_centered(self, text, color, y):
        """Draw status text centered at y — sits inside the HUD bar."""
        W = self.screen.get_width()
        surf = self.font_small.render(text, True, color)
        self.screen.blit(surf, surf.get_rect(center=(W // 2, y)))

    def _draw_timer_bar(self, fraction, gradient=True):
        """Slim rounded timer bar tucked between the HUD header and the buttons."""
        W = self.screen.get_width()
        bar_x, bar_h = 20, 10
        bar_y = 56
        bar_w = W - 40
        # Clamp incoming fraction defensively — out-of-range values from a
        # rogue timer state would otherwise push the fill rect or color
        # channels into invalid territory.
        f = max(0.0, min(1.0, float(fraction)))
        track_radius = bar_h // 2
        track = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(self.screen, (35, 35, 55), track, border_radius=track_radius)

        fill_w = max(0, int(f * bar_w))
        if fill_w > 0:
            if gradient:
                # Clamp so a near-empty bar doesn't push channels above 255.
                r = min(255, max(0, int(240 * (1 - f)) + 40))
                g = min(255, max(0, int(200 * f) + 55))
                color = (r, g, 90)
            else:
                color = (240, 90, 90)
            # pygame's rounded-rect renderer in pygbag can hang/crash when
            # border_radius >= min(width, height)/2. Drop the radius to fit.
            fill_radius = min(track_radius, fill_w // 2)
            pygame.draw.rect(self.screen, color,
                             pygame.Rect(bar_x, bar_y, fill_w, bar_h),
                             border_radius=fill_radius)
        pygame.draw.rect(self.screen, (80, 80, 110), track, width=1,
                         border_radius=track_radius)

    def draw(self, model, timer_fraction):
        """Render one frame based on current model state."""
        self.screen.fill((15, 15, 25))
        W = self.screen.get_width()

        hud_h = self._draw_hud_panel()
        # SCORE shifts right to leave room for the MENU button now living in the header.
        score_surf = self.font_small.render(f"SCORE  {model.score}", True, (235, 235, 245))
        self.screen.blit(score_surf, score_surf.get_rect(midleft=(100, hud_h // 2)))

        round_surf = self.font_small.render(
            f"ROUND  {len(model.sequence)}", True, (185, 205, 255))
        self.screen.blit(round_surf, round_surf.get_rect(midright=(W - 24, hud_h // 2)))

        # Only the remaining-input counter survives — no instructional alerts.
        if model.state == 'input':
            remaining = len(model.sequence) - model.player_index
            self._draw_status_centered(
                f"{remaining} left", (170, 255, 170), hud_h // 2)

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
            line_idx = min(max(round_num - 1, 0), len(self._emo_lines) - 1)
            emo_text = self._emo_lines[line_idx]
            H = self.screen.get_height()
            emo_surf = self.font_emo.render(emo_text, True, (160, 130, 200))
            emo_surf.set_alpha(180)
            self.screen.blit(emo_surf, emo_surf.get_rect(center=(W // 2, H - 20)))
