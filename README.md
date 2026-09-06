# fourdmem

**A 4D memory harness for AI agents.**  
Navigate a mnemonic palace. Recall only what the goal needs. Stop paying context rot.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org)
[![Status: design complete](https://img.shields.io/badge/status-design%20complete-orange.svg)](docs/DESIGN.md)

> Your model does not need a bigger window.  
> It needs a place to put things, and a way to walk back to them.

**Free for everyone.** MIT licensed. Clone it, fork it, wire it into Grok / Claude / Codex / your own loop.

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
| Lossy summaries | Lossless CAS (SHA-256, zlib, pack/delta/zstd) |
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

- **Hilbert curve (Skilling 2004)** folds \(\mathbb{Z}^4\) into a 1D pack order so similar cells sit near each other on disk.
- **Product quantization (Jégou 2011)** compresses a simhash + n-gram sketch into 8 bytes for *placement hints*. Original bytes are never destroyed.
- **4D → 3D blanket:** the engine renders the affine 3-flat \(w = c\). Projection \((x',y',z') = \frac{d}{d-w}(x,y,z)\). Invertible. No lighting.
- **Git-family store:** `{type} {size}\0` + SHA-256, zlib loose objects, Hilbert-ordered packfiles, copy/insert delta, zstd. Same family GitHub uses. Reconstruction is lossless.
- **Goal pertinence** is a gate, not an axis. Goals change every prompt; putting them on \(w\) would move the palace. Valence is a property of the object. They compose.

Scale path (real axes, not slogans): **4 = valence (v1)** → **5 = epoch** → **6 = principle-alignment** → **7 = echo/becoming**.

Invariants are checked with the same tools labs actually harness to models: **Lean 4 REPL** (AlphaProof / formal-math agents) and **HuggingFace Math-Verify**. Coding work on this repo runs through **mini-swe-agent** (Meta / NVIDIA / IBM baseline).

---

## Status

The architecture is written and reviewable. Implementation follows the [PR plan](docs/DESIGN.md#pr-plan): harness wiring first, then CAS, Hilbert (Lean-checked), palace, valence, goal filter, packs, MCP.

v1 success bar (must be testable):

- `note` / `store` / `judge` / `navigate` / `recall`
- Injected context ≤ 512 tokens (hard cap 1024), measured with tiktoken
- Cats distractor does not appear in recall
- Round-trip: text → 4D object → 3D locus → navigate → original bytes
- Lean or Math-Verify checks at least one 4D-index invariant

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

Intended CLI (lands with the PR plan):

```text
fourdmem store "Hilbert encode/decode is bijective on Fin 16^4" --mnemonic library
fourdmem note "I saw cats on screen"
fourdmem judge here good --reason "Lean proof passed"
fourdmem go library
fourdmem recall --goal "prove Hilbert bijection"
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

[MIT](LICENSE). Free for everyone — personal, research, and commercial. Vendor clones keep their own licenses (Math-Verify, lm-evaluation-harness, Lean REPL, mini-swe-agent).

---

## Contributing

PRs welcome. Read [docs/DESIGN.md](docs/DESIGN.md) before changing the lattice, the 4th axis, or the live-zone rule. Those are binding.

If you only read one math page, read [docs/MATH.md](docs/MATH.md).
