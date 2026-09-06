"""Lean 4 community REPL — JSON stdin/stdout, same tool AlphaProof-style agents use."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REPL = REPO_ROOT / "vendor" / "math" / "lean-repl"


def _elan_bins() -> list[Path]:
    home = Path.home()
    return [
        home / "scoop" / "apps" / "elan" / "current" / ".elan" / "bin",
        home / "scoop" / "persist" / "elan" / ".elan" / "bin",
        home / ".elan" / "bin",
    ]


def _env_with_elan() -> dict[str, str]:
    env = os.environ.copy()
    extra = [str(p) for p in _elan_bins() if p.is_dir()]
    if extra:
        env["PATH"] = os.pathsep.join(extra + [env.get("PATH", "")])
    return env


def find_lake() -> str | None:
    env = _env_with_elan()
    return shutil.which("lake", path=env.get("PATH"))


def find_repl_exe(root: Path | None = None) -> Path | None:
    """True if we can invoke the REPL (lake + vendor tree, or a built binary)."""
    base = Path(root) if root else DEFAULT_REPL
    if find_lake() and (base / "lakefile.toml").is_file():
        return base / "lakefile.toml"
    for p in (
        base / ".lake" / "build" / "bin" / "repl.exe",
        base / ".lake" / "build" / "bin" / "repl",
    ):
        if p.is_file():
            return p
    return None


def run_cmd(cmd: str, *, timeout: float = 60.0) -> dict:
    """Send one command-mode JSON object. Prefer `lake exe repl` (loads Lean DLLs)."""
    if not DEFAULT_REPL.is_dir():
        raise FileNotFoundError(
            "vendor/math/lean-repl missing. Run scripts/bootstrap-harnesses.ps1"
        )
    lake = find_lake()
    if lake is None:
        raise FileNotFoundError("lake not found. Install elan / Lean 4.")
    payload = json.dumps({"cmd": cmd}) + "\n\n"
    proc = subprocess.run(
        [lake, "exe", "repl"],
        input=payload,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(DEFAULT_REPL),
        env=_env_with_elan(),
    )
    out = (proc.stdout or "").strip()
    if not out:
        raise RuntimeError(
            f"Lean REPL empty stdout rc={proc.returncode} stderr={proc.stderr!r}"
        )
    first = out.split("\n\n")[0].strip()
    return json.loads(first)
