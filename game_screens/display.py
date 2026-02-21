import pygame
import asyncio
import random
import os


class GameScreen:
    # Maps button name -> keyboard key constant
    BUTTON_KEYS = {
        'left':  pygame.K_LEFT,
        'right': pygame.K_RIGHT,
        'up':    pygame.K_UP,
        'down':  pygame.K_DOWN,
        'space': pygame.K_SPACE,
    }

    # Maps button name -> sprite filename
    BUTTON_FILES = {
        'left':  'left.png',
        'right': 'right.png',
        'up':    'up.png',
        'down':  'down.png',
        'space': 'space.png',
    }

    def __init__(self, screen):
        self.screen = screen
        W, H = screen.get_width(), screen.get_height()

        # Load sprites from assets/Typo-buttons/
        asset_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'Typo-buttons')
        self.sprites = {}
        for name, filename in self.BUTTON_FILES.items():
            self.sprites[name] = pygame.image.load(
                os.path.join(asset_dir, filename)
            ).convert_alpha()

        # Button layout — arrow cross centered at (W//2, H//2 - 40), space below
        cx, cy = W // 2, H // 2 - 40
        s = 90   # arrow button size (square)
        gap = 120  # center-to-center distance

        self.button_rects = {
            'up':    pygame.Rect(cx - s // 2,       cy - gap - s // 2, s, s),
            'down':  pygame.Rect(cx - s // 2,       cy + gap - s // 2, s, s),
            'left':  pygame.Rect(cx - gap - s // 2, cy - s // 2,       s, s),
            'right': pygame.Rect(cx + gap - s // 2, cy - s // 2,       s, s),
            'space': pygame.Rect(cx - 110,          cy + gap + 60,     220, 55),
        }

        # Pre-scale each sprite to its rect size once (avoids per-frame scaling)
        self.scaled_sprites = {
            name: pygame.transform.smoothscale(self.sprites[name], (rect.width, rect.height))
            for name, rect in self.button_rects.items()
        }

        # Fonts
        self.font_large = pygame.font.SysFont(None, 72)
        self.font_small = pygame.font.SysFont(None, 32)

        self._reset()

    # ------------------------------------------------------------------
    # Public async entry point
    # ------------------------------------------------------------------

    async def run(self):
        clock = pygame.time.Clock()

        while True:
            now = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                if self.state == 'input':
                    if event.type == pygame.KEYDOWN:
                        for name, key in self.BUTTON_KEYS.items():
                            if event.key == key:
                                self._handle_input(name, now)
                                break
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        for name, rect in self.button_rects.items():
                            if rect.collidepoint(event.pos):
                                self._handle_input(name, now)
                                break

                elif self.state == 'gameover':
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        self._reset()
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self._reset()

            self._update(now)
            self._draw()

            pygame.display.flip()
            clock.tick(60)
            await asyncio.sleep(0)  # Required for pygbag

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _reset(self):
        self.sequence      = []
        self.player_index  = 0
        self.score         = 0
        self.flash_button  = None
        self.flash_end     = 0
        self._show_index   = 0
        self._next_time    = 0
        self._showing_lit  = False
        self.state         = 'adding'

    def _handle_input(self, name, now):
        """Called when the player presses a key or clicks a button during input state."""
        expected = self.sequence[self.player_index]

        # Always flash the button the player chose
        self.flash_button = name
        self.flash_end    = now + 300

        if name != expected:
            self.state = 'gameover'
            return

        self.player_index += 1
        if self.player_index >= len(self.sequence):
            # Completed the full sequence — add a new item next round
            self.score += 1
            self.state      = 'adding'
            self._next_time = now + 1000  # brief pause before next round

    def _update(self, now):
        if self.state == 'adding':
            if now >= self._next_time:
                self.sequence.append(random.choice(list(self.BUTTON_KEYS.keys())))
                self.player_index  = 0
                self._show_index   = 0
                self._showing_lit  = False
                self.flash_button  = None
                self._next_time    = now + 800  # pause before playback starts
                self.state         = 'showing'

        elif self.state == 'showing':
            if self._show_index >= len(self.sequence):
                # All buttons shown — player's turn
                self.state        = 'input'
                self.flash_button = None
                return

            if not self._showing_lit:
                # Waiting in the gap before lighting next button
                if now >= self._next_time:
                    self.flash_button  = self.sequence[self._show_index]
                    self.flash_end     = now + 600
                    self._showing_lit  = True
            else:
                # Button is currently lit — wait for lit period to end
                if now >= self.flash_end:
                    self.flash_button  = None
                    self._showing_lit  = False
                    self._show_index  += 1
                    self._next_time    = now + 300  # gap between flashes

        # Expire player-input flash
        if self.state == 'input' and self.flash_button and now >= self.flash_end:
            self.flash_button = None

    def _draw(self):
        self.screen.fill((15, 15, 25))

        W, H = self.screen.get_width(), self.screen.get_height()

        # HUD — score (top-left) and round (top-right)
        score_surf = self.font_small.render(f"Score: {self.score}", True, (200, 200, 200))
        self.screen.blit(score_surf, (20, 20))

        round_surf = self.font_small.render(f"Round {len(self.sequence)}", True, (150, 150, 150))
        self.screen.blit(round_surf, round_surf.get_rect(topright=(W - 20, 20)))

        # Status message
        if self.state == 'showing':
            status_text  = "Watch carefully..."
            status_color = (160, 160, 255)
        elif self.state == 'input':
            remaining    = len(self.sequence) - self.player_index
            status_text  = f"Your turn!  ({remaining} left)"
            status_color = (160, 255, 160)
        elif self.state == 'gameover':
            status_text  = "Space or click to retry"
            status_color = (255, 100, 100)
        else:
            status_text  = ""
            status_color = (200, 200, 200)

        if status_text:
            s = self.font_small.render(status_text, True, status_color)
            self.screen.blit(s, s.get_rect(center=(W // 2, 55)))

        # Draw buttons
        for name, rect in self.button_rects.items():
            img = self.scaled_sprites[name]

            if name == self.flash_button:
                # Brighten the lit button
                surf = img.copy()
                surf.fill((90, 90, 90), special_flags=pygame.BLEND_RGB_ADD)
                self.screen.blit(surf, rect)
            elif self.state in ('showing', 'gameover', 'adding'):
                # Dim unlit buttons while sequence plays or on game-over
                surf = img.copy()
                surf.set_alpha(80)
                self.screen.blit(surf, rect)
            else:
                # Input state — all buttons at full brightness
                self.screen.blit(img, rect)

        # Game-over title
        if self.state == 'gameover':
            go_surf = self.font_large.render("GAME OVER", True, (255, 80, 80))
            self.screen.blit(go_surf, go_surf.get_rect(center=(W // 2, H // 2 - 130)))
