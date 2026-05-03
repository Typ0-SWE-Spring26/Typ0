"""Server-side score persistence for TYP0.

Reads/writes JSON files, one per game type.
The SCORES_DIR environment variable controls where files are stored —
point it at a persistent directory (e.g. /home/typo/scores) so scores
survive redeployments.  Falls back to the directory containing this file.
"""

import json
import os
from pathlib import Path
import logging

MAX_SCORES = 10

# Per-mode leaderboards are split by difficulty, e.g. "simon_easy",
# "simon_normal", "simon_hard". Multiplayer is shared across difficulties
# because both players agree on a seed and there's no preset selector.
_DIFFICULTIES = ("easy", "normal", "hard")
_SINGLE_PLAYER_MODES = ("simon", "bopit", "keys_ninja")
VALID_GAME_TYPES = {
    f"{mode}_{difficulty}"
    for mode in _SINGLE_PLAYER_MODES
    for difficulty in _DIFFICULTIES
} | {"multiplayer"}


def _scores_dir() -> Path:
    d = os.environ.get("SCORES_DIR")
    base = Path(d) if d else Path(__file__).parent
    base.mkdir(parents=True, exist_ok=True)
    return base


def _scores_file(game_type: str) -> Path:
    return _scores_dir() / f"{game_type}_scores.json"


def _migrate_legacy_scores() -> None:
    """One-shot migration: move legacy {mode}_scores.json into {mode}_normal.

    Earlier versions stored a single leaderboard per mode; per-difficulty
    leaderboards split that into three. Existing data is treated as Normal
    runs (the previous default) so longtime players don't lose their scores.
    Runs only when the legacy file exists *and* the normal-bucket file does
    not — a destination-exists check is the migration's idempotency guard.
    """
    base = _scores_dir()
    logger = logging.getLogger(__name__)
    for mode in _SINGLE_PLAYER_MODES:
        legacy = base / f"{mode}_scores.json"
        target = base / f"{mode}_normal_scores.json"
        if legacy.exists() and not target.exists():
            try:
                legacy.rename(target)
            except OSError as err:
                # Migration is best-effort during import; do not abort import
                # if the filesystem operation fails. Log a non-fatal warning
                # including the paths and the caught error for troubleshooting.
                logger.warning(
                    "Failed to migrate legacy scores from %s to %s: %s",
                    str(legacy), str(target), err,
                    exc_info=True,
                )


_migrate_legacy_scores()


def load_scores(game_type: str) -> list:
    try:
        with open(_scores_file(game_type)) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    if not isinstance(data, list):
        return []
    result = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        score = entry.get("score")
        if isinstance(name, str) and isinstance(score, int) and not isinstance(score, bool):
            result.append({"name": name, "score": score})
    return sorted(result, key=lambda s: s["score"], reverse=True)[:MAX_SCORES]


def add_score(name: str, score: int, game_type: str) -> list:
    scores = load_scores(game_type)
    scores.append({"name": name, "score": score})
    scores = sorted(scores, key=lambda s: s["score"], reverse=True)[:MAX_SCORES]
    with open(_scores_file(game_type), "w") as f:
        json.dump(scores, f)
    return scores


def is_high_score(score: int, game_type: str) -> bool:
    scores = load_scores(game_type)
    if len(scores) < MAX_SCORES:
        return True
    return score > scores[-1]["score"]
