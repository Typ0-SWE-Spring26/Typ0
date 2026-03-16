import json
import os

SCORES_FILE = "high_scores.json"
MAX_SCORES = 10


def load_scores():
    """Load high scores from JSON file. Returns list of {"name": str, "score": int}."""
    try:
        with open(SCORES_FILE, "r") as f:
            scores = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        scores = []
    return sorted(scores, key=lambda s: s["score"], reverse=True)[:MAX_SCORES]


def save_scores(scores):
    """Save high scores list to JSON file."""
    scores = sorted(scores, key=lambda s: s["score"], reverse=True)[:MAX_SCORES]
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
