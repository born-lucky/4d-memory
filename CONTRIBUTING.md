# Contributing

fourdmem is MIT-licensed and free for everyone. PRs and issues are welcome.

1. Read [docs/DESIGN.md](docs/DESIGN.md) and [docs/MATH.md](docs/MATH.md).
2. Do not change Key Decisions K1–K14 (4th axis = valence, live-zone passthrough, no prefix rewriting, Hilbert-honest 17-valued `w`, `Coord4` occupancy) without a design revision.
3. New spatial axes must be a coordinate + Hilbert extension + slice rule, or they do not ship.
4. Wire tests first: Hilbert bijection on \(L_4\) (34,816 cells, including \(w=\pm 8\)), CAS round-trip, frozen cats fixture, token budget.
5. Do not commit `vendor/` or `.venv/`. See [THIRD_PARTY.md](THIRD_PARTY.md).

Implementation order is the PR plan at the bottom of the design doc. PR-1 adds harness wrappers on the **existing** package; it does not recreate `pyproject.toml`.
