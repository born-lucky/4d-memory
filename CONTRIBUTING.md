# Contributing

fourdmem is MIT-licensed and free for everyone. PRs and issues are welcome.

1. Read [docs/DESIGN.md](docs/DESIGN.md) and [docs/MATH.md](docs/MATH.md).
2. Do not change Key Decisions K1–K12 (4th axis = valence, live-zone passthrough, no prefix rewriting) without a design revision.
3. New spatial axes must be a coordinate + Hilbert extension + slice rule, or they do not ship.
4. Wire tests first: Hilbert bijection, CAS round-trip, cats distractor, token budget.
5. Do not commit `vendor/` or `.venv/`.

Implementation order is the PR plan at the bottom of the design doc. PR-1 (harness wiring) is first on purpose.
