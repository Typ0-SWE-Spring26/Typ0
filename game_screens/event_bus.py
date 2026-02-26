class EventBus:
    """Simple publish/subscribe event hub."""

    def __init__(self):
        self._listeners = {}

    def subscribe(self, event: str, callback) -> None:
        self._listeners.setdefault(event, []).append(callback)

    def emit(self, event: str, data=None) -> None:
        for cb in self._listeners.get(event, []):
            cb(data)
