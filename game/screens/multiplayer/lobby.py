"""Multiplayer lobby — see online players, send/receive challenges."""

import pygame
import asyncio
from game.utils import animation_utils
from game.utils.button import Button
from game.core import settings_flags


class MultiplayerLobbyScreen:
    """
    Shows the list of available players.  Click a name to challenge them.
    An incoming challenge prompts Accept / Decline buttons at the bottom.

    Returns:
        ("game", seed, settings, opponent_name)  — game_start received
        "menu"                                   — player left the lobby
        "quit"                                   — window closed
    """

    _GRAD_TOP    = (25, 25, 112)
    _GRAD_BOTTOM = (48, 25, 52)
    _ROW_H       = 62
    _ROW_GAP     = 8

    def __init__(self, screen, client, my_name: str):
        self.screen   = screen
        self.client   = client
        self.my_name  = my_name

        self.players: list[str] = []          # other available players
        self.status = f"Welcome, {my_name}!  Click a name to challenge."

        # Pending challenge state
        self._incoming_from: str | None = None
        self._incoming_settings: int    = 0
        self._outgoing_to: str | None   = None

        font_btn = pygame.font.Font(None, 34)
        self.font_title  = pygame.font.Font(None, 60)
        self.font_player = pygame.font.Font(None, 40)
        self.font_small  = pygame.font.Font(None, 30)

        W, H = screen.get_width(), screen.get_height()
        cx = W // 2

        self.btn_accept = Button(
            pygame.Rect(cx - 170, H - 120, 150, 52),
            "Accept",
            font_btn,
            color=(35, 95, 35),
            hover_color=(55, 145, 55),
        )
        self.btn_decline = Button(
            pygame.Rect(cx + 20, H - 120, 150, 52),
            "Decline",
            font_btn,
            color=(95, 35, 35),
            hover_color=(145, 55, 55),
        )
        self.btn_cancel = Button(
            pygame.Rect(cx - 85, H - 120, 170, 52),
            "Cancel",
            font_btn,
        )
        self.btn_leave = Button(
            pygame.Rect(W - 130, 16, 110, 42),
            "Leave",
            font_btn,
        )

        # Dict of player-name → row Rect, rebuilt each draw call
        self._row_rects: dict[str, pygame.Rect] = {}

    # ------------------------------------------------------------------

    async def run(self):
        clock = pygame.time.Clock()

        while True:
            W, H = self.screen.get_width(), self.screen.get_height()
            cx = W // 2

            # ── Events ──────────────────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    await self.client.close()
                    return "quit"

                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    await self.client.close()
                    return "menu"

                if self.btn_leave.handle_event(event):
                    await self.client.close()
                    return "menu"

                # Accept / Decline incoming challenge
                if self._incoming_from:
                    if self.btn_accept.handle_event(event):
                        await self.client.send(
                            {"type": "challenge_response", "accepted": True}
                        )
                        self.status = f"Accepted!  Starting vs {self._incoming_from}…"
                        self._incoming_from = None
                    elif self.btn_decline.handle_event(event):
                        await self.client.send(
                            {"type": "challenge_response", "accepted": False}
                        )
                        self._incoming_from = None
                        self.status = "Challenge declined."

                # Cancel outgoing challenge
                elif self._outgoing_to and self.btn_cancel.handle_event(event):
                    self._outgoing_to = None
                    self.status = "Challenge cancelled."

                # Click on a player row to challenge
                elif (not self._incoming_from and not self._outgoing_to
                      and event.type == pygame.MOUSEBUTTONDOWN
                      and event.button == 1):
                    for pname, rect in self._row_rects.items():
                        if rect.collidepoint(event.pos):
                            flags = settings_flags.encode(inverted_keys=False)
                            await self.client.send({
                                "type": "challenge",
                                "target": pname,
                                "settings": flags,
                            })
                            self._outgoing_to = pname
                            self.status = f"Challenged {pname}!  Waiting for response…"
                            break

            # ── Server messages ─────────────────────────────────────────
            while True:
                msg = self.client.poll()
                if msg is None:
                    break
                t = msg.get("type")

                if t == "player_list":
                    self.players = [p for p in msg["players"] if p != self.my_name]

                elif t == "challenge_received":
                    self._incoming_from     = msg["from"]
                    self._incoming_settings = msg.get("settings", 0)
                    self._outgoing_to       = None
                    self.status = f"{msg['from']} is challenging you!"

                elif t == "challenge_declined":
                    self._outgoing_to = None
                    self.status = f"{msg['opponent']} declined your challenge."

                elif t == "game_start":
                    return (
                        "game",
                        msg["seed"],
                        msg["settings"],
                        msg["opponent"],
                    )

                elif t == "opponent_disconnected":
                    self._outgoing_to   = None
                    self._incoming_from = None
                    self.status = "Opponent disconnected."

            # ── Draw ─────────────────────────────────────────────────────
            self._draw(cx, H)
            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)

    # ------------------------------------------------------------------

    def _draw(self, cx: int, H: int):
        W = self.screen.get_width()
        animation_utils.draw_gradient(self.screen, self._GRAD_TOP, self._GRAD_BOTTOM)

        # Title
        title_surf = self.font_title.render("LOBBY", True, (100, 200, 255))
        self.screen.blit(title_surf, title_surf.get_rect(center=(cx, 46)))

        # My name (top-left) and Leave button (top-right)
        me_surf = self.font_small.render(f"You: {self.my_name}", True, (160, 255, 160))
        self.screen.blit(me_surf, (18, 20))
        self.btn_leave.draw(self.screen)

        # ── Player list ──────────────────────────────────────────────────
        list_top = 90
        self._row_rects.clear()
        mouse_pos = pygame.mouse.get_pos()

        if not self.players:
            empty = self.font_player.render(
                "No other players online yet…", True, (100, 100, 150)
            )
            self.screen.blit(empty, empty.get_rect(center=(cx, H // 2 - 30)))
        else:
            for i, pname in enumerate(self.players):
                row_rect = pygame.Rect(
                    cx - 200,
                    list_top + i * (self._ROW_H + self._ROW_GAP),
                    400,
                    self._ROW_H,
                )
                self._row_rects[pname] = row_rect

                # Colour based on state
                if pname == self._outgoing_to:
                    bg, border = (45, 75, 30), (110, 190, 70)
                elif self._incoming_from or self._outgoing_to:
                    bg, border = (35, 35, 60), (80, 80, 120)  # dimmed
                elif row_rect.collidepoint(mouse_pos):
                    bg, border = (85, 85, 140), (140, 140, 210)
                else:
                    bg, border = (55, 55, 95), (110, 110, 180)

                # Shadow + button body
                pygame.draw.rect(self.screen, (20, 20, 40),
                                 row_rect.move(0, 3), border_radius=10)
                pygame.draw.rect(self.screen, bg, row_rect, border_radius=10)
                pygame.draw.rect(self.screen, border, row_rect, 1, border_radius=10)

                name_surf = self.font_player.render(pname, True, (220, 220, 255))
                self.screen.blit(name_surf, name_surf.get_rect(
                    midleft=(row_rect.left + 18, row_rect.centery)
                ))

                # Right-side hint
                if pname == self._outgoing_to:
                    hint = self.font_small.render("waiting…", True, (160, 220, 100))
                elif not self._incoming_from and not self._outgoing_to:
                    hint = self.font_small.render("Challenge", True, (150, 150, 210))
                else:
                    hint = None
                if hint:
                    self.screen.blit(hint, hint.get_rect(
                        midright=(row_rect.right - 18, row_rect.centery)
                    ))

        # ── Challenge prompt / action buttons ────────────────────────────
        if self._incoming_from:
            # Shaded backdrop so the popup stands out from the player list
            popup_rect = pygame.Rect(cx - 240, H - 200, 480, 140)
            popup_surf = pygame.Surface(popup_rect.size, pygame.SRCALPHA)
            popup_surf.fill((20, 20, 50, 200))
            self.screen.blit(popup_surf, popup_rect)
            pygame.draw.rect(self.screen, (100, 100, 200), popup_rect, 2, border_radius=8)

            prompt = self.font_player.render(
                f"{self._incoming_from} challenged you!", True, (255, 220, 60)
            )
            self.screen.blit(prompt, prompt.get_rect(center=(cx, H - 175)))

            status_surf = self.font_small.render(self.status, True, (190, 190, 200))
            self.screen.blit(status_surf, status_surf.get_rect(center=(cx, H - 148)))

            self.btn_accept.draw(self.screen)
            self.btn_decline.draw(self.screen)

        elif self._outgoing_to:
            # Shaded backdrop
            popup_rect = pygame.Rect(cx - 240, H - 200, 480, 130)
            popup_surf = pygame.Surface(popup_rect.size, pygame.SRCALPHA)
            popup_surf.fill((20, 20, 50, 200))
            self.screen.blit(popup_surf, popup_rect)
            pygame.draw.rect(self.screen, (80, 80, 160), popup_rect, 2, border_radius=8)

            animation_utils.flashing_text(
                self.screen,
                f"Waiting for {self._outgoing_to}...",
                (cx, H - 172),
                font_size=34,
                color_on=(255, 220, 60),
                color_off=(140, 120, 30),
            )

            status_surf = self.font_small.render(self.status, True, (190, 190, 200))
            self.screen.blit(status_surf, status_surf.get_rect(center=(cx, H - 148)))

            self.btn_cancel.draw(self.screen)

        else:
            # ── Status bar (no challenge active) ─────────────────────────
            status_surf = self.font_small.render(self.status, True, (190, 190, 200))
            self.screen.blit(status_surf, status_surf.get_rect(center=(cx, H - 40)))
