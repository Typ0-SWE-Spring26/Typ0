"""Tests for KeybindManager — covers #36 (button input keybind mapping)."""
import sys
import importlib
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def fake_pg():
    """Scoped pygame mock; reloads game.core.keybinds under the patch so that
    DEFAULT_MAP / INVERTED_MAP are built from real integer constants and
    key.name returns predictable strings."""
    mock = MagicMock()
    mock.K_a = 97
    mock.K_d = 100
    mock.K_w = 119
    mock.K_s = 115
    mock.K_SPACE = 32
    mock.key.name.side_effect = lambda k: {
        97: 'a', 100: 'd', 119: 'w', 115: 's', 32: 'space',
    }.get(k, 'unknown')

    with patch.dict(sys.modules, {'pygame': mock}):
        import game.core.keybinds
        importlib.reload(game.core.keybinds)
        yield mock


@pytest.fixture
def kb(fake_pg):
    from game.core.keybinds import KeybindManager
    return KeybindManager()


class TestKeybindDefaults:
    """Verify default (non-inverted) key mapping."""

    def test_default_has_all_buttons(self, kb):
        assert set(kb.button_keys.keys()) == {'left', 'right', 'up', 'down', 'space'}

    def test_default_not_inverted(self, kb):
        assert kb.inverted is False

    def test_default_map_matches_class_constant(self, kb):
        from game.core.keybinds import KeybindManager
        assert kb.button_keys is KeybindManager.DEFAULT_MAP

    def test_default_labels_generated_from_keys(self, kb):
        labels = kb.key_labels
        assert labels['left'] == 'A'
        assert labels['right'] == 'D'
        assert labels['up'] == 'W'
        assert labels['down'] == 'S'
        assert labels['space'] == 'SPACE'


class TestKeybindInvert:
    """Verify inverted controls swap directions but keep space."""

    def test_toggle_invert_switches_flag(self, kb):
        kb.toggle_invert()
        assert kb.inverted is True

    def test_toggle_invert_twice_restores(self, kb):
        kb.toggle_invert()
        kb.toggle_invert()
        assert kb.inverted is False

    def test_inverted_map_used_when_inverted(self, kb):
        from game.core.keybinds import KeybindManager
        kb.toggle_invert()
        assert kb.button_keys is KeybindManager.INVERTED_MAP

    def test_inverted_swaps_left_right(self, fake_pg):
        from game.core.keybinds import KeybindManager
        default_left = KeybindManager.DEFAULT_MAP['left']
        default_right = KeybindManager.DEFAULT_MAP['right']
        inverted_left = KeybindManager.INVERTED_MAP['left']
        inverted_right = KeybindManager.INVERTED_MAP['right']

        assert inverted_left == default_right
        assert inverted_right == default_left

    def test_inverted_swaps_up_down(self, fake_pg):
        from game.core.keybinds import KeybindManager
        default_up = KeybindManager.DEFAULT_MAP['up']
        default_down = KeybindManager.DEFAULT_MAP['down']
        inverted_up = KeybindManager.INVERTED_MAP['up']
        inverted_down = KeybindManager.INVERTED_MAP['down']

        assert inverted_up == default_down
        assert inverted_down == default_up

    def test_inverted_space_unchanged(self, fake_pg):
        from game.core.keybinds import KeybindManager
        assert KeybindManager.DEFAULT_MAP['space'] == KeybindManager.INVERTED_MAP['space']

    def test_labels_change_after_invert(self, kb):
        labels_before = kb.key_labels.copy()
        kb.toggle_invert()
        labels_after = kb.key_labels

        # Space stays the same, directions swap
        assert labels_before['space'] == labels_after['space']
        assert labels_before['left'] == labels_after['right']
        assert labels_before['right'] == labels_after['left']

    def test_invert_persists_across_reads(self, kb):
        kb.toggle_invert()
        first_read = kb.button_keys
        second_read = kb.button_keys
        assert first_read is second_read
