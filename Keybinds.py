import pygame


class KeybindManager:
    def __init__(self):
        self.inverted = False

        # Default
        self.default_map = {
            pygame.K_w: "W",
            pygame.K_a: "A",
            pygame.K_s: "S",
            pygame.K_d: "D",
            pygame.K_SPACE: "SPACE",
        }

        # Inverted 
        self.inverted_map = {
            pygame.K_w: "S",
            pygame.K_s: "W",
            pygame.K_a: "D",
            pygame.K_d: "A",
            pygame.K_SPACE: "SPACE",
        }

    def toggle_invert(self):
        self.inverted = not self.inverted
        print(f"Invert controls: {'ON' if self.inverted else 'OFF'}")

    def process_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        # Toggle invert mode
        if event.key == pygame.K_i:
            self.toggle_invert()
            return

        # Select correct mapping
        active_map = self.inverted_map if self.inverted else self.default_map

        if event.key in active_map:
            print(active_map[event.key])
