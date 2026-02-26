class GameTimer:
    """Countdown timer integrated with the EventBus.

    Emits:
        timer_started  — when start() is called
        timer_tick     — each update() while active; data = {'remaining': ms, 'fraction': 0–1}
        timer_expired  — when remaining hits 0; data = {'now': ticks}
        timer_paused   — when frozen by a game_paused event; data = {'remaining': ms}
        timer_resumed  — when restored by a game_resumed event; data = {'remaining': ms}

    Subscribes to:
        game_paused  — freezes the countdown
        game_resumed — restores the countdown from where it was frozen
    """

    TIME_LIMIT = 5000  # milliseconds

    def __init__(self, event_bus):
        self._bus = event_bus
        self._active = False
        self._start_ticks = 0
        self._paused_remaining = None  # ms remaining when frozen
        self.fraction = 1.0            # render-readable; 1.0 = full, 0.0 = empty

        event_bus.subscribe('game_paused',  self._on_game_paused)
        event_bus.subscribe('game_resumed', self._on_game_resumed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, now: int) -> None:
        self._start_ticks = now
        self._active = True
        self._paused_remaining = None
        self.fraction = 1.0
        self._bus.emit('timer_started')

    def stop(self) -> None:
        self._active = False
        self.fraction = 1.0

    def update(self, now: int) -> None:
        if not self._active:
            return
        elapsed = now - self._start_ticks
        remaining = max(self.TIME_LIMIT - elapsed, 0)
        self.fraction = remaining / self.TIME_LIMIT
        self._bus.emit('timer_tick', {'remaining': remaining, 'fraction': self.fraction})
        if remaining == 0:
            self._active = False
            self._bus.emit('timer_expired', {'now': now})

    # ------------------------------------------------------------------
    # EventBus callbacks
    # ------------------------------------------------------------------

    def _on_game_paused(self, data) -> None:
        if not self._active:
            return
        now = data['now']
        elapsed = now - self._start_ticks
        self._paused_remaining = max(self.TIME_LIMIT - elapsed, 0)
        self._active = False
        self._bus.emit('timer_paused', {'remaining': self._paused_remaining})

    def _on_game_resumed(self, data) -> None:
        if self._paused_remaining is None:
            return
        now = data['now']
        self._start_ticks = now - (self.TIME_LIMIT - self._paused_remaining)
        self._active = True
        self._bus.emit('timer_resumed', {'remaining': self._paused_remaining})
        self._paused_remaining = None
