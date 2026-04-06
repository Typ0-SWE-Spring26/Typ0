import random


# Button names used throughout the game — the canonical set of inputs.
BUTTON_NAMES = ('left', 'right', 'up', 'down', 'space')


# Difficulty presets for Simon mode:
# (flash_time_ms, inter_gap_ms, pre_show_pause_ms, post_round_pause_ms, timer_limit_ms)
_DIFFICULTY_PRESETS = {
    'easy':   (900, 450, 1200, 1500, 12000),
    'normal': (600, 300,  800, 1000,  8000),
    'hard':   (350, 200,  500,  700,  4000),
}


class GameModel:
    """Pure game state and logic — no pygame dependency.

    The sequence list lives here as the single source of truth,
    making it easy to share across players in a future multiplayer mode.

    Pass ``seed`` to get a deterministic sequence — used in multiplayer so
    both clients generate the exact same button order from the same seed.
    """

    def __init__(self, event_bus, seed=None, difficulty: str = 'normal'):
        self._bus = event_bus
        self._rng = random.Random(seed)
        preset = _DIFFICULTY_PRESETS.get(difficulty, _DIFFICULTY_PRESETS['normal'])
        (self._flash_time, self._inter_gap,
         self._pre_show_pause, self._post_round_pause,
         self.timer_limit) = preset
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
            self._next_time = now + self._post_round_pause
            self._bus.emit('round_complete', {'score': self.score})
            return 'round_complete'

        self._bus.emit('input_result', {'result': 'correct', 'name': name})
        return 'correct'

    def update(self, now: int) -> bool:
        """Advance the state machine. Returns True when entering 'input' state."""
        if self.state == 'adding':
            if now >= self._next_time:
                self.sequence.append(self._rng.choice(list(BUTTON_NAMES)))
                self.player_index = 0
                self._show_index  = 0
                self._showing_lit = False
                self.flash_button = None
                self.flash_state  = 'normal'
                self._next_time   = now + self._pre_show_pause
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
                    self.flash_end    = now + self._flash_time
                    self._showing_lit = True
            else:
                if now >= self.flash_end:
                    self.flash_button = None
                    self.flash_state  = 'normal'
                    self._showing_lit = False
                    self._show_index += 1
                    self._next_time   = now + self._inter_gap

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
