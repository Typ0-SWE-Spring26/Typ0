import pygame
import asyncio
import random
import os
from . import animation_utils


class GameScreen:
    BUTTON_KEYS = {
        # WASD keys for keyboard input
        'left':  pygame.K_a,
        'right': pygame.K_d,
        'up':    pygame.K_w,
        'down':  pygame.K_s,
        'space': pygame.K_SPACE,
    }

    # (normal, indicated, pressed) paths relative to assets/Typo-buttons/
    BUTTON_FILES = {
        'left':  ('left.png',  'button-indicated/leftIndicate.png',  'button-pressed/leftPress.png'),
        'right': ('right.png', 'button-indicated/rightIndicate.png', 'button-pressed/rightPress.png'),
        'up':    ('up.png',    'button-indicated/upIndicate.png',    'button-pressed/upPress.png'),
        'down':  ('down.png',  'button-indicated/downIndicate.png',  'button-pressed/downPress.png'),
        'space': ('space.png', 'button-indicated/spaceIndicate.png', 'button-pressed/spacePress.png'),
    }

    def __init__(self, screen, pause_overlay=None, score=0):
        self.screen = screen
        self.pause_overlay = pause_overlay
        self.paused = False
        W, H = screen.get_width(), screen.get_height()

        asset_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'Typo-buttons')

        # Load all 3 sprite states per button
        self.sprites = {}
        for name, (normal_f, indicated_f, pressed_f) in self.BUTTON_FILES.items():
            self.sprites[name] = {
                'normal':    pygame.image.load(os.path.join(asset_dir, normal_f)).convert_alpha(),
                'indicated': pygame.image.load(os.path.join(asset_dir, indicated_f)).convert_alpha(),
                'pressed':   pygame.image.load(os.path.join(asset_dir, pressed_f)).convert_alpha(),
            }

        # Button layout — tight d-pad cross centered slightly above mid, space below
        cx, cy = W // 2, H // 2 - 40
        s = 90    # arrow button size
        gap = 100  # center-to-center distance (10px between buttons)

        self.button_rects = {
            'up':    pygame.Rect(cx - s // 2,       cy - gap - s // 2, s, s),
            'down':  pygame.Rect(cx - s // 2,       cy + gap - s // 2, s, s),
            'left':  pygame.Rect(cx - gap - s // 2, cy - s // 2,       s, s),
            'right': pygame.Rect(cx + gap - s // 2, cy - s // 2,       s, s),
            'space': pygame.Rect(cx - 110,          cy + gap + 60,     220, 55),
        }

        # Pre-scale every state to its rect size once
        self.scaled = {}
        for name, rect in self.button_rects.items():
            size = (rect.width, rect.height)
            self.scaled[name] = {
                state: pygame.transform.smoothscale(surf, size)
                for state, surf in self.sprites[name].items()
            }

        # Derive key labels from BUTTON_KEYS so they stay in sync if keys change
        self.key_labels = {
            name: pygame.key.name(key).upper()
            for name, key in self.BUTTON_KEYS.items()
        }

        self.font_small = pygame.font.SysFont(None, 32)
        self.font_label = pygame.font.SysFont(None, 26)
        self._reset()
        self.score = score  # carry over score from previous round if retrying

    # ------------------------------------------------------------------
    # Public async entry point
    # Returns:
    #   ("gameover", score)  — player got a wrong input
    #   "quit"               — window was closed
    # ------------------------------------------------------------------

    async def run(self):
        clock = pygame.time.Clock()

        while True:
            now = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                if event.type == pygame.KEYDOWN:
                    # P always toggles pause regardless of game state
                    if event.key == pygame.K_p:
                        self.paused = not self.paused
                        continue

                    # Ctrl+E jumps to game over (debug shortcut)
                    if event.key == pygame.K_e and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        return ("gameover", 0, "Testing - Ctrl+E shortcut")

                    # Game inputs are blocked while paused
                    if not self.paused and self.state == 'input':
                        for name, key in self.BUTTON_KEYS.items():
                            if event.key == key:
                                self._handle_input(name, now)
                                break

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not self.paused and self.state == 'input':
                        for name, rect in self.button_rects.items():
                            if rect.collidepoint(event.pos):
                                self._handle_input(name, now)
                                break

            # After the wrong-input press-flash expires, hand off to game over
            if self.state == 'gameover' and now >= self.flash_end:
                return ("gameover", self.score, "Wrong input!")

            if not self.paused:
                self._update(now)
            self._draw()

            # Draw pause overlay on top if paused
            if self.paused and self.pause_overlay:
                self.pause_overlay.draw_pause_start()

            pygame.display.flip()
            clock.tick(60)
            await asyncio.sleep(0)  # Required for pygbag

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _reset(self):
        self.sequence     = []
        self.player_index = 0
        self.score        = 0
        self.flash_button = None
        self.flash_state  = 'normal'
        self.flash_end    = 0
        self._show_index  = 0
        self._next_time   = 0
        self._showing_lit = False
        self.state        = 'adding'

    def _handle_input(self, name, now):
        """Player pressed a key or clicked a button."""
        expected = self.sequence[self.player_index]

        # Show pressed sprite for this button
        self.flash_button = name
        self.flash_state  = 'pressed'
        self.flash_end    = now + 400

        if name != expected:
            self.state = 'gameover'
            return

        self.player_index += 1
        if self.player_index >= len(self.sequence):
            # Whole sequence matched — advance to next round
            self.score     += 1
            self.state      = 'adding'
            self._next_time = now + 1000  # pause before next round begins

    def _update(self, now):
        if self.state == 'adding':
            if now >= self._next_time:
                self.sequence.append(random.choice(list(self.BUTTON_KEYS.keys())))
                self.player_index = 0
                self._show_index  = 0
                self._showing_lit = False
                self.flash_button = None
                self.flash_state  = 'normal'
                self._next_time   = now + 800  # brief pause before playback
                self.state        = 'showing'

        elif self.state == 'showing':
            if self._show_index >= len(self.sequence):
                # Finished showing — player's turn
                self.state        = 'input'
                self.flash_button = None
                self.flash_state  = 'normal'
                return

            if not self._showing_lit:
                # Gap phase — waiting to light up the next button
                if now >= self._next_time:
                    self.flash_button = self.sequence[self._show_index]
                    self.flash_state  = 'indicated'
                    self.flash_end    = now + 600
                    self._showing_lit = True
            else:
                # Lit phase — waiting for the lit period to end
                if now >= self.flash_end:
                    self.flash_button = None
                    self.flash_state  = 'normal'
                    self._showing_lit = False
                    self._show_index += 1
                    self._next_time   = now + 300  # gap between flashes

        elif self.state == 'input':
            # Expire the press flash after it times out
            if self.flash_button and now >= self.flash_end:
                self.flash_button = None
                self.flash_state  = 'normal'

    def _draw(self):
        self.screen.fill((15, 15, 25))

        W = self.screen.get_width()

        # HUD
        score_surf = self.font_small.render(f"Score: {self.score}", True, (200, 200, 200))
        self.screen.blit(score_surf, (20, 20))

        round_surf = self.font_small.render(f"Round {len(self.sequence)}", True, (150, 150, 150))
        self.screen.blit(round_surf, round_surf.get_rect(topright=(W - 20, 20)))

        # timer bar (only shows during player's turn)
        if self.state == 'input':
            time_limit = 5000  # ms to complete the sequence
            elapsed = pygame.time.get_ticks() - (self.flash_end - 400)  # when player's first input window opened
            remaining = max(time_limit - elapsed, 0)
            bar_width = int((remaining / time_limit) * (W - 40))
            pygame.draw.rect(self.screen, (255, 100, 100), (20, 60, bar_width, 10))

        # Status message
        if self.state == 'showing':
            status_text  = "Watch carefully..."
            status_color = (160, 160, 255)
        elif self.state == 'input':
            remaining    = len(self.sequence) - self.player_index
            status_text  = f"Your turn!  ({remaining} left)"
            status_color = (160, 255, 160)
        else:
            status_text  = ""
            status_color = (200, 200, 200)

        if status_text:
            s = self.font_small.render(status_text, True, status_color)
            self.screen.blit(s, s.get_rect(center=(W // 2, 55)))

        # Draw buttons
        for name, rect in self.button_rects.items():
            if name == self.flash_button:
                # Active button: use whichever state is set (indicated or pressed)
                self.screen.blit(self.scaled[name][self.flash_state], rect)
            elif self.state in ('showing', 'adding', 'gameover'):
                # Dim non-active buttons during Simon playback / transition / wrong flash
                surf = self.scaled[name]['normal'].copy()
                surf.set_alpha(80)
                self.screen.blit(surf, rect)
            else:
                # Input state: all buttons fully visible at normal state
                self.screen.blit(self.scaled[name]['normal'], rect)

            # Key label centered on button
            animation_utils.draw_shadowed_text(
                self.screen, self.font_label, self.key_labels[name], rect.center
            )
