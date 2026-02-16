import pygame

class PauseOverlay:
    """Reusable pause overlay that can be drawn on any screen"""
    
    def __init__(self, screen):
        self.screen = screen
        self.font_large = pygame.font.Font(None, 96)
        self.font_small = pygame.font.Font(None, 36)
        
    def draw_pause_start(self):
        """Draw the pause overlay on the screen"""
        # Semi-transparent black overlay
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(128)  # 50% transparency
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # "PAUSED" text
        paused_text = self.font_large.render("PAUSED", True, (255, 255, 255))
        paused_rect = paused_text.get_rect(
            center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 50)
        )
        self.screen.blit(paused_text, paused_rect)
        
        # Instructions
        instruction_text = self.font_small.render(
            "Press P to Resume", 
            True, 
            (200, 200, 200)
        )
        instruction_rect = instruction_text.get_rect(
            center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 50)
        )
        self.screen.blit(instruction_text, instruction_rect)