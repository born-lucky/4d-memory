"""Math-Verify the way labs harness it: parse + verify, Windows-safe timeout."""

from __future__ import annotations


def verify_pair(gold: str, answer: str) -> bool:
    from math_verify import parse, verify

    # Wrap as a sentence so the extractor sees an answer. parsing_timeout=0
    # stays in-process (Windows python -c + timeout>0 raises WinError 6).
    g = parse(f"The answer is {gold}", parsing_timeout=0)
    a = parse(f"The answer is {answer}", parsing_timeout=0)
    if not g or not a:
        return False
    return bool(verify(g, a))
