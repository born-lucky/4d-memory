# The mathematics of fourdmem

This is the public explanation of the math the harness actually uses. It is not a metaphor sheet. Every object here has a type, a range, and a test.

If you want the engineering contract, read [DESIGN.md](DESIGN.md). If you want the pitch, read the [README](../README.md).

---

## 1. The problem, stated as a budget

Let \(C\) be the model's context window and \(R\) the tokens reserved for the reply. The live prompt must satisfy

\[
|P_{\text{live}}| \le B, \qquad B = \min(512,\, C - R)\ \text{by default, hard cap } 1024.
\]

Context rot is the empirical fact that quality falls as \(|P_{\text{live}}|\) grows, even when \(C\) is huge (Chroma 2025; NoLiMa; BABILong). fourdmem's job is to keep \(P_{\text{live}}\) a **high-signal slice** and park the rest in a store the agent can walk.

We refuse the usual “solution”: delete old messages from the prefix. That destroys provider prompt caches. The store is a **side channel**. Navigation is recall.

---

## 2. The 4-dimensional lattice

A memory occupies a point of

\[
L_4 = \mathbb{Z}^4 \cap \bigl([0,X)\times[0,Y)\times[0,Z)\times[-W,W]\bigr)
\]

v1 defaults: \(X=16\), \(Y=16\), \(Z=8\), \(W=8\). That is \(16\times 16\times 8\times 17 = 34{,}816\) cells. Many objects may share a cell (cap 16). The palace is a *view* over objects, not 1:1 with them.

This box is not a power-of-two hypercube on purpose: eight floors is a palace; 256 rooms per floor is walkable; **17 valence levels exist so both poles \(\pm 1.0\) and zero are representable**. Shrinking \(w\) to 16 values would drop \(w=+8\) (`judge good`). Forbidden.

**Valence map:** `good ≡ +1.0`, `bad ≡ -1.0`,

\[
w = \mathrm{clamp}(\mathrm{round}(v\cdot W),-W,W).
\]

So \(+1.0 \mapsto +8\), which the Hilbert coder in §4 must accept.

| Axis | Name | Meaning | Who writes it |
| --- | --- | --- | --- |
| \(x\) | east | floor plan | mnemonic, or Hilbert-folded PQ neighborhood |
| \(y\) | north | floor plan | same |
| \(z\) | up | stories | same |
| \(w\) | **valence** | bad \(\rightarrow\) good | `judge` (default \(0\)) |

**Why valence is the 4th axis, and goal is not.** A spatial axis has to be a stable property of an object. Goals change every prompt. If we put “pertinence to the current goal” on \(w\), the whole palace would re-embed every turn and landmarks would lie. Valence is a judgment attached to the object: nearby on \(w\) means similarly judged. “Recall the good stuff related to this” is a walk toward \(+w\) in the same \((x,y,z)\) neighborhood.

Goal pertinence is a **query-time gate** (section 6). The two compose. They are not the same coordinate.

Distance on the lattice is Chebyshev (not Manhattan: a diagonal neighbor is one look in a palace):

\[
d_\infty(p,q) = \max_i |p_i - q_i|.
\]

v1 recall neighborhood: radius \(1\) on \((x,y,z)\), radius \(1\) on \(w\) unless `prefer_good` / `prefer_bad` opens toward a pole.

Occupancy is always a `Coord4`. A landmark names an \((x,y,z)\) column; `go library` keeps the agent's \(w\). Two objects at the same \((x,y,z)\) and different \(w\) have different Hilbert keys and different blanket membership.

---

## 3. The blanket: a 3-flat in 4-space

The engine never renders \(\mathbb{R}^4\). It renders a **blanket** — an affine 3-flat

\[
B_{n,c} = \{ p \in \mathbb{R}^4 : n \cdot p = c \}, \qquad \|n\| = 1.
\]

v1: \(n = (0,0,0,1)\), \(c = w_{\text{agent}}\). The agent walks the 3D palace at a fixed valence slice. Objects with \(|w - c| > 0\) are off-slice: visible as “above/below,” not injected as text until the agent `ascend`/`descend`s or `recall` lets them through the goal filter.

Later, \(n\) may tilt in one of the six 4D coordinate planes by a **Givens rotation** \(R_{ij}(\theta)\). Quaternions are *not* used: they rotate \(\mathbb{R}^3\), not \(\mathbb{R}^4\).

### 3.1 Projection 4D → 3D

Camera distance \(d > W\) (v1 \(d = 16\)), looking along \(w\):

