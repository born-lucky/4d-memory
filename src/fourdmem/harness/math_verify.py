"""HuggingFace Math-Verify: the checker labs use in math RL/eval."""

from __future__ import annotations


def verify_pair(gold: str, answer: str) -> bool:
    """Return True iff `answer` is mathematically the same as `gold`.

    Timeouts are 0 so Windows does not spawn a multiprocessing grader
    (that path raises WinError 6 in short-lived processes).
    """
    from math_verify import ExprExtractionConfig, LatexExtractionConfig, parse, verify

    cfg = [LatexExtractionConfig(), ExprExtractionConfig()]
    g = parse(gold, cfg, parsing_timeout=0)
    a = parse(answer, cfg, parsing_timeout=0)
    if not g or not a:
        return False
    return bool(verify(g, a, timeout_seconds=0))
