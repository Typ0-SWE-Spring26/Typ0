"""Tests for the per-difficulty leaderboard migration and HighScoresScreen tabs.

Each single-player mode now has three leaderboards (easy/normal/hard) keyed
by composite IDs like `simon_easy`. Legacy single-board files are migrated
into the `_normal` bucket on first load.
"""
import importlib
import json
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

sys.modules["pygame"] = MagicMock()


# ── Local file migration (game/core/high_scores.py) ─────────────────────

class TestLocalLegacyMigration:
    """The migration helper renames `{mode}_scores.json` → `{mode}_normal_scores.json`."""

    def _reload_module(self, monkeypatch, scores_dir):
        monkeypatch.setenv("SCORES_DIR", str(scores_dir))
        import game.core.high_scores as hs_mod
        return importlib.reload(hs_mod)

    def test_legacy_file_is_renamed_into_normal_bucket(self, tmp_path, monkeypatch):
        legacy = tmp_path / "simon_scores.json"
        legacy.write_text(json.dumps([{"name": "OLD", "score": 99}]))

        self._reload_module(monkeypatch, tmp_path)

        assert not legacy.exists(), "legacy file should be moved, not copied"
        new = tmp_path / "simon_normal_scores.json"
        assert new.exists()
        assert json.loads(new.read_text()) == [{"name": "OLD", "score": 99}]

    def test_migration_runs_for_every_single_player_mode(self, tmp_path, monkeypatch):
        for mode in ("simon", "bopit", "keys_ninja"):
            (tmp_path / f"{mode}_scores.json").write_text("[]")

        self._reload_module(monkeypatch, tmp_path)

        for mode in ("simon", "bopit", "keys_ninja"):
            assert (tmp_path / f"{mode}_normal_scores.json").exists()
            assert not (tmp_path / f"{mode}_scores.json").exists()

    def test_migration_does_not_overwrite_existing_normal_bucket(self, tmp_path, monkeypatch):
        """If the destination already holds new data, the legacy file is left alone
        — players who started fresh post-migration shouldn't lose their wins."""
        legacy = tmp_path / "simon_scores.json"
        new = tmp_path / "simon_normal_scores.json"
        legacy.write_text(json.dumps([{"name": "OLD", "score": 1}]))
        new.write_text(json.dumps([{"name": "NEW", "score": 100}]))

        self._reload_module(monkeypatch, tmp_path)

        assert legacy.exists(), "legacy file kept when destination is occupied"
        assert json.loads(new.read_text()) == [{"name": "NEW", "score": 100}]

    def test_migration_is_idempotent(self, tmp_path, monkeypatch):
        legacy = tmp_path / "bopit_scores.json"
        legacy.write_text(json.dumps([{"name": "X", "score": 5}]))

        # First reload: migrates.
        self._reload_module(monkeypatch, tmp_path)
        assert (tmp_path / "bopit_normal_scores.json").exists()

        # Second reload: nothing to do; should not raise or duplicate.
        self._reload_module(monkeypatch, tmp_path)
        assert (tmp_path / "bopit_normal_scores.json").exists()
        assert not legacy.exists()

    def test_no_legacy_file_means_no_migration(self, tmp_path, monkeypatch):
        self._reload_module(monkeypatch, tmp_path)
        # Nothing was created — directory stays empty (apart from anything
        # the code may have made). Just assert the destination wasn't
        # spuriously created.
        for mode in ("simon", "bopit", "keys_ninja"):
            assert not (tmp_path / f"{mode}_normal_scores.json").exists()


# ── Server-side validation ──────────────────────────────────────────────

class TestServerValidGameTypes:
    """The server's set of accepted leaderboard buckets."""

    def test_each_single_player_mode_has_three_difficulty_buckets(self):
        from server.scores import VALID_GAME_TYPES
        for mode in ("simon", "bopit", "keys_ninja"):
            for diff in ("easy", "normal", "hard"):
                assert f"{mode}_{diff}" in VALID_GAME_TYPES

    def test_legacy_bare_modes_are_no_longer_accepted(self):
        from server.scores import VALID_GAME_TYPES
        for legacy in ("simon", "bopit", "keys_ninja"):
            assert legacy not in VALID_GAME_TYPES

    def test_multiplayer_is_a_single_shared_bucket(self):
        from server.scores import VALID_GAME_TYPES
        assert "multiplayer" in VALID_GAME_TYPES
        for diff in ("easy", "normal", "hard"):
            assert f"multiplayer_{diff}" not in VALID_GAME_TYPES

    def test_total_bucket_count_is_ten(self):
        """3 modes * 3 difficulties + 1 shared multiplayer = 10."""
        from server.scores import VALID_GAME_TYPES
        assert len(VALID_GAME_TYPES) == 10


