import random


# Button names used throughout the game — the canonical set of inputs.
BUTTON_NAMES = ('left', 'right', 'up', 'down', 'space')


class GameModel:
    """Pure game state and logic — no pygame dependency.

    The sequence list lives here as the single source of truth,
    making it easy to share across players in a future multiplayer mode.
    """

    def __init__(self, event_bus):
        self._bus = event_bus
        self.reset()

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def reset(self):
        self.sequence: list[str] = []
        self.player_index = 0
        self.score        = 0
        self.state        = 'adding'   # adding | showing | input | gameover

        # Visual flash info (read by the View)
        self.flash_button     = None
        self.flash_state      = 'normal'
        self.flash_end        = 0

        # Showing-phase bookkeeping
        self._show_index  = 0
        self._next_time   = 0
        self._showing_lit = False

        self.gameover_reason = "Wrong input!"

        # Multiplayer: guest waits for the host's button instead of generating locally
        self.guest_mode      = False
        self._pending_button: str | None = None

    # ------------------------------------------------------------------
    # Multiplayer helpers
    # ------------------------------------------------------------------

    def set_next_button(self, button: str) -> None:
        """Called by the multiplayer client when the host sends the next button."""
        self._pending_button = button

    # ------------------------------------------------------------------
    # Game logic
    # ------------------------------------------------------------------

    def handle_input(self, name: str, now: int) -> str:
        """Process a player button press.

        Returns 'correct', 'round_complete', or 'wrong'.
        """
        if not self.sequence or not (0 <= self.player_index < len(self.sequence)):
            return 'wrong'

        expected = self.sequence[self.player_index]

        # Show pressed sprite for this button
        self.flash_button = name
        self.flash_state  = 'pressed'
        self.flash_end    = now + 400

        if name != expected:
            self.state = 'gameover'
            self._bus.emit('input_result', {'result': 'wrong', 'name': name})
            return 'wrong'

        self.player_index += 1
        if self.player_index >= len(self.sequence):
            # Whole sequence matched — advance to next round
            self.score     += 1
            self.state      = 'adding'
            self._next_time = now + 1000  # pause before next round begins
            self._bus.emit('round_complete', {'score': self.score})
            return 'round_complete'

        self._bus.emit('input_result', {'result': 'correct', 'name': name})
        return 'correct'

    def update(self, now: int) -> bool:
        """Advance the state machine. Returns True when entering 'input' state."""
        if self.state == 'adding':
            if now >= self._next_time:
                if self.guest_mode:
                    if self._pending_button is None:
                        return False  # wait for host to send the next button
                    button = self._pending_button
                    self._pending_button = None
                else:
                    button = random.choice(list(BUTTON_NAMES))
                self.sequence.append(button)
                self.player_index = 0
                self._show_index  = 0
                self._showing_lit = False
                self.flash_button = None
                self.flash_state  = 'normal'
                self._next_time   = now + 800  # brief pause before playback
                self.state        = 'showing'
                self._bus.emit('sequence_updated', {'sequence': self.sequence})

        elif self.state == 'showing':
            if self._show_index >= len(self.sequence):
                # Finished showing — player's turn
                self.state        = 'input'
                self.flash_button = None
                self.flash_state  = 'normal'
                self._bus.emit('state_changed', {'state': 'input'})
                return True  # signals controller to start the timer

            if not self._showing_lit:
                if now >= self._next_time:
                    self.flash_button = self.sequence[self._show_index]
                    self.flash_state  = 'indicated'
                    self.flash_end    = now + 600
                    self._showing_lit = True
            else:
                if now >= self.flash_end:
                    self.flash_button = None
                    self.flash_state  = 'normal'
                    self._showing_lit = False
                    self._show_index += 1
                    self._next_time   = now + 300

        elif self.state == 'input':
            # Expire the press flash after it times out
            if self.flash_button and now >= self.flash_end:
                self.flash_button = None
                self.flash_state  = 'normal'

        return False

    def on_timer_expired(self, data) -> None:
        if self.state == 'input':
            self.state           = 'gameover'
            self.gameover_reason = "Time's up!"
            self.flash_end       = data['now']
