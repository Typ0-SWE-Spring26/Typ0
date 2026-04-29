import pygame


# Sans-serif fallback chain used when a screen wants a more readable face
# than the default Courier. First name that pygame can resolve wins.
SANS_SERIF_PREFERRED = "Verdana,DejaVuSans,Arial"


class FontManager:
    def __init__(self):
        # Cache key is (font_name or _default, size, bold) so multiple
        # families can coexist without trampling each other.
        self.font_sizes = {}

    def get_font(self, size, font_name=None, bold=True):
        """Return a font at *size*. Default face is bold Courier (the
        retro-terminal look used across the game). Pass `font_name` (a
        single name or comma-separated fallback list) to opt into a
        different face on a per-screen basis.
        """
        key = (font_name or "_default", size, bold)
        if key in self.font_sizes:
            return self.font_sizes[key]

        if font_name:
            try:
                self.font_sizes[key] = pygame.font.SysFont(font_name, size, bold=bold)
            except Exception:
                self.font_sizes[key] = pygame.font.Font(None, size)
        else:
            try:
                self.font_sizes[key] = pygame.font.SysFont('Courier New', size, bold=bold)
            except Exception:
                try:
                    self.font_sizes[key] = pygame.font.SysFont('Courier', size, bold=bold)
                except Exception:
                    self.font_sizes[key] = pygame.font.Font(None, size)
        return self.font_sizes[key]

    def render_text(self, text, color=(255, 255, 255), size=24, font_name=None, bold=True):
        """Render text. See `get_font` for `font_name`/`bold` semantics."""
        font = self.get_font(size, font_name=font_name, bold=bold)
        return font.render(text, True, color)