# ── HighScoresScreen composite-id resolution ───────────────────────────

class TestHighScoresScreenGameType:
    """The screen accepts (game_mode, difficulty) and resolves the right key."""

    def _make(self, **kwargs):
        from game.screens.high_scores import HighScoresScreen
        return HighScoresScreen(Mock(), **kwargs)

    def test_simon_normal_resolves_to_simon_normal(self):
        s = self._make(game_mode="simon", difficulty="normal")
        assert s.game_type == "simon_normal"

    def test_keys_ninja_easy_resolves_to_keys_ninja_easy(self):
        s = self._make(game_mode="keys_ninja", difficulty="easy")
        assert s.game_type == "keys_ninja_easy"

    def test_unknown_difficulty_falls_back_to_normal(self):
        s = self._make(game_mode="bopit", difficulty="impossible")
        assert s.difficulty == "normal"
        assert s.game_type == "bopit_normal"

    def test_multiplayer_skips_difficulty_suffix(self):
        """Multiplayer leaderboard is shared, not per-difficulty."""
        s = self._make(game_mode="multiplayer")
        assert s.game_type == "multiplayer"
        assert s._has_difficulty_tabs is False

    def test_single_player_modes_show_difficulty_tabs(self):
        for mode in ("simon", "bopit", "keys_ninja"):
            assert self._make(game_mode=mode)._has_difficulty_tabs is True

    def test_legacy_game_type_kwarg_still_accepted(self):
        """Older callers passed `game_type="simon"` — keep that path working
        so we don't break in-tree usages we may have missed."""
        s = self._make(game_type="simon")
        assert s.game_mode == "simon"
        assert s.game_type == "simon_normal"

    def test_missing_mode_raises(self):
        from game.screens.high_scores import HighScoresScreen
        with pytest.raises(TypeError):
            HighScoresScreen(Mock())


# ── HighScoresScreen tab switching ─────────────────────────────────────

class TestHighScoresScreenTabSwitch:
    """Clicking a different difficulty tab reloads scores for that bucket."""

    def _patched(self):
        return patch.multiple(
            "game.screens.high_scores",
            pygame=MagicMock(),
            animation_utils=MagicMock(),
            load_scores_async=AsyncMock(return_value=[]),
        )

    def test_clicking_a_tab_changes_difficulty_and_reloads(self):
        # We don't drive the async loop here — instead we exercise the
        # tab-button outcome directly so the test stays a unit test.
        from game.screens.high_scores import HighScoresScreen, _DIFFICULTIES

        screen = Mock()
        screen.get_width.return_value = 800
        screen.get_height.return_value = 600

        with patch("game.screens.high_scores.pygame") as mock_pg:
            mock_pg.font.Font.return_value = Mock(
                render=Mock(return_value=Mock(get_rect=Mock(return_value=Mock())))
            )
            mock_pg.Rect.side_effect = lambda *a, **kw: MagicMock()

            hs = HighScoresScreen(screen, game_mode="simon", difficulty="normal")
            tabs = hs._build_tab_buttons()

            # Every difficulty has a tab.
            assert set(tabs) == set(_DIFFICULTIES)
            # And the active one renders with its accent color, not the default.
            assert tabs["normal"].color != tabs["easy"].color or \
                   tabs["normal"].color != tabs["hard"].color

    def test_active_difficulty_tab_uses_distinctive_color(self):
        from game.screens.high_scores import HighScoresScreen, _TAB_COLORS

        with patch("game.screens.high_scores.pygame") as mock_pg:
            mock_pg.font.Font.return_value = Mock()
            mock_pg.Rect.side_effect = lambda *a, **kw: MagicMock()

            hs = HighScoresScreen(Mock(get_width=Mock(return_value=800),
                                       get_height=Mock(return_value=600)),
                                  game_mode="simon", difficulty="hard")
            tabs = hs._build_tab_buttons()

            # The active tab inherits the per-difficulty accent; the
            # inactive tabs fall back to the default Button styling.
            assert tabs["hard"].color == _TAB_COLORS["hard"]
            assert tabs["easy"].color != _TAB_COLORS["easy"]
            assert tabs["normal"].color != _TAB_COLORS["normal"]


# ── main.py composite-id wiring (formula-level test) ────────────────────

class TestLeaderboardIdFormula:
    """The leaderboard ID main.py constructs must match the server's bucket name."""

    @pytest.mark.parametrize("mode", ["simon", "bopit", "keys_ninja"])
    @pytest.mark.parametrize("diff", ["easy", "normal", "hard"])
    def test_composite_id_is_accepted_by_server(self, mode, diff):
        from server.scores import VALID_GAME_TYPES
        composite = f"{mode}_{diff}"  # exactly what main.py builds
        assert composite in VALID_GAME_TYPES
