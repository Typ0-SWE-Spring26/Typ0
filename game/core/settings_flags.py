"""Settings bit-flag helpers for multiplayer game configuration.

A single integer is passed from challenger to server and then to both clients
so both sides start with identical settings.

Bit layout:
    Bit 0 (0x01) — inverted_keys: swap WASD directions
"""

INVERTED_KEYS: int = 1 << 0  # 0x01


def encode(inverted_keys: bool = False) -> int:
    """Pack settings into a bitmask integer."""
    flags = 0
    if inverted_keys:
        flags |= INVERTED_KEYS
    return flags


def decode(flags: int) -> dict:
    """Unpack a bitmask into a readable settings dict."""
    return {
        "inverted_keys": bool(flags & INVERTED_KEYS),
    }
