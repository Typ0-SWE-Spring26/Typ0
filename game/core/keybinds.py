import pygame
from typing import ClassVar, Dict


class KeybindManager:
    """Manages the mapping from button names to pygame key constants.

    Supports an 'inverted' mode that swaps directional controls.
    """

    # button name → pygame key
    DEFAULT_MAP: ClassVar[Dict[str, int]] = {
        'left':  pygame.K_a,
        'right': pygame.K_d,
        'up':    pygame.K_w,
        'down':  pygame.K_s,
        'space': pygame.K_SPACE,
    }

    INVERTED_MAP: ClassVar[Dict[str, int]] = {
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


# ---------------------------------------------------------------------------
# Settings bit flags — compact representation for network transmission
# ---------------------------------------------------------------------------

SETTINGS_INVERTED = 0x01  # bit 0: inverted controls


def to_flags(keybinds: 'KeybindManager') -> int:
    """Encode keybind settings as a compact integer bit field."""
    flags = 0
    if keybinds.inverted:
        flags |= SETTINGS_INVERTED
    return flags


def from_flags(flags: int, keybinds: 'KeybindManager') -> None:
    """Apply a bit-flag integer to a KeybindManager instance."""
    keybinds.inverted = bool(flags & SETTINGS_INVERTED)
