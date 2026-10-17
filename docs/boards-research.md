# Boards research — running notes (ford-boards arc)

Ticket: `../../inbox/produce-ford-boards-tilesets.md` (order 1, OPEN).
Scope of THIS doc: the research phase of the arc. Blender authoring happens in
a later, joint phase with the maintainer; nothing here builds or renders the
factory. Scratch/provenance: `.cache/boards-research/` (superproject scratch,
recreated from this doc).

Method + limitations (2026-10-17 session): this session is headless and the
agent cannot view images — every visual claim below is **numeric** (PIL/numpy
measurements with scripts/method noted) and the maintainer does the eyeball
review (gwenview gates exist in the ticket's verification section anyway).
References: `docs/blender-factory-laws.md` (binding), `docs/ford-knobs.md`,
`docs/shore-rim.md`, `shadows.md`.

## Question register

| ID | Question | Status |
|---|---|---|
| R1 | What IS the inherited deck art, numerically? (planks.png palette anchors, plank geometry per 64px variant, grain/shade rhythm, alpha) — deliverable (a) | DONE |
| R2 | Stone/gravel palette sources: py gravel/stone item assets + vanilla stone assets; swatch set restricted to the mid-to-light half. Is planks.png == planks-base.png today? | DONE |
| R3 | "Rich tiles" precedents: vanilla concrete + Space-Age platform tile variant layouts (sizes/counts/layers), py tile definitions; what would rich mean for the land tile (stretch goal) and could it fit the ford too? | DONE (mechanism; design open) |
| R4 | Doodad fallback mechanics (maintainer's "decal" = in-game decorative components): can engine decoratives be composed over a tile face? mapgen vs script placement; control-stage legality vs the round-9 ban; does any local mod (AsphaltPaving?) do this | DONE (+ decision point D4) |
| R5 | Vanilla concrete consult (land tile registration): is_foundation, buildable-on vs the ford's not-buildable, collision_mask, decoratives fields | DONE (+ decision point D3) |
| R6 | Light rig extraction from ford-posts.blend (read-only): sun + ambient transforms/energies relative to origin for origin-staged boards | DONE |
| R7 | W3 response check: simulate the committed water mix on candidate stone swatches (in-sprite ballast lead option) — do mid-light pebbles survive the mix with enough contrast? | DONE (model-approx; bench ABS is the final verdict) |
| R8 | What board content, if any, lives in the pilings transition frames today (P1 composite re-derivation scope, ticket c3)? | DONE (+ decision point D2) |
| R9 | Pipeline shape for boards: where boards stages slot into bake.sh stages (strips/sheet/deploy/save/view), what --twice covers, deploy mechanics | DONE (enough for planning; deploy mechanics re-checked at build) |

## Findings

### R1 — the inherited deck art, measured (deliverable (a) anchors)

Source: `mod/graphics/planks.png` (512×64, 8 variants @ 64×64, engine `scale = 0.5`).
Method: `.cache/boards-research/extract-planks.py` + `extract-r1b-r2.py` (16-level
RGB bins; Rec.709 luminance; seam = local mean-luminance dip > 12).
Extract JSON: `.cache/boards-research/planks-extract.json`.

- **Today's `planks.png` is byte-equal to pristine `planks-base.png`**
  (DECK_WASH_STRENGTH = 0 in `tools/gen-textures.py`), so the extraction below
  IS the inherited, dreamed art — untouched by any of our machinery.
- **Fully opaque** (alpha 255 everywhere) — consistent with the knobs finding
  that variant-sprite alpha is flattened anyway.
- **Layout: HORIZONTAL planks.** Every variant has 1px gap seams at fixed
  rows **15 / 31 / 47** → four courses per cell: 15/15/15/16px tall on the
  sheet (**8px per course in game**). The seam grid is invariant across all
  8 variants — variant identity comes from elsewhere.
- **Butt joints: one per course per cell on average, staggered** — detected
  joint x varies per variant (some courses show none); board lengths ≈
  16–50px on the sheet (≈8–25 game px). This stagger IS the variant's fingerprint.
- **Palette anchors (top bins, ≥50% alpha):**

| hex | rgb | L | share |
|---|---|---|---|
| #96693b | (150,105,59) | 111 | 26.4% |
| #976b42 | (151,107,66) | 114 | 21.8% |
| #997245 | (153,114,69) | 119 | 15.9% |
| #8c663a | (140,102,58) | 107 | 13.4% |
| #3e2816 | (62,40,22) | 43 | 7.7% (gaps) |

  ≈78% of all pixels sit in four adjacent warm wood tones (L 106–123); the
  single dark tone #3e2816 carries ALL the seams/gaps. Global value range
  per frame: **L(min) 43.4 … L(max) ≈ 128** — a soft-banded art with a dark
  floor well above black and a modest highlight cap.
- **Grain:** high-frequency energy 13.68–14.47 (mean adjacent-pixel delta,
  across variants ~const) — lively grain along the plank axis; variant
  midtones drift L 110.2–115.9.
- **Re-interpretation targets (for "substantially similar"):** 4 horizontal
  courses @8 game-px, seams at the same rows (possible widened re-interpretation
  for ballast — see D1), warm palette in R137–163 / G94–117 / B53–70 with the
  wood core at L≈106–123, dark gap tone ≈ L43 (no darker), highlight cap ≈
  L128 (no brighter), grain energy ≈ 13.7–14.5, per-variant staggered butt
  joints + slight tone drift.

### R2 — stone/gravel palette harvest (mid-light filtered)

Sources (extracted to `.cache/boards-research/swatches/`; method: 16-level
bins, keep L∈[64,180]): py item icons from `pycoalprocessinggraphics_3.1.1.zip`
(the SAME items the py ford recipe consumes — in-game icon color = what the
player's eye links to the ingredient), plus vanilla `graphics/icons/stone.png`.

| Family | Key swatches (hex, L) | Character |
|---|---|---|
| py gravel icon (cool grey) | #474547 L70 · #595658 L87 · #686566 L102 · #787675 L118 · #9c9288 L148 | cool, slightly blue-grey |
| py crush-stone (warm khaki) | #796b51 L108 (36%) · #887456 L118 · #957b59 L126 · #b89868 L155 | warm olive-khaki |
| py crush-gravel (warm sandy) | #baa797 L170 (26%) · #a48b76 L143 · #b29c8a L160 · #93755b L121 | warm sandy pink-grey |
| py limestone (neutral grey) | #a9a298 L163 · #b1a899 L169 · #484747 L71 | chalky neutral |
| vanilla stone icon (ochre) | #967948 L124 · #a68a55 L140 · #b5975b L153 · #c6a668 L169 | warm ochre, closest to deck warmth |

All far from the water's mint/G-dominant hue ⇒ no water-shallow violations.

### R3 — "rich tiles" mechanism (measured from vanilla data)

`data/base/prototypes/tile/tiles.lua::tile_variations_template` (lines 44–106)
builds, from ONE picture + per-size options:

- `variants.main` = list of per-size entries over the SAME spritesheet with
  **y-band layout: size-1 @ y=0, size-2 @ y=128, size-4 @ y=320, size-8 @
  y=640**; `count = #weights` (16 typical), `line_length = 16` (8 for size-8),
  `scale = 0.5`; per-size `weights` (+ optional `probability`) shape selection.
- Precedents: `grass-1` uses `max_size = 4` with weights for sizes [1]/[2]/[4]
  (tiles.lua 1327+); SA planet tiles (Aquilo/Vulcanus/Gleba/...) repeat the
  pattern (`space-age/prototypes/tile/tiles-*.lua`).
- The ford's current `variants.main = {{picture=planks.png, count=8, size=1,
  scale=0.5}}` (frozen `data-updates.lua` L58) is a legal one-entry degenerate
  of exactly this shape.
- **For the land tile (stretch goal)**: one spritesheet sliced into 16 size-1
  + size-2 + size-4 bands = vanilla-idiomatic rich tiling, no plumbing beyond
  the sheet layout. **For the ford: NOT possible this round** — rich variants
  would change the frozen `variants.main` config, and the ticket pins the deck
  as a drop-in graphics swap. Rich-ford would need a config-moving follow-up
  (D5).

### R4 — the doodad (decorative) fallback, measured against the engine

- The in-game component is the **decorative** system: prototype types
  `decorative` / `optimized-decorative` (`data/base/prototypes/decorative/
  decoratives.lua`), 812 names in vanilla, rendered in the doodad/decal layer
  over tile faces. **Vanilla already ships the exact art precedent:**
  `huge-rock / big-rock / medium-rock / small-rock / tiny-rock` (16 picture
  variations each) + sand-rock family + sand-decal / sand-dune-decal — pebble
  scatter art with per-variation randomness is a solved engine shape.
- **Placement:** mapgen autoplace decoratives fire at world generation only.
  There is **NO tile-prototype hook that spawns decoratives on placement**:
  `doc-html/prototype-api.json` contains `destroy-decoratives` and
  `create-particle` / `create-explosion` (TriggerEffect types), but
  **`spawn-decoratives` does not exist** in the prototype API.
- The route that exists: **`LuaSurface.create_decoratives`** (runtime API,
  `doc-html/classes/LuaSurface.html`) called from script on tile-placement
  events. Decoratives are persisted entities (save-data cost per placed tile),
  and decoratives do NOT participate in the tile's water effect mixing
  (sprite-level; deck art gets W3 mix, decorative sprites presumably render
  dry — untested on this tile; a runtime probe would settle it if fallback
  is pursued).
- **Control-stage legality:** `mods/water-ford/mod/control.lua` is frozen to
  the placement guard (mod AGENTS.md invariant 2; round-9 ban on scripted
  visuals). A doodad-based ballast would require a scoped control-stage
  exemption by the maintainer (D4). Removal side exists as a tile field:
  `decorative_removal_probability` (concrete: 0.25; AsphaltPaving, a local
  managed copy: 0.97 — paving deliberately cleans).
- Verdict: mechanically reachable, but control-stage + save-cost + likely
  dry-over-wet look mismatch ⇒ correctly placed as the FALLBACK behind
  in-sprite ballast, exactly as the maintainer ordered.

### R5 — vanilla concrete consult (land tile registration)

From `tiles.lua`:

| Field | concrete (L2243) | landfill (L2602) | land boards tile — proposal |
|---|---|---|---|
| is_foundation | **absent** | true | **absent** (plain flooring; D3 for maintainer) |
| collision_mask | `tile_collision_masks.ground()` | ground() | ground() ⇒ normal buildings placeable ✓ (the ford excludes buildings via its water-family mask/floor layer membership) |
| walking_speed_modifier | 1.4 | — | 1.0–1.1 (boards, not poured concrete) |
| layer / layer_group | 13 / "ground-artificial" | 60 / —(default) | 13 / "ground-artificial" (border draw order vs the ford's layer 9) |
| decorative_removal_probability | 0.25 | — | 1.0 (boards sweep the ground clean) — D3 |
| map_color | (122,122,122) | (57,39,26) | warm plank tone from the R1/R2 spec |
| trigger_effect | (concrete: none) | create-particle dust | none |

`default_cover_tile = "landfill"` exists on water-family tiles (map-gen
cover) — irrelevant to a player-built floor.

### R6 — the light rig (read-only dump of `ford-posts.blend`)

- Scenes: `FORD`, `ICON`. Exactly **one light object**: `KEY`, type **POINT**,
  loc **(−42.0, 0.0, 42.0)** relative to origin-staged geometry, rot 0,
  **energy 40000**, white (1,1,1), linked into BOTH scenes. This is law-6's
  "west sun-substitute" realized as a distant pseudo-sun (x→−42 = west,
  elevated z→42).
- Ambient is NOT a light object: world `FORD_WORLD`, use_nodes with a single
  **Background: color (0.55, 0.55, 0.55), strength 0.06** — the ambient term.
- Boards factory replication (origin-staged): POINT `KEY` @ (−42, 0, 42),
  energy 40000, white; world background uniform 0.55 @ 0.06. No other lamps.

### R7 — W3 in-game mix simulation on candidate stones

Model from `ford-knobs.md` §1: render ≈ 0.75·art + 0.25·water, water =
(17,114,129) (W3 = grey tint (51,51,51) @ 25% alpha ≈ the tested grey-20%
point). Predicted post-mix deck tones: plank anchor (150,105,59) → (117,107,76)
**L107**; gap tone (62,40,22) → (51,58,49) **L56** (dark, safely not black).

| Candidate (authored hex) | Post-mix | ΔL vs mixed plank | Verdict |
|---|---|---|---|
| crush-stone khaki #796b51 | (95,109,93) | **−2.4** | invisible (luminance) — avoid |
| py gravel grey-mid #686566 | (82,104,109) | **−7.2** | invisible — avoid |
| stone-icon ochre #967948 | (117,119,86) | +9.3 | subtle, warm — cue only |
| crush-stone bright #957b59 | (116,121,99) | +11.1 | subtle |
| crush-gravel sandy #a48b76 | (127,133,121) | +23.7 | clear read |
| py gravel grey-light #9c9288 | (121,138,134) | +27.1 | clear read |
| stone-icon bright #b5975b | (140,142,100) | +31.4 | strong, warm |
| limestone light #b1a899 | (131,150,146) | +38.6 | strong |
| crush-gravel pale #baa797 | (144,154,146) | +44.0 | strongest — sparkle accents |

Cautions baked into guidance: everything drifts G-ward after mix (the plank
itself stays warm: R117 > G107); the palest options drift the most while
staying high-L (read as light stone, not water). Author ballast mostly in the
warm band L≈120–155 (ochre/bright crush-stone/sandy) with a few pale accents;
never below ≈L64 (mid-light rule, survives mixing). Final verdict per ticket:
gwenview + bench ABS capture — this sim is the model-approximate screen.

### R8 — pilings transition frames carry NO board content

`tools/gen-textures.py` docstring states pilings-exp.png "contains ONLY
pilings and water"; numerically confirmed on `pilings-composite.png`
(3200×2368): top band wood pixels confined to columns 24–40 (the pole), no
full-width plank-like rows in any 64px piece. ⇒ ticket c3's "transition-piece
frames update their board content" resolves as: **frames contain no boards
today; the P1 composite needs re-derivation only if the flat-water fill or
pole art changes.** The boards factories do not feed the pieces as things
stand (D2 for confirmation).

### R9 — pipeline shape for the boards stages

`tools/paper-pipeline/bake.sh`: stages `strips → sheet → deploy → save → view`;
`--twice` runs the strip stage twice and bit-compares all frames; header
invariants: paper pixels = Blender output only; hard-fail on empty/unwritten
frames; sheet cells bit-equal to frames; seed-pinned saves. `bake-strips.py`
opens `ford-posts.blend` headless, renders named scenes (`ICON` @ 64², context
`FORD`). For boards: sibling stages/bake script(s) operating on
`ford-boards.blend` with per-variant named scenes + cameras; deploy copies
sheets into `mod/graphics` (exact deploy mechanics re-checked at build).

## Decision points for the maintainer (collected)

| ID | Point | Default I would take |
|---|---|---|
| D1 | Inherited seams are 1px — too thin to read pebbles in. Re-interpret with wider visual seams (2–4px) carrying ballast stone runs at fixed rows | widen to ≈3px, same anchor rows; gwenview gate |
| D2 | c3 scope: no board content exists in transition pieces; confirm P1 composite re-derivation is NOT required unless the flat-water fill/pole art changes | treat c3 as satisfied-by-evidence |
| D3 | Land tile registration: is_foundation absent (concrete precedent), decorative_removal_probability 1.0, map_color warm plank, walking_speed_modifier 1.0–1.1 | as proposed in R5 table |
| D4 | If in-sprite ballast fails gwenview, doodad fallback needs a scoped control.lua exemption (invariant 2) + accepts save-cost and a dry-over-wet look risk | in-sprite first (maintainer's own lead) |
| D5 | Rich variants for the FORD would require moving the frozen `variants.main` config — out of this round's drop-in law | rich = land tile only, stretch |
| D6 | Land sheet filename + count (proposal: `boards-land.png`, 8 size-1 variants mirroring the deck's rhythm; rich sizes as stretch) | as proposed |

Scratch/provenance: `.cache/boards-research/` — extract-planks.py,
extract-r1b-r2.py, planks-extract.json, swatches/*.png. All regeneration is
from this doc + the scripts.

## Session log

- 2026-10-17 — opened doc during the research phase kickoff (agent session
  after maintainer's go-ahead; see ticket chat: ballast-in-sprite is the lead
  option, doodad composition is the fallback if in-sprite can't be made nice;
  land tile = plain single-cell flooring first, rich tiles are a stretch goal
  and may apply to the ford too).