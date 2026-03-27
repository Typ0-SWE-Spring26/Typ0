import pygame
from game.screens.gameplay.view import GameView
from game.utils import animation_utils


class BopItView(GameView):
    """Bop-It variant of the game view — shows the current command prominently."""

    def __init__(self, screen, key_labels):
        super().__init__(screen, key_labels)
        self.font_command = pygame.font.SysFont(None, 72)
        self.font_mode    = pygame.font.SysFont(None, 28)

    def draw(self, model, timer_fraction):
        """Render one frame for Bop-It mode."""
        self.screen.fill((15, 15, 25))
        W = self.screen.get_width()
        H = self.screen.get_height()
        # HUD
        score_surf = self.font_small.render(f"Score: {model.score}", True, (200, 200, 200))
        self.screen.blit(score_surf, (20, 20))

        mode_surf = self.font_mode.render("BOP IT", True, (255, 180, 50))
        self.screen.blit(mode_surf, mode_surf.get_rect(topright=(W - 20, 20)))

        # Command prompt
        if model.state == 'input' and model.current_command:
            press=self.font_small.render("Press", True, (255, 255, 100))
            label = model.COMMAND_LABELS.get(model.current_command, "???")
            cmd_surf = self.font_small.render(label, True, (255, 255, 100))
            self.screen.blit(press, press.get_rect(center=(W // 2, (H // 3)+50)))
            self.screen.blit(cmd_surf, cmd_surf.get_rect(center=(W // 2, (H // 3)+70)))
        elif model.state == 'prompting':
            s = self.font_small.render("Get ready...", True, (160, 160, 255))
            self.screen.blit(s, s.get_rect(center=(W // 2, (H // 3)+30)))

        # Draw buttons — highlight only the target command
        for name, rect in self.button_rects.items():
            if name == model.flash_button:
                self.screen.blit(self.scaled[name][model.flash_state], rect)
            elif model.state == 'input' and name == model.current_command:
                # Full brightness for the target button
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

        # Timer bar
        if model.state == 'input':
            H = self.screen.get_height()
            bar_width = int(timer_fraction * (W - 40))
            # Color shifts from green -> yellow -> red as time runs out
            r = int(255 * (1 - timer_fraction))
            g = int(255 * timer_fraction)
            pygame.draw.rect(self.screen, (r, g, 80), (20, H - 20, bar_width, 10))
