"""Behave environment hooks.

Mocks pygame once at session start so every step file can safely import
game modules without a real display being available.
"""
import sys
from unittest.mock import MagicMock


def before_all(context):
    # Provide a fake pygame module so game code can be imported headlessly.
    sys.modules['pygame'] = MagicMock()

    # Import after the mock is in place so the module-level pygame constants
    # (K_a, K_d, etc.) are already resolved against the MagicMock.
    from game.core.event_bus import EventBus
    from game.core.game_model import GameModel

    context.EventBus = EventBus
    context.GameModel = GameModel
