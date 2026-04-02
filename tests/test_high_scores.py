"""Unit tests for high scores system — load, save, ranking."""
import json
import pytest
from unittest.mock import patch
from game.core.high_scores import load_scores, save_scores, is_high_score, add_score, MAX_SCORES


def _patch_scores_file(tmp_path, game_type="simon"):
    """Helper: patch _scores_file to return a temp path for the given game type."""
    f = tmp_path / f"{game_type}_scores.json"
    return patch("game.core.high_scores._scores_file", return_value=f), f


class TestLoadScores:
    """Verify loading scores from JSON file."""

    def test_load_empty_file(self, tmp_path):
        p, f = _patch_scores_file(tmp_path)
        f.write_text("[]")
        with p:
            assert load_scores("simon") == []

    def test_load_missing_file(self, tmp_path):
        p, _ = _patch_scores_file(tmp_path)
        with p:
            assert load_scores("simon") == []

    def test_load_corrupt_file(self, tmp_path):
        p, f = _patch_scores_file(tmp_path)
        f.write_text("not json!!!")
        with p:
            assert load_scores("simon") == []

    def test_load_returns_sorted_descending(self, tmp_path):
        p, f = _patch_scores_file(tmp_path)
        data = [{"name": "AAA", "score": 5}, {"name": "BBB", "score": 20}, {"name": "CCC", "score": 10}]
        f.write_text(json.dumps(data))
        with p:
            scores = load_scores("simon")
            assert scores[0]["score"] == 20
            assert scores[1]["score"] == 10
            assert scores[2]["score"] == 5

    def test_load_truncates_to_max(self, tmp_path):
        p, f = _patch_scores_file(tmp_path)
        data = [{"name": f"P{i}", "score": i} for i in range(15)]
        f.write_text(json.dumps(data))
        with p:
            scores = load_scores("simon")
            assert len(scores) == MAX_SCORES

    def test_load_skips_invalid_entries(self, tmp_path):
        p, f = _patch_scores_file(tmp_path)
        data = [
            {"name": "GOOD", "score": 10},
            {"name": "BAD_NO_SCORE"},
            {"score": 50},
            "not-a-dict",
            {"name": 123, "score": 40},
        ]
        f.write_text(json.dumps(data))
        with p:
            scores = load_scores("simon")
        assert scores == [{"name": "GOOD", "score": 10}]

    def test_load_coerces_numeric_like_scores(self, tmp_path):
        p, f = _patch_scores_file(tmp_path)
        data = [
            {"name": "A", "score": "42"},
            {"name": "B", "score": "9.9"},
            {"name": "C", "score": 10.7},
        ]
        f.write_text(json.dumps(data))
        with p:
            scores = load_scores("simon")
        assert scores[0] == {"name": "A", "score": 42}


class TestSaveScores:
    """Verify saving scores to JSON file."""

    def test_save_writes_valid_json(self, tmp_path):
        p, f = _patch_scores_file(tmp_path)
        f.write_text("[]")
        data = [{"name": "AAA", "score": 42}]
        with p:
            save_scores(data, "simon")
        loaded = json.loads(f.read_text())
        assert len(loaded) == 1
        assert loaded[0]["score"] == 42

    def test_save_sorts_and_truncates(self, tmp_path):
        p, f = _patch_scores_file(tmp_path)
        f.write_text("[]")
        data = [{"name": f"P{i}", "score": i} for i in range(15)]
        with p:
            save_scores(data, "simon")
        loaded = json.loads(f.read_text())
        assert len(loaded) == MAX_SCORES
        assert loaded[0]["score"] == 14  # highest


class TestIsHighScore:
    """Verify high score qualification check."""

    def test_any_score_qualifies_when_list_empty(self, tmp_path):
        p, f = _patch_scores_file(tmp_path)
        f.write_text("[]")
        with p:
            assert is_high_score(0, "simon") is True

    def test_qualifies_when_list_not_full(self, tmp_path):
        p, f = _patch_scores_file(tmp_path)
        data = [{"name": "AAA", "score": 100}]
        f.write_text(json.dumps(data))
        with p:
            assert is_high_score(1, "simon") is True

    def test_qualifies_when_beats_lowest(self, tmp_path):
        p, f = _patch_scores_file(tmp_path)
        data = [{"name": f"P{i}", "score": (i + 1) * 10} for i in range(MAX_SCORES)]
        f.write_text(json.dumps(data))
        with p:
            assert is_high_score(11, "simon") is True

    def test_does_not_qualify_when_too_low(self, tmp_path):
        p, f = _patch_scores_file(tmp_path)
        data = [{"name": f"P{i}", "score": (i + 1) * 10} for i in range(MAX_SCORES)]
        f.write_text(json.dumps(data))
        with p:
            assert is_high_score(5, "simon") is False

    def test_zero_does_not_qualify_on_full_list(self, tmp_path):
        p, f = _patch_scores_file(tmp_path)
        data = [{"name": f"P{i}", "score": i + 1} for i in range(MAX_SCORES)]
        f.write_text(json.dumps(data))
        with p:
            assert is_high_score(0, "simon") is False


class TestAddScore:
    """Verify adding a new score persists correctly."""

    def test_add_to_empty(self, tmp_path):
        p, f = _patch_scores_file(tmp_path)
        f.write_text("[]")
        with p:
            result = add_score("HELLO", 50, "simon")
        assert len(result) == 1
        assert result[0] == {"name": "HELLO", "score": 50}

    def test_add_maintains_sort_order(self, tmp_path):
        p, f = _patch_scores_file(tmp_path)
        f.write_text(json.dumps([{"name": "AAA", "score": 100}, {"name": "BBB", "score": 20}]))
        with p:
            result = add_score("CCC", 50, "simon")
        assert result[0]["score"] == 100
        assert result[1]["score"] == 50
        assert result[2]["score"] == 20

    def test_add_bumps_lowest_when_full(self, tmp_path):
        p, f = _patch_scores_file(tmp_path)
        data = [{"name": f"P{i}", "score": (i + 1) * 10} for i in range(MAX_SCORES)]
        f.write_text(json.dumps(data))
        with p:
            result = add_score("NEW", 999, "simon")
        assert len(result) == MAX_SCORES
        assert result[0]["name"] == "NEW"
        assert result[0]["score"] == 999

    def test_add_persists_to_file(self, tmp_path):
        p, f = _patch_scores_file(tmp_path)
        f.write_text("[]")
        with p:
            add_score("TST", 77, "simon")
        loaded = json.loads(f.read_text())
        assert loaded[0]["name"] == "TST"

    def test_separate_files_per_game_type(self, tmp_path, monkeypatch):
        """Each game type gets its own independent leaderboard."""
        monkeypatch.setenv("SCORES_DIR", str(tmp_path))
        add_score("AAA", 100, "simon")
        add_score("BBB", 200, "bopit")
        add_score("CCC", 300, "multiplayer")
        assert load_scores("simon") == [{"name": "AAA", "score": 100}]
        assert load_scores("bopit") == [{"name": "BBB", "score": 200}]
        assert load_scores("multiplayer") == [{"name": "CCC", "score": 300}]