\[
(x',y',z') = \frac{d}{d-w}\,(x,y,z).
\]

On an axis-aligned slice \(w = c\) this is a uniform scale, so palace geometry is undistorted and the inverse is immediate:

\[
(x,y,z) = \frac{d-c}{d}\,(x',y',z').
\]

**Engineering test:** Python projector vs sympy `Rational`s on a grid of \(L_4\), plus invertibility on a slice. The identity \(\frac{d}{d-w}\cdot\frac{d-w}{d}=1\) is an algebraic tautology; Math-Verify may `parse`/`verify` it as **harness smoke only**. It is not a 4D-index invariant. The Hilbert bijection on \(L_4\) is.

---

## 4. Hilbert and Morton keys

Occupied cells need a locality-preserving 1D key: packfile order, B-tree key, “nearby in 4D ⇒ nearby on disk.”

**Default: n-dimensional Hilbert curve** (Skilling, *Programming the Hilbert curve*, AIP 707, 2004) on the **actual** \(L_4\), not a 4-bit cube.

A 4-bit unsigned axis is \(\{0,\ldots,15\}\). Mapping \(w' = w+W\) with \(W=8\) gives \(w'=16\) at the good pole, which **does not fit in 4 bits**. Dropping \(w=+8\) is forbidden.

Injection:

\[
\iota(x,y,z,w) = (x,\,y,\,z,\,w+8), \qquad w+8\in[0,16].
\]

**The on-disk coder (the only one):** equal-width **5-bit** Skilling 2004, \(n=4\), on the padded hypercube \(H=[0,32)^4\). Encode \(\iota(p)\); key is 20 bits in a `uint32`. Decode rejects points not in \(\iota(L_4)\) (\(z\ge 8\) or \(w'\ge 17\), etc.). Mixed-width \((4,4,3,5)\) is a different map (compact Hilbert, not Skilling) and is **not** v1.

```text
hilbert_encode_4d(x, y, z, w) -> int      # requires p in L_4; Skilling-5(ι(p))
hilbert_decode_4d(h) -> Coord4 | error    # error if not in L_4
```

**Morton (Z-order)** is the debug coder: bit-interleave of the same 5-bit padded \(\iota(p)\).

**Lean invariant** — same 34,816-cell set Python encodes, **not** `Fin 16^4`:

```lean
structure Lattice4 where
  x : Fin 16
  y : Fin 16
  z : Fin 8
  wShifted : Fin 17   -- valence w = wShifted.val - 8

theorem hilbert_encode_decode_id (p : Lattice4) :
    decode (encode p) = some p
```

Python exhaustive bijection on all 34,816 points (including \(w=\pm 8\)) is the engineering gate. Lean `#eval` over `Lattice4` if it fits the CI budget; otherwise a reduced-bit toy plus lockstep samples. Morton invertibility is `native_decide` on the bit operations.

This is 4D mathematics the agent can *run*, not a slide about tesseracts.

---

## 5. Quantizing context (without destroying it)

“Quantize” here is a pipeline. The blob always survives.

1. **Atomic notes.** Split on blank lines / tool-result boundaries. Do not split inside fenced code.
2. **Canonical bytes.** UTF-8, LF, no trailing spaces, final newline. This is the lossless payload.
3. **Git-style content addressing.**
   ```
   payload = f"{type} {len(data)}\0".encode() + data
   oid     = sha256(payload)
   ```
   Loose path: `.fourdmem/objects/{oid_hex[:2]}/{oid_hex[2:]}` zlib level 6, where `oid` is the **raw 32-byte** SHA-256 and `oid_hex` is its hex encoding. Same header convention as Git; hash is SHA-256, not SHA-1.
4. **Simhash (256-bit).** Charikar fingerprints: tokenize, SHA-256 each token, signed sum of feature bits. Hamming distance is the lexical metric.
5. **N-gram sketch (64 bytes).** 3-grams of lowercase letters into a 1-row count-min sketch.
6. **Product quantization** (Jégou, Douze, Schmid, IEEE TPAMI 2011). Concatenate simhash-as-32-uint8 + sketch → 96 bytes. Split into \(M=8\) subvectors. Each subspace: k-means with \(k=256\). Code = **8 bytes**. Identity OPQ (\(R = I\)) until an explicit train. Residual quantization is a later flag. **No FAISS required in v1** — numpy is enough at 10k–100k objects.
7. **Placement.** Always a `Coord4`. Named mnemonic wins (landmark \((x,y,z)\), current \(w\)). Else majority-vote of PQ-nearest cells if occupancy \(< 16\); else walk forward on the Hilbert curve. Else `hash_to_cell(digest: bytes) -> Coord4` on the **raw 32-byte SHA-256**: `(digest[0]%16, digest[1]%16, digest[2]%8, 0)`. \(w=0\) until `judge`.

Quantization **never replaces** the blob. `cas.get(oid)` is always the original.

PQ is an *index*. The palace is the *place*. Mixing those up is how you accidentally ship another vector DB.

---

## 6. Goal-conditioned pertinence (the cats rule)

Every prompt has a goal. The goal is an object (`type=goal`) and `refs/goal`.

**v1 (VSA stubbed, weights renormalized over 0.85):**

\[
\begin{aligned}
\mathrm{pertinence}(g,m)
&= 0.47\cdot J(\mathrm{tok}(g),\mathrm{tok}(m)) \\
&+ 0.29\cdot\bigl(1 - d_H(g.\mathrm{pq}, m.\mathrm{pq}) / M\bigr) \\
&+ 0.24\cdot \frac{1}{1 + d_{\mathrm{graph}}(\mathrm{agent}, m)}
\end{aligned}
\]

After the VSA layer ships, restore \(0.40+0.25+0.20+0.15\) with \(\sigma\) mapping VSA cosine from \([-1,1]\) to \([0,1]\). Until then `vsa_score = 0`.

\(J\) is Jaccard on tokens, \(d_H\) Hamming on PQ codes, \(d_{\mathrm{graph}}\) palace-graph distance on `Coord4`.

`look` and `recall` use the **same** \(\tau\) (default \(0.35\)). Neither bypasses the gate. `recall` may add **path crumbs** (landmark + oid of path vertices), not every occupant of those cells.

Include \(m\) in `recall` iff pertinence \(\ge \tau\) or \(m\) is a path crumb — **and not** if \(m\) is tagged `not_pertinent` for this goal, or exclude-terms match with pertinence \(< 0.50\).

**Frozen cats fixture.** Goal: *prove Hilbert 4D encode/decode is bijective* with **empty exclude list**. Agent spawn \(w=0\). Hilbert note at `library` `Coord4 (3,5,1,0)` — same slice `go library` lands on. Cats at `(12,2,0,0)`, no landmark, not on the path. Agent `go library` then `recall`. `go` does **not** snap to an occupant’s \(w\). Recall bytes are `title + oid_hex + first line of blob`. Must contain `Hilbert` and the Hilbert oid; must not contain `cats`. Cats oid remains in CAS. Do not “fix” this with `exclude=["cats"]`.

Valence chooses *which neighborhood* is walked (`prefer_good` opens toward \(+W\)). It does not decide whether cats pass the gate. `query_mode` is a field on the goal object, not an axis. Judgment without a goal still moves \(w\). Goal without judgment still filters.

---

## 7. Git-family compression (what GitHub actually uses)

Lossless reconstruction is a v1 success bar. We copy the **family**, not `git fsck` compatibility.

| Git / GitHub | fourdmem |
| --- | --- |
| content-addressable objects | SHA-256 of `{type} {size}\0` + payload |
| zlib loose objects | zlib level 6 under `.fourdmem/objects/` |
| packfiles, windowed delta | Hilbert-ordered `4DM1` pack, window-4 REF_DELTA copy/insert |
| recently zstd | optional `[pack]` extra; zlib always legal |
| pack idx CRC | `zlib.crc32` (IEEE CRC-32), not CRC32C |

`fourdmem gc`:

1. Sort oids by Hilbert key (locality → similar bytes nearby → better deltas).
2. For each object, try a copy/insert delta against the previous 4. Keep it if `len(delta) < 0.8 * len(zlib(full))`.
3. Write pack + fanout idx. Delete loose objects that are packed.

**Round-trip invariant:** `cas.get(oid) == original_bytes` for loose and packed, full and delta.

Hilbert-ordered packs are the joke that is not a joke: a 4D space-filling curve is also a compression preprocessor.

---

## 8. Language objects and VSA (narrow keep)

Hyperdimensional computing / vector-symbolic architecture (Kanerva; Plate) is **not** the palace. A 8192-D bipolar vector is not a room you can walk.

VSA earns a narrow keep:

- \(D = 8192\), bipolar \(\{\pm 1\}\)
- `name_vec(name) = bipolar_from_blake2b(b"name:" + name.encode(), D)`
- `locus_vec(x,y,z,w) = bipolar_from_blake2b(b"locus:" + pack("<4i", x,y,z,w), D)` — not a random table, not `blake2b(name)` alone
- **Bind:** componentwise multiply, `name_vec ⊙ locus_vec`
- **Bundle:** signed sum + sign (a room is the bundle of its occupant binds)
- **Cleanup:** probe the item memory by cosine; winner if \(\ge 0.15\) (heuristic; random cosine \(\sim 1/\sqrt{D}\))

`go <name>` uses cleanup for typos. Exact landmark match wins first. Coordinates still come from \(\mathbb{Z}^4\).

---

## 9. Principles and echo

The store has a real `principle` type: statement, weight, evidence oids, `echo_count`. `refs/principles` points at a tree of them. The VSA bundle of principle statements is the identity vector of the store.

`reorganize` (also auto every 64 `store`/`judge` events) **does not mint principles**:

1. Cluster by PQ code + \(w\) band.
2. Unnamed occupants may move at most one Chebyshev step toward the cluster median. **Landmarks never move.**
3. Increment `echo_count`. Append an event. Never touch conversation history.

Minting is a separate verb: `principle assert --statement "..."` (agent-authored; v1 does not hide an LLM call inside gc).

This is the “organization of itself” constraint, encoded as data.

---

## 10. Dimensions 5, 6, 7 (extension points, not slogans)

v1 code uses `LatticeND` with default \(n=4\). Hilbert, Morton, pack order, and `Coord` are parameterized by \(n\). If an axis cannot be written as a coordinate + a Hilbert extension + a slice rule, it does not ship.

| Dim | Axis | Object | Verb | When |
| --- | --- | --- | --- | --- |
| 4 | \(w\) valence | signed lattice coord | `judge` / `ascend` / `descend` | **v1** |
| 5 | \(t\) epoch | **discrete session index** (not \(\lfloor\log_2(1+\Delta t)\rfloor\), which would move objects as the clock ticks) | `earlier` / `later` | v2 |
| 6 | \(p\) principle-alignment | \(\mathrm{quantize}(\mathrm{sim}(obj, P_t))\), derived on echo | `align` | v3 |
| 7 | \(e\) echo/becoming | \(\mathrm{echo\_count}\) (or log), centrality in the store's own organization | `become` | v4 |

The engine **always** projects a 3-flat. Extra axes are selected by `slice`. In 5D the blanket is still a 3-flat (two constraints); default constraints \(w = c_w\), \(t = c_t\).

---

## 11. Why this composition

| Candidate | Role | Why it is not the whole product |
| --- | --- | --- |
| Product quantization / OPQ | Internal descriptor + placement | Not a palace; not lossless |
| Git CAS + pack/delta/zstd | Lossless object layer | Not spatial, not judgment |
| 4D Hilbert / Morton | Pack order + spatial keys | Not a UX |
| Method of loci | Primary navigation | Needs a 4D backing store |
| HDC / VSA | Name ↔ locus, room bundle | 10k-D, not walkable |
| Givens / 4D projection | 4D → 3D view | Not a store |
| Goal-conditioned retrieval | Query-time gate | Ephemeral; cannot be axis 4 |
| Valence as 4th coordinate | **The 4th axis** | Needs the other layers |

The winner is the **composition**: Hilbert + lattice + blanket as the spatial core, git-CAS as the lossless core, loci as the UX, PQ as the index, goal-filter as the prompt shield, VSA as the naming layer.

---

## 12. What the math harness is for

Frontier labs do not “prompt harder” at mathematics. They **harness** a checker.

| Tool | Who uses that class of tool | What fourdmem uses it for |
| --- | --- | --- |
| Lean 4 REPL (`lake exe repl`, JSON) at **v4.34.0-rc2** | DeepMind-style provers, Anthropic formal-math, Meta autoformalization | REPL smoke; not mixed with 4.33 `.olean` |
| `lean/FourDMem` Lake package at **v4.33.1** | same | Hilbert encode/decode on `Lattice4`; Morton invertibility |
| HuggingFace Math-Verify + sympy | Math RL / eval pipelines | Harness smoke; projector vs sympy `Rational` |
| EleutherAI lm-evaluation-harness | Standard company eval harness | Task YAML for the v1 success bar |
| mini-swe-agent | Meta, NVIDIA, IBM, … coding baseline | The loop that *builds* this repo |

Install locally with `scripts/bootstrap-harnesses.ps1`. Vendor trees are not shipped in git (lm-eval alone is tens of thousands of files). Their licenses stay theirs.

---

## References

- Jégou, Douze, Schmid. *Product Quantization for Nearest Neighbor Search.* IEEE TPAMI, 2011.
- Skilling. *Programming the Hilbert curve.* AIP Conf. Proc. 707, 2004.
- Charikar. *Similarity estimation techniques from rounding algorithms.* STOC, 2002.
- Kanerva. *Hyperdimensional computing.* Plate. *Holographic Reduced Representations.*
- Git pack format — content-addressable objects, zlib loose, windowed delta.
- Chroma. *Context Rot: How Increasing Input Tokens Impacts LLM Performance.* 2025.
- Headroom realignment: passthrough is sacred; offload; retrieve on demand.
