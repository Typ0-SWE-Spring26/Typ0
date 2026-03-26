import pygame

class FontManager:
    def __init__(self):
        # Use Courier font for that retro terminal look
        self.font_sizes = {}
        
    def get_font(self, size):
        """Get Courier font with specific size"""
        if size not in self.font_sizes:
            try:
                # Try to use Courier New or Courier
                self.font_sizes[size] = pygame.font.SysFont('Courier New', size, bold=True)
            except:
                try:
                    self.font_sizes[size] = pygame.font.SysFont('Courier', size, bold=True)
                except:
                    # Fallback to default font
                    self.font_sizes[size] = pygame.font.Font(None, size)
        return self.font_sizes[size]
    
    def render_text(self, text, color=(255, 255, 255), size=24):
        """Render text with Courier font"""
        font = self.get_font(size)
        return font.render(text, True, color)