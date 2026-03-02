"""Tests for KeybindManager — covers #36 (button input keybind mapping)."""
import sys
from unittest.mock import MagicMock

sys.modules['pygame'] = MagicMock()

from game.core.keybinds import KeybindManager


class TestKeybindDefaults:
    """Verify default (non-inverted) key mapping."""

    def test_default_has_all_buttons(self):
        kb = KeybindManager()
        assert set(kb.button_keys.keys()) == {'left', 'right', 'up', 'down', 'space'}

    def test_default_not_inverted(self):
        kb = KeybindManager()
        assert kb.inverted is False

    def test_default_map_matches_class_constant(self):
        kb = KeybindManager()
        assert kb.button_keys is KeybindManager.DEFAULT_MAP

    def test_default_labels_generated_from_keys(self):
        """Verify key_labels generates labels for all buttons."""
        kb = KeybindManager()
        # Verify that key_labels returns a dictionary with all expected buttons
        assert set(kb.key_labels.keys()) == {'left', 'right', 'up', 'down', 'space'}
        # Verify that key_labels is a dictionary
        assert isinstance(kb.key_labels, dict)
        # Verify that invoking key_labels property works (doesn't raise an exception)
        labels = kb.key_labels
        assert len(labels) == 5


class TestKeybindInvert:
    """Verify inverted controls swap directions but keep space."""

    def test_toggle_invert_switches_flag(self):
        kb = KeybindManager()
        kb.toggle_invert()
        assert kb.inverted is True

    def test_toggle_invert_twice_restores(self):
        kb = KeybindManager()
        kb.toggle_invert()
        kb.toggle_invert()
        assert kb.inverted is False

    def test_inverted_map_used_when_inverted(self):
        kb = KeybindManager()
        kb.toggle_invert()
        assert kb.button_keys is KeybindManager.INVERTED_MAP

    def test_inverted_swaps_left_right(self):
        default_left = KeybindManager.DEFAULT_MAP['left']
        default_right = KeybindManager.DEFAULT_MAP['right']
        inverted_left = KeybindManager.INVERTED_MAP['left']
        inverted_right = KeybindManager.INVERTED_MAP['right']

        assert inverted_left == default_right
        assert inverted_right == default_left

    def test_inverted_swaps_up_down(self):
        default_up = KeybindManager.DEFAULT_MAP['up']
        default_down = KeybindManager.DEFAULT_MAP['down']
        inverted_up = KeybindManager.INVERTED_MAP['up']
        inverted_down = KeybindManager.INVERTED_MAP['down']

        assert inverted_up == default_down
        assert inverted_down == default_up

    def test_inverted_space_unchanged(self):
        assert KeybindManager.DEFAULT_MAP['space'] == KeybindManager.INVERTED_MAP['space']

    def test_labels_change_after_invert(self):
        kb = KeybindManager()
        labels_before = kb.key_labels.copy()
        kb.toggle_invert()
        labels_after = kb.key_labels

        # Space stays the same, directions swap
        assert labels_before['space'] == labels_after['space']
        assert labels_before['left'] == labels_after['right']
        assert labels_before['right'] == labels_after['left']

    def test_invert_persists_across_reads(self):
        kb = KeybindManager()
        kb.toggle_invert()
        first_read = kb.button_keys
        second_read = kb.button_keys
        assert first_read is second_read
