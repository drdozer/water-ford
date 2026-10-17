# Boards visual language — spec (v1, pre-exploration)

Deliverable (a) of `../../inbox/produce-ford-boards-tilesets.md`. v1 = the
measured baseline that drives the Blender phase (big-floor build + look
probes); it will be REWRITTEN after the exploration/gwenview gates pick the
final look. Every number traces to `boards-research.md` (R-numbers below) and
regenerates from the scripts in `.cache/boards-research/` (superproject
scratch).

## 1. Anchors extracted from the inherited deck (R1)

Source art: `mod/graphics/planks.png` (512×64, 8 variants @64×64, scale 0.5;
byte-equal to pristine `planks-base.png` today). Palette anchors (16-level
bins, ≥50% alpha):

| hex | rgb | L | share |
|---|---|---|---|
| #96693b | (150,105,59) | 111 | 26.4% |
| #976b42 | (151,107,66) | 114 | 21.8% |
| #997245 | (153,114,69) | 119 | 15.9% |
| #8c663a | (140,102,58) | 107 | 13.4% |
| #3e2816 | (62,40,22) | 43 | 7.7% — all gaps |

Wood core = L106–123 warm browns; gap tone = the single dark anchor (L43,
the value floor — not black); highlight cap ≈ L128. Grain: hf energy
13.7–14.5 (keep lively), variant midtones drift L110–116.

Geometry targets ("substantially similar"): 4 horizontal courses per 64px
cell (**8 game px per course**), seam rows 15/31/47, one staggered butt joint
per course on average (boards ≈16–50px on sheet = 8–25 game px), variant
identity = joint stagger + grain seed + slight tone.

Edge furniture (inherited): E|W boundaries quiet (tone continuation, edge
imbalance ≤1 L); N|S boundary carries a variant-independent light/dark step
(top strip L113 / bottom strip L78).

## 2. Tiling law (R10) — binding for the Blender model

**Pin the boundary furniture, free the interiors.** Elements crossing a cell
boundary must meet variant-invariant content on both sides, or end at the
boundary identically in every variant. Lengths/cuts/bolts on the **16px quanta
(8 game px)**; bow profiles **h = A·sin²(π(x−x₀)/L)** (zero value + slope at
board ends) so amplitudes vary freely per board without tiling seams.
Lift cap: **¼ × board width**. End bolts: **2 per board end**, ≈⅓/⅔ across
the course width, 2–3px heads, east-side micro-shadow under the west key.

Schemes A (bolted bays) / B (continuation illusion) / C (hybrid) are
**exploration zones in the big floor, not pre-decisions**
(maintainer 2026-10-17). Default recipe: A — quanta 16px, per-variant
lengths/widths/waves, bolted splices at every cell edge. Detail: R10 table.

## 3. Ballast + metal palettes (ingredients as color keys)

Stone families (mid-light only; keep L≥64 authored; the deck band prefers
L120–155): py gravel icon cool greys (#474547 L70…#9c9288 L148), py
crush-stone warm khaki (#796b51 L108…#b89868 L155), py crush-gravel sandy
(#a48b76 L143…#baa797 L170), py limestone neutral (#a9a298 L163),
vanilla stone ochre (#967948 L124…#c6a668 L169). W3 post-mix pop band
(R7 sim): warm ochre/bright-crush/sandy read ΔL +9…+31 vs mixed plank L107;
pale accents +39…+44; AVOID crush-stone khaki / grey-mid (ΔL −2/−7).
Metal detailing (bolts, bars): iron-stick greys (#474949…#787876, highlight
#bab9b7 L185) and py bolts neutral greys (#686868…#a7a7a7).

Ballast look target: small pebbles/stones; integration in-sprite (lead
option) — widened seams 2–4px carrying pebble runs; doodad fallback is
prototype-native `bound_decoratives` (R11) with a bench probe if needed.

## 4. Lighting rig (R6, verbatim from ford-posts.blend)

- Key: ONE light object `KEY`, type **POINT**, world position **(−42, 0, 42)**
  relative to origin-staged geometry, energy **40000**, color white. Linked
  into every scene used for renders.
- Ambient: world background single node, **color (0.55, 0.55, 0.55),
  strength 0.06**.
- No other lamps. All boards geometry stage at the origin.

## 5. Engine / in-game constraints (binding)

- Deck set is a **drop-in graphics swap**: sheet 512×64, exactly 8 main
  variants, size 1, scale 0.5 — config never moves (frozen data-updates.lua).
- Author mid-bright, **no true blacks**; never derive colors from water-shallow
  values; variant-sprite alpha is flattened → design every cell full-bleed.
- Post-mix expectations (model-approx): plank anchor mixes L107, gap L56;
  final verdicts = gwenview + bench ABS (rim stays sealed −0.1/0.9, W3+P1).
- Land tile: same visual language, final-look render (no water mix), same key
  sun; concrete-based registration sketch (ground() mask, layer 13,
  buildable-on, no is_foundation, clean decoratives — D3); sheet name/count
  proposal `boards-land.png`, 8 size-1 variants (D6). Rich sizes = stretch
  (SA-template layout, R3; D5) — ford richness requires moving frozen config,
  out of this round.

## 6. Provenance

- Full research: `boards-research.md` (R1–R11, decision points D1–D6).
- Scratch/scripts: `.cache/boards-research/` — extract-planks.py,
  extract-r1b-r2.py, planks-extract.json, swatches/*.png.
- Blender phase plan: boards-research.md §"Blender phase plan (S2)".