"""
Virtual-resolution wrapper for Pygame.

All game code draws to a fixed 800x600 virtual surface. ScaledScreen
subclasses pygame.Surface so all drawing functions (blit, pygame.draw, etc.)
work directly on it. present() scales the result to the actual window.
"""

import pygame

VIRTUAL_WIDTH = 800
VIRTUAL_HEIGHT = 600
VIRTUAL_SIZE = (VIRTUAL_WIDTH, VIRTUAL_HEIGHT)


class ScaledScreen(pygame.Surface):
    """A pygame.Surface that auto-scales to a resizable window on present()."""

    def __init__(self, window):
        super().__init__(VIRTUAL_SIZE)
        self.window = window
        self._update_scaling()

    def _update_scaling(self):
        """Recalculate scale factor and letterbox offset."""
        ww, wh = self.window.get_size()
        scale_x = ww / VIRTUAL_WIDTH
        scale_y = wh / VIRTUAL_HEIGHT
        self.scale = min(scale_x, scale_y)

        scaled_w = int(VIRTUAL_WIDTH * self.scale)
        scaled_h = int(VIRTUAL_HEIGHT * self.scale)
        self.offset_x = (ww - scaled_w) // 2
        self.offset_y = (wh - scaled_h) // 2
        self.scaled_size = (scaled_w, scaled_h)

    def present(self):
        """Scale the virtual surface to the window. Call instead of pygame.display.flip()."""
        self._update_scaling()
        self.window.fill((0, 0, 0))  # letterbox bars
        scaled = pygame.transform.smoothscale(self, self.scaled_size)
        self.window.blit(scaled, (self.offset_x, self.offset_y))
        pygame.display.flip()

    def map_mouse(self, pos):
        """Convert window mouse coordinates to virtual coordinates."""
        mx, my = pos
        vx = (mx - self.offset_x) / self.scale
        vy = (my - self.offset_y) / self.scale
        return (int(vx), int(vy))

    def remap_event(self, event):
        """Remap mouse position in an event to virtual coordinates."""
        if hasattr(event, 'pos'):
            event = _clone_event(event, pos=self.map_mouse(event.pos))
        return event


def _clone_event(event, **overrides):
    """Create a new event with overridden attributes."""
    attrs = {}
    for attr in ['pos', 'button', 'buttons', 'rel', 'key', 'mod', 'unicode', 'scancode']:
        if hasattr(event, attr):
            attrs[attr] = getattr(event, attr)
    attrs.update(overrides)
    return pygame.event.Event(event.type, **attrs)
