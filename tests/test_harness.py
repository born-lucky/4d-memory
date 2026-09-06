"""These tests must fail if the math harness is not actually grading."""

from __future__ import annotations

import pytest

from fourdmem.harness.lean_repl import find_repl_exe, run_cmd as lean_cmd
from fourdmem.harness.math_verify import verify_pair


def test_math_verify_same_is_true() -> None:
    assert verify_pair("1000", "1000.0") is True


def test_math_verify_fraction_is_true() -> None:
    assert verify_pair("1/2", "0.5") is True


def test_math_verify_wrong_is_false() -> None:
    assert verify_pair("1/2", "1/3") is False


def test_cli_math_verify_true_false() -> None:
    from fourdmem.cli import main

    assert main(["harness", "math-verify", "--gold", "1/2", "--answer", "0.5"]) == 0
    assert main(["harness", "math-verify", "--gold", "1/2", "--answer", "1/3"]) == 1


def test_lean_repl_def_returns_env() -> None:
    if find_repl_exe() is None:
        pytest.skip("Lean REPL binary not built (vendor/math/lean-repl lake build)")
    out = lean_cmd("def f := 2")
    assert "env" in out, out
    assert out.get("messages", []) == [] or all(
        m.get("severity") != "error" for m in out.get("messages", [])
    )
