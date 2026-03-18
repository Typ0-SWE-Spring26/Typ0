import json
from pathlib import Path

SCORES_FILE = Path(__file__).resolve().parents[2] / "high_scores.json"
MAX_SCORES = 10


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


def load_scores():
    """Load high scores from JSON file. Returns list of {"name": str, "score": int}."""
    try:
        with open(SCORES_FILE, "r") as f:
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


def save_scores(scores):
    """Save high scores list to JSON file."""
    cleaned = []
    for entry in scores:
        coerced = _coerce_entry(entry)
        if coerced is not None:
            cleaned.append(coerced)

    scores = sorted(cleaned, key=lambda s: s["score"], reverse=True)[:MAX_SCORES]
    with open(SCORES_FILE, "w") as f:
        json.dump(scores, f)


def is_high_score(score):
    """Check if a score qualifies for the top 10."""
    scores = load_scores()
    if len(scores) < MAX_SCORES:
        return True
    return score > scores[-1]["score"]


def add_score(name, score):
    """Add a new score and save. Returns the updated list."""
    scores = load_scores()
    scores.append({"name": name, "score": score})
    scores = sorted(scores, key=lambda s: s["score"], reverse=True)[:MAX_SCORES]
    save_scores(scores)
    return scores
