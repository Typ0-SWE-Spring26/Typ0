"""Multiplayer Simon Says game screen.

Both players receive the same RNG seed so their GameModel instances produce
an identical button sequence.  The server arbitrates: whichever player's
"mistake" message arrives first is the loser.

Returns:
    ("win",  my_score, opponent_score)
    ("lose", my_score, opponent_score)
    "quit"
"""

import asyncio
import pygame

from game.core.event_bus  import EventBus
from game.core.game_model import GameModel
from game.core.game_timer import GameTimer
from game.core import settings_flags
from game.screens.gameplay.view import GameView
from game.utils import animation_utils


class MultiplayerGameScreen:

    def __init__(
        self,
        screen,
        client,
        my_name: str,
        opponent_name: str,
        seed: int,
        settings: int,
        keybinds,
    ):
        self.screen        = screen
        self.client        = client
        self.my_name       = my_name
        self.opponent_name = opponent_name
        self.settings      = settings

        # Apply settings flags
        decoded = settings_flags.decode(settings)
        keybinds.inverted = decoded["inverted_keys"]
        self.keybinds = keybinds

        # Build MVC with a seeded model so both clients are in sync
        self._bus   = EventBus()
        self.model  = GameModel(self._bus, seed=seed)
        self.view   = GameView(screen, keybinds.key_labels)
        self.timer  = GameTimer(self._bus)
        self._bus.subscribe("timer_expired", self.model.on_timer_expired)
        self._bus.subscribe("round_complete", self._on_round_complete)

        self.opponent_score = 0
        self._mistake_sent  = False
        self._pending_score = None   # score queued to send after round_complete

        self._paused = False
        self.font_hud  = pygame.font.Font(None, 32)
        self.font_opp  = pygame.font.Font(None, 28)
        self.font_pause = pygame.font.Font(None, 96)

    # ------------------------------------------------------------------

    async def run(self):
        clock = pygame.time.Clock()
        _INTRO = "assets/Typ0__Intro_Theme.ogg"
        _MAIN  = "assets/Typ0__Main_Theme.ogg"
        user_pick = animation_utils.get_user_music_selection()
        if user_pick is None or user_pick == _INTRO:
            animation_utils.play_music(_MAIN)

        while True:
            now = pygame.time.get_ticks()

            # ── Events ──────────────────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    animation_utils.stop_music()
                    return "quit"

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        self._paused = not self._paused
                        if self._paused:
                            animation_utils.pause_music()
                        else:
                            animation_utils.unpause_music()
                        continue

                    if (not self._paused
                            and not self._mistake_sent
                            and self.model.state == "input"):
                        for btn_name, key in self.keybinds.button_keys.items():
                            if event.key == key:
                                self._handle_input(btn_name, now)
                                break

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if (not self._paused
                            and not self._mistake_sent
                            and self.model.state == "input"):
                        for btn_name, rect in self.view.button_rects.items():
                            if rect.collidepoint(event.pos):
                                self._handle_input(btn_name, now)
                                break

            # ── Server messages ─────────────────────────────────────────
            while True:
                msg = self.client.poll()
                if msg is None:
                    break
                t = msg.get("type")

                if t == "opponent_score":
                    self.opponent_score = msg["score"]

                elif t == "you_win":
                    animation_utils.stop_music()
                    return ("win", self.model.score, msg["opponent_score"])

                elif t == "you_lose":
                    animation_utils.stop_music()
                    return ("lose", msg["your_score"], msg["opponent_score"])

                elif t == "opponent_disconnected":
                    animation_utils.stop_music()
                    return ("win", self.model.score, 0)

            # ── Send queued score update ─────────────────────────────────
            if self._pending_score is not None:
                await self.client.send({
                    "type": "score_update",
                    "score": self._pending_score,
                })
                self._pending_score = None

            # ── Detect local mistake → notify server ────────────────────
            if (self.model.state == "gameover"
                    and not self._mistake_sent
                    and now >= self.model.flash_end):
                self._mistake_sent = True
                await self.client.send({"type": "mistake"})

            # ── Model + timer update (skip while paused) ─────────────────
            if not self._paused and not self._mistake_sent:
                entered_input = self.model.update(now)
                if entered_input:
                    self.timer.start(now)
                if self.model.state == "input":
                    self.timer.update(now)

            # ── Draw ─────────────────────────────────────────────────────
            self.view.draw(self.model, self.timer.fraction)
            self._draw_multiplayer_hud()

            # Waiting-for-server overlay after mistake sent
            if self._mistake_sent:
                self._draw_waiting_overlay()

            if self._paused:
                self._draw_pause_overlay()

            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _handle_input(self, name: str, now: int) -> None:
        result = self.model.handle_input(name, now)
        if result in ("wrong", "round_complete"):
            self.timer.stop()

    def _on_round_complete(self, data: dict) -> None:
        """Called by the EventBus when the player finishes a full round."""
        self._pending_score = data["score"]

    def _draw_multiplayer_hud(self):
        """Draw the opponent's name and score in the top-right corner."""
        W = self.screen.get_width()

        opp_label = self.font_opp.render(
            f"{self.opponent_name}: {self.opponent_score}",
            True,
            (255, 200, 100),
        )
        # Shift left so it doesn't overlap the "Round N" text from the base view
        self.screen.blit(opp_label, opp_label.get_rect(topright=(W - 20, 44)))

        # Separator line
        pygame.draw.line(
            self.screen,
            (60, 60, 90),
            (0, 66),
            (W, 66),
            1,
        )

    def _draw_pause_overlay(self):
        """Semi-transparent PAUSED overlay — local only, game timer is frozen."""
        W, H = self.screen.get_width(), self.screen.get_height()
        cx, cy = W // 2, H // 2
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 360, 180
        panel_rect = pygame.Rect(cx - panel_w // 2, cy - panel_h // 2, panel_w, panel_h)
        pygame.draw.rect(self.screen, (30, 30, 55), panel_rect, border_radius=14)
        pygame.draw.rect(self.screen, (100, 100, 170), panel_rect, 2, border_radius=14)

        shadow = self.font_pause.render("PAUSED", True, (20, 20, 40))
        self.screen.blit(shadow, shadow.get_rect(center=(cx + 2, cy - 28)))
        text = self.font_pause.render("PAUSED", True, (200, 200, 255))
        self.screen.blit(text, text.get_rect(center=(cx, cy - 30)))

        hint_font = pygame.font.Font(None, 30)
        hint = hint_font.render("Press P to Resume", True, (160, 160, 210))
        self.screen.blit(hint, hint.get_rect(center=(cx, cy + 38)))

    def _draw_waiting_overlay(self):
        """Semi-transparent overlay shown while awaiting server verdict."""
        W, H = self.screen.get_width(), self.screen.get_height()
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        animation_utils.flashing_text(
            self.screen,
            "Waiting for result…",
            (W // 2, H // 2),
            font_size=48,
            color_on=(255, 255, 255),
            color_off=(120, 120, 120),
        )
