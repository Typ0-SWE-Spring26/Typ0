import random

from game.core.game_model import BUTTON_NAMES


class BopItModel:
    """Bop-It style game: one random command at a time, speed increases.

    States: prompting -> input -> (prompting | gameover)
    """

    COMMAND_LABELS = {
        'left':  'Press LEFT!',
        'right': 'Press RIGHT!',
        'up':    'Press UP!',
        'down':  'Press DOWN!',
        'space': 'Press SPACE!',
    }

    BASE_TIME   = 5000   # starting time limit (ms)
    MIN_TIME    = 1500   # fastest time limit
    TIME_STEP   = 200    # ms shaved off each round

    BASE_ROUND_DELAY = 600   # pause between commands at score 0 (ms)
    MIN_ROUND_DELAY  = 250   # shortest pause between commands (ms)
    ROUND_DELAY_STEP = 20    # ms shaved off per successful command

    BASE_FLASH_TIME = 500     # command highlight duration at score 0 (ms)
    MIN_FLASH_TIME  = 250     # shortest command highlight duration (ms)
    FLASH_TIME_STEP = 15      # ms shaved off per successful command

    def __init__(self, event_bus):
        self._bus = event_bus
        self.reset()

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def reset(self):
        self.score          = 0
        self.state          = 'prompting'   # prompting | input | gameover
        self.current_command = None
        self.player_index   = 0             # always 0 (compat with view HUD)
        self.sequence: list[str] = []       # grows by 1 each round (for round display)

        self.flash_button   = None
        self.flash_state    = 'normal'
        self.flash_end      = 0

        self._next_time     = 0
        self.gameover_reason = "Wrong input!"

    # ------------------------------------------------------------------
    # Timer scaling
    # ------------------------------------------------------------------

    @property
    def time_limit(self) -> int:
        """Current round's time limit in ms — gets shorter as score grows."""
        return max(self.MIN_TIME, self.BASE_TIME - self.score * self.TIME_STEP)

    @property
    def round_delay(self) -> int:
        """Delay before the next command — also shrinks as score grows."""
        return max(self.MIN_ROUND_DELAY, self.BASE_ROUND_DELAY - self.score * self.ROUND_DELAY_STEP)

    @property
    def flash_time(self) -> int:
        """How long the command stays highlighted before input timing pressure starts."""
        return max(self.MIN_FLASH_TIME, self.BASE_FLASH_TIME - self.score * self.FLASH_TIME_STEP)

    # ------------------------------------------------------------------
    # Game logic
    # ------------------------------------------------------------------

    def handle_input(self, name: str, now: int) -> str:
        """Process a player button press.  Returns 'correct', 'round_complete', or 'wrong'."""
        self.flash_button = name
        self.flash_state  = 'pressed'
        self.flash_end    = now + 400

        if name != self.current_command:
            self.state = 'gameover'
            self._bus.emit('input_result', {'result': 'wrong', 'name': name})
            return 'wrong'

        self.score += 1
        self.state  = 'prompting'
        self._next_time = now + self.round_delay
        self._bus.emit('round_complete', {'score': self.score})
        return 'round_complete'

    def update(self, now: int) -> bool:
        """Advance the state machine.  Returns True when entering 'input'."""
        if self.state == 'prompting':
            if now >= self._next_time:
                self.current_command = random.choice(list(BUTTON_NAMES))
                self.sequence.append(self.current_command)  # keep round counter accurate
                self.flash_button = self.current_command
                self.flash_state  = 'indicated'
                self.flash_end    = now + self.flash_time
                self.state = 'input'
                self._bus.emit('state_changed', {'state': 'input'})
                return True   # signals controller to start the timer

        elif self.state == 'input':
            if self.flash_button and now >= self.flash_end:
                self.flash_button = None
                self.flash_state  = 'normal'

        return False

    def on_timer_expired(self, data) -> None:
        if self.state == 'input':
            self.state           = 'gameover'
            self.gameover_reason = "Time's up!"
            self.flash_end       = data['now']
