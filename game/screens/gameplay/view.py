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
        s = 90    # arrow button size
        gap = 100  # center-to-center distance

        self.button_rects = {
            'up':    pygame.Rect(cx - s // 2,       cy - gap - s // 2, s, s),
            'down':  pygame.Rect(cx - s // 2,       cy + gap - s // 2, s, s),
            'left':  pygame.Rect(cx - gap - s // 2, cy - s // 2,       s, s),
            'right': pygame.Rect(cx + gap - s // 2, cy - s // 2,       s, s),
            'space': pygame.Rect(cx - 110,          cy + gap + 60,     220, 55),
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
        self.font_label = pygame.font.SysFont(None, 26)

    def draw(self, model, timer_fraction, opp_score=None, opp_status=""):
        """Render one frame based on current model state."""
        self.screen.fill((15, 15, 25))

        W = self.screen.get_width()

        # HUD — own score top-left
        score_surf = self.font_small.render(f"Score: {model.score}", True, (200, 200, 200))
        self.screen.blit(score_surf, (20, 20))

        # HUD — opponent score/status top-right (multiplayer only)
        if opp_score is not None:
            opp_color = (255, 120, 120) if opp_status == "gameover" else (180, 180, 255)
            opp_label = f"Opp: {opp_score}"
            opp_surf  = self.font_small.render(opp_label, True, opp_color)
            self.screen.blit(opp_surf, opp_surf.get_rect(topright=(W - 20, 20)))

        round_surf = self.font_small.render(f"Round {len(model.sequence)}", True, (150, 150, 150))
        # Shift round counter down if opponent HUD is present
        round_y = 50 if opp_score is not None else 20
        self.screen.blit(round_surf, round_surf.get_rect(topright=(W - 20, round_y)))

        # Status message
        if model.state == 'showing':
            status_text  = "Watch carefully..."
            status_color = (160, 160, 255)
        elif model.state == 'input':
            remaining    = len(model.sequence) - model.player_index
            status_text  = f"Your turn!  ({remaining} left)"
            status_color = (160, 255, 160)
        else:
            status_text  = ""
            status_color = (200, 200, 200)

        if status_text:
            s = self.font_small.render(status_text, True, status_color)
            self.screen.blit(s, s.get_rect(center=(W // 2, 55)))

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

        # Timer bar (only during player's turn)
        if model.state == 'input':
            H = self.screen.get_height()
            bar_width = int(timer_fraction * (W - 40))
            pygame.draw.rect(self.screen, (255, 100, 100), (20, H - 20, bar_width, 10))

        # Multiplayer result banner
        if opp_status in ("gameover", "disconnected"):
            H = self.screen.get_height()
            if opp_status == "gameover":
                banner_text  = "Opponent lost — You Win!"
                banner_color = (80, 200, 80)
            else:
                banner_text  = "Opponent disconnected!"
                banner_color = (200, 180, 60)
            overlay = pygame.Surface((W, 56), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, H // 2 - 28))
            banner_surf = self.font_small.render(banner_text, True, banner_color)
            self.screen.blit(banner_surf, banner_surf.get_rect(center=(W // 2, H // 2)))
