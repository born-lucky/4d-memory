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

**fourdmem** is a harness the agent **uses in its work**, the same way it uses Lean or Math-Verify: connect, call, get a clean slice, keep going. Two kinds of memory, judged when the note is written against **that** plan:

- **Good** — part of the plan. Tied. Stays. Default recall.
- **Bad** — useless to the creating prompt (cats during a proof). Not deleted. **Not tied** to the good. Cannot cloud the plan.

The fourth axis \(w\) *is* that kind. The first three axes are a palace the agent walks. Navigation of the **good** graph **is** recall.

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
| One pile, or “useful to what I am typing now” | **Two kinds**, judged at **store time** vs that plan |
| Pretty dashboards | No lighting. Instant teleports. A retrieval engine. |

**The cats test (work loop).** Goal at store: *prove Hilbert 4D encode/decode is bijective*. Hilbert note → `good`, tied to the plan. “I saw cats on screen” → `bad`, kept in CAS, **not** on `plan.good`. `recall` is unclouded. Changing the live prompt to a poem about cats does **not** retie the junk. We do not forget the universe. We do not let it into the plan.

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

Working core is in: `goal`, `store`, `judge`, `recall`, `cas`. The agent uses it in work. Kind is judged at store time. Default recall is the plan (good only). Palace/Hilbert PRs still follow the [PR plan](docs/DESIGN.md#pr-plan).

v1 success bar:

- Agent **calls** fourdmem during a task (same attachment as Math-Verify)
- Two kinds: good tied to the creating plan, bad kept but untied
- Cats stored under a Hilbert goal do not appear in default `recall`; CAS still has them
- Changing the live prompt does not retie bad onto a new plan

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

```text
fourdmem goal "prove Hilbert 4D encode/decode is bijective"
fourdmem store "Hilbert encode/decode is a bijection on Lattice4."
fourdmem store "I saw cats on screen."
fourdmem recall                  # good of that plan — no cats
fourdmem recall --kind bad       # junk, explicit
fourdmem cas <oid>               # lossless, even for bad
fourdmem harness math-verify --gold "$\frac{1}{2}$" --answer "$\frac{1}{2}$"
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
