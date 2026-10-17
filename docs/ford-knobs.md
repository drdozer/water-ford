# The Ford: knobs and pulleys

Measured parameter reference for the water-ford tile (2026-10-17). Every
claim traces to a capture in `.cache/ford-factory/provenance/` and a row in
`docs/shore-rim.md`; all rim numbers are ABS basis.

## 1. The deck: `effect_color` (primary tint) + alpha

The "water" tile effect draws an animated, tinted water layer over the tile.
Two dials, one surface:

- **Model (interpolation device — not a law):**
  `deck(t, a) = (1-a) * E(t) + a * WATER` with `WATER = (17, 114, 129)` and
  `E(t) ≈ E0 + S*t`, `E0 ≈ (140, 85, 41)`, `S ≈ 0.9/unit`.
  Verified only between the parked and water-exact tints (predicted C20/L2
  correctly). It FAILS at black tint (T1 deck R measured 100.9 vs predicted
  124.6) and alpha mixing measures darker and shallower-contrast than linear
  (V2 G 83.4 vs 100 predicted). Use it to interpolate inside that region,
  measure anything outside.
- **Tint hue families (measured):**
  - black = dark warm deck (boards dominant, driest look);
  - neutral grey = uniform lift, hue stays warm-neutral (G/R ≈ 0.96), no
    mint — the lightening axis that does not trip the wash;
  - water-family tints = mint wash; the wash is driven by tint GREEN
    (water G=147 nearly doubles the art's G);
  - parked tint = water × (0.37, 0.19, 0.20) — warm, the "good look" era.
- **Wash criterion:** deck R above the unveiled planks render = washed.
  Grey tints did not trip it at any stop; water-family tints do early.
- **Halo law (the other half of the tint):** rim dip on adjacent water ∝
  the tint's RGB distance to water (C-ladder on the water-scale axis, grey
  axis confirms). Black ≈ 25.4/26.9; grey-20% ≈ 0 (fractionally BRIGHT-edge,
  −2.4/−2.1); water-exact ≈ 0. Strong deck color and strong halo travel
  together on the tint axis alone.
- **Constraint (binding):** no water-shallow values in clones; alpha tuning
  permitted.
- **Committed (2026-10-17): W3 = tint (51, 51, 51) @ alpha 63.75 (25%).**

## 2. Primary alpha (the veil thickness)

- More alpha = more animated water over the deck ("slosh"). Deck darkens
  monotonically and non-linearly at black tint:
  a5 (109.7, 99.8, 72.9) → a12.5 (101.4, 93.7, 69.1) → a25 (87.3, 83.4,
  62.9) → a40 (70.5, 70.9, 55.2). With grey tint the lift per tint-unit is
  retained (W-family), and art texture-std GROWS with tint (10.6 → 16.9
  across W) — slosh and wood texture rise together.
- Halo: alpha-INDEPENDENT (uncovered rim flat ~25.4-25.5 across 5/12.5/25%).
- Current: 25%.

## 3. Secondary effect_color

Measured INERT in every combination tested (F0–F80, A-family: bit-identical
renders). Parked value retained. Do not budget effort here.

## 4. Boundary, outward: the ford's `transitions` entry (the halo-hider)

- A ford-owned `transitions` entry with `to_tiles` = water family stamps
  pieces ONTO the water-side seam (to-side rendering, measured). This is the
  only proven lever that reaches the halo rows (the halo is painted on
  neighbor water cells).
- Flat-water filler sheet proved the mechanic: rim 25.4/26.9 → **1.3/2.8**;
  touch bands restored to deep-water G (107.4 vs Ndeep 107.3), 100%
  water-classified, stamps render ABOVE the rim paint.
- Fire behavior: fires DESPITE `transition_merges_with_tile = "water"`
  (TC + UF0 precedent). Layout = stacked class bands (inner/outer/side/u/o
  counts + y offsets, tile_height 1); the `effect_map` mask sheet is
  optional (UF0 ran without one). Fill every frame opaque for full coverage.
