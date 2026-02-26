"""Comprehensive tests for GameTimer."""
import pytest
from unittest.mock import Mock
from game_screens.event_bus import EventBus
from game_screens.game_timer import GameTimer


class TestGameTimer:
    """Test suite for the GameTimer class."""

    def test_init_creates_inactive_timer(self):
        """GameTimer should initialize in an inactive state."""
        bus = EventBus()
        timer = GameTimer(bus)

        assert timer._active is False
        assert timer._start_ticks == 0
        assert timer._paused_remaining is None
        assert timer.fraction == 1.0

    def test_init_subscribes_to_pause_events(self):
        """GameTimer should subscribe to game_paused and game_resumed events."""
        bus = EventBus()
        timer = GameTimer(bus)

        assert 'game_paused' in bus._listeners
        assert 'game_resumed' in bus._listeners
        assert timer._on_game_paused in bus._listeners['game_paused']
        assert timer._on_game_resumed in bus._listeners['game_resumed']

    def test_start_activates_timer(self):
        """start() should activate the timer and set initial state."""
        bus = EventBus()
        timer = GameTimer(bus)

        timer.start(1000)

        assert timer._active is True
        assert timer._start_ticks == 1000
        assert timer._paused_remaining is None
        assert timer.fraction == 1.0

    def test_start_emits_timer_started_event(self):
        """start() should emit timer_started event."""
        bus = EventBus()
        timer = GameTimer(bus)
        events = []

        bus.subscribe('timer_started', lambda data: events.append('started'))

        timer.start(1000)

        assert 'started' in events

    def test_stop_deactivates_timer(self):
        """stop() should deactivate the timer and reset fraction."""
        bus = EventBus()
        timer = GameTimer(bus)

        timer.start(1000)
        timer.stop()

        assert timer._active is False
        assert timer.fraction == 1.0

    def test_update_when_inactive_does_nothing(self):
        """update() should do nothing when timer is not active."""
        bus = EventBus()
        timer = GameTimer(bus)
        events = []

        bus.subscribe('timer_tick', lambda data: events.append(data))

        timer.update(1000)

        assert len(events) == 0
        assert timer.fraction == 1.0

    def test_update_calculates_remaining_time(self):
        """update() should calculate remaining time correctly."""
        bus = EventBus()
        timer = GameTimer(bus)

        timer.start(1000)
        timer.update(2000)  # 1000ms elapsed

        expected_remaining = GameTimer.TIME_LIMIT - 1000
        assert timer.fraction == expected_remaining / GameTimer.TIME_LIMIT

    def test_update_emits_timer_tick(self):
        """update() should emit timer_tick event with correct data."""
        bus = EventBus()
        timer = GameTimer(bus)
        tick_events = []

        bus.subscribe('timer_tick', lambda data: tick_events.append(data))

        timer.start(1000)
        timer.update(2000)

        assert len(tick_events) == 1
        assert 'remaining' in tick_events[0]
        assert 'fraction' in tick_events[0]
        assert tick_events[0]['remaining'] == 4000  # 5000 - 1000
        assert tick_events[0]['fraction'] == 0.8

    def test_update_multiple_times_decreases_fraction(self):
        """Multiple updates should decrease the fraction over time."""
        bus = EventBus()
        timer = GameTimer(bus)

        timer.start(0)

        timer.update(1000)
        fraction_1 = timer.fraction

        timer.update(2000)
        fraction_2 = timer.fraction

        timer.update(3000)
        fraction_3 = timer.fraction

        assert fraction_1 > fraction_2 > fraction_3
        assert 0 <= fraction_3 <= 1.0

    def test_update_at_time_limit_expires_timer(self):
        """update() at exactly TIME_LIMIT should expire the timer."""
        bus = EventBus()
        timer = GameTimer(bus)
        expired_events = []

        bus.subscribe('timer_expired', lambda data: expired_events.append(data))

        timer.start(0)
        timer.update(GameTimer.TIME_LIMIT)

        assert timer._active is False
        assert timer.fraction == 0.0
        assert len(expired_events) == 1
        assert expired_events[0]['now'] == GameTimer.TIME_LIMIT

    def test_update_beyond_time_limit_expires_timer(self):
        """update() beyond TIME_LIMIT should expire the timer with fraction 0."""
        bus = EventBus()
        timer = GameTimer(bus)
        expired_events = []

        bus.subscribe('timer_expired', lambda data: expired_events.append(data))

        timer.start(0)
        timer.update(GameTimer.TIME_LIMIT + 1000)

        assert timer._active is False
        assert timer.fraction == 0.0
        assert len(expired_events) == 1

    def test_timer_expired_emits_once(self):
        """Timer should only emit timer_expired once even with multiple updates."""
        bus = EventBus()
        timer = GameTimer(bus)
        expired_count = []

        bus.subscribe('timer_expired', lambda data: expired_count.append(1))

        timer.start(0)
        timer.update(GameTimer.TIME_LIMIT)
        timer.update(GameTimer.TIME_LIMIT + 100)
        timer.update(GameTimer.TIME_LIMIT + 200)

        assert len(expired_count) == 1

    def test_on_game_paused_when_active(self):
        """_on_game_paused should freeze the timer when active."""
        bus = EventBus()
        timer = GameTimer(bus)
        paused_events = []

        bus.subscribe('timer_paused', lambda data: paused_events.append(data))

        timer.start(1000)
        timer.update(2000)  # 1000ms elapsed, 4000ms remaining

        bus.emit('game_paused', {'now': 2000})

        assert timer._active is False
        assert timer._paused_remaining == 4000
        assert len(paused_events) == 1
        assert paused_events[0]['remaining'] == 4000

    def test_on_game_paused_when_inactive(self):
        """_on_game_paused should do nothing when timer is not active."""
        bus = EventBus()
        timer = GameTimer(bus)
        paused_events = []

        bus.subscribe('timer_paused', lambda data: paused_events.append(data))

        bus.emit('game_paused', {'now': 1000})

        assert timer._paused_remaining is None
        assert len(paused_events) == 0

    def test_on_game_resumed_restores_timer(self):
        """_on_game_resumed should restore the timer from paused state."""
        bus = EventBus()
        timer = GameTimer(bus)
        resumed_events = []

        bus.subscribe('timer_resumed', lambda data: resumed_events.append(data))

        # Start, then pause
        timer.start(1000)
        timer.update(2000)  # 1000ms elapsed
        bus.emit('game_paused', {'now': 2000})

        # Resume
        bus.emit('game_resumed', {'now': 3000})

        assert timer._active is True
        assert timer._paused_remaining is None
        # start_ticks should be adjusted so 4000ms remain
        assert timer._start_ticks == 3000 - (GameTimer.TIME_LIMIT - 4000)
        assert len(resumed_events) == 1
        assert resumed_events[0]['remaining'] == 4000

    def test_on_game_resumed_when_not_paused(self):
        """_on_game_resumed should do nothing if timer wasn't paused."""
        bus = EventBus()
        timer = GameTimer(bus)
        resumed_events = []

        bus.subscribe('timer_resumed', lambda data: resumed_events.append(data))

        bus.emit('game_resumed', {'now': 1000})

        assert len(resumed_events) == 0

    def test_pause_resume_cycle_preserves_remaining_time(self):
        """Pausing and resuming should preserve the remaining time."""
        bus = EventBus()
        timer = GameTimer(bus)

        # Start and run for 1 second
        timer.start(0)
        timer.update(1000)  # 4000ms remaining
        fraction_before_pause = timer.fraction

        # Pause for 2 seconds
        bus.emit('game_paused', {'now': 1000})

        # Resume
        bus.emit('game_resumed', {'now': 3000})

        # Continue for 1 more second
        timer.update(4000)

        # Should have 3000ms remaining (4000 - 1000)
        expected_remaining = 3000
        expected_fraction = expected_remaining / GameTimer.TIME_LIMIT
        assert abs(timer.fraction - expected_fraction) < 0.001

    def test_multiple_pause_resume_cycles(self):
        """Should handle multiple pause/resume cycles correctly."""
        bus = EventBus()
        timer = GameTimer(bus)

        timer.start(0)

        # First cycle
        timer.update(500)
        bus.emit('game_paused', {'now': 500})
        bus.emit('game_resumed', {'now': 1000})

        # Second cycle
        timer.update(1500)
        bus.emit('game_paused', {'now': 1500})
        bus.emit('game_resumed', {'now': 2000})

        # Final update
        timer.update(2500)

        # Total elapsed: 500 + 500 + 500 = 1500ms
        # Remaining: 5000 - 1500 = 3500ms
        expected_fraction = 3500 / GameTimer.TIME_LIMIT
        assert abs(timer.fraction - expected_fraction) < 0.001

    def test_timer_expiration_while_paused_scenario(self):
        """Should handle the edge case where timer is paused with minimal time."""
        bus = EventBus()
        timer = GameTimer(bus)
        expired_events = []

        bus.subscribe('timer_expired', lambda data: expired_events.append(data))

        # Start and let almost all time elapse
        timer.start(0)
        timer.update(4990)  # 10ms remaining

        # Pause
        bus.emit('game_paused', {'now': 4990})

        # Resume and finish
        bus.emit('game_resumed', {'now': 5000})
        timer.update(5010)  # Should expire

        assert timer._active is False
        assert len(expired_events) == 1

    def test_fraction_never_negative(self):
        """Fraction should never go negative even with large time values."""
        bus = EventBus()
        timer = GameTimer(bus)

        timer.start(0)
        timer.update(GameTimer.TIME_LIMIT * 10)

        assert timer.fraction >= 0.0

    def test_restart_timer_after_stop(self):
        """Should be able to start timer again after stopping."""
        bus = EventBus()
        timer = GameTimer(bus)

        timer.start(1000)
        timer.update(2000)
        timer.stop()

        timer.start(5000)
        assert timer._active is True
        assert timer._start_ticks == 5000
        assert timer.fraction == 1.0

    def test_restart_timer_after_expiration(self):
        """Should be able to start timer again after it expires."""
        bus = EventBus()
        timer = GameTimer(bus)

        timer.start(0)
        timer.update(GameTimer.TIME_LIMIT)

        assert timer._active is False

        timer.start(10000)
        assert timer._active is True
        assert timer._start_ticks == 10000
        assert timer.fraction == 1.0

    def test_time_limit_constant(self):
        """TIME_LIMIT should be 5000 milliseconds."""
        assert GameTimer.TIME_LIMIT == 5000

    def test_pause_at_zero_remaining(self):
        """Should handle pause when timer reaches exactly zero."""
        bus = EventBus()
        timer = GameTimer(bus)

        timer.start(0)
        timer.update(GameTimer.TIME_LIMIT - 100)
        bus.emit('game_paused', {'now': GameTimer.TIME_LIMIT - 100})

        assert timer._paused_remaining == 100
        assert timer._active is False

    def test_fraction_calculation_precision(self):
        """Fraction should be calculated with good precision."""
        bus = EventBus()
        timer = GameTimer(bus)

        timer.start(0)
        timer.update(2500)  # Exactly halfway

        assert timer.fraction == 0.5

    def test_concurrent_updates_dont_break_state(self):
        """Multiple rapid updates should maintain consistent state."""
        bus = EventBus()
        timer = GameTimer(bus)

        timer.start(0)

        for i in range(100, 5001, 100):
            timer.update(i)
            assert 0.0 <= timer.fraction <= 1.0

    def test_edge_case_resume_immediately_after_pause(self):
        """Resume immediately after pause should work correctly."""
        bus = EventBus()
        timer = GameTimer(bus)

        timer.start(1000)
        timer.update(2000)

        bus.emit('game_paused', {'now': 2000})
        bus.emit('game_resumed', {'now': 2000})

        # Timer should be active again with same remaining time
        assert timer._active is True

    def test_timer_tick_emitted_on_every_update(self):
        """timer_tick should be emitted on every update when active."""
        bus = EventBus()
        timer = GameTimer(bus)
        tick_count = []

        bus.subscribe('timer_tick', lambda data: tick_count.append(1))

        timer.start(0)

        for i in range(10):
            timer.update(i * 100)

        assert len(tick_count) == 10

    def test_negative_time_handling(self):
        """Should handle edge case of update with time before start_ticks."""
        bus = EventBus()
        timer = GameTimer(bus)

        timer.start(1000)
        timer.update(500)  # Time before start

        # Elapsed is negative (-500), so remaining = TIME_LIMIT - (-500) = 5500
        # This gives fraction > 1.0, which is expected behavior (timer hasn't started counting down)
        assert timer.fraction > 1.0

    def test_very_large_time_values(self):
        """Should handle very large time values without overflow."""
        bus = EventBus()
        timer = GameTimer(bus)

        large_time = 1000000000
        timer.start(large_time)
        timer.update(large_time + 2500)

        assert timer.fraction == 0.5