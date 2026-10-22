# The ladder export recipe — wooden boards & cobbles (2026-10-21)

One recipe, two inputs. Nothing happens in ephemeral bridged python calls;
every stage is a committed script; every intermediate is a committed
artifact. Written after the reverse-engineering round (see journal
2026-10-21): the boards' export pipeline was bridge-session code that died
with each session, the cobble's was a condemned per-file bake, and the
committed masters/sheets drifted across generations with nothing enforcing
agreement.

## The game contract (the ground truth this recipe exists to satisfy)

From `mod/data-updates.lua` (the wiring = the authoritative consumer):

- **16 sprites (variants) per ladder size**; sizes 1, 2, 4 (game tile counts
  per design).
- **Each sprite = (128 x size)² px** (1x1 design = 128², 2x2 = 256², 4x4 =
  512²); the **pixel depth is constant: 128 px per game tile**, at engine
  `scale = 0.25`.
- **Sheet shapes** (maintainer-confirmed arithmetic, 2026-10-21 revision):
  **ALL sizes render as 4x4 sprite grids.** Size 1 = `512x512` (16 sprites
  of 128², `line_length = 4` — maintainer: keep the 1x1 sprites in the 4x4
  grid, do not reflow into a row; admissibility proven by the running
  2x2/4x4 sheets); size 2 = `1024x1024` (16 sprites of 256²); size 4 =
  `2048x2048` (16 sprites of 512²). The `2048x128` strip layout retires.
  (In raw 128² units: 4x4 / 8x8 / 16x16 cells.)
  The lua's size-1 `line_length` flips to 4 AT THE SAME COMMIT as the first
  replaced sheet — a lua pointing at a new sheet-shape while the png is old
  is a broken mid-state, so sheet + lua always ship together.
- Variant identity: the engine consumes `count = 16` interchangeable
  variations — the specific art per variant ID is ours to define.

## Stage A — LAYOUT (in the .blend, governed by this doc; nothing scripted)

Law for BOTH files (boards and cobble; the cobble uses the exact same tile
geometry — the recipe differs only by blend + sprite base name + wetness):

1. Every design area is **contiguous**: a 4x4 grid of design cells per
   ladder size laid out at world positions documented below, so variant k's
   window can be expressed as "cell (row r, col c) of area X".
2. **Variant IDs are row-major**: variant k = the k-th cell (r = k div 4,
   c = k mod 4).
3. 2x2 and 4x4 designs are built **crossing the internal 1x1 boundaries by
   construction** — that is what a "2x2 design" *means*; boundary furniture
   respects the doc'd tiling law (boards: R10 "pin the boundary furniture".
4. **128 px per game tile at 128 px-per-BLENDER-unit ⇒ 1 blender unit = 1
   game tile** for the ladder grids (cobbles note: their deck mesh is
   currently at a different mesh-cell scale — the layout round re-bases it
   onto this same lattice; the cobble's *mesh texture scale* is a mesh-local
   concern, the ladder contract is unchanged).
5. Cameras live in the file, one per design area, naming scheme
   `<AREA>_CAM`, ortho = area width in units, top-down at z=60, matching the
   boards roster (FLOOR_CAM ortho 12 … LAND_CAM ortho 24 …).
6. Dry-look art only; wetness NEVER paints into art pixels (piling pattern:
   wetness = the gray data block from the wetness pass).

Per-file area registry lives in this doc's commit history as it changes
(journal records layout rounds).

## Stage B — RENDER (committed driver: `tools/paper-pipeline/bake-ladder.py`)

Per design area x world scene:

1. Renders the area with its in-file camera at the contract depth
   (px/tile = 128 ⇒ area render = cells x 128 px per side).
2. Masters are committed to `assets-src/<family>/<sheet>-master.png` BEFORE
   any cut happens (the cut must be runnable offline against committed
   bytes).
3. **Wetness flag** (cobble only): each area additionally renders its
   wetness mask through the `Mask` view layer + `M_COBBLE_MASK`
   material_override with the runtime pass state (Standard transform, opaque
   film, world 0, dither 0) **wrapped all-or-nothing (try/finally)** — the
   aborted-toggle lesson from 2026-10-21. Mask masters are committed the
   same way; wiring to the engine is a separate, named change (the current
   committed state ships art-only wiring).
4. Light rigs: boards/posts standard rig per
   `boards-visual-language.md` §4 / the applied stones-verbatim sun in the
   cobble (2026-10-21 sun transplant).

