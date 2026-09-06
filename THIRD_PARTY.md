# Third-party notices

fourdmem itself is MIT licensed ([LICENSE](LICENSE)).

This file exists so a public MIT tree does not pretend every byte you might copy locally is MIT. **Do not commit `vendor/`.** Bootstrap clones stay on the machine that ran `scripts/bootstrap-harnesses.ps1`. CI installs runtime checkers from pip and elan, not from a force-added vendor tree.

## Runtime Python dependencies (pip)

| Package | License | Role |
| --- | --- | --- |
| [math-verify](https://github.com/huggingface/Math-Verify) ≥0.9.0 | Apache-2.0 | Parse/verify math answers. MIT-compatible as a **dependency** (not a relicense of fourdmem). |
| sympy | BSD-3-Clause | Exact arithmetic for the projector tests. |
| numpy | BSD-3-Clause | PQ, Hilbert helpers. |
| tiktoken | MIT | Token budget. |
| zstandard (optional extra `[pack]`) | BSD-3-Clause / dual | Pack payloads in PR-11. Not required for PRs 1–10. |

Apache-2.0 obligations for `math-verify` apply if you redistribute **that package**. Shipping fourdmem with `pip install math-verify` is the intended path.

## Local vendor clones (gitignored, bootstrap only)

| Clone | Upstream | License | Notes |
| --- | --- | --- | --- |
| `vendor/math/Math-Verify` | huggingface/Math-Verify | Apache-2.0 | Keep `LICENCE` / NOTICE if you ever copy this tree. Prefer the pip package. |
| `vendor/math/lean-repl` | leanprover-community/repl | Apache-2.0 | `lean-toolchain` pins `leanprover/lean4:v4.34.0-rc2`. Do not relicense. |
| `vendor/math/lm-evaluation-harness` | EleutherAI/lm-evaluation-harness | MIT **at repo root** | Contains ~15k task/dataset files whose licenses are **not** MIT-by-default. Do not publish this tree as “MIT fourdmem.” |
| `vendor/coding/mini-swe-agent` | SWE-agent/mini-swe-agent | MIT | Optional coding harness (`[harness]` extra). |

`git add -f vendor/` is a license incident: it would put Apache-2.0 sources and lm-eval datasets into this MIT repository without their notices.

## Toolchains

Lean 4 / Lake / elan are copyright Lean FRO / contributors (Apache-2.0). Project proofs live in `lean/FourDMem` (this repo, MIT) and compile with `leanprover/lean4:v4.33.1`. The vendor REPL is a separate Lake package at 4.34.0-rc2. Never mix `.olean` files across those versions.
