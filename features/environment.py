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
    from game.core.bopit_model import BopItModel

    context.EventBus = EventBus
    context.GameModel = GameModel
    context.BopItModel = BopItModel


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


def _cleanup_per_difficulty_scores(context):
    """Tear down the temp SCORES_DIR set up by per_difficulty_high_scores_steps."""
    if not hasattr(context, "_pdh_scores_dir") or context._pdh_scores_dir is None:
        return
    prev = getattr(context, "_pdh_prev_env", None)
    if prev is None:
        os.environ.pop("SCORES_DIR", None)
    else:
        os.environ["SCORES_DIR"] = prev
    try:
        import importlib
        import game.core.high_scores as hs_mod
        importlib.reload(hs_mod)
    except Exception:
        pass
    try:
        import shutil
        shutil.rmtree(context._pdh_scores_dir, ignore_errors=True)
    except Exception:
        pass
    context._pdh_scores_dir = None


def after_scenario(context, scenario):
    _cleanup_per_difficulty_scores(context)
    for attr in (
        "_menu_pg_patch",
        "_menu_fm_patch",
        "_bopit_pg_patch",
        "_bopit_anim_patch",
        "_go_pg_patch",
        "_go_anim_patch",
        "_hs_pg_patch",
        "_hs_anim_patch",
        "_hs_load_patch",
        "_credits_pg_patch",
        "_credits_anim_patch",
        "_ne_pg_patch",
        "_ne_anim_patch",
        "_mm_pg_patch",
        "_mm_anim_patch",
        "_bhs_pg_patch",
        "_bhs_vol_patch",
        "_bhs_mus_patch",
        "_bhs_fl_patch",
        "_bhs_hs_pg_patch",
    ):
        _safe_stop(context, attr)

    for path in getattr(context, "_temp_files", []):
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
