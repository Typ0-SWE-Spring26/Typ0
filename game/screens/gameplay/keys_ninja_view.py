import pygame
import math
from game.screens.gameplay.view import GameView


class KeysNinjaView(GameView):
    """Keys Ninja variant - shows falling keys that must be pressed."""
    
    def __init__(self, screen, key_labels):
        super().__init__(screen, key_labels)
        self.font_key = pygame.font.SysFont(None, 48)
        self.font_mode = pygame.font.SysFont(None, 28)
        self.font_combo = pygame.font.SysFont(None, 36)
        
        # Purple theme colors
        self.purple_light = (180, 120, 255)
        self.purple_dark = (120, 60, 200)
        self.purple_glow = (200, 150, 255)
        self.red_bomb = (255, 60, 60)
    
    def _draw_key_object(self, key_obj):
        """Draw a single falling key with rotation and high quality rendering."""
        # Key size with scale
        base_size = 70  # Larger for better quality
        key_size = int(base_size * key_obj.scale)
        
        # Create surface for the key with extra padding for anti-aliasing
        surf_size = key_size + 20
        key_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        
        # Determine color
        if key_obj.is_bomb:
            color = self.red_bomb
            border_color = (200, 40, 40)
            inner_color = (255, 80, 80)
        else:
            color = self.purple_light
            border_color = (220, 180, 255)
            inner_color = (200, 150, 255)
        
        # Calculate center position
        center = surf_size // 2
        key_radius = (key_size - 10) // 2
        
        # Draw multiple layers for depth and quality
        offset = 5
        rect = pygame.Rect(offset, offset, key_size - 10, key_size - 10)
        
        # Outer shadow (soft)
        shadow_rect = rect.move(3, 4)
        shadow_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 80), shadow_rect, border_radius=12)
        key_surf.blit(shadow_surf, (0, 0))
        
        # Main key body with gradient effect
        pygame.draw.rect(key_surf, color, rect, border_radius=12)
        
        # Inner gradient for depth
        inner_rect = pygame.Rect(rect.x + 3, rect.y + 3, rect.width - 6, rect.height - 6)
        pygame.draw.rect(key_surf, inner_color, inner_rect, border_radius=10)
        
        # Top highlight (glossy effect)
        highlight_rect = pygame.Rect(rect.x + 8, rect.y + 8, rect.width - 16, rect.height // 2 - 8)
        if highlight_rect.width > 0 and highlight_rect.height > 0:
            highlight_surf = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(highlight_surf, (255, 255, 255, 60), 
                            pygame.Rect(0, 0, highlight_rect.width, highlight_rect.height), 
                            border_radius=8)
            key_surf.blit(highlight_surf, (highlight_rect.x, highlight_rect.y))
        
        # Outer border (thick for quality)
        pygame.draw.rect(key_surf, border_color, rect, width=4, border_radius=12)
        
        # Inner border for extra definition
        inner_border_rect = pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, rect.height - 4)
        pygame.draw.rect(key_surf, (255, 255, 255, 100), inner_border_rect, width=2, border_radius=10)
        
        # Draw character with anti-aliasing
        char_text = key_obj.char
        font_size = int(52 * key_obj.scale)
        char_font = pygame.font.SysFont('Arial', font_size, bold=True)
        
        # Character shadow for depth
        char_shadow = char_font.render(char_text, True, (0, 0, 0, 150))
        char_shadow_rect = char_shadow.get_rect(center=(center + 2, center + 2))
        key_surf.blit(char_shadow, char_shadow_rect)
        
        # Main character
        char_surf = char_font.render(char_text, True, (255, 255, 255))
        char_rect = char_surf.get_rect(center=(center, center))
        key_surf.blit(char_surf, char_rect)
        
        # Apply alpha
        key_surf.set_alpha(int(key_obj.alpha))
        
        # Rotate with smooth interpolation
        rotated = pygame.transform.rotozoom(key_surf, key_obj.rotation, 1.0)
        rotated_rect = rotated.get_rect(center=(int(key_obj.x), int(key_obj.y)))
        
        self.screen.blit(rotated, rotated_rect)
    
    def draw(self, model, timer_fraction):
        """Render one frame for Keys Ninja mode."""
        # Dark background with slight gradient
        self.screen.fill((10, 5, 20))
        W = self.screen.get_width()
        H = self.screen.get_height()
        
        # Draw subtle grid pattern
        grid_color = (30, 20, 50)
        for i in range(0, W, 50):
            pygame.draw.line(self.screen, grid_color, (i, 0), (i, H), 1)
        for i in range(0, H, 50):
            pygame.draw.line(self.screen, grid_color, (0, i), (W, i), 1)
        
        # Draw HUD
        hud_h = self._draw_hud_panel()
        
        # Score (left side, moved right to avoid menu button)
        score_surf = self.font_small.render(f"SCORE  {model.score}", True, (235, 235, 245))
        self.screen.blit(score_surf, score_surf.get_rect(midleft=(140, hud_h // 2)))  # Moved from 24 to 140
        
        # Lives (right side) - draw X symbols
        lives_x = W - 24
        life_spacing = 35
        for i in range(model.lives):
            life_x = lives_x - (i * life_spacing)
            # Draw X symbol for lives
            life_surf = self.font_combo.render("X", True, (255, 100, 100))
            self.screen.blit(life_surf, life_surf.get_rect(midright=(life_x, hud_h // 2)))
        
        # Mode label (center)
        mode_surf = self.font_mode.render("KEYS NINJA", True, self.purple_light)
        self.screen.blit(mode_surf, mode_surf.get_rect(center=(W // 2, hud_h // 2)))
        
        # Combo display (center of HUD) - removed for now
        # if model.combo > 1:
        #     combo_text = f"COMBO x{model.combo}!"
        #     combo_surf = self.font_combo.render(combo_text, True, (255, 220, 100))
        #     pulse = abs(math.sin(pygame.time.get_ticks() / 200)) * 0.2 + 0.8
        #     combo_surf = pygame.transform.scale(
        #         combo_surf, 
        #         (int(combo_surf.get_width() * pulse), int(combo_surf.get_height() * pulse))
        #     )
        #     self.screen.blit(combo_surf, combo_surf.get_rect(center=(W // 2, hud_h // 2)))
        
        # Draw all falling keys
        for key_obj in model.keys:
            self._draw_key_object(key_obj)
        
        # Draw max combo at bottom - removed for now
        # if model.max_combo > 1:
        #     max_combo_surf = self.font_small.render(
        #         f"Best Combo: {model.max_combo}", True, (150, 150, 200)
        #     )
        #     self.screen.blit(max_combo_surf, max_combo_surf.get_rect(center=(W // 2, H - 120)))
