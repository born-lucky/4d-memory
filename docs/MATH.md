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

v1 defaults: \(X=16\), \(Y=16\), \(Z=8\), \(W=8\). That is \(16\times 16\times 8\times 17 = 34{,}816\) cells. Many objects may share a cell. The palace is a *view* over objects, not 1:1 with them.

| Axis | Name | Meaning | Who writes it |
| --- | --- | --- | --- |
| \(x\) | east | floor plan | mnemonic, or Hilbert-folded PQ neighborhood |
| \(y\) | north | floor plan | same |
| \(z\) | up | stories | same |
| \(w\) | **valence** | bad \(\rightarrow\) good | `judge` (default \(0\)) |

**Why valence is the 4th axis, and goal is not.** A spatial axis has to be a stable property of an object. Goals change every prompt. If we put “pertinence to the current goal” on \(w\), the whole palace would re-embed every turn and landmarks would lie. Valence is a judgment attached to the object: nearby on \(w\) means similarly judged. “Recall the good stuff related to this” is a walk toward \(+w\) in the same \((x,y,z)\) neighborhood.

Goal pertinence is a **query-time gate** (section 6). The two compose. They are not the same coordinate.

Distance on the lattice is Chebyshev:

\[
d_\infty(p,q) = \max_i |p_i - q_i|.
\]

v1 recall neighborhood: radius \(1\) on \((x,y,z)\), radius \(1\) on \(w\) unless `prefer_good` / `prefer_bad` opens toward a pole.

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

**Invariant (checked with sympy / HuggingFace Math-Verify):**

\[
\frac{d}{d-w}\cdot\frac{d-w}{d} = 1 \qquad (w \ne d).
\]

The Python projector is tested against sympy `Rational`s. Math-Verify `parse` / `verify` scores the closed form. That is why a math harness is a *tool* of this project, not a badge.

---

## 4. Hilbert and Morton keys

Occupied cells need a locality-preserving 1D key: packfile order, B-tree key, “nearby in 4D ⇒ nearby on disk.”

