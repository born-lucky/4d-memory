# Contributing

fourdmem is **public, MIT, free for everyone**. You can use it, fork it, open issues, and send pull requests.

Repo: https://github.com/born-lucky/4d-memory

## Use it

```bash
git clone https://github.com/born-lucky/4d-memory.git
cd 4d-memory
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix:    source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

```text
fourdmem goal "your plan"
fourdmem store "something that belongs on that plan"
fourdmem store "noise that does not"
fourdmem recall
```

Kind is judged against **the goal at store time**. Default recall is the plan (`good`). Bad is kept in CAS, not tied to the plan.

## Help build it

1. Fork the repo on GitHub.
2. Clone your fork, install as above, run `pytest -q`.
3. Pick an open issue labeled `help wanted` or `good first issue`, or a PR from [docs/DESIGN.md](docs/DESIGN.md#pr-plan).
4. Branch, implement, keep tests green.
5. Open a PR against `born-lucky/4d-memory` `main`.

Issues: https://github.com/born-lucky/4d-memory/issues  
PRs: https://github.com/born-lucky/4d-memory/pulls

## Binding rules (do not drive-by)

Read [docs/DESIGN.md](docs/DESIGN.md) and [docs/MATH.md](docs/MATH.md).

- **K0** — this harness is used in work, or it has failed.
- **K1 / K15** — two kinds, judged at store time vs `goal_at_store`. Good is tied to the plan. Bad is kept, **not tied**, not deleted. Live prompt does not retie junk.
- **K6** — do not rewrite the conversation prefix. Recall is a tool result.
- **K13** — Hilbert must encode \(w=+8\) (`judge good`). Do not shrink valence to 16 values.
- **K14** — occupancy is `Coord4`.
- New spatial axes need a coordinate + Hilbert extension + slice rule, or they do not ship.
- Do not commit `vendor/` or `.venv/`. See [THIRD_PARTY.md](THIRD_PARTY.md).

## Tests that must stay green

- `tests/test_work_loop.py` — cats are `bad`, Hilbert is `good`, recall unclouded, CAS still has cats, live prompt does not retie.
- `tests/test_harness.py` — Math-Verify wrapper is callable.

When you add Hilbert / CAS / palace code, add the tests named in the design success bar.

## What to work on first

The merge bar is PRs 1–8 then 13 in the design doc. Already landed: package, CLI (`goal store judge recall cas`), two-kind store, work-loop tests.

Still open for contributors:

- Lean REPL wrapper (portable elan discovery)
- Hilbert on \(L_4\) (5-bit Skilling, 34,816 cells)
- Palace graph / `go` / `look`
- Windows Git-bash notes for mini-swe-agent
- Docs and extra work-loop tests
