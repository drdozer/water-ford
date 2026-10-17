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
| R10 | Visual-model / tilering lattice: how do varied board lengths+widths, end bolts and mid-span bows line up at tiling edges — vanilla precedents measured, schemes derived | DONE (scheme choice = maintainer, see S1) |
| R11 | bound_decoratives semantics for the doodad fallback (upgrades R4/D4) | FOUND (runtime probe still open if fallback is pursued) |

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

## Addenda (same session, after the register was written)

- **Metal family swatches** (the deck interpretation's bolts-through-boards
  and metal bars — recipe ingredients `iron-stick` / `bolts`): vanilla
  `iron-stick` icon = cool grey L72–120 (#474949 L72, #565959 L88, #666869
  L104, #787876 L120) + highlight #bab9b7 L185; py `bolts` icon = neutral
  grey L104–167 (#686868 → #a7a7a7). Both families are neutral-to-cool against
  the warm wood core — the natural contrast cue for metal detailing.
- **No wooden-floor tile precedent exists** in vanilla 2.1, Space Age, or any
  local py data zip (grep over all tile prototypes: zero wood/floor names).
  The land boards tile has no in-game look reference — its visual language
  must come entirely from the boards spec (R1 anchors + shared lighting),
  which is exactly what the ticket's "same visual language" clause wants.

### R10 — the tiling lattice: what "the standard way" is, measured

Motivation (maintainer, ticket chat): boards raising a little at the middle,
bolted down at the ends (2 bolts per end), up to quarter-board-width lift at
the middle, boards of different lengths AND widths — "what is the standard way
to ratio this stuff out so that the pattern lines up at tiling edges?"

Measured precedents:

- **space-platform-1x1.png** (1024×64; 16 size-1 variants — the SA platform
  floor, a bolted-panel look): butt joints at ARBITRARY interior x per variant
  (patterns (16,54)/(41,)/(16,40,54,59)/()—), horizontal joints rare, and the
  **edge columns are tone-neutral: L at x=0 vs x=63 differs by 0–3, and
  across all 16 variants the edge columns sit within ±4 of each other**.
  Wube's lattice rule: tiles butt INVISIBLY by tone-continuation — no joints,
  no edge treatment at the cell boundary.
- **space-platform-2x2.png** (2048×128; 16 count, probability 0.75): joints
  cross the internal 64px boundary freely (seam at x=80/109 inside a 128px
  window) — inside a rich window the layout is unconstrained because the
  engine guarantees the window's cells render that one sprite. The window's
  OUTER edges follow the same tone-neutral rule (Δ≤3).
- **Our inherited planks.png**: fixed full-width horizontal seam lattice
  (rows 15/31/47, variant-invariant), interior butt joints, near-uniform
  per-variant tones (edge x-columns L105–113, imbalance 0.0–0.9), and a
  **variant-independent bottom edge strip: L(y=0..1)=113 light, L(y=62..63)=
  78 dark, while courses are uniform L111–112** — i.e., every N|S tile
  boundary carries a consistent full-width light-over-dark step and every
  E|W boundary relies on tone continuation. Variant-invariant edge furniture
  + tone-neutral continuation coexist in one art.
- `concrete.png` (4096×512) turned out to be the masked-transition band sheet,
  not a main-sprite lattice precedent — no signal taken from it.

The distilled standard (the one rule that makes all of it work):

> **Pin the boundary furniture, free the interiors.** Any element crossing a
> cell boundary must find, ON BOTH SIDES, content that is variant-invariant
> (tone, topography) — or the element must END at the boundary identically in
> every variant. Cuts/bolts should land on a quanta grid so that the
> construction reads consistently across random neighbor pairs. Rich sizes
> free internal layout entirely (engine guarantee); their outer edges obey
> the same rule.

For OUR boards — the wave changes the calculus. Three schemes, all legal:

| Scheme | Edges | Lengths | Widths (courses) | Waves (bows) | Variety |
|---|---|---|---|---|---|
| **A — bolted bays (rec)** | every course ENDS at the cell edge (cap strip + 2 bolts), variant-invariant | quanta quanta = 16px sheet (8 game px, the inherited course height); boards k·16, k∈{2,3,4} typical, k=1 occasional; joints+bolts ONLY at quanta columns | FREE per variant (integer px, full-width seams) | per-BOARD: apex at own mid, A ≤ ¼·board width; profile h = A·sin²(π(x−x₀)/L) — zero value AND slope at ends | maximal: per-variant lengths, widths, waves, joints, bolts |
| B — continuation illusion (inherited/platform style) | crossing rows: tone + wave at edge columns variant-INVARIANT; lattice y-rows frozen global (15/31/47) | free interior joints (quanta optional) | LATTICE FROZEN globally | per-ROW-fixed (period 64), amplitudes fixed per row | grain/joint tone only; "some boards lift" becomes "some rows lift" |
| C — hybrid | per-row policy fixed GLOBALLY across variants (e.g. rows 1&3 crossing-pinned, rows 0&2 short-free); per-variant y-lattices do NOT mix with crossing rows (overlapping edge bands break tone matching) | mixed | pinned globally if any crossing rows | pinned rows: fixed waves; free rows: per-boards | good, at the cost of global row discipline |

Key piece of load-bearing math: **h = A·sin²(π(x−x₀)/L) has zero value and
zero slope at both ends** — that is why scheme A permits per-variant
amplitudes (each board's wave lives entirely inside its own cell-span and
meets every boundary at h=0, h′=0 on both sides). Under B, per-variant wave
freedom is impossible because a crossing board's wave value at the boundary
would have to match a random neighbor's.

Consequence of bolts-at-ends (explicit): under A, EVERY tile boundary is a
bolted splice (4 bolt heads around it) — the ford reads as 1-tile boards
bolted edge-to-edge; a visible rhythm change vs the inherited art's invisible
E|W joins. Under B, boundaries stay quiet and bolts appear only at interior
joints. Scheme C gives both looks per row. The bolt heads: 2 per end spaced
across the course width (≈⅓/⅔ points), 2–3px heads on the sheet, the R2
addendum grey family (iron-stick L72–120 / bolts L104–167), tiny east shadow
under the west key.

The lift cap: ¼ board width ⇒ ≤4px on the sheet (2 game px) for a 16px
course; wider courses (18–20px, scheme A width freedom) lift proportionally
more. Wave shading under the west key: lit west flank brightens (+), east
flank darkens toward the gap tone but never below the L43 dark floor; the
lifted gap-side shadow widens/softens toward mid-span (rendered in-scene —
law 3, no painted detail).

In-sprite ballast interplay (D1 refined): the widened seams (2–4px) carry the
pebble runs; quanta-pitched joints give the pebbles consistent bays. Ballast
and bolts BOTH at boundaries could crowd the cap strip — if scheme A, put the
bolt pair ON the cap and pebbles in the interior seam, or vice versa; gwenview
decides.

### R11 — bound_decoratives: the doodad fallback becomes engine-native

Discovered while mining the SA platform tile as a rich-tile precedent:
`space-platform-foundation` binds decoration sprites to the TILE PROTOTYPE
itself (`bound_decoratives = {"space-platform-decorative-pipes-2x1",
... "-4x4", "-2x2", "-1x1", "-tiny"}`; SA tiles.lua L260+). The prototype
API confirms the field: `TilePrototype.bound_decoratives: DecorativeID |
array<DecorativeID>` (optional). The bound decorations themselves are
`optimized-decorative` prototypes with:

- `pictures = spritesheet_variations(51, 10, {...})` — up to 510 variations
  in ONE sheet (engine picks randomly — the organic composition);
- `target_count = 100` (engine density target), `minimal_separation = 0.19`
  (packing), small `collision_box`, explicit `render_layer = render_layer[7]`.

⇒ The maintainer's fallback (tiles without ballast + separately-rendered
ballast sprites, composed by the engine at random over the tile) is
**prototype-native**: tile gets `bound_decoratives = {ballast-pebbles-...}`;
NO control.lua scripting — the D4 "invariant-2 exemption" problem mostly
dissolves. Open runtime questions IF the fallback is pursued: do bound
decoratives fire on `place_as_tile` builds (platform foundation is a
place_as_tile, so expected yes); do they render above or below the ford's
water effect (dry-pebble-over-wet-deck risk; `render_layer` chosen so they
read as on-tile); do they interact with the ford's transitions stamps
(z-order vs P1). A bench probe settles all three in one scene. Status:
fallback stays behind in-sprite ballast per maintainer lead, but it is no
longer "needs an exemption" — it is "needs a runtime probe".

## Decision points for the maintainer (collected)

| ID | Point | Default I would take |
|---|---|---|
| D1 | Tiling lattice scheme (R10/S1): A bolted bays / B continuation illusion / C hybrid per-row | A — quanta 16px, per-variant lengths+widths+waves, bolted splices at every cell edge; seam widening 2–4px for pebble bays; gwenview gate |
| D2 | c3 scope: no board content exists in transition pieces; confirm P1 composite re-derivation is NOT required unless the flat-water fill/pole art changes | treat c3 as satisfied-by-evidence |
| D3 | Land tile registration: is_foundation absent (concrete precedent), decorative_removal_probability 1.0, map_color warm plank, walking_speed_modifier 1.0–1.1 | as proposed in R5 table |
| D4 | Fallback composition for ballast: now prototype-native `bound_decoratives` (R11) — prototype-only, no control.lua; still needs the render-layer/water-effect runtime probe if pursued | in-sprite first (maintainer's own lead); fallback upgraded |
| D5 | Rich variants for the FORD would require moving the frozen `variants.main` config — out of this round's drop-in law | rich = land tile only, stretch |
| D6 | Land sheet filename + count (proposal: `boards-land.png`, 8 size-1 variants mirroring the deck's rhythm; rich sizes as stretch) | as proposed |

Scratch/provenance: `.cache/boards-research/` — extract-planks.py,
extract-r1b-r2.py, planks-extract.json, swatches/*.png. All regeneration is
from this doc + the scripts.

## Blender phase plan (S2) — agreed direction, pre-session

Maintainer direction (2026-10-17, ticket chat): schemes A/B/C are to be
**explored visually, not decided now** — build the MECHANISMS for as much of
it as possible and then judge by eye. Big-floor approach approved: model a
large continuous floor in Blender, render it out at the per-tile pixel depth,
and slice spritesheet windows from it.

Integration law (agent, answered): slicing is legal as a **law-3 pure
arrangement stage** (copy 64px windows 1:1 out of the big render, per-cell
bit-equal verification), and random-neighbor tiling is solved by construction
if the model keeps the variant-invariant boundary furniture ON the 64px grid
lines (scheme-A splices and/or pinned edge bands). The big floor can carry
side-by-side zones demonstrating A / B / C plus ballast-on/off and land-deco
on/off, so one render session produces the exploration contact sheet.

Factory shape (ford-boards.blend, sibling of ford-posts.blend; law 1):

- Scenes: `FLOOR` (deck/water look) and `LAND` (final-look) sharing the board
  geometry collections; per-world content via collection inclusion (committed
  state, nothing toggled at render time).
- Toggleable mechanism collections: `BALLAST` (water-only pebble group),
  `TRIM` (land-only group TBD by look), plus the shared board/base furniture.
- Staging: geometry at the origin; light rig per R6 exactly (POINT KEY
  (−42,0,42) @ 40000 + world 0.55 @ 0.06).
- Big floor: a continuous deck plane spanning an M×N tile grid at origin
  (initial target 24×24 tiles ⇒ 1536² px at 64px/tile depth), boards of
  varied lengths/widths per scheme zones, bows, bolts, end caps.
- Render depth: **64px per tile** (2× art; engine `scale = 0.5`) — ortho
  camera top-down over the floor.
- Slice stage (later, in the bake chain): law-3 arrangement copying windows
  into the 512×64 drop-in sheet (8/row) and contact sheets for review;
  `--twice` bit-compare as in bake.sh.
- First build (this session): the **base wooden floor model** — shared
  boards/base furniture/bows/bolts/seams WITHOUT ballast or trim; the toggle
  collections exist but stay disabled. Previews rendered to
  `.cache/boards-research/previews/` for the maintainer's gwenview.

Session mechanics (verified 2026-10-17): `mcp-for-blender` bridge is running;
the `blender_mcp` addon is installed in Blender 4.3.2's scripts; DISPLAY=:0.
Launch: start Blender on :0 in the background, then `get_addon_status` and
drive the build via `execute_blender_code` (live visible session — law 2),
save-as to `mods/water-ford/blender/ford-boards.blend`. Scene facts verified
via `get_scene_info` / bpy queries (the agent cannot view images — numeric
verification + maintainer gwenview).

Decision-point amendments:

- D1 → scheme choice is EXPLORATION (zones in the big floor; gwenview), not a
  pre-decision.
- D4 → doodad fallback = prototype-native `bound_decoratives` (R11); bench
  probe only if pursued.
- D2, D5, D6 unchanged.

## Session log

- 2026-10-17 — opened doc during the research phase kickoff (agent session
  after maintainer's go-ahead; see ticket chat: ballast-in-sprite is the lead
  option, doodad composition is the fallback if in-sprite can't be made nice;
  land tile = plain single-cell flooring first, rich tiles are a stretch goal
  and may apply to the ford too).
- 2026-10-17 — same session, after the maintainer raised the visual model:
  boards rise at the middle, 2 bolts per end, varied lengths/widths; asked for
  the standard tiling-ratio scheme. Answered with R10 (measured precedents:
  SA platform floor's tone-neutral edges; inherited art's fixed seam lattice +
  tone continuation + bottom edge strip) and scheme table S1/A-B-C; plus R11:
  `bound_decoratives` discovered — the doodad fallback is prototype-native
  (D4 amended; runtime probe listed).