import pygame


class KeybindManager:
    """Manages the mapping from button names to pygame key constants.

    Supports an 'inverted' mode that swaps directional controls.
    """

    # button name → pygame key
    DEFAULT_MAP = {
        'left':  pygame.K_a,
        'right': pygame.K_d,
        'up':    pygame.K_w,
        'down':  pygame.K_s,
        'space': pygame.K_SPACE,
    }

    INVERTED_MAP = {
        'left':  pygame.K_d,
        'right': pygame.K_a,
        'up':    pygame.K_s,
        'down':  pygame.K_w,
        'space': pygame.K_SPACE,
    }

    def __init__(self):
        self.inverted = False

    @property
    def button_keys(self):
        """Current button-name → pygame-key mapping."""
        return self.INVERTED_MAP if self.inverted else self.DEFAULT_MAP

    @property
    def key_labels(self):
        """Button-name → display label (e.g. 'left' → 'A')."""
        return {
            name: pygame.key.name(key).upper()
            for name, key in self.button_keys.items()
        }

    def toggle_invert(self):
        self.inverted = not self.inverted
