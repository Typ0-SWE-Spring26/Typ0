"""Behave environment hooks.

Mocks pygame once at session start so every step file can safely import
game modules without a real display being available.
"""
import sys
import os
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


def before_scenario(context, scenario):
    context._temp_files = []


def _safe_stop(context, attr):
    patcher = getattr(context, attr, None)
    if patcher is None:
        return
    stop = getattr(patcher, "stop", None)
    if not callable(stop):
        return
    try:
        stop()
    except Exception:
        # Avoid masking the real scenario failure due to double-stop/no-op cleanup.
        pass


def after_scenario(context, scenario):
    for attr in (
        "_go_pg_patch",
        "_go_anim_patch",
        "_hs_pg_patch",
        "_hs_anim_patch",
        "_hs_load_patch",
        "_credits_pg_patch",
        "_credits_anim_patch",
        "_ne_pg_patch",
        "_ne_anim_patch",
    ):
        _safe_stop(context, attr)

    for path in getattr(context, "_temp_files", []):
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