## Stage C — CUT (part of the same committed driver)

1. **Law-3 pure arrangement**: variant k's cell = the exact (128·size)²
   window from the committed master, copied 1:1 into the contract sheet
   shape (strip for size 1; 4x4 grid for sizes 2/4). No resampling, no
   stitching, no touch-ups: any change goes upstream in LAYOUT or RENDER.
2. `--twice`: the cut runs twice; the sheets must be pixel-identical
   (PNG-writer byte-instability is known and expected; PIXEL equality is the
   gate — see the drift incident below). This is SELF-consistency of the new
   pipeline, not parity with any older generation.
3. **Byte/pixel identity with the pre-recipe committed sheets is NOT a goal.**
   The old ladder (`wooden-flooring*`, `boards-ford-c*`, restore points in
   `testing/testing-mods/2026-10-17-boards-16-16-16/`) is the LOOK REFERENCE
   for the maintainer's eyes; the new pipeline produces a NEW generation from
   the re-based layout, and the old sheets retire as archive once the
   maintainer approves the new look side-by-side. The approval gate is the
   maintainer's eyes, never pixel statistics alone.
3. **Deploy = verified copy**: `assets-src/<family>/<sheet>.png` (committed)
   → `mod/graphics/<sheet>.png`, byte-identical copy.
4. **Gate**: output sheets conform to the lua contract (16 cells, cell
   sizes, shapes, depth) AND `mod/graphics` == `assets-src` byte-equal AND
   mask sheets (if any) present in `assets-src`.
5. Any gate failure aborts loudly with a non-zero exit.

## Known current-state faults against this recipe (to be closed, in order)

- **Generation drift**: committed `assets-src/cobble` staging vs committed
  `mod/graphics` sheets differ by 230k-4.1M PXELS per sheet (three
  sheets) — two art generations from the old pipeline, never re-gated.
  Resolution: the new pipeline replaces BOTH committed generations with its
  new output once the maintainer approves the look (old sheets retire to
  archive/restore points); staging and deployed must agree byte-equal from
  then on.
- **Layout law not implemented**: boards slabs are scattered/partial (the
  "bits of the sheets are findable but not contiguous" observation);
  cobble deck is an irregular 58x52 blob. Both files get re-based onto the
  Stage-A lattice.
- The old tooling (`auth-cobble.py`, `bake-cobble.py/sh`, cranks) was
  PURGED 2026-10-22 (maintainer ruling: "all the old cobble code and blend
  gone — it is all cursed"): the crank + the fresh-toolchain session
  scripts (`mat-fresh.py`/`wet-fresh.py`) + `palette-ladder-cobble.py` +
  `blender/ford-cobble.blend(+1)` all removed. Nothing carries into the
  remake; the rebuild consumes `docs/cobble-visual-language.md`.

## Increment plan (working through it, per maintainer)

1. This doc (done).
2. `bake-ladder.py` + `bake-ladder.sh` skeleton with the cut/deploy/gate
   machinery proven against committed bytes (no renders yet).
3. Re-base the boards layout onto the Stage-A lattice (live session,
   maintainer watching), then render + cut + gate the boards ladder, eyes
   on old-vs-new.
4. Re-base the cobble deck onto the SAME lattice, add the wetness pass to
   the driver (`--base cobblestone-ford --wetpass`), same gates.
## Material state law (2026-10-21, maintainer-approved during the pins A/B)

- **Pin window** = M_PLANK's shader mechanism: within ±9px of the pin
  period's edge lines, the plank's colour is replaced by the flat
  per-COURSE tone (ND_CRSRAMP via the plank_course face attr) and the
  grain fades neutral (ND_TPIN tone pin × ND_GPIN grain pin). The old
  file named it TPIN/GPIN; the R10 law's implementation.
- **The approved B look: per-sprite pins.** The window's period = the
  design sprite, not the 1u tile: shaded bands at each design's outer
  left/right edges only; grain continuous across internal tile lines.
  Builder: `--pins per-sprite` (default) — per-size material variants
  M_PLANK_2 / M_PLANK_4 (same spec, x/side before the FRACT; the window
  shape's constants verbatim, so the edge band = ±9px × size).
- `--pins per-tile` = the rejected A (bands at every integer tile edge);
  kept request-able. The geometric crown stays per-tile lattice-periodic
  in both (its own `--crown` flag; the planks-arch-per-plank variant was
  tested and not asked for twice).
