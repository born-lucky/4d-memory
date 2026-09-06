# Testing plan

fourdmem fails if it is a library nobody calls, or if bad memories cloud the plan, or if the math harness “runs” without grading. This plan is the bar. Every row has a command, a file, and a pass that cannot be cheated with `exclude=["cats"]` or `assert isinstance(x, bool)`.

Binding product rules (see [DESIGN.md](DESIGN.md)):

- **K0** — the agent uses this in work.
- **K1 / K15** — two kinds, judged against **`goal_at_store`**, not the live prompt. Good is tied to the plan. Bad is kept, not tied, not deleted.
- **K6** — conversation prefix is never rewritten.
- **K13** — Hilbert must encode \(w=+8\).

---

## How to run

```bash
cd 4d-memory
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q
```

Optional Lean (skip if missing; Math-Verify must not skip):

```powershell
pwsh -File scripts/bootstrap-harnesses.ps1
# elan + lake already on PATH
cd vendor/math/lean-repl
lake exe repl   # once, to build
cd ../../..
pytest -q
```

CLI smoke (must match pytest):

```text
fourdmem harness math-verify --gold 1/2 --answer 0.5     # prints true, exit 0
fourdmem harness math-verify --gold 1/2 --answer 1/3     # prints false, exit 1
fourdmem harness lean --lean-cmd "def f := 2"            # {"env": 0}
```

One command that means “v1 works” (lands in PR-13):

```text
fourdmem eval v1
```

Until that exists, `pytest -q` is the gate.

---

## Layers

```
L0  install / CLI parses
L1  math + Lean harness (must actually grade)
L2  two-kind store + CAS (work loop)
L3  lattice / Hilbert / projection (math of the palace)
L4  palace navigation + token budget
L5  live-zone (prefix untouched)
L6  eval suite + CI  →  merge bar
L7  post-bar (principles, VSA, packs, MCP, window)
```

L0–L2 are **now**. L3–L6 are the v1 merge bar with the rest of the PR plan. L7 is after.

---

## L0 — Install

| ID | Test | File / command | Pass |
| --- | --- | --- | --- |
| T0.1 | Package imports | `python -c "import fourdmem; print(fourdmem.__version__)"` | prints `0.1.0` |
| T0.2 | CLI status | `fourdmem status` | JSON with `goal`, `good`, `bad`, `tau` |
| T0.3 | `vendor/` not in git | `git ls-files vendor` | empty |

---

## L1 — Mathematics harness (must grade)

These tests **fail the build** if Math-Verify is a no-op. Lean is skip-if-missing on machines without elan; it is **required** on the maintainer box and on CI once the workflow file is pushed.

| ID | Test | File | Pass |
| --- | --- | --- | --- |
| T1.1 | Same value | `tests/test_harness.py::test_math_verify_same_is_true` | `"1000"` ≡ `"1000.0"` → `True` |
| T1.2 | Fraction | `::test_math_verify_fraction_is_true` | `"1/2"` ≡ `"0.5"` → `True` |
| T1.3 | Negative | `::test_math_verify_wrong_is_false` | `"1/2"` vs `"1/3"` → `False` |
| T1.4 | CLI exit codes | `::test_cli_math_verify_true_false` | gold=answer exit 0; mismatch exit 1 |
| T1.5 | Lean REPL | `::test_lean_repl_def_returns_env` | `def f := 2` → `{"env": 0}`, no error messages |

**Forbidden:** `assert isinstance(result, bool)` as the only check. That used to be the test. It is not a test.

**Windows:** wrappers call Math-Verify with `parsing_timeout=0` and `timeout_seconds=0` so the grader stays in-process (multiprocessing timeouts raise `WinError 6`).

When Hilbert lands (L3), Lean is used for the **real** invariant, not only `def f := 2`:

```lean
-- lean/FourDMem/Hilbert.lean
theorem encode_decode_id (p : Lattice4) : decode (encode p) = p
```

Python exhausts all **34,816** cells including \(w=\pm 8\). Lean and Python must agree on the same set (`Lattice4`, not `Fin 16^4`).

---

## L2 — Work loop (two kinds)

The product: the agent stores while working; good stays on the plan; bad is not tied; nothing clouds recall.

Frozen fixture (creating goal = `prove Hilbert 4D encode/decode is bijective`):

| Item | Kind | Tied to plan.good? | In default `recall`? | In CAS? |
| --- | --- | --- | --- | --- |
| Hilbert bijection note | `good`, \(w=+8\) | yes | yes | yes |
| `I saw cats on screen.` | `bad`, \(w=-8\) | **no** | **no** | **yes** |

| ID | Test | File | Pass |
| --- | --- | --- | --- |
| T2.1 | Auto-kind | `tests/test_work_loop.py::test_good_stays_bad_untied_not_deleted` | Hilbert `good`; cats `bad`; recall has Hilbert, not `cats`; `cas.get(cats)` equals original bytes; cats oid ∉ `plan.good` |
| T2.2 | Kind is store-time | `::test_kind_is_creation_goal_not_live_prompt` | After `set_goal("write a poem about cats")`, cats still not on the new plan’s good list |
| T2.3 | Judge reties | `::test_judge_reties` | `judge good` moves oid onto `plan.good` and into default recall |
| T2.4 | CAS round-trip | `::test_cas_roundtrip` | `cas.get(oid) == original bytes` |
| T2.5 | Two plans (todo) | `tests/test_work_loop.py` | Bad from plan A never appears in plan B recall |

