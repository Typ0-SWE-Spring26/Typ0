"""Unit tests for the multiplayer settings bit-flag helpers."""
import pytest
from game.core import settings_flags


class TestEncode:
    def test_default_is_zero(self):
        assert settings_flags.encode() == 0

    def test_inverted_keys_sets_bit_0(self):
        assert settings_flags.encode(inverted_keys=True) == 0b00000001

    def test_normal_keys_clears_bit_0(self):
        assert settings_flags.encode(inverted_keys=False) == 0b00000000

    def test_returns_int(self):
        assert isinstance(settings_flags.encode(), int)


class TestDecode:
    def test_zero_flags_all_false(self):
        result = settings_flags.decode(0)
        assert result["inverted_keys"] is False

    def test_bit_0_sets_inverted_keys(self):
        result = settings_flags.decode(0b00000001)
        assert result["inverted_keys"] is True

    def test_unrelated_high_bits_ignored(self):
        # Bit 0 not set — inverted_keys stays False regardless of other bits
        result = settings_flags.decode(0b11111110)
        assert result["inverted_keys"] is False

    def test_returns_dict(self):
        assert isinstance(settings_flags.decode(0), dict)


class TestRoundTrip:
    def test_roundtrip_defaults(self):
        flags = settings_flags.encode()
        assert settings_flags.decode(flags)["inverted_keys"] is False

    def test_roundtrip_inverted(self):
        flags = settings_flags.encode(inverted_keys=True)
        assert settings_flags.decode(flags)["inverted_keys"] is True