- **`apply_effect_color_to_overlay = true`** exists on transition
  definitions (out-of-map entries use it). Effect on regular entries:
  UNTESTED — if it works, stamped art auto-tints with our effect color.
- Current: flat-water cover (flat (17,114,129), all frames, no mask) —
  deliberately invisible-as-filler; any boundary art replaces it.

## 5. Boundary, inward: `variants.transition.overlay_layout`

- Vanilla's tile-owned edge system (shallow: tiles.lua 1192-1226; mud 1280+;
  stone-path/concrete/etc.). Stamps pieces INSIDE the tile's own border,
  only against out-of-transition-group neighbors. Cannot reach the halo rows
  even fully firing.
- On the ford: barely fired (1-2% edge coverage) with the merge present;
  merge-suppression is a LABELED GUESS, untested (the UB1/UB2 rows exist on
  paper only). The vanilla shallow sheets live in
  `graphics/terrain/water-shallow/` (side 6×4, corners 6×4, u 1×4, o single;
  art = shallow's own color, alpha-soft at the meeting edge).
- Status: optional dressing for the ford's own border band. Not in the
  committed row.

## 6. `transition_merges_with_tile`

- Ford currently = "water": water↔ford treated as same tile for transitions
  → the group machinery skips stamps between them (inward overlay suppression
  is the suspected casualty). Outward entries are measured immune. Keep only
  if the inward dressing or water-side vanilla stamps are NOT wanted.

## 7. Registration (`water_tile_type_names` insert)

- Legacy land-side trick: vanilla land tiles' water-targeting transitions
  key off this list, so LAND borders stamp their bank art onto the ford.
  Game-critical (cargo ships, fish) AND seam-relevant on the land side.
  Keep (binding).

## 8. Tile-definition knobs (acquitted or frozen)

- `layer` 9 (above shallow/mud so pieces render over neighbors) — acquitted
  as halo cause (layer 3 same rim); stays 9.
- `layer_group = "water"` (inherited via deepcopy) — part of the shader
  membership gate (effect + layer_group OR registration). Stays while the
  under-water look is required.
- `is_foundation = true` — maintainer ruling (under-tile memory); measured
  render/rim-neutral. Stays. ALL probe tiles carry it (everything-foundation
  ruling).
- **Art alpha in variant sprites is FLATTENED** (checker probes: alpha-0
  pixels render as opaque RGB; the remembered under-tile never shows
  through). Overlay transparency as a design tool is dead; transition-piece
  transparency is NOT (pieces' transparent bg showed under-water at the seam,
  TC) — piece-level alpha works, sprite-level variant alpha does not.
- `collision_mask` {water_tile, resource, floor} — gameplay binding (fish +
  cargo waterways + walkable). Frozen.

## 9. Environment and measurement conventions

- Cloud shadows drift across the scene (positional capture artifact) — judge
  blocks only where the reference region is unshadowed; noon-locked lighting.
- ABS screenshots: 32 px/tile, centered {0,2.5}, zoom 1, no HUD. Band map:
  Ntouch y−3, Nrow2 y−4, Ndeep y−9, Stouch y7, Srow2 y8, Sdeep y10.
- The row runner prints the ABS measure FIRST, win-basis second. All ledger
  numbers are ABS.
- Rows live in `tools/paper-pipeline/sweep-row.sh`; captures never overwrite
  (provenance law).

## 10. The committed row (2026-10-17, updated same day)

W3 deck (tint (51,51,51) @ 63.75) + **P1 boundary**: a SINGLE outward
transitions entry (to_tiles = water family, group = water's) whose
spritesheet is the composed `pilings-composite.png` (flat-water background
alpha-composited under the existing piling frames, every frame opaque, mask
kept) on the W3 deck. Halos sealed (rim -0.1/0.9 = covered level), posts
render on the water side. Measured constraints baked into this design:
two entries with the same group+to_tiles do NOT stack (last wins, X1);
art alpha in variant sprites is flattened; `apply_effect_color_to_overlay`
works on regular entries but tints the whole entry's art (P2). Live via
`sweep-row.sh P1`. Note: the piling palette reads slate/steel-toned, not
warm wood - re-art is a possible future fork.