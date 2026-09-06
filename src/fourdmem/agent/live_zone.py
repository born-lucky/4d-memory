"""Live-zone rule: recall is a tool result. The prefix is never rewritten."""

from __future__ import annotations

from typing import Any


class LiveZoneError(ValueError):
    pass


def assert_prefix_frozen(original: list[Any], proposed: list[Any]) -> None:
    """Fail if anything in the already-sent prefix changed.

    Allowed: append after the original list. Forbidden: edit, drop,
    reorder, or summarize earlier turns (Headroom ICM lesson).
    """
    n = len(original)
    if len(proposed) < n:
        raise LiveZoneError("live-zone: cannot drop prefix messages")
    if proposed[:n] != original:
        raise LiveZoneError("live-zone: cannot rewrite frozen prefix")


def append_tool_result(original: list[dict], result: dict) -> list[dict]:
    """Return a new list: frozen prefix + one tool result."""
    out = list(original) + [result]
    assert_prefix_frozen(original, out)
    return out
