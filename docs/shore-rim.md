# Investigation — the ford shore rim

Status: active (2026-10-16 evening). Governing process:
`../../../docs/how-to-investigate.md` (scope + interventions). This file is the
investigation's own record; it supersedes RESUME.md/journal.md for this
question going forward. NOTE the RESUME bisect list is hereby corrected: its
"collision_mask → vanilla water()" candidate is invalid (entry #3 below).

## Scope

**Gameplay constraints (maintainer, 2026-10-16, binding):** the ford tiles
must (1) function as water from the gameplay point of view — fish swimming,
cargo-ship waterways and similar water mechanics; (2) be pathable for
players and units (pyanodon caravans walk over); (3) visually read as the
ford being UNDER the water (the animated water overpaint is load-bearing).
Constraints (1)+(3) keep the ford inside the water rendering system and its
registration/collision semantics; (2) keeps the walkable collision mask.
Route consequences recorded later in this file follow from these.

### 1. What is it we are investigating?

Which property of the ford tile prototype causes the engine's water effect to
paint a dark shore rim onto the water tiles neighboring the ford. The ford is
a custom water-effect tile (vanilla `water` clone); every water cell adjacent
to it renders a dark band, on both north and south edges, ~15–19 G darker than
water one/two rows out; pieces on or off; either clone source. Deliverable:
the identity of the triggering property (or set), plus a measured
demonstration of causing and removing the rim through that property alone.

Carried in — established before this file:

- Not the piling pieces, not the gray effect map (prior session probe 7: rim
  present with pieces off, touch 91.1/97.1 vs row2 110.1/114.4).
- Not is_foundation (prior session, shallow clone; re-run as #2 below); not
  layer (this session, #1).
- Prior-session verdict (rim = water effect's shore pass reacting to the ford
  tile itself, visible under pieces and bare water): **DISCARDED** with all
  prior-session conclusions (maintainer: heavy hallucination). Not evidence.
- Vanilla facts (base prototypes/tile/tiles.lua + tile-collision-masks.lua,
  read directly this session):
  `water` = effect "water", effect_color {21,147,167} (opaque), layer 3,
  subgroup "nauvis-tiles", collision water() = {water_tile, resource, item,
  player, doodad, floor}; `water-shallow` = same effect, translucent
  (12.5% alpha), shallow_water() = {water_tile, resource, floor}.

### 2. Why do we care?

The rim is a visible defect in the mod's core look — a dark band hugging the
ford wherever it meets water; maintainers have flagged the darkening
repeatedly (journal: the "shore pre-darkening ring"; the bare poles now sit
against it). The workaround class tried so far (opaque coverings, kludged
effect maps) was rejected. Knowing the trigger converts that guesswork into a
targeted config fix. Generic value: engine knowledge of which tile property
drives the water-effect shore pass, applicable to any modded water tile.

### 3. How will we know if we find it?

A property P passes only if, one variable at a time against the parked
baseline:

1. on→off: setting P collapses the rim dip from ~15–19 to ≤ noise (order of
   4 G) in the day-bright baseline scene;
2. off→on: restoring P restores the dip;
3. no collateral breakage: the ford stays functional with P's winning value
   (walkable, deck visible, ships/offshore-pump semantics intact);
4. measured, not eyeballed, under the settled capture regime. Historical
   numbers are player-view-anchored (window captures at pinned spawn) and
   become the *reference*, not the standard; thresholds and bands must be
   re-derived under absolute-coordinate captures before further scoring.

### 4. How will the player know if it is fixed?

Load the ford and see no dark band in the water around it — the water reads
continuous right up to the deck edge (and eventually the pilings), in
daylight, final art state. Precedent: the Version D round, maintainer-verified
"ring-free / correctly has no shore effect". Boundary: rim at a land/water
shore is correct vanilla behavior and out of scope — the fix must not remove
vanilla shores, only the ford's. The player's/maintainer's eyes are the
arbiter; the numbers are the prediction that keeps the verdict cheap, never
its replacement.

## Interventions

Ledger format per the how-to doc. **Entries #1–#3 predate the process**: they
are reconstructed records of the 2026-10-16 evening session; their expectation
blocks were one pre-frozen session decision rule (stated before the first
run), not per-intervention pre-writes. Reverts used a file snapshot, not git —
the committed-baseline prerequisite (below) was unmet.

**Frozen session decision rule (pre-capture, 2026-10-16):** culprit ⟺
touch-vs-row2 rim dip collapses to ≤4 G; acquitted ⟺ dip ≈15–18 G;
day-bright capture; water-only G means.

### Status tensor

| #  | change                                    | status |
|----|-------------------------------------------|--------|
| 1  | layer 9 → 3                               | acquitted |
| 2  | is_foundation true → false                | acquitted |
| 3  | collision_mask → vanilla water()          | invalid (by design, recognized post-run) |
| 4  | subgroup → nauvis-tiles                   | proposed |
| 5  | variants.main → vanilla water pictures    | proposed |
| 6  | collision_mask +item+doodad (player off)  | proposed |
| 7  | effect_color value sweep (matrix)         | **implicated** (alpha+secondary acquitted; primary color identity is the trigger; eyes check pending) |
| 8  | transitions restore water_to_out_of_map   | proposed |
| 9  | deregister from water_tile_type_names     | proposed, weak prior |
| 10 | vanilla reference patches in test world   | proposed, ruling pending |
| 11 | ribbonia-style transition augmentation    | proposed, maintainer-directed |

### The entries

**#1 — `tile.layer` 9 → 3 — acquitted**

- *What/how:* single edit in `mod/data-updates.lua` (data-updates stage);
  rebake save (bake.sh --stages save,view --seed 4242) + fresh relaunch +
  window capture.
- *Revert:* file-snapshot restore of data-updates.lua (at the time; today's
  rule: git rollback).
- *Intent:* handoff bisect candidate. Layer is a proven delta between the
  ford (9) and vanilla water (3); suspicion: the effect region keys on tile
  layer.
- *Expectation (frozen):* the session decision rule above.
- *Observation:* capture /tmp/ford_b1_layer3.png; dip **N=13.5/S=16.4** —
  signature persisted; matched the acquitted branch. Also surfaced: X window
  ids are reused across relaunches (freshness must be proven by process/zip
  times, not by id change).
- *Status moves:* proposed → run (20:0x) → acquitted (same evening).

**#2 — `tile.is_foundation` true → false — acquitted**

- *What/how:* single edit, same cycle as #1.
- *Revert:* file-snapshot restore.
- *Intent:* handoff candidate; foundations may be treated as land by the
  effect region. Prior session had tested this on the shallow clone (rim
  persisted); this run re-tests on the water clone.
- *Expectation (frozen):* session decision rule; side-prediction "persists,
  consistent with the shallow-clone result".
- *Observation:* capture /tmp/ford_b2_nofound.png; dip **N=16.3/S=15.8** —
  persisted; matched both predictions.
- *Status moves:* proposed → run → acquitted.

**#3 — `collision_mask` → vanilla `water()` — invalid**

- *What/how:* replace the ford's {water_tile, resource, floor} with vanilla
  {water_tile, resource, item, player, doodad, floor}.
- *Revert:* executed — parked mask restored on disk (file snapshot).
- *Intent:* handoff candidate; suspicion: the effect region keys on
  collision-mask content.
- *Expectation (frozen):* session decision rule.
- *Observation:* **none obtainable.** The vanilla mask includes `player` —
  the character-collision layer — making the ford unwalkable; the character
  was displaced from spawn {0.5,4.5} onto map-gen terrain outside the painted
  region (maintainer report: standing on grass); camera followed, so the
  scene-validation capture loop never saw the ford (12 failed scene checks).
  The prediction was never tested — the probe invalidated itself.
- *Status moves:* proposed (as written in RESUME) → run → **invalid** (by
  design; recognized only after execution → process lesson: the invalid check
  happens at catalogue-writing time).
- *Residue:* the live window still shows this build at session pause; one
  bake from the parked config clears it.

### Pending catalogue (fields partial → completed where determinable)

**#4 — subgroup "artificial-tiles" → "nauvis-tiles"**

- *What/how:* single edit of `tile.subgroup`.
- *Intent:* subgroup is a delta between the ford and vanilla water; if the
  effect's region/category logic consults it, the rim collapses.
- *Expectation (pre-stated):* decision rule at the then-current baseline.
- *Revert:* git rollback (pending committed baseline).
- *Risks:* subgroup feeds the map-editor/palette grouping; expected harmless
  in-game.

**#5 — variants.main: planks.png entries → vanilla water pictures**

- *What/how:* restore the clone-inherited water variant table (`deepcopy` of
  water's variants.main) in place of the planks entries.
- *Intent:* the effect's per-tile coverage/mask may derive from variant
  content; the planks are the ford's own delta vs vanilla.
- *Expectation (pre-stated):* decision rule; NOTE — deck disappears under
  this change (no planks drawn), so collateral-check #3 of the scope cannot
  be scored for deck visibility; the run only tests the rim.
- *Revert:* git rollback.

**#6 — collision_mask +item+doodad (player stays omitted)**

- *What/how:* add `item = true` and `doodad = true` to the parked mask
  {water_tile, resource, floor} — exactly the shallow_water()→water() delta
  minus the player layer.
- *Intent:* the valid redesign of the acquitted-in-principle mask family:
  tests whether mask content beyond resource/floor matters, while preserving
  walkability.
- *Expectation (pre-stated):* decision rule.
- *Revert:* git rollback.

**#7 — effect_color value sweep (intervention matrix) — IMPLICATED**
maintainer-directed (2026-10-16). Goals to find in one sweep: values that
(a) keep the deck visible, (b) let the water effect overpaint the ford
visibly, (c) remove the shadow/rim. Standing constraint: if the ford clones
water, no values from water-shallow are used — the fix may be as simple as
using water's own effect_color.

- *What/how:* rows vary the primary effect_color RGB identity and alpha and
  the secondary policy; one bake+capture per row (script sweep-row.sh);
  grid R0..R6 as pre-stated below. All captured on the absolute-coordinate
  basis (game.take_screenshot, zoom=1, 32 px/tile, centered {0,2.5},
  no HUD), noon-locked lighting (`always_day=true` added to the view
  scenario this session), seed 4242.
- *Intent:* maintainer hypothesis — the shore pass keys on the effect color
  identity/alpha vs the region's water color.
- *Expectation (pre-stated):* rim collapse on water-exact rows ⟺ color-keyed
  shore pass (fix found); rim persisting under water-exact color at every
  alpha ⟹ effect_color acquitted.
- **Observation (all rows, water-only G means, dip = row2−touch):**

| row | primary effect_color | alpha | secondary | dip N | dip S | verdict |
|-----|----------------------|-------|-----------|-------|-------|---------|
| R0  | {7.75,28.5,33.25} (shallow-scaled wash) | 12.5% | parked | **21.1** | **20.9** | rim present (reference) |
| R1  | {21,147,167} (water rgb) | 12.5% | parked | 0.4 | 0.3 | collapsed |
| R2  | {21,147,167} | 50% | parked | 0.8 | 2.2 | collapsed |
| R3  | {21,147,167} | 100% | parked | 0.9 | 1.9 | collapsed |
| R4  | {21,147,167} | 100% | water {49,80,14} | 0.9 | 1.8 | collapsed |
| R5  | {21,147,167} | 12.5% | water {49,80,14} | 0.7 | 2.2 | collapsed |
| R6  | {21,147,167} | 50% | water {49,80,14} | 0.8 | 2.1 | collapsed |

- *Alpha-refinement rows (maintainer direction after seeing R1 live: "boards
  look washed out — vanilla water tint with adjusted alpha"):* water's pair
  wholesale, primary alpha swept down. Pre-stated: rim stays collapsed (the
  R-rows established alpha-independence); decision axis = board visibility,
  maintainer eyes.

| row | alpha | dip N/S | deck-mid warm | outcome |
|-----|-------|---------|---------------|---------|
| E3  | 10%  | 0.8 / 2.0 | 83,881 | rim collapsed |
| E2  | 5%   | 0.9 / 1.8 | 83,516 | rim collapsed |
| E1  | 2.5% | 0.9 / 1.9 | 83,559 | rim collapsed |
| E4  | 20%  | 0.8 / 1.6 | 83,157 | rim collapsed (coarse sweep) |
| E5  | 40%  | 0.8 / 2.1 | 84,049 | rim collapsed (coarse sweep) |
| E6  | 60%  | 0.8 / 2.1 | 84,049 | rim collapsed (coarse sweep) |
| E7  | 80%  | 0.9 / 0.0 | 79,433 | rim collapsed (coarse sweep; 100% = R4 0.9/1.8) |

  Deck-mid warm counts are FLAT across 2.5%→100% alpha — the warm-count
  metric does not track deck visibility under the teal wash at all and is
  retired as a proxy; deck visibility is an eyes measurement only.
  Captures: provenance/20261016-210918-E3-{abs,win}, 20261016-211051-E2-{abs,win},
  20261016-211224-E1-{abs,win}, 20261016-212731-G1-{abs,win},
  20261016-212904-G2-{abs,win}, 20261016-213037-G3-{abs,win},
  20261016-213210-G4-{abs,win}, 20261016-213343-G5-{abs,win},
  20261016-213516-G6-{abs,win}, 20261016-211606-E4-{abs,win},
  20261016-211739-E5-{abs,win}, 20261016-211912-E6-{abs,win},
  20261016-212045-E7-{abs,win}.png. R1 (12.5%) maintainer-reviewed live:
  "boards look really washed out". E-column eyes verdict: "the higher the
  alpha, the more invisible the ford; at 100% the ford is invisible; of
  these 2.5% is best but still washed out". For future flipbooks: ABS
  captures only (maintainer instruction) — WIN captures are for the live
  view only.
- *Selection flipbook (maintainer request):* `.cache/ford-factory/provenance/
  flipbook/` — ordered symlinks ascending in primary alpha, per row ABS
  (absolute framing, no HUD) + WIN (player POV): 00 parked wash a12.5 (the
  "before"-like reference), 01 a2.5, 02 a10, 03 a20, 04 a40, 05 a60,
  06 a80, 07 a100. Opened in gwenview for selection.
- *Micro-sweep down (maintainer direction after E-column verdict: alpha
  sweep 2 / 1.5 / 1 / 0.5 / 0.2 / 0.1%):* primary alpha only, secondary
  held water-wholesale. Pre-stated: rim stays collapsed (alpha-independent
  per the R-rows); decision axis = board readability (eyes).

| row | alpha  | dip N/S   | outcome |
|-----|--------|-----------|---------|
| G1  | 2%     | 0.1 / 1.4 | rim collapsed |
| G2  | 1.5%   | 0.1 / 1.9 | rim collapsed |
| G3  | 1%     | 0.8 / 2.1 | rim collapsed |
| G4  | 0.5%   | 0.1 / 1.8 | rim collapsed |
| G5  | 0.2%   | 0.4 / 2.2 | rim collapsed |
| G6  | 0.1%   | 0.1 / 1.5 | rim collapsed |

  Micro flipbook (ABS only, per the ABS-only rule): provenance/flipbook-alpha/
  (00 parked reference, 01 a2.5 E1, 02..07 the G rows) — opened in gwenview.
- *Mechanics note (maintainer discussion, pre-F-sweep):* the effect_color
  alpha is the opacity of the water-effect LAYER over the ford graphics
  ("how solid the water is"), not the ford's own art; effect_color_secondary
  has its own alpha (the moving dark patch layer). Secondary is
  rim-irrelevant (R1 vs R5) — a free look axis. Parked config combined
  primary 12.5% + secondary 36%.
- **F-rows — secondary-alpha sweep at primary 20% (maintainer-directed,
  to home in on the two-parameter space):** primary {21,147,167} a=51 (20%)
  fixed; secondary {49,80,14} at 0/20/40/60/80%; 100% bracket = E4 (identical
  values, existing capture). Pre-stated: rim collapsed in every row (both
  alphas rim-irrelevant per the R-column); decision axis = board
  readability. Open possibility pre-stated: if no F row reads "like
  before", the old look may depend on the shallow DARK tint color itself →
  constraint question for the maintainer, not a unilateral decision.

| row  | sec alpha | dip N/S   | outcome |
|------|-----------|-----------|---------|
| F0   | 0%        | 0.7 / 2.2 | rim collapsed |
| F20  | 20%       | 0.8 / 0.5 | rim collapsed |
| F40  | 40%       | 0.9 / 1.9 | rim collapsed |
| F60  | 60%       | 1.6 / 0.2 | rim collapsed |
| F80  | 80%       | 0.8 / 2.1 | rim collapsed |
| (E4) | 100%      | 0.8 / 1.6 | rim collapsed (same-value bracket) |

  Flipbook (ABS only): provenance/flipbook-alpha2/ (00 parked reference,
  01 F0 .. 05 F80, 06 E4 = sec100, 07 E1 = primary 2.5 bracket) — opened in
  gwenview. Captures: provenance/20261016-214210-F0-{abs,win},
  20261016-214343-F20-{abs,win}, 20261016-214526-F40-{abs,win},
  20261016-214659-F60-{abs,win}, 20261016-214843-F80-{abs,win}.png.
- **F-sweep eyes verdict (maintainer, 2026-10-16): the parked reference is
  BOTH the target saturation for the wooden tiles AND the rim to avoid;
  nothing in the sweep approaches the reference board saturation.**
  Analysis (pre-discussion): each alpha (primary, secondary) is an opacity
  knob on a veil whose color is fixed by the tint VALUES; the reference look
  is a DARK veil (parked tint = water's hue at roughly a fifth of water's
  brightness; G ratio 28.5/147 ≈ 0.19) at 12.5% + translucent patches. The
  bright water-exact tint cannot be darkened by opacity. Candidate routes:
  (A) primary = water's exact RGB ratios scaled dark (water-derived values,
  no shallow content) — rim risk unknown (identity vs similarity of the
  color match is unresolved); (B) primary stays water-exact, richness baked
  into the plank art instead (Blender); (D) primary water-exact + secondary
  as the only dark element (patched look). Discussion pending; no run.
- **Comparator tile (maintainer request):** harness-owned `wf-plank-land`
  (exact same planks.png sheet, land semantics, layer 60 — the `layer` key is
  MANDATORY on tiles, first attempt failed load with it omitted), placed
  x 18-26 / y -2..5 on native grass beyond the sculpted lake edge (x+/-16),
  three water columns from the ford edge, no touch. Console-verified placed;
  renders confirmed in the clean capture below. It persists in every future
  bake — all subsequent captures carry the raw-wood reference by design.
  A1010 captures 220613/221013 are INTERFERENCE-EPOCH SUSPECT (their block
  region reads terrain-identical); superseded by
  provenance/20261016-221440-A1010-abs-clean.png (block region 122/89/49,
  68k plank px, +32.9 mean vs pre-comparator). Note: two input sources on
  the focused game window corrupt both streams — maintainer stops typing
  during runs (2026-10-16).
- **RESPONSE-SURFACE MODEL (established 2026-10-16 evening, verified on 9
  configs to ±0.6 G/channel):** inside the water effect region the deck
  renders as deck = (1−primary_alpha)·E(tint) + primary_alpha·WATER, where
  WATER = (17,114,129) (the full-water look; R4's deck = exactly this) and
  E(tint) = a tint-VALUE-dependent endpoint: water's bright tint
  {21,147,167} → E = (159.0, 213.9, 188.7) (pale mint — the "washed out"
  look); the parked dark tint {7.75,28.5,33.25} → E ≈ (147, 109, 71)
  ≈ the planks themselves (the saturated look the maintainer verified as
  correct). Secondary alpha AND secondary color are INERT on this rendering
  (F0..F80 bit-identical; A00 = A010 = E1 = G6 within 0.1 G). Land-render
  control: the same sheet outside the effect renders (134, 95, 56) ≈
  authored (143, 102, 60) — the plank art is faithful; the wash lives
  entirely in the effect pipeline.
- **Consequence:** no alpha pair can reveal the planks — alpha only mixes
  between E(tint) and WATER. The deck look is fully determined by the tint
  VALUES plus primary alpha. NOTE: the parked tint = water × (0.37, 0.19,
  0.20) — numerically it IS an (almost) water-scaled dark tint, differing
  from water×0.2 mainly in the R channel (7.75 vs 4.2).
- **DECISIVE ROW PROPOSED (not run):** primary = {4.2, 29.4, 33.4}
  (water × 0.2 exactly) at ~12.5%, secondary whatever (provably inert).
  Pre-stated: deck expected rich-warm (dark endpoint) by the model; rim
  UNKNOWN by design — collapsed ⟹ the rim trigger tolerates water-scaled
  values and the fix is found; returns ⟹ the rim requires water-exact tint
  and the look/rim goals conflict inside effect_color → art route (B): keep
  the effect water-exact and bake saturation into planks.png (paper
  pipeline). This row changes ONLY the R channel vs parked (7.75 → 4.2),
  isolating whether R matters to the rim trigger.
- **L-FAMILY (layer_group=nil on the registered ford, single-variable vs L1's
  base):** L1 (parked tint): rim flips DARK→BRIGHT (touch 125.7/126.6 vs
  row2 111; dip −17/−15) AND the deck renders a FLAT NEUTRAL GRAY
  (197.2, 197.1, 197.0, warm px 0.4%) — reproduced on a fresh capture
  (224527) — an anomalous half-broken render state. L2 (water x0.2): deck
  IDENTICAL to in-group C20 (128.5, 110.8, 78.0), rim 20.6/21.8 == C20's
  rim. L3 (water exact): deck ≈ in-group mint blend (141.7, 201.9, 181.4),
  rim ~0.8/2.0. => for the REGISTERED ford, layer_group does not gate the
  render; the gray appears only with the parked tint+sec at no-group.
- **D-FAMILY (unregistered probe tiles, dark sheet, water-exact tint a=0):**
  bare (no layer_group): FAITHFUL dark art (94.7, 67.3, 38.6) AND no rim on
  adjacent water (114.8 vs clean 115.8). D2 (+layer_group="water" ONLY):
  WASHED (93.7, 167.7, 160.0 — G/B pushed, R art-retained) AND rim present
  (105.4 vs clean 115.8, north side; south side none — asymmetric, not yet
  resolved). D3/D4 (+merges / +is_foundation): ≈ D2, no added effect.
- **SYNTHESIS:** the water treatment (G/B veil) and the neighbor-shore rim
  toggle TOGETHER. For an UNREGISTERED tile the toggle is layer_group="water";
  for the REGISTERED ford (water_tile_type_names member) the treatment is ON
  regardless of layer_group, and its intensity tracks the tint deviation
  (C-ladder). The registration axis itself is UNTESTED (catalogue #9 never
  ran) — it is the remaining hypothesis for a faithful-deck + no-rim state.
- **BAND-LABEL CORRECTION (regime):** py = 800+(y−2.5)·32 gives N deep =
  tile row y −9 (not −11..−10), N row2 = y −4, N touch = y −3, S touch = y 7,
  S row2 = y 8, S deep = y 10; earlier in-file row labels were off.
- **Rendering-channel facts for the "under-water deck" design (2026-10-16):**
  the piling art entry is the ford tile's OWN transition (to_tiles = water
  family) and its pixels draw ABOVE the water rendering of the boundary cells
  it covers (this is what made the old opaque composites hide the
  pre-darkening); ordering inside the entry is background-below-art
  (background_enabled/overlay_layer_offset, the parked shadow work). The
  semi-submerged pole look is carried by the strip's spec ramp through the
  effect map (= the project's wetness-data mechanism). "Platform tile" is a
  Space-Age surface concept — conferencing no above-water rendering on nauvis;
  the above-the-veil channels on a tile are: transitions (BOUNDARY cells
  only), decoratives/entities (script placement — banned by round 9), and
  tile-layer ordering. There is no known per-tile mask that modulates a tile's
  OWN water effect in 2.1 — the effect map is transition-bound. Consequence:
  the deck interior cannot ride the above-veil channels; the interior veil is
  tunable only by tint (C-ladder), and the boundary has the proven
  pieces-with-mask machinery.
- **MAINTAINER RULING: `is_foundation = true` stays** — per the maintainer
  it is what lets the game remember the tile underneath (the base water tile
  continues to exist under the ford). NOTE: the shipped prototype docs leave
  this field's description EMPTY (prototype-api.json) — the under-tile
  semantics are not verifiable from available docs; today's measurements are
  consistent with keeping it (render-neutral, rim-neutral). Fixed constraint.
- **THE SHADER-OVER-TILE GATE (measured):** the water shader treatment
  requires `effect = "water"` (necessary, not sufficient — the unregistered
  groupless probe tile renders faithful art WITH effect="water") AND
  membership in the water rendering system, which the engine accepts via
  EITHER `layer_group = "water"` (D2 probe: bare+group = veiled) OR
  `water_tile_type_names` registration (L2/L3: registered ford, layer_group
  = nil, STILL veiled). The ford currently holds BOTH (the group inherited
  silently in the deepcopy; the registration is our land-side line).
  Removing either alone does not disable the shader; only leaving both does
  (never run — would also remove the required under-water look).
- **CHECKER PROBES (maintainer-directed, 2026-10-16): does the water beneath
  render through art alpha, with is_foundation set?** Two identical in-lake
  tiles (quadrant checkerboard: 50% alpha-255 planks, 50% alpha-0; effect
  omitted; foundation per the everything-foundation ruling) at y 12..15.
  RESULT: **NO — alpha is flattened.** Both blocks render (143.8, 101.6,
  60.2) == authored planks exactly, warm 100%, teal 0% in every cell; the
  alpha-0 quadrants draw as opaque RGB. The remembered under-tile does not
  show through transparent tile pixels. Also: effect-omitted in-lake tiles
  carry NO shore rim on adjacent water (rows above/below the blocks are
  normal 112-115 G). A plain no-effect block farther south read dark and
  uneven per row — re-check minutes later shows the darkness moved: CLOUD
  SHADOWS, a positional artifact (the stable blocks barely moved). For
  future fair comparisons: cloud shadows drift over the scene; judge blocks
  or use captures where the reference region is unshadowed.
- *Next axis if no primary-alpha value satisfies the eyes:* the secondary
  rides at full alpha ({49,80,14} olive) — its wave patches may dominate the
  board look; follow-up would sweep secondary alpha (F-rows).
- *Interpretation:* **alpha is not the trigger** (12.5%→100% all collapse
  with water rgb); **the secondary is not the trigger** (parked and water
  secondary both collapse). **The primary effect_color RGB identity is the
  trigger**: R0↔R1 differ only in primary color values (same 12.5% alpha,
  same secondary) — rim 21.1/20.9 vs 0.4/0.3. Two-way flip satisfied within
  one capture basis. The maintainer's "use the water effect_color" hypothesis
  is supported at every alpha tried. Deck-mid warm counts: R0 140k, R1 77.7k,
  R2 84.5k, R3 83.6k, R4 83.5k, R5 84.6k, R6 84.1k — **internal
  contradiction with the alpha model of deck washing** (12.5%-alpha rows
  classify similar/less warm than 50%+ rows) — pixel deck-visibility is
  classifier-confounded under the teal wash → **eyes check requested**.
- *Eyes checks open (maintainer):* (1) is the deck visible at R1/R5
  (water rgb @ 12.5%)? — R1 is the live window state; (2) at R2/R3 (50% and
  opaque) is it gone? (3) does the water effect overpaint visibly on the
  ford at 12.5%? (4) which satisfies all three goals → final choice.
- *Revert per row:* git rollback (config left on R6 at sweep pause; parked
  snapshot untouched in data-updates.lua.parked).
- *Capture provenance (never overwritten, .cache/ford-factory/provenance/):*
  R0: 20261016-205039-win, 20261016-205228-abs (+205208-abs-superseded);
  R1: 20261016-205248-win (aborted attempt), 20261016-210245-win,
  20261016-210451-abs; R2: 20261016-205420-{win,abs}; R3:
  20261016-205553-{win,abs}; R4: 20261016-205726-{win,abs}; R5:
  20261016-205859-{win,abs}; R6: 20261016-210032-{win,abs}. Older session
  captures copied into provenance by basename (ford_b1_layer3, ford_b2_nofound,
  ford_b3_watermask, ford_parked_restore, ford_parked_reopen, ford_notrans).

**#8 — transitions restore: water_to_out_of_map_transition**

- *What/how:* restore the clone-inherited `tiles.transitions` entry lost when
  transitions were set to nil (independent of the piling entry, which stays
  parked).
- *Intent:* weak prior — whether the empty-transitions state participates in
  region edge computation.
- *Expectation (pre-stated):* decision rule; weak prior acknowledged.
- *Revert:* git rollback.

**#9 — deregister "water-ford" from water_tile_type_names**

- *What/how:* remove the table.insert in data-updates.lua's land-side
  registration block.
- *Intent:* the registration is our own code delta; vanilla water IS in the
  list and draws vanilla land banks — the test asks whether list membership
  contributes any rim component. Weak prior (no land tiles adjacent on the
  test map), kept for delta-space completeness.
- *Expectation (pre-stated):* decision rule.
- *Note:* deregistration is a functional change for the land-side join; any
  observation is scoped to the water-side rim only.
- *Revert:* git rollback.

**#10 — observation-enriching: vanilla reference patches in the test world**

- *What/how:* extend control.lua's painted region with reference islands —
  e.g. a water-shallow strip and a landfill strip, each surrounded by water —
  same bake, same capture.
- *Intent:* anchor the rim signature against vanilla: does the water effect
  rim next to water-shallow/landfill in vanilla? Calibrates both the
  measurement and the "correct vanilla behavior" boundary in scope §4.
- *Expectation (pre-stated, before capture):* vanilla landfill → rim present
  (vanilla shore look); vanilla water-shallow → unknown, this is the anchor
  being measured; the ford signature is then judged against these.
- *Status:* proposed; runs only after the reference-frame-intervention ruling
  (also affects the save/scenario, so extra revert care: control.lua change
  must be staged/reverted with the save).
- *Revert:* git rollback of control.lua + save regen.

**Combinations:** none pre-declared; pending the combination ruling (a
pre-declared combination would enter as its own unit with the same fields).

Standing constraint (maintainer, 2026-10-16): while the ford clones water,
no water-shallow values are used anywhere in the ford config; the parked
translucent wash is the known violation, resolved by the #7 sweep.

Provenance note for #11: maintainer-relayed input from the Factorio modding
Discord (a moderator making modded lava via a water-shallow clone injects
its tile into every other tile's water-shallow transitions — "WHY DO
TRANSITIONS WORK LIKE THIS"); relevance to this investigation acknowledged
as uncertain by the maintainer.

**#11 — ribbonia-style: inject ford-directed transition copies into every
tile that transitions to water**

- *What/how:* post-clone (data-updates) pass over data.raw["tile"]: for every
  tile with `transitions`, deepcopy each transition whose `to_tiles` include
  "water", retarget the copy to {"water-ford"}, append (the relayed snippet's
  mechanism). Ford's own transitions stay parked.
- *Intent:* vanilla practice shows shore/bank transitions are declared on the
  OTHER tile; a custom water tile gets none unless injected. Tests whether
  the ford's rim involves missing transition declarations. Cross-reference:
  the water_tile_type_names registration (#9) may already provide this
  mechanism via the base global — the manual injection is the explicit path.
- *Expectation (pre-stated):* on the current test map (ford surrounded by
  water; water itself declares no water-targeting transitions) the rim
  measurement is expected UNCHANGED. Rim persisting unchanged ⟹ missing
  transition declarations acquitted as the rim's source; any change ⟹ the
  transition machinery is involved after all. The injected copies gain their
  full effect only once land adjacency exists (#10 reference patches).
- *Revert:* git rollback.

## Baseline & measurement regime

- Scenario: spawn {0.5,4.5} on the ford; ford painted x −14..14, y −2..6;
  water elsewhere within x/y ±16; seed 4242; save regenerated per run by
  bisect-run.sh (mind the scratch-lock race: the prior windowed game must be
  fully dead first).
- **Lighting locked:** the view scenario sets `always_day = true` and
  `daytime = 0` (maintainer direction, 2026-10-16) — no day-cycle variance.
- **Absolute-coordinate basis (compliant measurement regime, live since the
  #7 sweep):** one-shot console `game.take_screenshot{position={0,2.5},
  zoom=1,resolution={2560,1600},show_gui=false}` → 32 px/tile,
  py = 800+(y−2.5)·32; bands (y px): N deep 432–463, row2 592–623, touch
  624–655; S touch 944–975, row2 976–1007, deep 1040–1071; deck-mid 688–752
  (warm count, not water G). Window captures remain only as the
  maintainer-view recorder.
- Reference levels on the absolute basis (noon, R0): rim present ≈ dip 21;
  collapse threshold ≤4 stands (observed collapsed range 0.3–2.2).
- **Provenance law (maintainer, 2026-10-16): screenshots are evidence —
  unique never-overwritten names under .cache/ford-factory/provenance/, each
  result row links its capture by name.**
- Calibration (window basis): reproduces the prior session's recorded
  numbers within ~1.6 G — this establishes the prior numbers were real
  captures; their conclusions remain discarded.

## Vanilla edge-sprite survey (maintainer-directed, 2026-10-16)

Question: what does vanilla use to mask the water-edge bleed? Fact sheet
(asset + data survey only, no bake):

- `graphics/terrain/water-shallow/` holds the edge family: `-side.png`
  (384x256 = 6 templates x 4 rotations of 64px), `-inner-corner.png`,
  `-outer-corner.png` (same 6x4), `-u.png` (64x256, 1x4), `-o.png` (64x64,
  single island). All scale 0.5; side+corners count=6, u/o count=1.
  Copies + 2x contact sheet in provenance/asset-study/.
- Pixel content: side/corner sprites carry the SHALLOW water color itself
  (opaque mean 70.8,98.0,91.3 vs base art 71.6,98.3,91.3 - same tone, not a
  contrasting band) with alpha erosion concentrated at the meeting edge
  (outer 8px ring 67% opaque vs tile center 98%): alpha-soft edge pieces.
- Referenced exactly at tiles.lua 1192-1226: inside the `water-shallow`
  tile's `variants.transition.overlay_layout` (entries inner_corner,
  outer_corner, side, u_transition, o_transition). water-mud carries the
  identical structure at 1280+ (its own art). Non-water tiles use the same
  mechanism: stone-path (~2003), tutorial-grid, concrete, refined-concrete
  each have overlay_layout with their own -side/-corner sheets.
- Doc (prototype-api.json): overlay_layout "Overrides the `overlay`
  definition inside `layout`" - a TileTransitionVariantLayout: the tile's
  own edge pieces, rendered where it borders other tiles.
- Plain `water` and `water-green` have NO such pieces: main variants +
  `empty_transitions = true`; their only transitions are out-of-map ones
  using `masks/water-edge-transition.png` - a grayscale (~64/255) MASK
  sheet (side_x=128, outer_corner_x=64, u=192, o=256) used with
  `mask_enabled`, `apply_waving_effect_on_masks`,
  `apply_effect_color_to_overlay` - a motion mask, not a shore edge.
- `transitions_between_transitions` for shallow/mud: only the out-of-map
  to-water sheet; nothing else between water family members.
- Vanilla effect_color parameterization of the water family (context for
  our calibration): water {21,147,167} full-alpha; water-green {49,80,14}
  full-brightness unscaled; water-shallow and water-mud:
  {31,114,133} x 0.25 @ alpha 0.125 - i.e. a UNIFORM scalar 0.25 on the
  water rgb at 12.5% alpha, the same shape as our L3 config.
- **Implication (analysis, not yet measured): our ford defines no edge
  pieces at all (empty transitions), so nothing alpha-softs its boundary -
  vanilla shallow would paint these side/corner sheets there. The ford
  could adopt the shallow structure (`variants.transition.overlay_layout`
  with side/corner sheets of plank-toned art) or have its boundary pieces
  reuse these vanilla sprites; whether overlay art can carry our tint
  (apply_effect_color_to_overlay exists as a knob on transition defs) is
  unknown until tested.

## Three-probe set (maintainer-directed, 2026-10-16 late): boards-visible tint,
## shallow-style edges, pilings boundary

Reference for "boards visible": the in-scene unveiled blocks (plain, no
effect; land comparator) measured in the SAME capture. Target: rough 80-90%
per channel, halo artifacts accepted by the maintainer.

Model (tonight's response surface, two-point linear fit verified on C20/L2):
deck(t,a) = (1-a)*(E0 + S*t) + a*WATER with E0 = (140, 84.9, 41.2),
S = (0.907, 0.877, 0.883) per tint unit, WATER = (17, 114, 129).
Predictions:
- T1 black tint @ a=12.5%: deck (124.6, 88.6, 52.2) = ratios 0.94/0.92/0.94
  (lum 0.93 of plain) - just above the 0.9 band, most uniform row; MAX halo
  (tint maximally non-water).
- T2 black @ a=5%: deck (133.9, 86.3, 45.6) = 1.01/0.90/0.84 - warm golden
  boards, R above band (brighter than unveiled), G/B in band.
- T3 black @ a=25%: deck (109.3, 92.2, 63.1) = 0.82/0.96/1.17 - R in band but
  G/B pushed waterward; predicted least "planky".
Selection criterion (pre-stated): nearest to the 0.8-0.9 band with G
prioritized (the green leak is the wash signature). Prediction: T1 wins.

- T-family PROBE: intent = tint/alpha-only path to boards-visible deck;
  expect T1 halo strong (black tint, dips >= parked's 21 expected to grow),
  observe deck ratios + N/S touch dips.
- PROBE B ("shallow approach"): chosen T-row + ford variants.transition.
  overlay_layout = vanilla water-shallow sheets verbatim (side/corners/u/o).
  Expected from the mod's own history (parked header): "pale halo on
  bordering water" - the boundary gains vanilla's pale fringe; the dark
  neighbor-row rim is predicted to PERSIST (overlay paints the ford's own
  edge only, not the neighbor water). Gameplay untouched (no new tiles).
- PROBE C (pilings): chosen T-row + pilings transition re-enabled (parked
  sheet+mask, transparent backgrounds on the deep-water clone). Expected:
  piling posts render at the water-side seam covering part of the touch
  band; neighbor rim rows may still measure dark/bright OUTSIDE the piece
  footprint; eyes criterion = boundary reads deliberate.
Observation rows (captures under .cache/ford-factory/provenance/, ABS basis):

- T1 233923: deck (100.9, 90.5, 65.5), rim 21.4/19.5 (win-basis line 25.5/26.9
  is a different pixel mapping, not an inconsistency). Black tint @12.5%.
- T2 234056: deck (109.2, 96.3, 69.0), rim 21.4/19.6. Black @5%. CHOSEN BASE.
- T3 234228: deck (86.9, 80.7, 59.8), rim 21.4/19.6. Black @25%.
- MEASURED FACTS beyond predictions: (1) the E-model does NOT extrapolate to
  black tint (T1 deck R 100.9 vs predicted 124.6) - the linear response
  surface is interpolation-only; measured values rule. (2) The rim is
  alpha-INDEPENDENT across 5/12.5/25% (all three rows ~21.4/19.5, parked
  level) - the primary-alpha knobs change the deck, not the halo; halo tracks
  tint deviation only. This kills the earlier "T2 mildest halo" reasoning
  (win-basis line misread); all three T rows share the max-deviation halo.
- Ratio reference caveat: the plain block is cloud-shadowed in these caps
  (112.1 const across the three caps - suspicious; land 132.7 stable); the
  land block was used as the unveiled reference. Ratios (R/G/B vs land):
  T1 0.76/0.94/1.22; T2 0.82/1.00/1.28; T3 0.66/0.84/1.11. B overshoots in
  ALL rows: the water effect adds warmth(blue+yellow) to the deck regardless
  of tint; no black-tint config reaches B<=0.9x-land. Eyes decision pending
  between T1 (darkest uniform) and T2 (brightest boards).
- TB (T2 + vanilla shallow overlay_layout): BAKES AND RUNS; rim 21.8/19.4
  (= T2, as predicted - overlay does not touch neighbor rows). The fringe
  renders but SPARSELY: 1.3% of the ford's north edge band changed vs T2,
  changed-px mean (82.6, 112.3, 98.8) = shallow-pale art confirmed present.
  GUESS (untested): pieces are sparse because the ford's neighbors are the
  water transition group (same group as the ford clone) - the tile-owned
  overlay system stamps pieces at group boundaries, and water-to-ford is
  same-group, so almost nothing qualifies. Making the B probe meaningful
  likely needs the ford outside the water group for this row - ONE config
  change, not yet tried.
- TC (T2 + pilings transition re-enabled): pieces RENDER on the water-side
  seam: 19-21% of the touch bands changed vs T2, changed-px mean (18, 82, 91)
  (dark post/water art); the ford's outer edge band shows WATER-COLORED
  changed px (16, 112, 127) - the transparent piece backgrounds let the
  remembered under-water show at the seam (transition mechanism, unlike
  variant alpha which flattened). Rim dip 21.5/19.5 = unchanged: the halo
  persists BETWEEN the posts (pieces cover ~20% of the band). Bakes:
  captures 234429 (TB) / 234622 (TC); LIVE WINDOW = TC config.
- Next per maintainer: eyes-verdict on the three alternatives, THEN the
  combined-path conversation.

## U-family + re-based boundary rows (maintainer feedback after eyes: deck OK,
## lighten toward under-water, not washed; halo seen in all screenshots)

Intent: more water presence in the deck without the mint wash; then the two
boundary treatments re-based on the chosen grey row, plus an isolation
control for the suspected group-merge suppression of the overlay stamps.
Expectations honestly UNKNOWN for the grey direction: the response surface
does not extrapolate into the near-black region (T1 deviation -24 R / +13 B),
so U rows MAP the surface; halo expected to persist (grey tint remains far
from water color; rim was alpha-independent).
- U1 grey 10% (25.5) @ a5%; U2 grey 20% (51) @ a5%; U3 grey 35% (89.25) @ a5%.
  Deck sample + land reference measured per capture; halo bands unchanged.
- UB1: chosen U tint + transition_merges_with_tile = nil (no overlay) -
  isolates whether the group-merge removal itself changes the halo/edges.
  (Discipline note: UB2 changes two things vs the U control - the merge
  removal is argued as part of the minimal working "shallow approach"
  package, since overlay alone measured 1-2% edge coverage = no-op.)
- UB2: UB1 + vanilla shallow overlay_layout (the shallow approach, working
  version). Expected: fringe stamps appear along the ford boundary; rim rows
  may still read dark between stamps.
- UC: chosen U tint + pilings transition re-enabled (as TC, re-based).
Selection rule (pre-stated): maximize water-lean without wash - prefer rows
where deck B rises toward water (69 -> higher B) and R does not rise with it
(mint signature = R and G rising together); eyes verdict final.
Observation rows:
- BASIS CORRECTION: the runner prints the ABS measure FIRST, win second; the
  earlier T/TB/TC table quoted the WIN-basis values. Correct ABS rims:
  T1 25.5/26.9, T2 25.4/26.9, T3 25.5/26.9, TB 25.6/26.9, TC 25.5/27.3.
  Historical sweep numbers' basis now ambiguous; tonight's comparisons are
  ABS-consistent. Conclusions unchanged (rim alpha-independent across T rows).
- U1 235336: deck (124.8, 111.9, 84.6) vs-land 0.94/1.16/1.57, rim 20.9/22.5.
- U2 235509: deck (141.0, 128.1, 100.8) vs-land 1.06/1.33/1.88, rim 16.8/18.2.
- U3 235642: deck (164.7, 151.8, 124.5) vs-land 1.24/1.58/2.32, rim 10.4/11.8.
- MEASURED: grey tint lightens the deck via the WASH (all channels rise above
  the unveiled reference, G/B inflating fastest - the mint structure), while
  the halo shrinks monotonically (rim tracks the tint's RGB distance to
  water; the C-ladder law extends to the grey axis). Therefore the grey
  direction cannot deliver 'under water but not washed' by itself: the wash
  arrives before the water-lean is strong. Eyes choice between T2 (dark,
  dry, boards-dominant) and U1 (lighter, water-leaning, borderline wash);
  U2+ rejected as washed. NEXT: re-base UB1/UB2/UC on the eyes-picked row.

## UF0 mechanics row (maintainer directive: prove the halo-hiding mechanic
## before any art)

Intent: prove that an outward, ford-owned `transitions` entry (to_tiles =
water family) can fully cover the halo band on the water side, using a FLAT
water-color fill sheet (17,114,129, fully opaque) - no authored art, no
piling art; geometry composed to the existing entry layout's dimensions.
Base tint: T2 (black @5%) chosen for maximal halo contrast (25.4/26.9 ABS);
the mechanic is tint-independent.
Expectation (pre-stated): Ntouch/Stouch band water-classified px remain,
band G rises to clean-water level, rim dip drops 25.4/26.9 -> ~0-6. If the
dips persist >10 or the band stays dark, the stamp does not reach/cover the
band and the mechanic is refuted for halo-hiding. Render order assumed:
transition stamps draw above the water effect's rim paint (TC precedent);
if the cover renders BELOW the rim, dips persist with full coverage numbers
- that outcome would isolate a render-order problem instead.
Observation (capture 20261017-001029-UF0-abs.png, gwenview shown 2026-10-17):
- **MECHANIC PROVEN.** Rim dip 25.4/26.9 (T2) -> **1.3/2.8**; band means
  Ntouch 107.4 / Stouch 108.2 G = clean-water level (Ndeep 107.3); band
  water-class share 100%; 78% of both touch bands' pixels changed vs T2
  (the fully-opaque stamp footprint; remainder = unchanged-by-chance/edges).
  The outward, ford-owned transitions entry fully covers the halo band on
  the water side; the stamps render ABOVE the rim paint (render-order
  assumption held). Flat filler color (17,114,129) was invisible-as-filler:
  the ONLY visible change vs T2 is the dark rim band vanishing.
- Consequence: any outward-stamped art now rides in the proven slot. Options
  on file: (a) shallow-derived composite sheet (needs the composer rebuilt,
  tool absent from repo); (b) apply_effect_color_to_overlay = true on the
  entry to tint stamped art with our effect color (property exists on
  transition defs, untested on regular entries); (c) authored waterline art.
- The pilings entry itself remains parked and unmentioned in this row (its
  SLOTS/geometry served only as the layout reference, per maintainer
  instruction).

## V-family: alpha ladder for water-slosh on the deck (maintainer accept of
## UF0, 2026-10-17)

Intent: more animated water over the ford deck; cover row (UF0 mechanism)
kept at every alpha so the halo stays hidden; tint stays black (the accepted
deck color direction), one variable = primary alpha.
Rows: V1 a=12.5%, V2 a=25%, V3 a=40% (UF0 = a5% already captured).
Expectation: deck darkens with alpha (measured T-family: a5 (109.2,96.3,69)
-> a25 (86.9,80.7,59.8), curve NONLINEAR vs linear blend - these rows map
it); halo stays ~0-6 under the cover at all alphas; eyes criterion = slosh
visible, boards still readable, no mint wash.
Observation (captures 001546 V1 / 001719 V2 / 001852 V3, gwenview shown):
- deck curve vs alpha (black tint, cover present): a5 UF0 (109.7,99.8,72.9)
  tex-std 14.5; a12.5 V1 (101.4,93.7,69.1) 12.6; a25 V2 (87.3,83.4,62.9)
  10.6; a40 V3 (70.5,70.9,55.2) 11.1. Monotone darkening, texture flattens.
- rim under cover creeps with alpha: 1.3/2.8 -> 2.7/2.4 -> 5.9/4.7 -> 9.9/7.7
  (ABS). Still hidden-grade through a25; mild at a40. The T-family's
  alpha-independence referred to the UNCOVERED rim (25.4-25.5 flat); with the
  cover the residual dip grows slightly - seam-edge interaction, small.
- Eyes pending: which alpha reads as 'water sloshing, boards readable'.

## W-family: joint axis per maintainer hypothesis (2026-10-17)

"Deck must not darken; more alpha = more slosh; lightness restored via an
intermediate tint." Diagnosis confirmed by measurement: at black tint the
tinted-art term is dark-warm (E = (114, 95.4, 65.9) from T2/T3 inversion),
and alpha lifts darken the deck non-linearly (V2 G 83.4 vs linear-predicted
100). Grey tint raises E ~uniformly (U-family slopes ~0.9/unit); the mint
signature comes from tint GREEN (water G 147), avoided by neutral grey.
Rows: grey 10/15/20% (25.5/38.25/51) at a=25% (V2's slosh), cover retained.
Expectations: W1 lightest non-washed stop; W2 borderline; W3 wash. Deck
criteria: not brighter than unveiled planks in R; G/R not mint-leaning;
slosh visible; halo stays hidden (cover). If hue reads too warm at the
bright stops, a cool-grey follow-up (B-boosted) is the next single variable.
Observation (captures 002240 W1 / 002413 W2 / 002546 W3; vs V2 anchor):
- W1 grey10 a25: deck (102.9, 99.0, 78.5) vs-land 0.78/1.03/1.46, tex 12.3,
  rim 1.8/1.3.
- W2 grey15 a25: deck (111.0, 107.1, 86.6) vs-land 0.84/1.12/1.61, tex 14.4,
  rim -0.0/-0.3.
- W3 grey20 a25: deck (119.2, 115.3, 94.7) vs-land 0.90/1.20/1.76, tex 16.9,
  rim -2.4/-2.1.
- MEASURED: the maintainer's joint fix works. At V2's slosh the deck lifts
  monotonically with grey; NO row exceeds unveiled brightness in R (the
  pre-stated wash criterion never trips); G stays water-glazed (1.03-1.20)
  while the hue stays warm-neutral (G/R ~0.96 - no mint at any stop). NEW
  fact: art texture-std GROWS with grey tint (10.6 -> 16.9 across W) - more
  tint = more art contrast under the veil; slosh and texture rise together.
  Rim stays hidden at all stops; W2/W3 lean fractionally BRIGHT-edge
  (negative dips, the L1 family at tiny scale) - small, watch it.
- Eyes pending: W1 vs W2 vs W3 for the frozen deck look. Unification talk
  (piling artwork x cover slot) queued after the pick.

- **DECISION (2026-10-17, maintainer): deck look frozen at W3 for now** -
  tint (51,51,51) grey-20% @ alpha 63.75 (25%), flat-water cover in the
  outward slot, 'best balance of board color interest and visible water
  shader'. The full knob/pulley reference now lives in docs/ford-knobs.md
  (measured curves, laws, constraints, current settings).

## X-family: option-1 stack test (maintainer directive: no new sheets yet,
## 2026-10-17)

X1 = W3 base + piling entry restored as a SECOND entry (flat-cover entry
first, piling entry second, piling art + mask as parked). One variable vs W3:
the piling entry. Answers: does the piling entry render ABOVE the flat cover
(posts visible), and does the cover keep the halo hidden under the posts?
X2 = X1 + apply_effect_color_to_overlay = true on the PILING entry only
(cover unflagged - the flag must not tint the seal). One variable vs X1: the
flag. Answers: does the knob work on regular entries, and what does it do to
the posts (expect a grey glaze toward our (51,51,51) tint if it works).
Expectations (pre-stated): X1 rim ~W3 level (-2.4/-2.1) with posts adding
~20% warm px to the touch bands (TC's footprint); if posts are INVISIBLE in
X1 vs W3 diffs -> the cover renders above the entry order assumption fails,
next step would be entry-order swap. X2: posts shift toward grey if the
knob works; cover stays flat-water (measure its band mean unchanged).
Observation (X1 004953, X2 005206) - plus two process items:
- RELOCATION (maintainer directive): the test bench moved into the mod -
  mods/water-ford/testing/{scratch,wf-piling-viewer}; runner/bake/save paths
  updated; first X-bake verified from the new location. Provenance captures
  stay in .cache per the standing rule. Sweep-row lesson recorded: the X
  patch originally inserted entry #2 at a stale absolute index after the
  string rebuild (corrupted collision_mask; the mod failed to load; saves
  vanished because bake-save deletes-then-regenerates and regeneration
  aborted) - fixed by anchoring insertion on data:extend. Never reuse
  indices into a rebuilt string.
- **X1: stacking REFUTED - last entry wins.** Rim 16.7/18.1 == the UNCOVERED
  grey-51 rim (U2 measured 16.8/18.2 on the same tint): the flat cover's
  seal is gone. Touch bands re-rendered 75-79% vs W3 (the piling entry DID
  stamp). Two entries sharing group + to_tiles: the second replaces the
  first; transitions are keyed, not accumulated (mechanism guess, consistent
  with all numbers).
- **X2: the flag WORKS.** apply_effect_color_to_overlay = true on a regular
  entry tinted the stamped pieces toward our effect color: changed-px mean
  (29.1, 86.0, 93.9) -> (17.8, 68.4, 72.5) (teal-dark, water-classified, so
  the ABS dip metric now reads them: 20.1/22.1). The knob functions on
  regular entries - stamped art can auto-tint with the deck tint.
- OPTIONS update: option-1-as-two-entries is dead; still alive WITHOUT new
  art: X3 = give the COVER entry a DIFFERENT transition_group id (if keys
  are per-group, both entries render - posts over sealed water). Otherwise
  the path is option 2 (single composed sheet, opaque water-composite
  background under the posts - the original Ford-A design).

## P-family: the composed sheet (maintainer direction after X1/X2, 2026-10-17)

X1 refuted stacking (last entry wins); X2 proved the tint flag works. Now
the single-entry composite: sheet = flat-water (17,114,129) background
alpha-composited under the EXISTING piling frames (every frame opaque;
no new art authored - a paste, the original Ford-A opaque-composite design),
mask kept. P1 = composite, art as-authored. P2 = composite +
apply_effect_color_to_overlay = true (the underwater-tinted variant X2
previewed). Base = W3 (grey-20% a25%).
Expectations: rim ~W3's covered level (-2.4/-2.1) since the bg seals the
band; posts visible over it (~20% band footprint, TC precedent); P2 posts
shift teal-dark per X2 and enter the dip metric; the bg in P2 stays
unflagged? NO - the flag on the entry tints the WHOLE stamped art including
the background: P2's background will NOT stay flat-water - expect the cover
seal to shift color in P2 and the dip to move; P1 is the control that should
hold the seal.
Observation (P1 010056, P2 010229 - gwenview shown with X1/W3 refs):
- **P1: the composed sheet WORKS.** Rim -0.1/0.9 = W3's covered level
  (-2.4/-2.1): the flat-water background under the piling frames seals the
  band in a SINGLE entry; posts render over it (15-16% band footprint;
  changed-px mean (57.3, 89.0, 89.0) - the post art reads slate/steel-toned,
  warm share only 1-3%, so the posts are NOT warm wood in color.
- **P2: the flag tints the WHOLE entry's art, background included.** 35% of
  the band shifted vs P1 (semi-transparent/edge px too), changed-px mean
  (22.9, 89.1, 99.2); the seal color leaves flat-water and the dip rises
  (10.6/12.3) - exactly the pre-stated risk. Consequence: tinted posts and
  an untinted seal cannot coexist on ONE entry under this flag; if tinted
  posts win the eyes, the untinted-seal requirement needs either a second
  entry under a different transition_group (the keying lesson from X1) or
  pre-baked tint in the art itself.
- The composite asset: mods/water-ford/testing/wf-piling-viewer/graphics/
  pilings-composite.png (flat (17,114,129) under the existing 3200x2368
  piling frames; no authored art).
- Eyes pending: P1 vs P2 for the boundary look; W3 remains the deck base.

- **DECISION (2026-10-17, maintainer): P1 is the committed boundary row** -
  the single-entry composed sheet (flat-water bg under piling frames, no
  flag) on the W3 deck. P2's tinted variant set aside: the flag tints the
  whole entry including the seal background. Shadows re-visit announced as
  the next topic (not yet scoped: cloud vs cast - ask).

## STATE AT COMPACTION (2026-10-16 late evening)

- Decision point: the maintainer is taking the investigation "in a new
  direction" — not yet specified. Everything below is fully recorded; resume
  from this file. **Do not assume the bisect framing continues** — check with
  the maintainer first.
- Disk state: working-tree `mod/data-updates.lua` = L3 config (water-exact
  tint at 12.5%, layer_group nil? — NO: L3 kept layer_group; only the tint
  differs from parked). The parked baseline is `mod/data-updates.lua.parked`
  (restore = cp). Nothing committed; the committed-baseline prerequisite
  (open item 3) never ran.
- Live game: L3 config, noon-locked, with the harness reference blocks in
  the world (land comparator, plain, checker pair, dark + D2/D3/D4 probes).
- The L1 gray anomaly and D2's asymmetric rim are OPEN anomalies (recorded).
- Maintenance rules added this session: screenshots absolute-coordinate
  (AGENTS.md); `is_foundation=true` stays on the ford (binding); the
  maintainer stops typing during runs (two-input corruption); screenshots
  are provenance (unique names, never overwritten, linked per result).
- Suggested next calibration if the new direction re-enters this problem:
  catalogue #9 (deregistration) remains the untested axis; route-U is
  disqualified by the gameplay constraints (fish/cargo waterways +
  under-water look).

## Open items (ordered)

1. **Eyes checks on #7** (deck visibility per alpha row; water overpaint
   visibility; final value choice). R1 (water rgb @ 12.5%) is the live
   window state.
2. Final-value collision with the standing constraint: water rgb is
   confirmed; if the chosen row keeps a shallow-inherited alpha (12.5%),
   does the no-shallow-values constraint apply to alpha levels too, or only
   to color/tint values? Ruling needed.
3. Committed-baseline prerequisite: park the current state as a portal-clean
   commit so reverts become git rollbacks (currently file snapshots).
4. Rulings still open: combination rows; reference-frame interventions
   (affects #10).
5. Remaining catalogue entries (#4 subgroup, #5 variants, #6 mask,
   #8 transitions, #9 deregistration) — now LOW priority: they were delta
   candidates against a rim whose trigger is found (#7); run only if the
   effect_color mechanism fails the eyes/off→on gates.
6. The #3 live-window residue was cleared by the sweep (every row rebaked
   from a valid parked-derived config).