"""Multiplayer lobby screen.

States:
  'username' — player types their username and presses Enter to connect.
  'lobby'    — connected; shows the live player list; click a name to challenge.
  'waiting'  — challenge sent; waiting for opponent to accept/decline.
  'incoming' — another player challenged us; show Accept (Y) / Decline (N).

Returns:
  ("game_start", role, opponent_settings_flags)  — match is ready
  "quit"                                          — window closed
  "menu"                                          — Escape pressed
"""
import asyncio
import pygame
from game.utils import animation_utils


class MultiplayerLobby:
    _GRADIENT_TOP    = (25, 25, 112)
    _GRADIENT_BOTTOM = (48, 25, 52)

    def __init__(self, screen, mp_client):
        self.screen    = screen
        self.client    = mp_client
        self.font_lg   = pygame.font.Font(None, 72)
        self.font_md   = pygame.font.Font(None, 42)
        self.font_sm   = pygame.font.Font(None, 32)

        self._state          = "username"   # username | lobby | waiting | incoming
        self._username_buf   = ""
        self._status_msg     = ""
        self._players: list  = []           # list of {username, settings}
        self._challenger     = None         # name of player who challenged us
        self._challenger_settings = 0

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def run(self):
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                result = await self._handle_event(event)
                if result is not None:
                    return result

            # Poll WebSocket for incoming server messages
            if self.client.connected:
                result = await self._poll_messages()
                if result is not None:
                    return result

            self._draw()
            pygame.display.flip()
            clock.tick(60)
            await asyncio.sleep(0)  # Required for pygbag

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    async def _handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return await self._handle_click(event.pos)
            return None

        key = event.key

        if key == pygame.K_ESCAPE:
            if self.client.connected:
                await self.client.disconnect()
            return "menu"

        if self._state == "username":
            if key == pygame.K_RETURN and self._username_buf.strip():
                await self._do_connect()
            elif key == pygame.K_BACKSPACE:
                self._username_buf = self._username_buf[:-1]
            elif event.unicode and len(self._username_buf) < 20:
                self._username_buf += event.unicode

        elif self._state == "incoming":
            if key == pygame.K_y:
                await self._accept_challenge()
            elif key == pygame.K_n:
                await self._decline_challenge()

        return None

    async def _handle_click(self, pos):
        if self._state == "lobby":
            for i, player in enumerate(self._players):
                rect = self._player_rect(i)
                if rect.collidepoint(pos):
                    await self._send_challenge(player["username"])
                    return None
        return None

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    async def _do_connect(self):
        from game.core.keybinds import KeybindManager, to_flags
        username = self._username_buf.strip()
        flags = to_flags(KeybindManager())   # use default (not inverted) settings
        self._status_msg = "Connecting..."
        try:
            await self.client.connect(username, flags)
            self._state = "lobby"
            self._status_msg = "Connected! Click a player to challenge them."
        except Exception as exc:
            self._status_msg = f"Connection failed: {exc}"

    async def _send_challenge(self, target: str):
        await self.client.send({"type": "challenge", "target": target})
        self._state = "waiting"
        self._status_msg = f"Challenge sent to {target}. Waiting..."

    async def _accept_challenge(self):
        await self.client.send({"type": "challenge_accept", "from": self._challenger})
        self._status_msg = "Accepted! Starting match..."

    async def _decline_challenge(self):
        await self.client.send({"type": "challenge_decline", "from": self._challenger})
        self._challenger = None
        self._state = "lobby"
        self._status_msg = "Challenge declined."

    # ------------------------------------------------------------------
    # WebSocket polling
    # ------------------------------------------------------------------

    async def _poll_messages(self):
        msg = await self.client.poll()
        if msg is None:
            return None

        msg_type = msg.get("type", "")

        if msg_type == "player_list":
            self._players = [
                p for p in msg.get("players", [])
                if p.get("username") != self.client.username
            ]

        elif msg_type == "challenged":
            self._challenger          = msg["from"]
            self._challenger_settings = int(msg.get("settings", 0))
            self._state               = "incoming"
            self._status_msg          = f"{self._challenger} challenged you!"

        elif msg_type == "challenge_declined":
            self._state      = "lobby"
            self._status_msg = f"{msg.get('from')} declined your challenge."

        elif msg_type == "game_start":
            self.client.role     = msg.get("role")
            self.client.opponent = msg.get("opponent")
            opp_settings         = int(msg.get("settings", 0))
            return ("game_start", self.client.role, opp_settings)

        elif msg_type == "error":
            self._status_msg = msg.get("message", "Server error.")
            if self._state == "waiting":
                self._state = "lobby"

        elif msg_type == "opponent_disconnected":
            self._state      = "lobby"
            self._status_msg = "Opponent disconnected."

        return None

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _player_rect(self, index: int) -> pygame.Rect:
        w = self.screen.get_width()
        y = 260 + index * 60
        return pygame.Rect(w // 2 - 200, y, 400, 48)

    def _draw(self):
        animation_utils.draw_gradient(self.screen, self._GRADIENT_TOP, self._GRADIENT_BOTTOM)

        cx = self.screen.get_width() // 2

        # Title
        title = self.font_lg.render("Multiplayer", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(cx, 80)))

        if self._state == "username":
            self._draw_username_entry(cx)
        elif self._state in ("lobby", "waiting"):
            self._draw_lobby(cx)
        elif self._state == "incoming":
            self._draw_incoming(cx)

        # Status bar at bottom
        if self._status_msg:
            status = self.font_sm.render(self._status_msg, True, (200, 200, 100))
            self.screen.blit(status, status.get_rect(center=(cx, self.screen.get_height() - 30)))

    def _draw_username_entry(self, cx):
        prompt = self.font_md.render("Enter username:", True, (200, 200, 200))
        self.screen.blit(prompt, prompt.get_rect(center=(cx, 200)))

        # Input box
        box = pygame.Rect(cx - 180, 230, 360, 50)
        pygame.draw.rect(self.screen, (60, 60, 120), box, border_radius=6)
        pygame.draw.rect(self.screen, (150, 150, 200), box, 2, border_radius=6)
        cursor = "_" if (pygame.time.get_ticks() // 500) % 2 == 0 else " "
        text = self.font_md.render(self._username_buf + cursor, True, (255, 255, 255))
        self.screen.blit(text, text.get_rect(midleft=(box.left + 10, box.centery)))

        hint = self.font_sm.render("Press Enter to connect", True, (150, 150, 150))
        self.screen.blit(hint, hint.get_rect(center=(cx, 300)))

        esc = self.font_sm.render("Esc — back to menu", True, (120, 120, 120))
        self.screen.blit(esc, esc.get_rect(center=(cx, 340)))

    def _draw_lobby(self, cx):
        header = self.font_md.render("Online players — click to challenge", True, (200, 200, 200))
        self.screen.blit(header, header.get_rect(center=(cx, 200)))

        if not self._players:
            none_msg = self.font_sm.render("No other players online yet.", True, (150, 150, 150))
            self.screen.blit(none_msg, none_msg.get_rect(center=(cx, 280)))
        else:
            mouse_pos = pygame.mouse.get_pos()
            for i, player in enumerate(self._players):
                rect   = self._player_rect(i)
                hovered = rect.collidepoint(mouse_pos) and self._state == "lobby"
                color  = (80, 80, 160) if hovered else (50, 50, 110)
                pygame.draw.rect(self.screen, color, rect, border_radius=6)
                name_surf = self.font_sm.render(player["username"], True, (255, 255, 255))
                self.screen.blit(name_surf, name_surf.get_rect(midleft=(rect.left + 12, rect.centery)))

                # Show inverted-mode indicator
                if int(player.get("settings", 0)) & 0x01:
                    inv = self.font_sm.render("[inv]", True, (180, 180, 100))
                    self.screen.blit(inv, inv.get_rect(midright=(rect.right - 12, rect.centery)))

        esc = self.font_sm.render("Esc — disconnect & back", True, (120, 120, 120))
        self.screen.blit(esc, esc.get_rect(center=(cx, self.screen.get_height() - 60)))

    def _draw_incoming(self, cx):
        msg = self.font_md.render(f"{self._challenger} wants to play!", True, (255, 220, 80))
        self.screen.blit(msg, msg.get_rect(center=(cx, 220)))

        # Show opponent's settings
        from game.core.keybinds import SETTINGS_INVERTED
        inv_text = "Inverted controls" if (self._challenger_settings & SETTINGS_INVERTED) else "Normal controls"
        inv_surf = self.font_sm.render(f"Their settings: {inv_text}", True, (200, 200, 200))
        self.screen.blit(inv_surf, inv_surf.get_rect(center=(cx, 270)))

        accept = self.font_md.render("Y — Accept", True, (100, 255, 100))
        self.screen.blit(accept, accept.get_rect(center=(cx, 340)))

        decline = self.font_md.render("N — Decline", True, (255, 100, 100))
        self.screen.blit(decline, decline.get_rect(center=(cx, 400)))
