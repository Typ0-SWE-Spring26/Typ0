"""Comprehensive tests for EventBus."""
import pytest
from game_screens.event_bus import EventBus


class TestEventBus:
    """Test suite for the EventBus class."""

    def test_init_creates_empty_listeners_dict(self):
        """EventBus should initialize with an empty listeners dictionary."""
        bus = EventBus()
        assert bus._listeners == {}

    def test_subscribe_single_listener(self):
        """Should allow subscribing a single callback to an event."""
        bus = EventBus()
        callback = lambda data: None
        bus.subscribe('test_event', callback)

        assert 'test_event' in bus._listeners
        assert callback in bus._listeners['test_event']
        assert len(bus._listeners['test_event']) == 1

    def test_subscribe_multiple_listeners_same_event(self):
        """Should allow multiple callbacks to subscribe to the same event."""
        bus = EventBus()
        callback1 = lambda data: None
        callback2 = lambda data: None
        callback3 = lambda data: None

        bus.subscribe('test_event', callback1)
        bus.subscribe('test_event', callback2)
        bus.subscribe('test_event', callback3)

        assert len(bus._listeners['test_event']) == 3
        assert callback1 in bus._listeners['test_event']
        assert callback2 in bus._listeners['test_event']
        assert callback3 in bus._listeners['test_event']

    def test_subscribe_different_events(self):
        """Should track listeners for different events separately."""
        bus = EventBus()
        callback1 = lambda data: None
        callback2 = lambda data: None

        bus.subscribe('event_a', callback1)
        bus.subscribe('event_b', callback2)

        assert 'event_a' in bus._listeners
        assert 'event_b' in bus._listeners
        assert callback1 in bus._listeners['event_a']
        assert callback2 in bus._listeners['event_b']

    def test_emit_with_no_listeners(self):
        """Emitting an event with no listeners should not raise an error."""
        bus = EventBus()
        # Should not raise any exception
        bus.emit('nonexistent_event')
        bus.emit('nonexistent_event', {'some': 'data'})

    def test_emit_calls_single_listener(self):
        """Should call the subscribed callback when event is emitted."""
        bus = EventBus()
        called = []

        def callback(data):
            called.append(data)

        bus.subscribe('test_event', callback)
        bus.emit('test_event', {'value': 42})

        assert len(called) == 1
        assert called[0] == {'value': 42}

    def test_emit_calls_all_listeners(self):
        """Should call all subscribed callbacks for an event."""
        bus = EventBus()
        results = []

        def callback1(data):
            results.append(('cb1', data))

        def callback2(data):
            results.append(('cb2', data))

        def callback3(data):
            results.append(('cb3', data))

        bus.subscribe('test_event', callback1)
        bus.subscribe('test_event', callback2)
        bus.subscribe('test_event', callback3)

        bus.emit('test_event', 'test_data')

        assert len(results) == 3
        assert ('cb1', 'test_data') in results
        assert ('cb2', 'test_data') in results
        assert ('cb3', 'test_data') in results

    def test_emit_with_none_data(self):
        """Should handle emitting events with None as data."""
        bus = EventBus()
        received_data = []

        def callback(data):
            received_data.append(data)

        bus.subscribe('test_event', callback)
        bus.emit('test_event', None)

        assert len(received_data) == 1
        assert received_data[0] is None

    def test_emit_without_data_argument(self):
        """Should handle emitting events without providing data."""
        bus = EventBus()
        received_data = []

        def callback(data):
            received_data.append(data)

        bus.subscribe('test_event', callback)
        bus.emit('test_event')

        assert len(received_data) == 1
        assert received_data[0] is None

    def test_listeners_isolated_by_event_name(self):
        """Emitting one event should not trigger listeners of other events."""
        bus = EventBus()
        event_a_calls = []
        event_b_calls = []

        bus.subscribe('event_a', lambda data: event_a_calls.append(data))
        bus.subscribe('event_b', lambda data: event_b_calls.append(data))

        bus.emit('event_a', 'data_a')

        assert len(event_a_calls) == 1
        assert len(event_b_calls) == 0
        assert event_a_calls[0] == 'data_a'

    def test_same_callback_subscribed_twice(self):
        """Should allow the same callback to be subscribed multiple times."""
        bus = EventBus()
        call_count = []

        def callback(data):
            call_count.append(data)

        bus.subscribe('test_event', callback)
        bus.subscribe('test_event', callback)

        bus.emit('test_event', 'data')

        # Callback should be called twice
        assert len(call_count) == 2

    def test_emit_preserves_callback_order(self):
        """Callbacks should be called in the order they were subscribed."""
        bus = EventBus()
        order = []

        bus.subscribe('test_event', lambda data: order.append(1))
        bus.subscribe('test_event', lambda data: order.append(2))
        bus.subscribe('test_event', lambda data: order.append(3))

        bus.emit('test_event')

        assert order == [1, 2, 3]

    def test_callback_exception_doesnt_stop_other_callbacks(self):
        """If one callback raises an exception, others should still be called."""
        bus = EventBus()
        results = []

        def failing_callback(data):
            results.append('before_error')
            raise ValueError("Test error")

        def success_callback(data):
            results.append('after_error')

        bus.subscribe('test_event', failing_callback)
        bus.subscribe('test_event', success_callback)

        # The exception should propagate but second callback should still run
        with pytest.raises(ValueError):
            bus.emit('test_event')

        # First callback should have run
        assert 'before_error' in results

    def test_complex_data_types(self):
        """Should handle complex data types being passed through events."""
        bus = EventBus()
        received = []

        bus.subscribe('test_event', lambda data: received.append(data))

        complex_data = {
            'nested': {'dict': 'value'},
            'list': [1, 2, 3],
            'tuple': (4, 5),
            'number': 42
        }

        bus.emit('test_event', complex_data)

        assert len(received) == 1
        assert received[0] == complex_data
        assert received[0]['nested']['dict'] == 'value'

    def test_multiple_emits_same_event(self):
        """Should handle multiple emits of the same event."""
        bus = EventBus()
        calls = []

        bus.subscribe('test_event', lambda data: calls.append(data))

        bus.emit('test_event', 1)
        bus.emit('test_event', 2)
        bus.emit('test_event', 3)

        assert calls == [1, 2, 3]

    def test_callback_with_method(self):
        """Should work with instance methods as callbacks."""
        bus = EventBus()

        class Handler:
            def __init__(self):
                self.received = []

            def handle(self, data):
                self.received.append(data)

        handler = Handler()
        bus.subscribe('test_event', handler.handle)
        bus.emit('test_event', 'test_data')

        assert handler.received == ['test_data']

    def test_event_names_are_case_sensitive(self):
        """Event names should be case sensitive."""
        bus = EventBus()
        lower_calls = []
        upper_calls = []

        bus.subscribe('event', lambda data: lower_calls.append(data))
        bus.subscribe('EVENT', lambda data: upper_calls.append(data))

        bus.emit('event', 'lower')
        bus.emit('EVENT', 'upper')

        assert lower_calls == ['lower']
        assert upper_calls == ['upper']

    def test_empty_string_event_name(self):
        """Should handle empty string as event name."""
        bus = EventBus()
        calls = []

        bus.subscribe('', lambda data: calls.append(data))
        bus.emit('', 'data')

        assert calls == ['data']

    def test_stress_many_listeners(self):
        """Should handle many listeners on a single event."""
        bus = EventBus()
        results = []

        # Subscribe 100 listeners
        for i in range(100):
            bus.subscribe('stress_test', lambda data, i=i: results.append(i))

        bus.emit('stress_test')

        assert len(results) == 100
        assert sorted(results) == list(range(100))