"""Two memory kinds. Judged against the goal at store time, not the live prompt."""

from __future__ import annotations

from enum import Enum

W_GOOD = 8
W_BAD = -8
TAU = 0.35


class Kind(str, Enum):
    GOOD = "good"
    BAD = "bad"

    @property
    def w(self) -> int:
        return W_GOOD if self is Kind.GOOD else W_BAD


def tokenize(text: str) -> set[str]:
    out: set[str] = set()
    buf: list[str] = []
    for ch in text.lower():
        if ch.isalnum():
            buf.append(ch)
        else:
            if buf:
                out.add("".join(buf))
                buf.clear()
    if buf:
        out.add("".join(buf))
    return out


def jaccard(a: str, b: str) -> float:
    ta, tb = tokenize(a), tokenize(b)
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def classify(goal_at_store: str, text: str, *, tau: float = TAU) -> Kind:
    """Useless to the creating prompt → bad. Part of that plan → good."""
    return Kind.GOOD if jaccard(goal_at_store, text) >= tau else Kind.BAD
