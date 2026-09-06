# fourdmem

**A 4D memory harness for AI agents.**  
Navigate a mnemonic palace. Recall only what the goal needs. Stop paying context rot.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org)
[![Status: Draft](https://img.shields.io/badge/status-Draft-orange.svg)](docs/DESIGN.md)

> Your model does not need a bigger window.  
> It needs a place to put things, and a way to walk back to them.

**Free for everyone.** MIT licensed. Clone it, fork it, wire it into Grok / Claude / Codex / your own loop. Third-party notices: [THIRD_PARTY.md](THIRD_PARTY.md). Do not commit `vendor/` (Apache-2.0 clones and lm-eval task files stay local).

---

## The pitch

Long sessions rot. Every frontier model degrades as the prompt fills — Chroma's *Context Rot* study, Anthropic's own engineering notes, BABILong, NoLiMa. Stuffing more history in does not make the agent remember. It makes the agent worse, and more expensive.

Vector databases treat memory as cosine soup. That is an index, not a memory. Humans do not recall by nearest neighbor. They walk a **palace**.

**fourdmem** turns quantized context into a **four-dimensional integer lattice**. The first three axes are a method-of-loci palace the agent actually moves through. The fourth axis is **valence** — good ↔ bad — so “recall the good stuff related to this” is a walk, not a prompt hack. Navigation **is** recall.

The live prompt stays small. Everything else lives in a git-family content-addressable store and comes back only when the agent walks to it.

```
prompt (bounded)     4D palace (side channel)
────────────────     ────────────────────────
current goal    →    go library
latest tool     →    step n / ascend
recall slice    →    look / recall
                     judge good|bad
```

We do **not** rewrite conversation history. Dropping old messages to “compress” busts provider caches. fourdmem is a side channel: store, navigate, retrieve. The prefix is sacred.

---

## Why 4D, not another embedding store

| Usual memory | fourdmem |
| --- | --- |
| Dump history into the window | Offload to a lattice; inject ≤512 tokens |
| kNN as the product | kNN is internal; **loci** are the UX |
| One undifferentiated pile | 3D rooms + **valence** as the 4th axis |
| Lossy summaries | Lossless CAS (SHA-256, zlib now; pack/delta; zstd in extra `[pack]`) |
| Goal hoped-for in the prompt | Goal is a **query-time gate** (the cats test) |
| Pretty dashboards | No lighting. Instant teleports. A retrieval engine. |

**The cats test.** Goal: *prove Hilbert 4D encode/decode is bijective*. Stored: that proof note, and “I saw cats on screen.” `recall` must return the Hilbert note and must **not** contain `cats`. The cats blob stays on disk. We forget from the prompt, not from the universe.

---

## The mathematics, in one screen

Full write-up: **[docs/MATH.md](docs/MATH.md)**. Design: **[docs/DESIGN.md](docs/DESIGN.md)**.

A memory occupies a point on

\[
L_4 = \mathbb{Z}^4 \cap \bigl([0,16)\times[0,16)\times[0,8)\times[-8,+8]\bigr)
\]

| Axis | Name | Meaning |
| --- | --- | --- |
| \(x,y,z\) | palace | rooms, floors, landmarks |
| \(w\) | valence | bad → good, written by `judge` |

- **Hilbert curve (Skilling 2004)** folds \(L_4\) (including \(w=+8\)) into a 1D pack order. Equal-width **5-bit** Skilling on \(\iota(x,y,z,w)=(x,y,z,w+8)\) padded into \([0,32)^4\); 20-bit keys in `uint32`. `judge good` does not fall off the cube.
- **Product quantization (Jégou 2011)** compresses a simhash + n-gram sketch into 8 bytes for *placement hints*. Original bytes are never destroyed.
- **4D → 3D blanket:** the engine renders the affine 3-flat \(w = c\). Projection \((x',y',z') = \frac{d}{d-w}(x,y,z)\). Invertible. No lighting.
- **Git-family store:** `{type} {size}\0` + SHA-256, zlib loose objects, Hilbert-ordered packfiles, copy/insert delta. **zlib now; zstd in optional extra `[pack]`** (PR-11). Reconstruction is lossless.
- **Goal pertinence** is a gate, not an axis. Goals change every prompt; putting them on \(w\) would move the palace. Valence is a property of the object. They compose.

Scale path (real axes, not slogans): **4 = valence (v1)** → **5 = epoch** → **6 = principle-alignment** → **7 = echo/becoming**.

Invariants are checked with the same tools labs actually harness to models: **Lean 4** (`lean/FourDMem` at 4.33.1; vendor REPL at 4.34.0-rc2, never mixed) and **HuggingFace Math-Verify** (harness smoke; Hilbert bijection on \(L_4\) is the math bar). **mini-swe-agent** is an optional POSIX-first coding harness, not the only way to land PRs.

---

## Status

**Draft.** Architecture is written and review-revised. Implementation follows the [PR plan](docs/DESIGN.md#pr-plan): harness wrappers on the existing `fourdmem` package first, then CAS, Hilbert on \(L_4\), `Coord4` palace, valence, goal filter. `fourdmem eval v1` (PR-13) is the merge bar.

v1 success bar (must be testable):

- `note` / `store` / `judge` / `navigate` / `recall`
- Injected context ≤ 512 tokens (hard cap 1024), measured with tiktoken
- Frozen cats fixture does not appear in recall (no `exclude=["cats"]` cheat)
- Round-trip: text → 4D object → 3D locus → navigate → original bytes
- Hilbert encode/decode bijection on all 34,816 \(L_4\) cells (Python exhaustive; Lean `Lattice4`)

---

## Quick start

```bash
git clone https://github.com/born-lucky/4d-memory.git
cd 4d-memory
uv venv --python 3.12
uv pip install -e ".[dev]"
```

Optional lab harnesses (Lean REPL, Math-Verify source, lm-eval, mini-swe-agent):

```powershell
pwsh -File scripts/bootstrap-harnesses.ps1
```

Today the CLI is argparse (`fourdmem status`). Palace verbs land with the PR plan:

```text
fourdmem store "Hilbert encode/decode is a bijection on Lattice4." --mnemonic library
fourdmem go library
fourdmem recall --goal "prove Hilbert 4D encode/decode is bijective"
fourdmem judge here good --reason "Lean proof passed"
fourdmem harness lean --cmd "def f := 2"
fourdmem harness math-verify --gold "1/2" --answer "0.5"
```

MCP: tools stay **always registered**. Recall is a tool result. The conversation prefix is never rewritten.

---

## What you get as an agent

```
fourdmem tools
  note store judge go step follow look recall
  ascend descend slice mark
  principle_assert principle_list
  harness_math_verify harness_lean harness_mini_swe
```

The 3D view exists so the agent has a **place**. Movement is a dict lookup. Paths are stored as memory. Recurring walks increment `echo_count`. The store reorganizes itself; landmarks never move.

---

## License

[MIT](LICENSE). Free for everyone — personal, research, and commercial. Pip dependencies and local vendor clones keep their own licenses; see [THIRD_PARTY.md](THIRD_PARTY.md). Never commit `vendor/` (Math-Verify and lean-repl are Apache-2.0; lm-eval task files are not MIT-by-default).

---

## Contributing

PRs welcome. Read [docs/DESIGN.md](docs/DESIGN.md) before changing the lattice, the 4th axis, or the live-zone rule. Those are binding.

If you only read one math page, read [docs/MATH.md](docs/MATH.md).
