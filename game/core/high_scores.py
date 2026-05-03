import json
import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAX_SCORES = 10

# Single-player modes whose leaderboards split by difficulty.
_SINGLE_PLAYER_MODES = ("simon", "bopit", "keys_ninja")


def _scores_dir() -> Path:
    scores_dir = os.environ.get("SCORES_DIR")
    base = Path(scores_dir) if scores_dir else _PROJECT_ROOT
    base.mkdir(parents=True, exist_ok=True)
    return base


def _scores_file(game_type: str) -> Path:
    """Return the path to the scores file for a given game type.

    Uses the SCORES_DIR environment variable when set (e.g. a persistent
    volume on a server), so scores survive redeployments.  Falls back to
    the project root for local development.
    """
    return _scores_dir() / f"{game_type}_scores.json"


def _migrate_legacy_scores() -> None:
    """One-shot migration of legacy `{mode}_scores.json` → `{mode}_normal_scores.json`.

    The leaderboards were split per-difficulty after release; existing
    scores are migrated into the Normal bucket (the previous default) so
    they aren't lost. Idempotent: skips when the destination already exists.
    """
    base = _scores_dir()
    for mode in _SINGLE_PLAYER_MODES:
        legacy = base / f"{mode}_scores.json"
        target = base / f"{mode}_normal_scores.json"
        if legacy.exists() and not target.exists():
            try:
                legacy.rename(target)
            except OSError:
                # Best-effort — a failure here just leaves legacy data behind
                # rather than crashing the game on launch.
                pass


_migrate_legacy_scores()


def _coerce_entry(entry):
    if not isinstance(entry, dict):
        return None

    name = entry.get("name")
    score = entry.get("score")

    if not isinstance(name, str):
        return None

    if isinstance(score, bool):
        return None

    coerced_score = None
    if isinstance(score, int):
        coerced_score = score
    elif isinstance(score, float):
        coerced_score = int(score)
    elif isinstance(score, str):
        raw = score.strip()
        if not raw:
            return None
        try:
            coerced_score = int(float(raw))
        except ValueError:
            return None
    else:
        return None

    return {"name": name, "score": coerced_score}


def load_scores(game_type: str):
    """Load high scores for *game_type* from JSON. Returns list of {"name": str, "score": int}."""
    try:
        with open(_scores_file(game_type), "r") as f:
            scores = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        scores = []

    if not isinstance(scores, list):
        scores = []

    valid_scores = []
    for entry in scores:
        coerced = _coerce_entry(entry)
        if coerced is not None:
            valid_scores.append(coerced)

    return sorted(valid_scores, key=lambda s: s["score"], reverse=True)[:MAX_SCORES]


def save_scores(scores, game_type: str):
    """Save high scores list for *game_type* to JSON."""
    cleaned = []
    for entry in scores:
        coerced = _coerce_entry(entry)
        if coerced is not None:
            cleaned.append(coerced)

    scores = sorted(cleaned, key=lambda s: s["score"], reverse=True)[:MAX_SCORES]
    with open(_scores_file(game_type), "w") as f:
        json.dump(scores, f)


def is_high_score(score, game_type: str):
    """Check if a score qualifies for the top 10 in *game_type*."""
    scores = load_scores(game_type)
    if len(scores) < MAX_SCORES:
        return True
    return score > scores[-1]["score"]


def add_score(name, score, game_type: str):
    """Add a new score for *game_type* and save. Returns the updated list."""
    scores = load_scores(game_type)
    scores.append({"name": name, "score": score})
    scores = sorted(scores, key=lambda s: s["score"], reverse=True)[:MAX_SCORES]
    save_scores(scores, game_type)
    return scores


# ── Async API wrappers (browser → HTTP API, native → file I/O) ───────────────

_IN_BROWSER: bool = sys.platform == "emscripten"


async def load_scores_async(game_type: str) -> list:
    if _IN_BROWSER:
        from game.network.scores_client import fetch_scores
        return await fetch_scores(game_type)
    return load_scores(game_type)


async def is_high_score_async(score, game_type: str) -> bool:
    scores = await load_scores_async(game_type)
    if len(scores) < MAX_SCORES:
        return True
    return score > scores[-1]["score"]


async def add_score_async(name, score, game_type: str) -> list:
    if _IN_BROWSER:
        from game.network.scores_client import submit_score
        return await submit_score(name, score, game_type)
    return add_score(name, score, game_type)