**Forbidden:** passing T2.1 by setting `exclude=["cats"]` on the goal.

**Status:** T2.1–T2.4 green. T2.5 is the next work-loop test.

---

## L3 — Lattice, Hilbert, projection (when PR-3 / PR-6 land)

| ID | Test | File | Pass |
| --- | --- | --- | --- |
| T3.1 | Domain | `tests/test_hilbert.py` | `in_bounds` allows \(w=+8\) and \(w=-8\) |
| T3.2 | Bijection | same | `decode(encode(p))=p` for all 34,816 points |
| T3.3 | Good pole | same | `Kind.GOOD.w == 8` encodes; pack key defined |
| T3.4 | Lean | `lean/FourDMem/Hilbert.lean` | `lake build` in `lean/` (toolchain 4.33.1); theorem on `Lattice4` |
| T3.5 | Projection | `tests/test_project.py` | Python vs sympy `Rational` inverse on a grid. Math-Verify is **not** the 4D invariant (tautologies do not count) |
| T3.6 | Coord4 | `tests/test_nav.py` | Same \((x,y,z)\), different \(w\) → different Hilbert keys and different blanket membership |

---

## L4 — Palace, budget, engine (PR-5–8)

| ID | Test | File | Pass |
| --- | --- | --- | --- |
| T4.1 | `go` / `look` | `tests/test_nav.py` | Landmark teleport keeps agent \(w\); does not snap to occupant \(w\) |
| T4.2 | Token cap | `tests/test_budget.py` | 200 notes; `recall` ≤ 512 tiktoken `cl100k_base` tokens; never silent overrun |
| T4.3 | Recall bytes | `tests/test_cats.py` | Lines are `title oid` + first line of blob, not the full blob |
| T4.4 | Engine | `tests/test_project.py` | Headless snapshot JSON; `cell` is four ints; no window required |

---

## L5 — Live zone (PR-12)

| ID | Test | File | Pass |
| --- | --- | --- | --- |
| T5.1 | Frozen prefix | `tests/test_live_zone.py` | Helper refuses to mutate a copied messages list |
| T5.2 | Tools constant | same | Tool list does not gain/lose names across a store/recall |

---

## L6 — Merge bar (`fourdmem eval v1`, PR-13)

One command runs T1–T5 that exist. CI (once `.github/workflows/ci.yml` is on GitHub):

- `pytest -q` on Python 3.12
- `git ls-files vendor` empty
- Optional job: elan install 4.33.1 + 4.34.0-rc2, then T1.5 and T3.4

**v1 is mergeable only if** T1.1–T1.4, T2.1–T2.4, T0.3 are green, **and** T3.1–T3.3, T4.2, T2.1 still hold after Hilbert/palace land.

---

## L7 — Post-bar

| Area | PR | Gate |
| --- | --- | --- |
| Principles / echo | 9 | Landmarks immovable; unnamed move ≤ 1 cell; no hidden LLM in `reorganize` |
| VSA | 10 | Cats fixture still green after restoring the 0.15 term |
| Pack / zstd | 11 | `cas.get` after `gc` equals original bytes |
| MCP | 12 | T5.1–T5.2 |
| Window | 14 | Optional; no lighting |

---

## Map to PRs

| PR | Tests that must land with it |
| --- | --- |
| Now (store + harness) | T0, T1.1–T1.5, T2.1–T2.4 |
| PR-1 leftover (Lean portable) | T1.5 on a clean machine |
| PR-2 CAS hardening | T2.4 + `tests/test_cas.py` |
| PR-3 Hilbert | T3.1–T3.4 |
| PR-4 PQ | property: codes are 8 bytes; placement does not change CAS bytes |
| PR-5 palace | T4.1, T3.6 |
| PR-6 engine | T3.5, T4.4 |
| PR-7 judge | already T2.3; plus \(w=+8\) encodes |
| PR-8 recall/budget | T4.2, T4.3, T2.5 |
| PR-13 eval | `fourdmem eval v1` wraps the table |

---

## Cheats that fail the plan

- Passing cats by `exclude=["cats"]`
- Passing math by `assert isinstance(verify_pair(...), bool)`
- Passing Hilbert by testing `Fin 16^4` and dropping \(w=+8\)
- Passing recall by deleting bad from CAS
- Passing live-zone by summarizing old turns
- Committing `vendor/`

---

## Current score (2026-09-06, maintainer box)

```
pytest -q   →  9 passed
  T1.1–T1.5  green (Math-Verify true/false + Lean env=0)
  T2.1–T2.4  green (kinds, store-time, judge, CAS)
  T2.5, T3–T6  not implemented yet
```

Next test to write: **T2.5** (two plans) then **T3.1–T3.3** with Hilbert.
