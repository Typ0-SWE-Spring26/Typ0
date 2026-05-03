"""Steps for per-difficulty leaderboard scenarios.

Each scenario gets its own temporary SCORES_DIR so leaderboards don't leak
between scenarios or stomp on the project root's *_scores.json files.
"""
import importlib
import json
import os
import tempfile
from pathlib import Path

from behave import given, when, then


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_scores_dir(ctx):
    """Lazily allocate a per-scenario SCORES_DIR + reload high_scores against it."""
    if getattr(ctx, "_pdh_scores_dir", None) is not None:
        return
    tmp = tempfile.mkdtemp(prefix="behave_scores_")
    ctx._pdh_scores_dir = tmp
    ctx._pdh_prev_env = os.environ.get("SCORES_DIR")
    os.environ["SCORES_DIR"] = tmp

    import game.core.high_scores as hs_mod
    importlib.reload(hs_mod)
    ctx._pdh_hs_mod = hs_mod
    # Track for cleanup so behave's after_scenario hook tears it down.
    if not hasattr(ctx, "_temp_files"):
        ctx._temp_files = []
    ctx._pdh_cleanup_dir = tmp


def _hs(ctx):
    _ensure_scores_dir(ctx)
    return ctx._pdh_hs_mod


def _bucket_path(ctx, bucket: str) -> Path:
    return Path(ctx._pdh_scores_dir) / f"{bucket}_scores.json"


# ---------------------------------------------------------------------------
# Server-side validation steps
# ---------------------------------------------------------------------------

@then('the server should accept "{game_type}" as a valid game type')
def step_server_accepts(ctx, game_type):
    from server.scores import VALID_GAME_TYPES
    assert game_type in VALID_GAME_TYPES, (
        f"{game_type!r} should be valid but isn't"
    )


@then('the server should reject "{game_type}" as a game type')
def step_server_rejects(ctx, game_type):
    from server.scores import VALID_GAME_TYPES
    assert game_type not in VALID_GAME_TYPES, (
        f"{game_type!r} is unexpectedly valid"
    )


# ---------------------------------------------------------------------------
# Bucket isolation steps
# ---------------------------------------------------------------------------

@given('an empty leaderboard for "{bucket}"')
def step_empty_bucket(ctx, bucket):
    _ensure_scores_dir(ctx)
    path = _bucket_path(ctx, bucket)
    path.write_text("[]")


@given('a "{filename}" file with one entry "{name}" {score:d}')
def step_existing_bucket_file(ctx, filename, name, score):
    _ensure_scores_dir(ctx)
    path = Path(ctx._pdh_scores_dir) / filename
    path.write_text(json.dumps([{"name": name, "score": score}]))


@when('the player posts score {score:d} with name "{name}" to "{bucket}"')
def step_add_to_bucket(ctx, score, name, bucket):
    hs = _hs(ctx)
    hs.add_score(name, score, bucket)


@then('the leaderboard for "{bucket}" should have {n:d} entry')
@then('the leaderboard for "{bucket}" should have {n:d} entries')
def step_bucket_count(ctx, bucket, n):
    hs = _hs(ctx)
    scores = hs.load_scores(bucket)
    assert len(scores) == n, (
        f'Expected {n} entries in {bucket!r}, got {len(scores)}: {scores}'
    )


@then('the top score on "{bucket}" should be {score:d}')
def step_top_score(ctx, bucket, score):
    hs = _hs(ctx)
    scores = hs.load_scores(bucket)
    assert scores, f"{bucket!r} is empty"
    assert scores[0]["score"] == score, (
        f'Expected top score {score} on {bucket!r}, got {scores[0]}'
    )


# ---------------------------------------------------------------------------
# Migration steps
# ---------------------------------------------------------------------------

@given('a legacy "{filename}" file with one entry "{name}" {score:d}')
def step_legacy_file(ctx, filename, name, score):
    _ensure_scores_dir(ctx)
    path = Path(ctx._pdh_scores_dir) / filename
    path.write_text(json.dumps([{"name": name, "score": score}]))


@when('the high scores module is reloaded')
def step_reload_module(ctx):
    _ensure_scores_dir(ctx)
    import game.core.high_scores as hs_mod
    ctx._pdh_hs_mod = importlib.reload(hs_mod)


@then('a "{filename}" file should exist with one entry "{name}" {score:d}')
def step_file_exists_with_entry(ctx, filename, name, score):
    path = Path(ctx._pdh_scores_dir) / filename
    assert path.exists(), f"{filename} should exist after migration"
    data = json.loads(path.read_text())
    assert data == [{"name": name, "score": score}], (
        f'Expected [{{"name":"{name}","score":{score}}}] in {filename}, got {data}'
    )


@then('no "{filename}" file should exist')
def step_no_file(ctx, filename):
    path = Path(ctx._pdh_scores_dir) / filename
    assert not path.exists(), f"{filename} should have been removed by migration"


@then('the legacy "{filename}" file should still exist')
def step_legacy_still_exists(ctx, filename):
    path = Path(ctx._pdh_scores_dir) / filename
    assert path.exists(), (
        f"{filename} should still exist when destination is occupied"
    )


# Per-scenario teardown lives in features/environment.py so the SCORES_DIR
# env var, the temp directory, and the cached high_scores module get reset
# between scenarios. (Behave only invokes the hook from environment.py.)