**Default: n-dimensional Hilbert curve** (Skilling, *Programming the Hilbert curve*, AIP 707, 2004). \(n=4\), \(b=4\) bits per unsigned axis. Map valence by \(w' = w + W\) so \(w' \in [0,16)\), then encode \((x,y,z,w')\) → a 16-bit index (stored in `uint32` so dimensions 5+ have headroom).

```text
hilbert_encode_4d(x, y, z, w, bits=4) -> int
hilbert_decode_4d(h, bits=4) -> (x, y, z, w)
```

**Morton (Z-order)** is the debug coder: bit-interleave of the four axes. Worse locality, trivial invertibility. Used as a differential test against Hilbert.

**Lean invariant.** The Lean 4 community REPL — the same JSON stdin/stdout tool AlphaProof-style agents talk to — machine-checks:

```lean
theorem hilbert_encode_decode_id
    (p : Fin 16 × Fin 16 × Fin 16 × Fin 16) :
    decode (encode p) = p
```

\(16^4 = 65{,}536\), so exhaustive `#eval` over the grid is a legitimate check (seconds). Morton invertibility is `native_decide` on the bit operations. Python property tests: 10k random points, `decode(encode(p)) = p`.

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
   Loose path: `.fourdmem/objects/{oid[:2]}/{oid[2:]}` zlib level 6. Same header convention as Git; hash is SHA-256, not SHA-1.
4. **Simhash (256-bit).** Charikar fingerprints: tokenize, SHA-256 each token, signed sum of feature bits. Hamming distance is the lexical metric.
5. **N-gram sketch (64 bytes).** 3-grams of lowercase letters into a 1-row count-min sketch.
6. **Product quantization** (Jégou, Douze, Schmid, IEEE TPAMI 2011). Concatenate simhash-as-32-uint8 + sketch → 96 bytes. Split into \(M=8\) subvectors. Each subspace: k-means with \(k=256\). Code = **8 bytes**. Identity OPQ (\(R = I\)) until an explicit train. Residual quantization is a later flag. **No FAISS required in v1** — numpy is enough at 10k–100k objects.
7. **Placement.** Named mnemonic wins. Else majority-vote of PQ-nearest cells. Else `hash-to-cell` from the oid.

Quantization **never replaces** the blob. `cas.get(oid)` is always the original.

PQ is an *index*. The palace is the *place*. Mixing those up is how you accidentally ship another vector DB.

---

## 6. Goal-conditioned pertinence (the cats rule)

Every prompt has a goal. The goal is an object (`type=goal`) and `refs/goal`.

\[
\begin{aligned}
\mathrm{pertinence}(g,m)
&= 0.40\cdot J(\mathrm{tok}(g),\mathrm{tok}(m)) \\
&+ 0.25\cdot\bigl(1 - d_H(g.\mathrm{pq}, m.\mathrm{pq}) / M\bigr) \\
&+ 0.20\cdot \frac{1}{1 + d_{\mathrm{graph}}(\mathrm{agent}, m)} \\
&+ 0.15\cdot \sigma(\mathrm{vsa}(g,m))
\end{aligned}
\]

\(J\) is Jaccard on tokens, \(d_H\) Hamming on PQ codes, \(d_{\mathrm{graph}}\) palace-graph distance, \(\sigma\) maps VSA cosine from \([-1,1]\) to \([0,1]\).

Include \(m\) in `recall` iff pertinence \(\ge \tau\) (default \(0.35\)), **or** \(m\) lies on the current stored path, **or** the agent `look`s at that cell — **and not** if \(m\) is tagged `not_pertinent` for this goal, or exclude-terms match with pertinence \(< 0.50\).

**Cats test.** Goal: *prove Hilbert 4D encode/decode is bijective*. Stored: that note, and “I saw cats on screen.” `recall` must contain the Hilbert note and must not contain `cats`. The cats oid **remains in the CAS**. We offload. We do not delete.

Valence chooses *which neighborhood* is walked (`prefer_good` opens toward \(+W\)). It does not decide whether cats pass the gate. Judgment without a goal still moves \(w\). Goal without judgment still filters.

---

## 7. Git-family compression (what GitHub actually uses)

Lossless reconstruction is a v1 success bar. We copy the **family**, not `git fsck` compatibility.

| Git / GitHub | fourdmem |
| --- | --- |
| content-addressable objects | SHA-256 of `{type} {size}\0` + payload |
| zlib loose objects | zlib level 6 under `.fourdmem/objects/` |
| packfiles, windowed delta | Hilbert-ordered pack, window-4 copy/insert delta |
| recently zstd | zstd on packed payloads (`4DM1` magic) |

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

- \(D = 8192\), bipolar \(\{\pm 1\}\), seeded from `blake2b(name)`
- **Bind:** componentwise multiply, `name ⊙ locus`
- **Bundle:** signed sum + sign (a room is the bundle of its occupant binds)
- **Cleanup:** probe the item memory by cosine; winner if \(\ge 0.15\)

`go <name>` uses cleanup for typos. Exact landmark match wins first. Coordinates still come from \(\mathbb{Z}^4\).

---

## 9. Principles and echo

The store has a real `principle` type: statement, weight, evidence oids, `echo_count`. `refs/principles` points at a tree of them. The VSA bundle of principle statements is the identity vector of the store.

`reorganize` (also auto every 64 `store`/`judge` events):

1. Cluster by PQ code + \(w\) band.
2. If a cluster has ≥3 same-sign judgments, reinforce a principle from majority reasons (agent-authored; v1 does not hide an LLM call inside gc).
3. Unnamed occupants may move at most one Chebyshev step toward the cluster median. **Landmarks never move.**
4. Increment `echo_count`. Append an event. Never touch conversation history.

This is the “organization of itself” constraint, encoded as data.

---

## 10. Dimensions 5, 6, 7 (extension points, not slogans)

v1 code uses `LatticeND` with default \(n=4\). Hilbert, Morton, pack order, and `Coord` are parameterized by \(n\). If an axis cannot be written as a coordinate + a Hilbert extension + a slice rule, it does not ship.

| Dim | Axis | Object | Verb | When |
| --- | --- | --- | --- | --- |
| 4 | \(w\) valence | signed lattice coord | `judge` / `ascend` / `descend` | **v1** |
| 5 | \(t\) epoch | session index (or \(\lfloor\log_2(1+\Delta t)\rfloor\)) | `earlier` / `later` | v2 |
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
| Lean 4 REPL (`lake exe repl`, JSON) | DeepMind-style provers, Anthropic formal-math, Meta autoformalization | Hilbert encode/decode bijection; Morton invertibility |
| HuggingFace Math-Verify + sympy | Math RL / eval pipelines | Projection identity; rational closed forms |
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
