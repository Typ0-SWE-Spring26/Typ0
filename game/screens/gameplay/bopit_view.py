import pygame
from game.screens.gameplay.view import GameView
from game.utils import animation_utils


class BopItView(GameView):
    """Bop-It variant of the game view — shows the current command prominently."""

    def __init__(self, screen, key_labels):
        super().__init__(screen, key_labels)
        self.font_mode = pygame.font.SysFont(None, 28)
        self.font_emo   = pygame.font.SysFont(None, 28)

    def draw(self, model, timer_fraction):
        """Render one frame for Bop-It mode."""
        self.screen.fill((15, 15, 25))
        W = self.screen.get_width()

        hud_h = self._draw_hud_panel()
        # SCORE shifts right to leave room for the MENU button now living in the header.
        score_surf = self.font_small.render(f"SCORE  {model.score}", True, (235, 235, 245))
        self.screen.blit(score_surf, score_surf.get_rect(midleft=(100, hud_h // 2)))

        mode_surf = self.font_mode.render("BOP IT", True, (255, 185, 60))
        self.screen.blit(mode_surf, mode_surf.get_rect(midright=(W - 24, hud_h // 2)))

        # Emo flavor in HUD center
        emo_idx = min(model.score, len(self._emo_lines) - 1)
        emo_surf = self.font_emo.render(self._emo_lines[emo_idx], True, (180, 150, 220))
        emo_surf.set_alpha(200)
        self.screen.blit(emo_surf, emo_surf.get_rect(center=(W // 1.87, hud_h // 2)))

        # Draw buttons — highlight only the target command
        for name, rect in self.button_rects.items():
            if name == model.flash_button:
                self.screen.blit(self.scaled[name][model.flash_state], rect)
            elif model.state == 'input' and name == model.current_command:
                self.screen.blit(self.scaled[name]['normal'], rect)
            elif model.state in ('prompting', 'gameover'):
                surf = self.scaled[name]['normal'].copy()
                surf.set_alpha(80)
                self.screen.blit(surf, rect)
            else:
                surf = self.scaled[name]['normal'].copy()
                surf.set_alpha(120)
                self.screen.blit(surf, rect)

            animation_utils.draw_shadowed_text(
                self.screen, self.font_label, self.key_labels[name], rect.center
            )

        if model.state == 'input':
            self._draw_timer_bar(timer_fraction, gradient=True)


            
