"""Multiplayer login screen — enter a name and connect to the server."""

import pygame
import asyncio
from game.utils import animation_utils
from game.utils.button import Button

MAX_NAME_LEN = 20


class MultiplayerLoginScreen:
    """Type a name, hit Connect/Enter, and get assigned to the lobby."""

    def __init__(self, screen, client):
        self.screen = screen
        self.client = client

        self.name = ""
        self.error = ""
        self.connecting = False

        W, H = screen.get_width(), screen.get_height()
        cx = W // 2

        self.font_title  = pygame.font.Font(None, 80)
        self.font_label  = pygame.font.Font(None, 36)
        self.font_input  = pygame.font.Font(None, 48)
        self.font_status = pygame.font.Font(None, 32)
        self.font_btn    = pygame.font.Font(None, 36)

        self.input_rect = pygame.Rect(cx - 220, H // 2 - 35, 440, 60)
        self.close_rect = pygame.Rect(0, 0, 0, 0)
        self.btn_connect = Button(
            pygame.Rect(cx - 120, H // 2 + 50, 240, 58),
            "Connect",
            self.font_btn,
        )

    async def run(self):
        """Returns:
            ("lobby", confirmed_name)  — connected successfully
            "back"                     — ESC pressed
            "quit"                     — window closed
        """
        clock = pygame.time.Clock()
        W, H = self.screen.get_width(), self.screen.get_height()
        cx = W // 2

        while True:
            self.close_rect = pygame.Rect(
                self.screen.get_width() - 52,
                16,
                36,
                36,
            )
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                if event.type == pygame.KEYDOWN and not self.connecting:
                    if event.key == pygame.K_ESCAPE:
                        return "back"
                    elif event.key == pygame.K_BACKSPACE:
                        self.name = self.name[:-1]
                        self.error = ""
                    elif event.key == pygame.K_RETURN:
                        await self._attempt_connect()
                    elif len(self.name) < MAX_NAME_LEN and event.unicode.isprintable():
                        self.name += event.unicode
                        self.error = ""

                if self.btn_connect.handle_event(event) and not self.connecting:
                    await self._attempt_connect()

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.close_rect.collidepoint(event.pos) and not self.connecting:
                        return "back"

            # Check server responses
            while True:
                msg = self.client.poll()
                if msg is None:
                    break
                if msg.get("type") == "joined":
                    return ("lobby", msg["name"])
                elif msg.get("type") == "error":
                    self.error = msg["message"]
                    self.connecting = False

            self._draw(cx, H)

            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)

    async def _attempt_connect(self):
        name = self.name.strip()
        if not name:
            self.error = "Please enter a name first"
            return
        self.connecting = True
        self.error = ""
        try:
            await self.client.connect()
            await self.client.send({"type": "join", "name": name})
        except Exception as exc:
            self.connecting = False
            self.error = str(exc)[:60]

    def _draw(self, cx, H):
        animation_utils.draw_gradient(self.screen, (25, 25, 112), (48, 25, 52))

        # Title
        animation_utils.wave_text(
            self.screen, "MULTIPLAYER",
            (cx, 110),
            font_size=80,
            color=(100, 200, 255),
            bounce_height=8,
            wave_speed=0.3,
        )

        # Label
        label_surf = self.font_label.render("Player Name:", True, (180, 180, 255))
        self.screen.blit(label_surf, (self.input_rect.left, self.input_rect.top - 34))

        # Input box
        pygame.draw.rect(self.screen, (30, 30, 65), self.input_rect, border_radius=8)
        pygame.draw.rect(self.screen, (120, 120, 220), self.input_rect, 2, border_radius=8)

        display_name = self.name if self.name else ""
        # Blinking cursor
        cursor_visible = (pygame.time.get_ticks() // 530) % 2 == 0
        display_str = display_name + ("|" if cursor_visible and not self.connecting else "")
        name_surf = self.font_input.render(display_str or " ", True, (240, 240, 255))
        self.screen.blit(name_surf, name_surf.get_rect(midleft=(
            self.input_rect.left + 14, self.input_rect.centery
        )))

        # Error or connecting status
        if self.error:
            err_surf = self.font_status.render(self.error, True, (255, 80, 80))
            self.screen.blit(err_surf, err_surf.get_rect(center=(cx, H // 2 + 28)))
        elif self.connecting:
            animation_utils.flashing_text(
                self.screen, "Connecting...",
                (cx, H // 2 + 28),
                font_size=32,
                color_on=(100, 220, 255),
                color_off=(60, 140, 180),
            )

        # Connect button (hidden while connecting)
        if not self.connecting:
            self.btn_connect.draw(self.screen)

        # Close button (top-right)
        hovered = self.close_rect.collidepoint(pygame.mouse.get_pos())
        close_color = (140, 70, 80) if hovered else (110, 55, 65)
        pygame.draw.rect(self.screen, (10, 10, 20), self.close_rect.move(0, 2), border_radius=8)
        pygame.draw.rect(self.screen, close_color, self.close_rect, border_radius=8)
        pygame.draw.rect(self.screen, (200, 170, 180), self.close_rect, width=2, border_radius=8)
        close_text = self.font_btn.render("X", True, (255, 235, 235))
        self.screen.blit(close_text, close_text.get_rect(center=self.close_rect.center))

        animation_utils.flashing_text(
            self.screen, "ESC  back to menu",
            (cx, H - 38),
            font_size=28,
            color_on=(140, 140, 180),
            color_off=(70, 70, 100),
        )
