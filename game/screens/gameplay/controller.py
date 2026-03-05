import pygame
import asyncio
from game.core.game_timer import GameTimer


class GameController:
    """Orchestrates input, model updates, and view rendering."""

    def __init__(self, screen, model, view, event_bus, keybinds, pause_overlay=None,
                 mp_client=None, mp_role=None):
        self.screen = screen
        self.model = model
        self.view = view
        self._bus = event_bus
        self.keybinds = keybinds
        self.pause_overlay = pause_overlay
        self.paused = False

        # Multiplayer client (None in single-player mode)
        self._mp      = mp_client
        self._mp_role = mp_role   # 'host' | 'guest' | None

        # Opponent score / state for HUD display
        self._opp_score: int | None = None
        self._opp_status: str = ""          # "correct" | "wrong" | "gameover" | "disconnected" | ""
        self._opp_gameover_time: int | None = None   # ticks when opponent lost

        self.game_timer = GameTimer(self._bus)
        self._bus.subscribe('timer_expired', self.model.on_timer_expired)

        # NOTE: sequence_updated subscription for the host is added in run(),
        # AFTER model.reset(), so guest_mode is set correctly before subscribing.

        if pause_overlay is not None:
            pause_overlay.subscribe(self._bus)

    def _on_sequence_updated(self, data):
        """Host: send the latest sequence button to the server (fire-and-forget)."""
        if self._mp and data and data.get("sequence"):
            button = data["sequence"][-1]
            asyncio.get_event_loop().create_task(self._mp.send_sequence_add(button))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _process_input_result(self, name: str, now: int) -> bool:
        """Call model.handle_input, stop the timer on terminal results.

        Returns True so callers can ``break`` after a matched input.
        """
        result = self.model.handle_input(name, now)
        if result in ('wrong', 'round_complete'):
            self.game_timer.stop()
        # Share progress with opponent
        if self._mp:
            idx = self.model.player_index
            score = self.model.score
            asyncio.get_event_loop().create_task(
                self._mp.send_input_result(idx, result, score)
            )
        return True

    # ------------------------------------------------------------------
    # Multiplayer message handling
    # ------------------------------------------------------------------

    async def _handle_mp_messages(self):
        """Process all queued multiplayer messages for this frame."""
        while True:
            msg = await self._mp.poll()
            if msg is None:
                break
            msg_type = msg.get("type", "")

            if msg_type == "sequence_add":
                # Guest receives the next button from the host
                self.model.set_next_button(msg["button"])

            elif msg_type == "input_result":
                self._opp_score  = int(msg.get("score", 0))
                self._opp_status = msg.get("result", "")

            elif msg_type == "opponent_game_over":
                self._opp_score        = int(msg.get("score", 0))
                self._opp_status       = "gameover"
                self._opp_gameover_time = pygame.time.get_ticks()

            elif msg_type == "opponent_disconnected":
                self._opp_status        = "disconnected"
                self._opp_gameover_time = pygame.time.get_ticks()

    # ------------------------------------------------------------------
    # Public async entry point
    # Returns:
    #   ("gameover", score, reason)  — player lost
    #   "quit"                       — window was closed
    # ------------------------------------------------------------------

    async def run(self):
        self.model.reset()

        # Apply multiplayer role AFTER reset (reset() clears guest_mode)
        if self._mp_role == 'guest':
            self.model.guest_mode = True
        elif self._mp_role == 'host':
            # Only the host relays new sequence buttons to the server
            self._bus.subscribe('sequence_updated', self._on_sequence_updated)

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
                        now_tick = pygame.time.get_ticks()
                        if self.paused:
                            self._bus.emit('game_paused', {'now': now_tick})
                        else:
                            self._bus.emit('game_resumed', {'now': now_tick})
                        continue

                    # Ctrl+E jumps to game over (debug shortcut)
                    if event.key == pygame.K_e and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        return ("gameover", 0, "Testing - Ctrl+E shortcut")

                    # Game inputs are blocked while paused
                    if not self.paused and self.model.state == 'input':
                        for name, key in self.keybinds.button_keys.items():
                            if event.key == key:
                                self._process_input_result(name, now)
                                break

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not self.paused and self.model.state == 'input':
                        for name, rect in self.view.button_rects.items():
                            if rect.collidepoint(event.pos):
                                self._process_input_result(name, now)
                                break

            # Poll multiplayer messages
            if self._mp and self._mp.connected:
                await self._handle_mp_messages()

            # Opponent lost: show banner for 2 s then declare winner
            if self._opp_gameover_time is not None and now - self._opp_gameover_time >= 2000:
                reason = ("You Win!" if self._opp_status == "gameover"
                          else "Opponent disconnected!")
                return ("gameover", self.model.score, reason)

            # After the wrong-input press-flash expires, hand off to game over
            if self.model.state == 'gameover' and now >= self.model.flash_end:
                if self._mp:
                    await self._mp.send_game_over(self.model.score, self.model.gameover_reason)
                return ("gameover", self.model.score, self.model.gameover_reason)

            if not self.paused:
                entered_input = self.model.update(now)
                if entered_input:
                    self.game_timer.start(now)
                # Let timer update during input phase
                if self.model.state == 'input':
                    self.game_timer.update(now)

            self.view.draw(self.model, self.game_timer.fraction,
                           opp_score=self._opp_score, opp_status=self._opp_status)

            if self.pause_overlay:
                self.pause_overlay.draw()

            pygame.display.flip()
            clock.tick(60)
            await asyncio.sleep(0)  # Required for pygbag
