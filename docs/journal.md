# water-ford — journal (session work log)

Chronological log of agent work sessions on this mod. Evidence scratch dirs
live under the superproject's gitignored `.cache/` and are recreated from the
referenced recipes. Companion documents: `dependency-audit.md`,
`refactor-plan.md`, `shadow-experiments.md` (predecessor session, pre-1.0.0).

## Session 2026-10-15 — audit, refactor, pypp fix, stage experiment

Starting point: water-ford 1.0.0 (`b2e7589`), repo-root layout, declared
`factorio_version: "2.1"` / `base >= 2.1.0` / `? cargo-ships >= 2.1.8` /
`? pyalienlife >= 3.1.8`.

### 1. Dependency audit (empirical)

- Probed both managed installs (vanilla 2.0.77, dlc 2.1.21): every API
  touchpoint is 2.0-era; `water-wube` in `to_tiles` is the logo easter-egg tile
  (present in both majors), not dead config.
- **2.0 floor test**: probe copy with only info.json changed (`"2.0"` +
  `base >= 2.0.0`) dumps cleanly on 2.0.77; declared-2.1 is rejected there;
  `testing.md` had already shown 2.1 rejecting `"2.0"` — the
  `factorio_version` gate is exact both ways.
- **py item provenance**: `treated-wood`/`log`/`gravel`/tech `creosote` ←
  pycoalprocessing; `bolts` ← pypetroleumhandling; reached only via
  pyalienlife's hard deps (audit §5).
- **Decision (user)**: support 2.1 only — no 2.0 branch.
- Commit `b35c0f1` (audit + refactor plan), `ea878ca` (2.1-only revision).

### 2. Refactor executed (no release, per user)

- `5283e29` **layout**: deployable moved to `mod/` (unlocks `devctl mods
  build`, which refuses repo-root layouts); live link re-pointed
  (`unlink`+`link` resolves `mod/` automatically).
- `a5e970a` **hygiene**: vanilla/py ingredients + prereq selected *before* a
  single `data:extend` (kills the extend-then-mutate trap behind 019fd2b);
  hardcoded `localised_*` dropped; locale became load-bearing.
- `ce1de46` **tools**: `gen-placeholders.py` → `gen-textures.py` (writes into
  `mod/graphics/`, `--base/--out/--force`, write-only-on-pixel-change;
  docstring refreshed); new `gen-branding.py`. Forensics: only one script ever
  existed — icon (`a020dad`) and thumbnail (`c4033c5`) were one-off composites.
  Verified: pilings/mask/planks/icon regenerate **pixel-identical**; thumbnail
  reconstruction ≠ shipped → shipped thumbnail kept canonical (its border
  water matches no base-art crop).
- `989b4c9` docs (AGENTS.md + README).
- Zip rebuilt via `devctl mods build`; contents vs 1.0.0: graphics/info.json/
  changelog/control.lua byte-identical; no scaffolding files.

### 3. pypostprocessing crash — discovered, then fixed

- The equivalence-pass py dump crashed: pypostprocessing's data-final-fixes
  (gated on `py.has_any_py_mods()`) eager-`TILE()`s the `place_as_tile` result
  of every single-product recipe lacking `localised_name`; our tile only
  existed in our own final-fixes, and `p…` < `w…` alphabetically. Old code
  (1.0.0) failed identically → pre-existing, not a refactor regression
  (`14c2383`).
- **User's recollection confirmed**: play-testing with py happened as
  `py-caravan-ford` (0.2.0, `74e755a`), which sorts *before* pypostprocessing;
  the 0.3.0 rename (`ea39105`) planted the latent crash.
- **Why the suggested fixes don't fit**: dependency sequencing can't work from
  the dependent side (`? pypostprocessing` pushes *us* later — wrong
  direction). Applied the ecosystem idiom instead: recipe carries
  `{"?", {"recipe-name.water-ford"}, {"item-name.water-ford"}}` (user
  approved going all-in on localisation hooks).
- **Locale hooks completed** (`cc452f1`): `[recipe-name]`, `[mod-name]`,
  `[mod-description]` (official info.json overrides), placement-denied flying
  text → `[water-ford-messages]`.
- Verification: **real py closure + pypostprocessing dumps exit 0** (1.0.0:
  crash); pre/post diff = the single `localised_name` addition;
  `recipe-locale.json` resolves to "Water Ford"; live 22-mod set smoke exit 0.
- pypostprocessing is effectively mandatory for the suite (pyalienlife needs
  its `py` metas); py requires space-age **disabled** — and the engine
  auto-enables data-dir DLC mods unless explicitly disabled in mod-list.json.

### 4. Stage experiment — "is final-fixes genuine?" (user-initiated)

- Question: move tile-building as early as possible; find the lowest stage
  that works (runs + looks correct).
- **Harness** (user: don't overthink; later corrected: **same seed or it
  proves nothing**): throwaway scenario mod `.cache/stage-exp/` carves a lake
  and script-places fords in three arrangements (open water / shallow border /
  land border) + reference patches; offscreen `game.take_screenshot` at fixed
  ticks; `--map-gen-seed` applies to `--load-scenario` — same-seed runs are
  **0-diff pixel-perfect** (verified with a same-variant control pair).
- Ladder (seed 12345):
  - **data.lua**: loads; renders **pixel-identical**; but the clone predates
    the stack's data-updates mutations of water-shallow — space-age adds a
    lava-dirt transition rule + mech `landing_steps_sound` there → 58-diff
    silent divergence.
  - **data-updates**: loads; pixel-identical; prototypes **byte-identical**
    to the final-fixes baseline ('w' sorts after every mutator); tile exists
    before every mod's final-fixes → pypp-safe (exit 0 both variants).
  - **data-final-fixes**: baseline; the stage whose position *caused* the pypp
    crash.
- **Verdict: data-updates is the lowest stage that fully works.** Applied
  (`0fd2889`): `git mv data-final-fixes.lua data-updates.lua`; real-mod
  verification: dump == final-fixes baseline, live-set smoke exit 0, real py
  closure exit 0 (piling rule intact in the py env), seed-pinned screenshots
  0-diff vs baseline.

### End state

- Mod repo HEAD: `0fd2889`; superproject pointer bumped. Zip:
  `dist/water-ford_1.0.0.zip` (16 files, no scaffolding; vs 1.0.0 the
  intentional diffs are `data.lua`, `data-updates.lua` (ex-final-fixes),
  `locale/en/locale.cfg`, `control.lua`).
- **No release made** (user instruction) — version stays 1.0.0; changelog
  entry deliberately deferred to release time.
- Knowledge transfer: all-mods procedures → superproject `AGENTS.md` +
  `docs/` (`data-lifecycle.md`, `locale-hooks.md`, `py-suite.md`,
  `visual-testing.md`, `tooling-candidates.md`); this AGENTS.md trimmed to
  mod-specific pointers.

### Scratch evidence dirs (recreate from docs recipes)

- `.cache/water-ford-refactor/` — dump-diff baselines, py-closure sets, stub
  pyalienlife, locale dumps (`data-lifecycle.md` §dump-diff).
- `.cache/stage-exp/` — stage-experiment variants + seed-pinned scenario
  harness (`docs/visual-testing.md`; promotable to `testmods/` if wanted).
- `.cache/water-ford-2.0-probe/` — obsolete after the 2.1-only decision.

## 2026-10-15 — devctl tooling: `devctl mods env` lands; first env is ours

The water-ford session's most-repeated hand procedure (scratch dir +
config.ini + mod-list assembly, ~10×) is now a verb: `devctl mods env create`
(superproject `lib/envspec.py` + `lib/mods/env.sh`, format contract
`docs/test-envs.md`).

- Our first committed spec: `envs/dlc-smoke.toml` — hermetic smoke env
  (water-ford live-linked, DLC data-dir mods disabled, optional deps
  cargo-ships/pyalienlife left out).
- First real provisioning: `.cache/envs/dlc/dlc-smoke-c84c8820/` — load smoke
  through the env exit 0 (tee'd log: superproject `.cache/env-first-run.log`).
  Game state landed inside the env (hermetic write-data confirmed).
- Re-provision is a no-op (`env up-to-date`); changed specs provision a fresh
  content-addressed env; `env prune` GCs superseded ones.

## 2026-10-16 — `devctl mods check` lands; water-ford is the first gated project

The superproject's verification-gate runner (smoke / dump-diff / locale /
floor probes over a provisioned env) was built with water-ford as the subject:

- `check water-ford --env dlc-smoke` → smoke PASS (dump cached, repeat runs
  launch-free); `--locale` PASS (4 attributed prototypes, 0 dead refs,
  0 missing keys — the recipe localised_name resolves).
- `--against` the session's stub-pre full dump: 7 expected diffs (the
  localised_* drops) + 4 unexpected (the real ingredient/technology changes
  from the stub round) — the triage split matches the journal exactly.
- `--factorio vanilla` floor probe: smoke fails on 2.0.77 — empirical
  confirmation of the declared `base >= 2.1.0` floor.
- Bonus find: 43 dead `entity-description.<type>-asteroid` references in
  VANILLA space-age (asteroid.lua builds keys no locale file defines) —
  caught by the new dead-key scan as non-gating warnings.

## 2026-10-16 — Blender factory: piling sheets into an in-game viewer

Blender paper pipeline (`.cache/ford-factory/`): 108 per-frame renders of the
piling (crown variation, jitter σ=0.0625) verified per-frame, then projected
into `piling-sheet-64.png` (12×9 grid of 64px cells, row-major = frame order,
alpha in the PNG). Sheet cells verified **bit-equal** to their source frames —
a pure repack, zero external pixel processing.

### Naming refactor (pole → piling)
Single naming law: `PILING` object, `piling_builder` GN, `M_PILING` material,
collection, comments. Rename proven pixel-neutral by bit-exact re-render hash.

### Crank hardening (bg-remake.py)
- Removed the "missing frame" fallback that silently copied a stale
  `blender/.png` into slots when a render wrote nothing — it had masked the
  intermittent empty-write bug as warm frames (stale slots 27/54 found by
  bit-hash against live re-renders).
- Empty writes now abort the crank loudly. Two consecutive cranks:
  108/108 icon + sprite frames **bit-identical between runs**; zero empty;
  zero border touches; centroid σ 3.1/2.4 px (pure keyed jitter).
- The old strips are archived under /tmp for forensics only.

### In-game viewer (test-only, repo's mod/ untouched)
- Throwaway scenario mod `wf-piling-viewer` in `.cache/ford-factory/test-save/`:
  one **optimized-decorative** (`DecorativePrototype`, 2.1) whose
  `pictures.sheet` is the piling sheet (width/height 64, line_length 12,
  variation_count 108, scale 0.5) + a seed-pinned scenario `ford-view` that
  carves a lake, lays a `water-ford` causeway (shipped art as context) and
  scatters 61 viewer pilings on open water.
- 2.1 API notes learned: `script.on_tick` does not exist (use
  `script.on_event(defines.events.on_tick, …)`); `game.create_player` is gone
  (playerless save + `LuaForce.set_spawn_position` on the south bank instead);
  `LuaGameScript.server_save` only saves in multiplayer (host headless →
  graceful SIGTERM → clean shutdown save); windowed load is
  `--load-game FILE` (singleplayer), server load is `--start-server FILE`;
  `global` is gone in 2.x (it is `storage`) — the first in-game session crashed
  on a `global` reference at tick 40, which the headless save-gen had masked by
  pausing at tick 39 (default pause-when-empty); fix: view-only scenarios put
  ALL their work in `on_init` and register NO persistent handlers, so loading
  the save runs zero scenario Lua.
- Stable save: `scratch/saves/ford-view-test.zip`, map-gen-seed 4242,
  verified loadable headless before the windowed view.

### Next (gated)
Sheet spec/decision memo delivered to the maintainer; tile integration
(alpha-in-transition vs opaque composite) is DEFERRED under the frozen-config
law until the sheet passes in-game eyeball.

## 2026-10-16 — paper-pipeline consolidation (bake chain into the repo)

Visual calibration closed: piling luma reconciled against the retired
`gen-textures.py` art (old sprite mean 116; pipeline now: bright pass 117 →
maintainer's ¼ rollback → 106 full-strip ✓ visual match approved in-game).

**Per-cycle scripts consolidated** into `tools/paper-pipeline/` (repo home,
never ships; `.cache` keeps artifacts only):
- `bake.sh` — orchestrator: `strips → sheet → deploy → save → view`; `--twice`
  runs the crank twice and bit-compares all 108 frames (reproducibility gate);
  `--seed` pins the viewer save.
- `bake-strips.py` — both strips + hard per-frame verification + the strip
  metrics (centroid σ, border scan, piling luma distribution) that were a
  retyped heredoc each cycle. Empty/unwritten renders abort loudly.
- `bake-sheet.py` — 12×9/64px repack, cells proven bit-equal to frames.
- `bake-save.py` — idempotent scratch provisioning + seed-pinned scenario
  run + SIGTERM shutdown save + rename + headless load-check; logs scanned
  for script exceptions.
- `calibrate-icon64.py` — ICON camera aim loop (on-demand, not per cycle).
- First path bug caught by its own `set -e`: the orchestrator used a 3-up
  `.cache` path (`mods/.cache` — pollution inside the repo, now removed);
  fixed to an explicit 4-up `$CACHE`.

**Blend-side** (project helpers only; the .blend must not carry bake-script
copies): stale in-file `ford_crank.py` text block (1545B, predating the
empty-frame hardening) DELETED; canonical text blocks added: handler
re-registration via `ford_gui_setup.py` (needed after any GUI restart — Blender
does not persist handler state) and `ford_pane_resync.py` (post-crank pane
resync).
Both executed via the MCP bridge and verified (handler count 1, props intact).

## 2026-10-16 — wetness: water-plane mesh split + separate gray mask block

The piling is CUT by the water plane in GN: two **DIFFERENCE** mesh booleans
against axis-aligned half-space cubes (top face z=0.25 / bottom face z=0.25)
joined back into one mesh — a true vertex ring at the waterline. (The
INTERSECT variant returned the cube wholesale on this cut-up mesh —
maintainer's diagnosis: a "logical union with a big square"; both cuts now use
the operation that works.) Segments verified: wet 64 verts exactly z 0..0.25,
dry 66 verts exactly z 0.25..0.636, no leak, 108/108 frames evaluate.

- Attributes: `in_wet` (0/1 per side, stored on each segment pre-join) and
  `wet_depth` (1 at base → 0 at waterline, stored post-join).
- Spec (maintainer 2026-10-16): above water COMPLETELY dry; below water ramps
  somewhat wet → fully wet.
- Mask (`piling-mask-sheet-64.png`, separate gray block, same 12×9 grid —
  never the art's alpha): crown constant 170; wet zone ramps 85 → 25 with
  depth, holding fully-wet at the base; 0 outside. NOTE: the byte ramp tops
  ~95 not literal 85 — the sRGB display encoding curves the linear mix; shape
  verified instead of byte literals. The seam's antialiasing legitimately
  spans 95..170 for ~2 rows (tolerated).
- Art pixels: an attempt to paint submersion into the art (`in_wet ×
  (0.30 + 0.35·wet_depth)`) was REVOKED at the maintainer's correction — the
  wetness spec belongs to the mask only; the piling renders as the dry-look
  asset and Base Color is rewired to the pre-paint shading (paint chain and
  orphan attribute reads deleted).
- Mask render: emission-override view layer, Standard transform, dither 0,
  world 0 — linear-exact grays; runtime toggles restored.
- Fixed wet depth confirmed numerically: wet-band size constant 12-13 px
  across all 108 frames despite jitter (the band moves with the piling in the
  cell; its size cannot — by the 45° projection of a fixed 0.25 world).

## 2026-10-16 — sprite strip realigned to the asset camera

The sprite strip previously rendered the FORD context at 256px through the
FORD scene camera (aimed at the waterline) — a DIFFERENT framing than the
icon/mask cells, so the three flipbook panes could not be compared. The crank
now renders the sprite strip at 64px THROUGH the asset camera (ICON_CAM,
runtime-linked into FORD, camera+res set and restored — never saved): the
context view (water level, bed) is framed per the asset cell. Verified
pixel-for-pixel: icon ≡ sprite extents on sampled frames (e.g. frame 27:
x24..38 y14..53 in both). Consequence: the sprite pane shows the context the
way cell-placement tuning needs — the water plane occludes the submerged part
(the tile-level look), the mask remains the authoritative wet/dry record.

## 2026-10-16 — shadow block: separate 64px strip + sheet + fourth flipbook pane

`bake-shadow.py`: the FORD SHADOW view layer (pole + CATCHER plane; ART's
catcher exclusion means only this layer shows it) rendered per frame through
the asset camera (ICON_CAM runtime-linked, 64px, view layers toggled and
restored, never saved). Verification: **east-of-piling darkening on every
frame** (lit catcher west ~140 luma vs shadowed east ~72; the key sits due
west so the cast shadow falls due east — the lighting law, checked per frame).
`shadows64/` → `piling-shadow-sheet-64.png` (12×9, cell-bit-equal), deployed
with the art + mask blocks. Fourth flipbook pane SHADOW_PREVIEW_64 wired into
the sync handler; panes now read mask | icon | sprite | shadow — all aligned
(frame-synced, same asset camera framing). LESSON: Blender refreshes area RNA
wrappers on area_split — after splitting, assign pane images by listing
positions in the same script pass, never by stale object identity.
- Correction (maintainer): "the shadow block should be the shadow only" — the
  catcher-view render was replaced with the pure shadow-sprite pass: the
  CATCHER object is already a Cycles shadow catcher (`is_shadow_catcher`,
  from the old experiments); with the piling hidden from CAMERA rays (still
  casting), film transparence, and the SHADOW view layer, the strip renders
  the shadow alone — translucent dark coverage on transparency. Verified per
  frame: coverage ≥200px on every frame, ≥60% of the coverage lies east of the
  piling's column, coverage pixels near-black. The bisect that found it: the
  catcher-view probe (786px) vs pole-camera-invisible (469px near-black) —
  the catcher was a shadow catcher all along, so the F-recipe is the block.

## 2026-10-16 — piling height −10%

`Crown Height` socket 0.55 → **0.47** (the pole 0.8 → 0.72 total; the fixed
0.25 water depth untouched — the crown band shrinks 0.08 per the fixed-depth
model). NOTE: the socket value must be set BOTH on the tree default AND the
modifier override (`mod["Socket_2"]`) — the modifier value wins evaluation
(the tree-default-only edit silently did nothing). Verified: frame-5 top
z = 0.556 = 0.72 − sink(0.164); wet band unchanged (z ≤ 0.25, ~11px in-cell);
cuts/shadow/wet ring ride parametrically. Full chain re-run: 108/108 all
strips, wet-band size −13..−12 (constant), sheets bit-equal, save load-checked,
window alive.

## 2026-10-16 — jitter keys were starting at frame 45 (maintainer catch)

Socket_4/Socket_17 (jitter X/Y) carried their 108 keys on frames 45..152 only —
frames 1..44 held the frame-45 value, so the first third of the sheet had zero
lateral jitter (the centroid σ 3.1px = 4.0px × sqrt(64/108) — the tell).
Re-keyed both sockets on frames 1..108: paired gaussians seed 41004 (X then Y),
σ 0.0625, CONSTANT interpolation; modifier static values set to the frame-1
draw. Verified: first evaluated change = frame 2; drawn σ X 0.0628 / Y 0.0556.
Full chain re-run: centroid σ now X 4.0px / Y 2.6px (Y stays smaller because
the water plane absorbs part of a vertical shift); luma/wet-band/sheets all
unchanged-clean; save regen + view ok. NOTE: other param sockets' key lists
are a historic patchwork (1..64 dense, stray 71, 110..152) but they vary
everywhere they render — left untouched; flagged for a future tidying pass.

## 2026-10-16 — durable backlog note

Created `docs/BACKLOG.md` carrying the maintainer-queued FULL TIDYING PASS
(fcurve timeline hygiene incl. the 1..64/71/110..152 patchwork + dead keys
beyond 108, legacy blend objects, naming-law remnants like the modifier name
pole_builder and POLEAction.004, .cache quarantine cleanup, README
reconcile). Per-transaction rule: measure, bit-hash, one candidate per step,
journal entry each.

## 2026-10-16 — Stage B opens (transition swap)

Step 1 = READ-ONLY measurement of the transition layout (gen-textures.py +
PIL on pilings-exp.png / pilings-mask.png + the frozen data-updates.lua
transition entry). Step 2 = present the re-layout plan. Step 3 = gated edit.

## 2026-10-16 — Stage B: transition asset = our icon frames (simplified per maintainer)

Directive: "copy-paste our 64x64 icons into the asset and use it for the ford
transitions" — no anchors, no water-backdrop composite, no waterline math.
- bake-transition-sheet.py: icons64-wood pasted 1:1 into the 108 transition
  cells (inner 8x4 @0, outer @576, side @1152, u 2x4 @1728, o 4x1 @2304; the
  gen-textures loop order, frame k -> cell k); masks64 pasted at the same
  cells into the gray sheet. Pure bit-copy arrangement; 108/108 cells
  bit-equal verified, unused sheet area clean. Writes mod/graphics/
  pilings-transition.png + pilings-transition-mask.png.
- data-updates.lua pf points at the new files. The mask stays a separate file
  because the transition API takes the art and the dryness map as two
  different spritesheet paths (gray data cannot ride inside color art) — the
  same separation as our wetness law.
- Old asset (pilings-exp.png / pilings-mask.png) deleted per "get rid of";
  git-recoverable. The old art's opaque water cover (the 12-round
  pre-darkening shield) is NOT carried over: the engine's shore darkening
  now shows around the bare poles — the in-game look decides.
- Test game cleaned: the 61 wf-view-piling decoratives + prototype + the three
  deployed sheet PNGs removed ("the big texture of pilings now serves no
  purpose"). bake.sh deploy = the transition builder; bake-save's guard
  checks the transition asset. Save regen (headless load OK) + window alive;
  the ford's water edges now wear our real sprites.

## 2026-10-16 — shadow layer registered; sculpt grass->ford (maintainer eyes = verdict)

- Shadows are their own sprites, registered in the lua: the art transition
  entry gained `background_enabled = true` + `background_spritesheet =
  pf.shadow` + `background_mask_enabled = false` — the transition's background
  layer always draws BELOW the pole overlay (docs: TileTransitionsToTiles
  background_* fields). bake-transition-sheet.py now also pastes shadows64
  into pilings-transition-shadow.png (3200x2368, same 108 cells, bit-equal
  verified). Headless load OK = the entry parsed.
- Sculpt: maintainer rejected the land island ("lose the strip of land in the
  water") then specified the fix: replace the grass with ford so the spawn
  stays on the walkable tile — control.lua now lays water-ford x -14..14,
  y -2..6; water everywhere else; spawn {0.5,4.5} unchanged on ford. Save
  regen + window alive.
- The save is PERSISTENT (on_init-only scenario, zero Lua on load): manual
  in-game editor edits would stick, but the pipeline `save` stage regenerates
  and would clobber them (maintainer informed).
- Programmatic pixel forensics on the window capture could not cleanly
  separate the water-effected ford tiles / shadow translucency from the HUD;
  the render verdict is the maintainer's (strip gone? shadows east of each
  pole?).

Follow-up: the maintainer still saw grass because the previous regen had died
in the save stage and left NO zip on disk — the on-screen factorio was the old
process showing its in-memory state (the capture reused the same X window id:
the tell that no relaunch happened). The retry ran clean end-to-end (zip
regenerated + HEADLESS LOAD OK + fresh window). Lessons: (1) after a save-stage
failure the old game window persists and shows stale state; (2) the capture
script must require a NEW window id (and the zip present) before trusting a
view; (3) the maintainer's eyes on a stale window are not a regression signal
— verify the pipeline state on disk first.

## 2026-10-16 — Version D verified ring-free; the shore-effect ladder

Maintainer verdict on the stepped-back version (the original gen-textures
asset): "correctly has no shore effect". That pins the dark frame to the
transition-pipeline content, not the tile registration: the engine
PRE-DARKENS the water beneath every transition piece (the vanilla shore
contract); Version D's opaque baked backing covered it, our bare sprite
frames exposed it. Both versions share the identical tile-level config.

Chosen fix (maintainer-approved kludge, pending a possibly cleaner word from
the factorio devs):
1. Effect-map else-value 0 -> 170 in bake-transition-sheet.py: the piece
   cell's whole else-region now suppresses the water rendering (waves +
   pre-darkening); the piling silhouette keeps its spec ramp (crown 170 dry,
   foot 85->25 hold) for the semi-submerged look. Config filenames unchanged.
2. Piling shadow layer, attempt 2 with corrected flags: background_enabled
   + background_spritesheet + background_mask_enabled=false +
   draw_background_layer_under_tiles=false (attempt 1 likely drew UNDER the
   water tiles -> invisible) + background_layer_occludes_light=false (do not
   feed the water mask). Sheet pilings-transition-shadow.png (bit-equal
   pasted shadows64) sits on disk ready.

Open risks: the else-170 rim = static water like Version D (accepted
there); the old generator's "R>0 = dark patches" note = watch for; the
AA edge px (1..6) keep near-zero values = a possible 1-2px remnant ring
along the pole silhouette. The shadow background path is attempt 2 of the
engine channel; if it still renders nothing, next = a separate transitions
entry with explicit overlay_layer_group/offset. Verdict = maintainer eyes.

## 2026-10-16 — the black background: the else-170 was the culprit (maintainer catch)

Maintainer: "the black background is not gone" after the background-layer
revert; two changes had shipped in one turn (else-170 + background attempt 2),
so the black = the else-170. CONFIRMED SEMANTICS: the effect map's R channel is
the water-side darkening ("dry dirt" shading) itself — R>0 = dark patches
(literally the old generator note); the old asset's 170s sat under opaque art
and were never visible. An else-170 tile-wide = black cells under the waves.
Reverted: the mask sheet = bit-equal paste of the spec mask (else 0) again.
Now live: art + spec mask + the SHADOW as its own second transitions entry
(below the art entry, overlay_layer_offset -1, same group, same effect map) —
its first unobstructed look. Still open: the shore pre-darkening ring (R=0
else) — the cure remains the opaque backing (D's approach) or whatever the
factorio devs' answer is; a kludge hunt on the effect map is dead.

## 2026-10-16 evening — deep-water clone era (maintainer-directed bisection)
- is_foundation=false: rim unchanged → reverted true. transition_merges_with_tile="water": unchanged → kept.
- Clone source → data.raw.tile["water"] (maintainer order): deck buried by the effect (vanilla water effect_color = opaque; shallow's = 12.5% alpha — read from base prototypes).
- Copied shallow's translucent effect_color pair → deck restored on the water clone. Water clone shows NO rim under the opaque wash… but see the probe.
- Pilings entry re-instated on the water clone (strip-built sheets, same layout/effect_map as git-HEAD). Pieces verified on the rim cells.
- Ordered probe: pilings transition disabled → rim STILL present (touch 91/97 vs row2 110/114). Mask acquitted; the rim = the water effect's shore pass around the ford tile. The "no rim on water clone" reading = occlusion artifact.
- Config parked mid-probe: entry commented (--[[ ]]), transitions = nil. Full state + bisect list in docs/RESUME.md.

## 2026-10-16 evening — the shore-rim investigation formalized and run (see docs/shore-rim.md)

Session arc: pre-session chat established project rules (screenshots in
absolute coordinates — now in superproject AGENTS.md; experiment-design-before-
work), then the how-to-investigate doc (scope template + interventions:
intent/expectation/observation separation, git-rollback reverts, pre-documented
tensor). The investigation got its own file (docs/shore-rim.md) with the scope
and the full intervention ledger.

Prior session's conclusions were DISCARDED by the maintainer (heavy
hallucination); tonight's facts stand on fresh measurements.

Key results (all recorded in shore-rim.md with capture provenance under
.cache/ford-factory/provenance/):
- layer 9→3 and is_foundation flips: rim persists (acquitted).
- effect_color response surface: deck = lerp(E(tint), water, primary_alpha);
  E tracks the tint values (water-exact tint → pale-mint "washed" endpoint;
  dark scaled tint → rich planks endpoint ≈ the reference look). Secondary
  alpha/color provably inert (bit-identical renders). The rim scales smoothly
  with the tint's deviation from the water color (C-ladder: x0.9→2.8 G dip,
  x0.5→13, x0.2→21) — strong planks and no rim are inversely locked inside
  the effect.
- The water-treatment gate: effect="water" + membership via EITHER
  layer_group="water" OR water_tile_type_names registration — removing one
  leaves the treatment on (L-family); the ford holds both memberships.
  layer_group rides in silently via the deepcopy.
- Probe tiles: no-effect tiles in-lake carry no shore rim on adjacent water;
  tile art alpha is FLATTENED (alpha-0 pixels render opaque RGB — the
  remembered under-tile does not show through, is_foundation set); is_foundation
  ruled binding-true by the maintainer (under-tile memory; docs silent on
  semantics; measured render/rim-neutral). Cloud shadows drift over the scene
  (positional capture artifact; judge under unshadowed moments).
- Harness now carries in-world reference blocks (foundation everywhere):
  raw-wood land comparator, dark-sheet probe, property-bisect probes, checker
  probes, plain probe — every future capture includes them.
- Capture/measurement: absolute-coordinate screenshots (game.take_screenshot,
  zoom=1, 32px/tile, centered {0,2.5}, no HUD), noon-locked lighting
  (always_day in the view scenario), calibrated band tool (measure-rim.py),
  row runner sweep-row.sh with provenance naming (unique, never overwritten).

Parked state: working-tree data-updates.lua = L3 config (water-exact tint,
12.5% — a sweep state, NOT the parked probe config); the parked baseline
lives in data-updates.lua.parked; restore = cp snapshot over data-updates.lua.
Live window on L3. The maintainer is taking the work in a NEW DIRECTION —
next session's first decision; candidate paths discussed are in
shore-rim.md Open items (interior tint calibration + boundary opaque-composite
pieces vs other directions).

## 2026-10-17 — composite boundary, shadows survey, route (a)
X-family: two stacked transition entries do NOT render additively — same
group+to_tiles → last entry wins, flat cover's seal vanished (rim back to
uncovered grey-51 level, matching U2); `apply_effect_color_to_overlay` WORKS
on regular entries but tints the whole stamped art incl. background (X2).
P-family: the composite sheet (flat-water background alpha-composited under
the existing piling frames, single entry, mask kept) sealed the halo at
covered level (−0.1/0.9) with posts rendering (P1); the flag variant P2
shifted the seal. **P1 committed** (maintainer): W3 deck + P1 boundary is the
baseline; P2 set aside. Patch lesson: never reuse indices into rebuilt
strings — anchor all insertions on text markers. Test bench moved into the
mod (`mods/water-ford/testing/{scratch,wf-piling-viewer}`) per directive;
runner/bake/save paths repointed; first bake verified from the new location.
Shadows topic scoped as poles with shadows/reflections; survey done against
vanilla prototypes (character, steam-engine, trees, turrets) + api json:
`draw_as_shadow` = sprite-level shadow pass, `water_reflection` = entity-level
(EntityWithHealth/Corpse only, dedicated pre-drawn sheet), TilePrototype has
NO shadow/reflection mechanism. **Decision: route (a) — poles stay pure tile
art**; knowledge preserved in docs/shadows.md (build-time cheat sheet) for
the next graphics build.

## 2026-10-17 — boards research phase (ford-boards arc)

Direction from the maintainer (ticket chat): ballast-in-sprite is the lead
option for the ford deck (pebbles between boards / boxes; wider seams are on
the table — inherited seams are 1px); engine doodad (decorative) composition
is the fallback; land tile = plain single-cell flooring (buildable-on, unlike
the ford), not "anything special"; land recipe = ford minus ballast, py also
minus log (no sleepers on the tile face — water-side logs stay represented by
the committed pilings); palette from py gravel/stone + vanilla stone assets,
mid-to-light half only for BOTH sets; lighting = 1 directional + 1 ambient,
positions lifted from ford-posts.blend; factory structure is agent's call;
rich tiles = stretch goal, single-cell first.

Research executed (docs/boards-research.md — full findings + decision points
D1-D6): R1 deck art measured (4 courses @8 game px, seams at rows 15/31/47,
palette #96693b-family L106-123 + gap #3e2816 L43, value band 43..128, grain
13.7-14.5, staggered butt joints = variant identity; planks.png byte-equal
planks-base.png today). R2 stone palettes harvested from py item icons +
vanilla stone. R3 rich-tile mechanism decoded from tile_variations_template
(one sheet, y-banded size 1/2/4/8). R4 doodad: spawn-decoratives does NOT
exist in the prototype API (create-particle/destroy-decoratives do);
LuaSurface.create_decoratives is script-only -> control-stage exemption would
be needed (invariant 2) -> fallback status confirmed. R5 concrete consult:
no is_foundation on concrete (landfill only), ground() mask, layer 13,
decorative_removal_probability 0.25. R6 rig: KEY = POINT light (-42,0,42)
energy 40000 white + world bg 0.55 @ 0.06. R7 W3 mix sim: pop band = stones
authored L120-155 (warm ochre/bright-crush/sandy), avoid khaki/grey-mid
(post-mix dL negative vs plank L107); gap mixes to L56. R8: transition pieces
contain no board content (docstring + numeric) -> c3 composite re-derivation
moot unless fill/poles change (D2). R9: bake.sh stage/--twice shape recorded.
Scratch: .cache/boards-research/ (extract scripts + swatches + JSON).
Commit: beac4c4 (findings), 46b2fb7 (register).

## 2026-10-17 — boards visual-model round + spec
Maintainer discussion: bows at mid-span (≤¼ board width), 2 bolts per end,
varied lengths/widths — asked for the standard tiling-ratio scheme. Answered
with measured precedents (SA platform floor tone-neutral edges; inherited
art's fixed seam lattice + tone continuation + bottom edge strip) → rule:
"pin the boundary furniture, free the interiors" (boards-research R10).
Scheme table A/B/C; maintainer: explore visually, don't pre-decide; approved
big-floor render + per-tile slicing (law-3 arrangement), 64px/tile depth.
R11: `bound_decoratives` discovered — doodad fallback is prototype-native
(D4 amended; bench probe only if pursued).
Deliverable (a) v1 committed: docs/boards-visual-language.md (anchors, tiling
law, palettes, rig, engine constraints — v1 pre-exploration).
Next: S2 Blender phase per boards-research.md §Blender phase plan — launch
visible Blender on :0 (mcp-for-blender bridge verified running), build the
base wooden floor model (no ballast/trim), preview renders for gwenview.

## 2026-10-17 — S2 Blender session: base wooden floor (v1 for review)
Visible session via blender MCP (law 2) on :0; ford-boards.blend created and
saved (17.8 MB). Factory: scenes FLOOR+LAND sharing collections
(BOARDS/UNDERLAY/LIGHTING/CAMERAS shared; BALLAST+TRIM created empty,
excluded in FLOOR, absent from LAND); KEY verbatim-then-adapted
(see scene custom prop boards_rig_note): distance x3 for falloff flatness,
energy calibrated x4.5 (iter3) to hit planks anchors; world 0.15 (no-true-
black); underlay raised for shallow seams; Cycles 96ss adaptive, no denoiser
(build lacks OIDN); view Standard (posts' AgX ate the midtones vs anchors).
Floor: 24x24 tiles at origin, 64px/tile; zones: A bolted bays (83 courses,
1441 boards, caps+2 hex bolts per end, sin2 bows <=1/4 width, 2/4px seams),
B through-running pinned-wave rows (94 courses, interior splices only, 1/3px
seams), C hybrid alternating rows (82 courses, A-style furniture per-row).
Two build bugs found+fixed via ray-cast diagnosis (accidental B+C merge into
one mesh pair; duplicated coplanar furniture in C causing z-fight blacks).
Numerics v3: cells L100.7-118 (anchor family), no true blacks, falloff W:E
1.05, hue on-anchor. Preview assets in .cache/boards-research/previews/
(base-floor-v3, crops-zoneA/B/C, sheet-mockup, tiling-selftest,
tiling-adjacent-runs). Awaiting maintainer gwenview verdict.

## 2026-10-17 — maintainer feedback round: plank colorings from the pilings palette
Feedback at v3: wood too uniform; wants pool-of-colorings per plank and the
palette taken from the pilings' cap/side textures. Probed ford-posts.blend
via in-session library-append: M_PILING is fully procedural (per-instance
bark_off attributes -> noise+wave -> two ColorRamps; Normal-Z mix = cap vs
side). Extracted both ramps verbatim:
  side ramp stops (lin): (0.504,0.476,0.434) / (1.91,1.798,1.453) / (1.797,1.453,0.85)
  cap  ramp stops (lin): (0.04,0.034,0.034)   / (1.345,1.11,0.757)  / (2.011,1.636,0.957)
Family exposure to our calibrated rig: x0.159. Pool of 8 plank colorings
(scene custom prop plank_pool): side_mid, side_warm, side_grey, cap_bright,
cap_mid + 3 mixes; per-board seeded pick (random.Random(77000+z*401+c*17+si*7),
weights 3,3,2,2,2,2,2,1, no immediate repeats) written as per-face attributes
plank_rgb (FLOAT_COLOR/FACE) + plank_seed; M_PLANK shader = piling family
kin (Attribute -> Wave Y-bands scale 34 + noise 2.7 distortion -> MapRange
0.74-1.06 -> multiply pool color); caps = posts cap-ramp ring bands
(X-bands scale 26) via M_CAP_ENDGRAIN. Flat 4-anchor wood materials retired.
v4 render: 41 distinct wood bins, top-1 share 27.5%->13.4%, floor mean 114
(inherited ~110), cells 92-132 (overshoot flagged for verdict), blacks 0,
gaps 49-68. Previews rebuilt incl comparison-planks-vs-v4.png (inherited
planks row over our 512x64 mock, same layout). gwenview launched on :0 with
the full review set. Render-loop lesson: MCP exec timeout 60s < render time:
use bpy.app.timers fire-and-forget + flag polling next time.
Bugs fixed this round: `not X if cond else Y` precedence inverted zone B/C
row styles (B/C built as identical hybrids) — corrected with explicit
parens; ZB/ZC rebuilt, structure verified by ray probes + histograms.

## 2026-10-17 — feedback round 2: honey tones, grain arcs, poly bump, bolts 4→2
Maintainer verdicts: wash out in the "nordic white pine" range → mix in the
honey/amber tones of the original floor art; wants visible cross-cut
undulating grain (the v4 wave wash was invisible); poly count on boards
2×+ (jagged bow facets, strange catchlights); bolts per joint 4→2 (single
width-wise pair).
Changes:
- M_PLANK v2 (31 nodes): grain = per-board arc (0.5 − sin²(π·u))·amp(0.02-0.075,
  amp seeded) + noise ripple ±0.035 (scale 6.5) added into the wave vector
  (bands Y, scale 80) → MapRange 0.70-1.08 multiply over the pool color; new
  face attrs plank_origin/plank_len alongside plank_rgb/plank_seed (shader
  overlay approach, per board — no custom textures).
- Pool 8 → 12: + honey entries straight from inherited planks.png anchors
  (150,105,59)/(151,107,66)/(153,114,69)/(140,102,58) as albedo-linear;
  weights [3,3,2,2,2,2,2,1]+[2,2,2,2]/25 → honey 32% of picks.
- Boards re-emitted at 4px columns (was 8px: ≥2× verts); bolts 12-gon,
  per joint single width-wise pair (A-rows: cap side alternates by row).
Incident + diagnosis (documented for reproducibility): a duplicated unlinked
Principled (0.8 grey) wired to the active Material Output + stray duplicate
world Background (0.05@0.15 — also revealed my iter-3 ambient raise had hit
the template node = no-op) made v5 render ×1.6-3.5 hot with desaturation;
bisected via (a) world-only probes (exonerated ambient), (b) attr-direct vs
full-chain (exonerated shader: both "bright" in broken probe), (c) 2-plane
rig test (revealed the in-session probe double-encoded sRGB → probe numbers
inflated, hence false alarm on a second blowout). Ground-truth = bash PIL.
v6 verified: zones 114.9/112.4/106.2 mean, cells 90-126 (mean 111.2,
inherited band 107-123), blacks 0, bolts p99 145 (cap 185 family),
67 wood bins, top share 11.1%, honey bins r/g 1.29-1.50 present.
gwenview relaunched with comparison-planks-vs-v6 (3-row sheet) + v6 set.

## 2026-10-17 — feedback round 3: grain direction/visibility, honey 3/8, bolts
Maintainer: grain runs perpendicular = actually (a) fine grain was INVISIBLE
(subpixel: wave "scale" = waves-per-unit, so scale 80 = 0.8px bands, AA
averaged them away — maintainer right on both counts across the rounds) and
(b) what read as grain was the wide bow-shading band across the board.
Also: honey to ~3/8 (visual read was 1/4); greys = spice, not flavour; keep
2x poly density + improved bolts; bolts still don't read in pixelart.
Changes:
- grain redesigned art-style: wave scale 8 (period 4 game px), arc 0.02-0.05,
  ripple +-0.008 (long coherent lines), NARROW DARK STREAKS via color ramp
  (0.78 stop at phase 0.78 = -22% line, 1.03 bright return) replacing the
  sine maprange; per-pixel streak depths measured 10-16L row-P2P, deeper
  per-pixel; still to be visually confirmed by gwenview.
- pick weights W = [2,3,1,3,3,1,2,1,2,2,3,3]/26: honey 10/26 = 38.5% (3/8),
  grey spice ~11.5%; verified in renders: honey-hue pixel share 37.4%.
- bolts: r 0.030 (dia ~1.9 game px) 12-gon, iron body L~72 (was grey L111),
  rough 0.22 spec 0.7 (highlight pop); caps 4px proud 0.008. Rendered dark
  iron pixels mean L77 vs boards L110-116 = strong contrast; reflection/
  lighting work on bolts deferred per maintainer ("later").
- incident (documented): after a probe session I forgot to restore render
  res 512->1536: v7 rendered small (35KB junk) — restored, v7b true depth;
  also the earlier "world 0.15" raise + world/template confusion cleaned:
  world = single Background 0.55@0.06 verbatim.
- in-session numeric probe lesson: img.pixels for saved PNGs are sRGB-encoded,
  NOT linear — a helper encoding again inflates (the false "blowout"). bash
  PIL is ground truth. Renders now: fire-and-forget via bpy.app.timers +
  file/flag polling (MCP exec window is 60s, renders exceed it).
v8 numbers: zones 114.4/115.9/108.6; cells 96-130 (mean 114); blacks 0;
71 wood bins; top share 10.2. gwenview relaunched (comparison 3-row sheet,
grain-closeup-4x, floor, crops, tiling tests).

## 2026-10-17 — grain menu round: the real root cause
Maintainer: grain still uniform; bolts read now, widen pair to ~1/4-1/2 apart;
colors balanced; proposed a LIBRARY of grain options.
Sweeps on the live M_PLANK rendered byte-identical across 8 configs → the
grain chain never reached the render. Root cause found (via a fresh
from-scratch material test): the wave→ramp Fac link was missing on the
hand-built trees (the multiply was scaling by a ramp constant); the v8-era
maprange→ramp swap also lost the input link. Fixed and rebuilt M_PLANK fresh
(6 nodes); sweep now responds per config (windowed P2P 16.5-23.6; control
included). Also found+removed: my abandoned GRAIN_LAB panels were sitting in
the sweep frame (unlinked now); the key light had cutoff_distance=40 at some
point (Custom Distance — kills light beyond 40m; reset to rig 0; likely an
editor-side tweak). COLLAB HAZARD noted: the maintainer's editor session and
my MCP session share the file — interleaved edits (duplicated nodes earlier,
light cutoff, a wave->ramp link added mid-session) make debugging
non-reproducible; protocol needed for shared-session work.
Deliverables: grain-menu-v3.png (8 options A-H, labeled, floor on D = 4gpx
-25% pending pick); bolt pair 1/4-1/2-apart spacing staged (rides the next
full re-bake); honey ~37% kept. Next: maintainer picks a menu letter + scale
preference; one re-bake applies grain+bolts; then 3-depth land tiles in-game.

## 2026-10-17 — feedback round 4 & volumetric turn
Maintainer: bolts wider = big improvement (¼/¾ spacing stays); grain visible
but subtle (≤1 streak/board, wants 2-3x density or more depth); "single
streak pattern across the whole floor is not physical — each piece of wood
has an independent grain"; proposed volumetric x,y,z wood texture oriented
onto planks; asked for online research; likes comparison menus; asked for
another sweep of the scene data model for construction issues.
R12 written: the volumetric design = per-plank virtual cut (hash of plank
seed -> pith offsets cx/cy + ringfreq 8-16 + seed) evaluated as rings
(early/late + ink winter line + pore teeth + fine fibre) multiplied into the
pool color; Cornell "board function" precedent + Blender per-face-mapping
attr precedent + shader.gallery ring parameters. Menu format kept.
Then compact; carry on per maintainer order.

### round-5 build (post-compact): audit + volumetric grain + bolt spacing

Audit (full data-model sweep, both scenes): mesh data CLEAN — every face attr
populated/counts exact, no NaN/zero-colors, material indices all in range,
normals sampled fine, transforms identity, spans ±12, KEY cutoff 0.0, world
single Background 0.55@0.06, FLOOR 96ss/Standard/no-denoise, M_PLANK fresh
6-node chain fully linked (Wave->Ramp->Mix->BaseColor). CLEANED: 24
GRAIN_LAB sweep objects + GRAIN_LAB collection + 10 lab materials
(M_G_G0..G7, CLONE) + M_PLANK_OLD (corrupt tree), 42 orphans purged; DRIFT
fix: LAND samples 24 -> 96 (builder default would have bitten the land
round). Kept LAB_CAM (harmless). Scene now 11 objects, 4 materials.

Bolt spacing (approved 1/4..3/4): moved live furniture bolts: separation
x1.5, midpoint kept = pairs at 1/4 & 3/4 of board width; ZA 1540 pairs,
ZB 1140, ZC 1242, 0 orphans, all units matched; 13 edge-trim pairs at y~+12
(3px-apart strip hardware) detected and REVERTED (they are not board-course
bolts). Flag bolts_half_done set; ZB check: 930+ pairs now in
[w/2 for w 16..24px].

Volumetric grain (R12) BUILT:
- new FACE attrs on the 3 boards meshes: plank_cx/plank_cy (per-plank pith
  position: x = plank mid + (-0.6..+0.6), y = row center ± (2..6), 10%
  near-pith) and plank_ringfreq (8..16/unit), all hashed deterministically
  from plank_seed (sin-hash, salts 1..5); grouping key (seed,origin,len) ->
  1455/1234/1241 planks per zone.
- M_PLANK rebuilt fresh: 40 nodes / 44 links, FULL link list printed and
  verified before rendering (silent-disconnect class pre-empted): rings =
  |P-pith| (+warp 0.12, noise 2.5) x ringfreq x gain + seed phase 13.77 ->
  WRAP(0,1) -> ramp [pale 1.10 -> latewood 0.80 (0.72..0.86) -> ink line
  0.45 @0.94 -> recovery] -> x fibre (noise (3,18) amp 0.24) -> x pores
  (GT knob 2.0=off) -> x plank_rgb -> Base Color. Attribute float attrs read
  via 'Fac' socket (NOT 'Value' — 4.3); CombineXYZ output index 0; beware
  Math hidden inputs[2] when setting MULTIPLY constants.

Menu v4 rendered (mv4-control + density vf08/12/16 + pores + deep, 1024x128
window of the real floor, FLOOR_CAM ortho 16): previews grain-menu-v4.png +
mv4-sbs-4x.png + mv4-vf12-4x.png; gwenview open on :0.
Measures: grain vertical activity dV: control 9.17 -> vf08 11.58, vf12
12.15, vf16 12.48, deep 13.13 (+26..43%); ring lines/board 2-4 (design,
board widths 12-24px vs ring period 4-8px); levels stable (window mean ~117,
p1 54); DEFAULT live config left = vf12 (gain 1.0, STD ramp, pores off).
Column-profile inter-plank correlation ~0 in both control and volumetric —
metric too coarse to separate; independence to be judged by eye (rings
breaking at plank boundaries) on the 4x sheet.
Next: maintainer picks density/depth option; then base-floor render v9 +
full pipeline + in-game tiles at three scales.

### round-5b: B/C wash-out matrix (maintainer question)
Q: will pore speckle / deep winter line survive pixelation? Rendered 9-row
matrix at GAME depth (grain-menu-v5.png + mv5-sbs-4x.png crops): B and C
x {plain, pores, deep, both} + pores-STRONG ceiling row.
Measures: pore option adds only +2..+58 isolated dark px vs ~600 baseline
(window incl. cap/bolt edges) — speckle nearly vanishes at 64px/BU even at
padj -0.30 ceiling; deep line lifts dV 12.15 -> 13.13 and darkens mean by
~1.7 — it survives as 1px ring lines. Default config restored after.

### round-6: locked look rendered out into the mod (dev compare tiles)
Maintainer pick: "8 pores deep" = ringfreq~8 + PORES + DEEP winter line.
Config locked in M_PLANK (gain 2/3, DEEP ramp, PGT 0.74) and saved into
ford-boards.blend.
Rendered the SAME 24x2-tile band at each art depth (Blender, one render per
depth: 32px/tile t32, 64px t64, 128px t128) and law-3-sliced 8 variant tiles
(A-zone x=-11,-8,-5 / B x=-1,2 / C x=6,9,11; rows r0/r1 mixed): 6 sheets in
mod/graphics/: boards-land-a/b/c.png (256x32, 512x64, 1024x128) + identical
boards-ford-a/b/c.png (veil is definition-side). All 8 variants distinct per
depth (chunk-hash check).
Mod wiring in data-updates.lua (DEV COMPARE TILES block): boards-land-a/b/c =
gravel clones (D3 precedent: no is_foundation), autoplace nil, minable nil,
map_color warm plank, full variants replacement (empty_transitions);
boards-ford-a/b/c = water-ford clones (W3 veil layer-9 piling bank inherited)
with new variants.main; all six registered in water_tile_type_names (ford).
Locale tile-name + tile-description entries added for all six.
Mock contact sheet: .cache/boards-research/previews/boards-mock-v1.png (3
tiles per row at 32 world px; ford rows show a STATIC W3 veil simulation
px'=0.75px+0.25(51,51,51) - the real veil is animated). gwenview open.
Next: maintainer paints patches in the map editor, picks the best set;
high-quality sprite follows; deck drop-in scale decision still maintainer's.

### round-6b: in-game launch with the dev tiles
bake.sh --stages save,view --seed 4242: FIRST RUN FAILED — data.raw.tile
["gravel"] is nil: gravel does not exist in 2.1 (terrain rework removed it;
D3's "gravel precedent" reasoning was written against 1.1-era tiles). Fixed:
land dev tiles clone **concrete** (is_foundation absent, artificial-tiles
subgroup, tile_collision_masks.ground(), layer 13) + walking_speed_modifier
1.1 (D3 band; concrete's 1.4 overridden). Second run: save regenerated,
HEADLESS LOAD OK (validates the whole dev block incl. 6 new prototypes),
VIEW WINDOW ALIVE on :0 — water-ford + wf-piling-viewer loaded, log clean.
Launch recipe (RESUME): bake.sh save,view; scratch mods symlink the repo mod
so edits flow in without redeploy.

### round-7: tileable 1x1 atlas BUILT + verified; viewport wedge root-caused
Viewport "all black" report: scene data was clean (F12 bright throughout,
probe 0.45, cutoff 0, no overrides, no GPU); root cause = the viewport's
rendered-shading session held DEAD data-block references after the destructive
rebuild churn (removed-node ReferenceError in blender.log = fingerprint);
fix = shading toggle RENDERED->MATERIAL->RENDERED re-initializes. STANDING
RULE added: after any destructive rebuild, poke the viewport shading
programmatically (now done at the end of every rebuild call).
Window-capture misstep noted: import -window must use the RIGHT id
(Konsole grabbed once); xdotool windowactivate + root grab works.
ATLAS CONTINUITY QA (the real find): global gap lattice exact (48 gap rows,
pitch 32.0px@128 everywhere). Tone pin verified (plateaus +-0.3 L at every
boundary x course). REMAINING defect root-caused: per-board z-phase jumps ->
2-3px DROP-SHADOW strips at every cell x-boundary (localized rows 44 L dark;
slice col-abutment 17.1/40.3). FIX: lattice-PERIODIC board crowns
z = 0.052 + amp*sin(pi*u_tile) — faces coplanar at every cell edge.
RE-RENDER + QA: slice col-abutment mean 3.23 max 6.96 (old planks.png atlas:
6.1 mean / 9.4 max measured) — better than the accepted old art; x-abutment
in the big render 0.28/0.35; rows abut 42.7 (seam-row meets face-top =
intended lattice junction, same class as old art's ~70). Variants distinct
8/8. Sheets swapped in place: boards-land-c.png / boards-ford-c.png
(dev tiles pick them up on next load). gwenview on the atlas render.

### round-8: player-facing items for the dev tiles (maintainer feedback)
Verdict: boards-compare-1 saved under the SAME name (fine — nothing
regenerates it; it is the painted reference ground). The 1x1 tileable set
PASSED in-game ("looks better than the previous boards").
Glitch closed: tiles need an item backside for player placement (landfill
pattern). Addead six items with place_as_tile - land family = concrete
condition (ground_tile, place on ground); ford family = water-ford's exact
water-only rule (water_tile + invert=true) - plus dev convenience recipes
(2 wood + 1 iron-stick -> 4, enabled) and 64px icons (variant-0 crops);
locale item/recipe names+descriptions. Validated headless with a throwaway
config (--create: 2.1 renamed --create-save; zero errors, checksums clean).
Prototype changes need a game reload to appear.

### round-9: 2x2 + 4x4 straddler supplement (maintainer green light)
LAT_BIG built in band y[-18,-8]: 4x 2x2 sites + 2x 4x4 sites; per-band
lattice-periodic crowns (z = 0.052 + amp*sin(pi*u/sw), coplanar at site
edges AND interior butts); interiors: straddling boards crossing cell lines
tone-continuously (0.65 of wide bands), butt joints at interior cell lines,
0-2 splices per long board with bolt pairs, WIDER courses (0.5/0.75 BU =
64/96px@128) from interior pattern tables; plank_course = (offset*4)%4 so
perimeter pins read the neighbors' canonical tones.
QA: sheets 1024x256 (4x 2x2) + 1024x512 (2x 4x4), all variants distinct;
perimeter vs 1x1 pins mean 5.7/6.2 max 26/16 - residual = the documented
cost of wider boards: wide-band flanks cross neighbor course boundaries
(seam stubs 2px@128 every 64px = sub-pixel at game depth + normal board-end
tone steps). Rendered via LATBIG_CAM (0,-12,60) ortho 12; camera swap+restore
inside the timer.
Wiring: boards-{land,ford}-c variants.main now = 3 entries (1x1 count 8;
2x2 count 4 probability 0.3; 4x4 count 2 probability 0.1, line_length 4/2)
mirroring the vanilla template keys; headless --create validation clean.
MISSTEP kept for posterity: first slicing used (ty+18)*128 row mapping -
y-axis flipped; sites are at rows (−6−ty−sw)*128. The "identical 2x2
variants" and flat-L51 sheets were VOID crops (world 0.55*0.06 -> sRGB 52).
Wait: to see sizes in-game the maintainer reloads; big-size appearance under
player-stamped patches is engine-side behavior to verify by eye.

### round-10: dev game relaunched for the size-ladder check
Launched boards-compare-1.zip (20:07 paint state) with the size-ladder mod
pending the maintainer's in-game verdict on 2x2/4x4 appearance under player
stamping; then compact per maintainer order.

### round-11: hand-placement rules fixed (maintainer caught a real bug)
First hand placement (no editor) exposed wrong place_as_tile configs:
condition semantics = "target must NOT lie in these collision layers"
(invert=true flips to "must") - I had named ground_tile on the LAND items
(the LANDFILL shape, water-only) instead of water_tile like vanilla
stone-brick/concrete. Land boards could ONLY place over water. Fixed to
{layers={water_tile=true}} + no invert. Ford family kept water-ford's exact
item rule (water_tile + invert=true) AND control.lua's revert guard now
covers boards-ford-a/b/c too - the guard is the part of the original ford
setup data-stage cannot express (water stayed hidden under landfill: the
stack still counts as water_tile). Tiles now minable->their own items
(land clone was unminable; ford clone would have mined back water-ford
items). Relaunched with boards-compare-1.

### round-12: big-tile variety expansion (maintainer: repetitive stamping)
Maintainer verdict: C tilesets very clearly better in-game (hand-placed;
saved boards-compare-2); complaint = only 4x 2x2 + 2x 4x4 variants ->
repetition. Built LAT_BIG2 frame2 [0,12]x[-30,-18]: 8x 2x2 + 2x 4x4 new
sites, seeds continuing the 77000+si*911 sequence (si 6..15), same
per-band crowns/pins/bolt rules, additive object (no rebuild churn) +
LATBIG_CAM2 (6,-24,60) ortho 12. Sliced 12+4 (2x2 sheet 1024x768 rows of
4; 4x4 sheet 1024x1024 rows of 2, y=0 explicit), all variants distinct;
perimeter vs 1x1 pins mean 8.1/9.3 (= the accepted wide-band flank cost).
Variants rewired count 12/4, probabilities unchanged (0.3/0.1). Template
y-defaults (128/320) never applied to our literal variant tables - they
bypass tile_variations_template, engine default y=0.

### round-13: 16/16/16 ladder at 1:1:1 (maintainer order after vanilla audit)
Vanilla audit: terrain tiles run 16 variants per size with probabilities
0.75-1.0 (dirt/desert p1/p1, sand even no-1x1 and 8x8; our 0.6/0.3/0.1 with
8/12/4 was under both counts and big-format presence). Order: 16/16/16 at
1:1:1. Built LAT_BIG3 (9x 4x4 gap-free 3-wide, frame [0,12]x[-42,-30]) and
LAT_BIG4 (3x 4x4 + 4x 2x2, frame [0,12]x[-54,-42]) with DIVERSITY ENGINE:
8 interior course patterns round-robin (4 new sum-3.5 patterns), per-site
shuffled tone weights (distinct color casts), varied long-run (0.45/0.65/
0.85) and splice (0.25/0.4/0.55) rates, wider crown amp range. 1x1: 8 more
cells sliced from the existing atlas (16 rows of the same render). Sheets:
2048x128 / 1024x1024 / 2048x2048, y=0, line_lengths 16/4/4, probabilities
1/1 (unbiased). BUGS caught by perimeter QA on the way: INTERIOR4[3] =
[0.25]*12 sums 3.0 not 3.5 -> 0.5 BU VOID at two new 4x4 sites' north
((0,-38) and (8,-54) via round-robin; old sites lucky, verified by
deterministic seed replay); fixed additively (LAT_FIX, appended [3.5,4.0)
kc2/kc3 bands + crown-continued) after two misfired strikes (strip at wrong
x; strip base off by one quarter causing z-fight rows at L85). Final QA:
16/16/16 distinct; big-tile perimeter max 26.5 (accepted wide-band level);
no p10<60 anywhere; 4x4 casts spread 109-126 mean L.

### round-16: promotion pass - ford unfrozen, land collapsed (snapshot first)
Question answered plainly: every edit all along went to the REAL mod at
mods/water-ford/mod/; testing/scratch is only a launcher whose mods dir is a
SYMLINK to the real mod, so scratch sessions always ran the working files.
Per maintainer order, new structure testing/testing-mods/<stamp>/water-ford/
now holds dated self-contained copies (README.md explains the scheme and the
side-by-side rename rule). Snapshot 2026-10-17-boards-16-16-16/ = full 14M
pre-surgery copy (old deck art, six dev compare tilesets, 16/16/16 C ladder).
Then the surgery on the real mod:
- water-ford tile UNFROZEN: variants.main planks.png 512x64@0.5 ->
  boards-ford.png / -2x2 / -4x4 ladder (16/16/16, scale 0.25, y=0,
  probabilities 1 on the big two); piling bank, W3 veil, is_foundation,
  minable, water registration all untouched.
- Land family collapsed to boards-land (was boards-land-c): sheets renamed
  boards-{land,ford}{,-2x2,-4x4}.png (git mv); tile = concrete clone with
  autoplace nil, walking 1.1, map_color, minable->boards-land + the 16/16/16
  ladder; item keeps the brick land pattern place_as_tile (refuses water);
  recipe 2 wood + 1 iron-stick -> 4, enabled (economics revisited next),
  localised_name pypp guard mirroring the water-ford recipe.
- Retired: boards-{land,ford}-{a,b,c} tiles/items/recipes/locale,
  boards-ford-icon.png, A/B sheets. control.lua revert guard = water-ford
  only. planks.png stays on disk unreferenced (docs anchor it).
- Headless --create validation clean (check7); dev game relaunched on
  boards-compare-2 (old dev-tile placements in the save clear to water on
  load - repaint with boards-land / water-ford).

### round-17: recipe redesign (maintainer spec), both boards under the ford tech
Maintainer sense-checked spec applied verbatim. Vanilla: floor board = 2 wood
+ 1 iron-stick -> 1 (was ->4 dev); ford board = 1 floor board + 2 wood +
100 stone -> 1 (was 4 wood + 1 stick + 50 stone -> 100; per-ford stone goes
0.5 -> 100 - the deliberate premium repositioning, not a landfill rival).
Py: floor board = the old py line minus log/gravel = 2 treated-wood +
1 iron-stick + 8 bolts -> 1; ford board = 1 floor board + 1 log +
200 gravel -> 1 (ballast stack preserved; treated/bolts move into the
board). boards-land recipe gains its own py_loaded branch mirroring the
ford one; both recipes enabled = false and added to the water-ford
technology effects (prereqs unchanged: concrete / creosote). localised_name
on boards-land recipe upgraded to the full pypp "?" chain matching the ford
recipe. Locale: boards-land item-description no longer claims a stone bed
(art shows no bed on land). Headless validation clean (check8); dev game
relaunched on boards-compare-3 (maintainer save).

### round-18: intermediates out of the shipped mod (maintainer flag: VRAM/clutter)
Maintainer eyeballed the piling sheets and asked why most of the canvas is
blank - answer: the only LIVE piling assets are pilings-composite.png (100%
opaque water BY DESIGN - the round-12 shore-pre-darkening fix) and
pilings-transition-mask.png (full-coverage dryness map BY DESIGN); the
mostly-blank transition/shadow/exp/mask files were bake intermediates
(0.9%/0.6%/5.8% content). Move executed: git rm the four from mod/graphics;
new reproducible home .cache/ford-factory/intermediates/ (untracked,
regenerable). Tool paths updated in the same change: gen-textures.py writes
exp/mask to the intermediates home (planks wash still lands in the mod);
bake-transition-sheet.py writes transition/shadow there (transition-mask
stays live in mod/graphics); bake-save.py harness guard modernized to the
live sheets (was still guarding on pilings-transition.png). Regen check:
exp/mask regenerate into the new home (the git copies had gone stale vs the
current generator - .cache now holds current-truth output; seed-pinned);
planks.png unchanged; headless --create clean (check9); live sheets
untouched (zero diff under mod/graphics besides the staged deletions).
VRAM: unchanged this pass (intermediates never reached VRAM); zip -1.24MB.
Next (standing plan, awaiting go): 128px re-render + tight canvases
(1024x2560+512x1280 separate bands ~13.1MB, or merged u/o ~10.5MB vs 34MB
today at half the density).

### round-19: piling density pass - 128px cells, tight canvases (P1 recipe preserved)
Maintainer eyeballed the sheet canvases (flat-water = "blank" false-negative
resolved: the live composite's canvas is opaque water by design; the truly
spare sheets were bake intermediates, unshipped in round-18). Lineage
re-verified bit-exact: live composite == alpha_composite(flat water
17,114,129,255, icons64-wood frame), worst channel diff 0 across all 108
cells - the P1 recipe (2026-10-17 composite-boundary round). Baseline
captured with the FULL old state first (save stage + window capture
20261017-232712-piling-baseline-64px.png). Then one big change:
- bake-strips.py renders the icon + sprite strips at 128px into density-
  labeled dirs (icons128-wood, frames128); 108/108 verified, --twice re-
  pointed. Metrics: centroid sigma 8.0/5.1px (same relative jitter), luma
  mean 87.
- bake-transition-sheet.py rewritten for TIGHT canvases: art 1024x2176 /
  mask 512x1088; band y inner 0 / outer 512 / side 1024 / u 1536 / o 2048
  (art) and 0/256/512/768/1024 (mask, 64px windows - wetness granularity
  unchanged); o band = 4 cols x 1 rot row (canvas height 2048+128).
  Slack (x past count windows in u/o) stays TRANSPARENT - engine never
  samples it (512-wide mask anchor proof). P1 blend reproduced bit-exact
  at 128 (worst diff 0). Shadow sheet write retired (route (a), dead
  config; last artifact = moved INTER copy).
- data-updates.lua layout: scale 0.25 (art), effect map 0.5 (unchanged),
  y-fields to the tight strides. pf filenames unchanged.
- Headless clean (check10); save stage regenerated the seeded ford-view
  save; new look captured 20261017-233355-piling-128px.png; A/B in gwenview;
  window up for the maintainer's high-zoom eye-check.
- VRAM (RGBA): composite 30.3MB -> 8.9MB, mask 4.9MB -> 2.2MB: 35.1MB ->
  11.1MB (-68%) at double the pixel density. Optional further lever parked:
  u/o same-row merge (~ -2.6MB).

### round-20: wooden bumper edge on boards-land (SHIPPED, maintainer-approved)
Maintainer: "look at the concrete border art, and basically copy that but with
wood boards where the concrete is... side-on boards, looking very much like
the stone trim"; transparent water option, no color-match heroics; 2x
oversample (vanilla parity). THREE-WAY CORNERS DEFERRED (concrete's
between-transitions stay); land-to-ford transition join = future increment.

Audit (from tiles.lua, maintainer pushed back from pixel-forensics to the Lua):
boards-land = deepcopy(concrete) inherited concrete's water transitions +
between-transitions + out-of-map entries. The vanilla sheet splits into three
x-slabs at the layout x_offsets: overlay (x0) = the lip ON the land tile
(single course blending up), background (x1024) = the SUBMERGED curb (double
course + alpha slide-off, drawn beneath the water layer so the water shades
it; pixels are neutral grey - vanilla does NOT water-paint it), mask (x2048)
= flat grey value maps (shore contour/darkening). Cells 64x128 art, counts
16/8/16/4/4, 4 rows per band (o: 1), bands y 0/576/1152/1728/2304.

- v1: overlay-only sheet + background/mask disabled -> submerged curb missing
  (maintainer: "confusing mix", then taught the channel structure).
- v2: all three channels copied (mask passthrough), entry flags verbatim, but
  band y tightened to 512-strides (rows flush, gaps removed) -> maintainer saw
  N/W/SW/SE edges broken ("water renders as mostly waves") = rows 2/3 of every
  band. Bit-compare proved the copy faithful -> the spacing was the suspect.
- v3 (SHIPPED): GEOMETRY-CLONE of vanilla - same 3072x2368 canvas, same band
  y-fields and inter-band gaps; only pigment swapped (overlay+background
  remapped stone->boards-ladder p2..p98 ramp; grey value maps bit-identical).
  Alpha drift 0, 540 pieces, slack 0. Lua entry: vanilla flags verbatim
  (background_enabled, layer offsets, effect_map_layout referencing vanilla's
  concrete-mask.png value map like the out-of-map entry does), to_tiles =
  water_tile_type_names global. check11 clean.
- In-game A/B (viewer patch, same coords): all 8 directions show the wooden
  curb + submerged boards; boards rows untouched (8-direction sweep warm 0.9+
  everywhere); maintainers eye-approved: "That looks correct. So you can bake
  that into the mod."
- Ledger: 27.7MiB RGBA - vanilla-equal (deliberate clone). Tightening the
  canvas waits until row semantics are provable (v2 lesson: the inter-band
  gaps may be load-bearing).

## 2026-10-18 — land trim + wooden three-way corners (round-21)
Audit round-20 closed: vanilla splits land edges into two systems. The water
edge = tile.transitions (round-20's bumper). The LAND-to-LAND edge =
concrete.variants.transition, piece families inner-corner/outer-corner/side/
u/o (square 64x64 cells, counts 16/8/16/4/4, 4 rotation rows, o: 1 row). The
promotion pass had cleared it (empty_transitions=true, transition=nil), so
boards vs grass rendered as a hard cut = the queued TRIM.
- bake-land-trim.py: 10 sheets (5 families + mask twins), geometry clones of
  vanilla concrete-{piece}.png (dimensions inner 1024x256 / outer 512x256 /
  side 1024x256 / u 256x256 / o 256x64, perfectly packed); overlay art
  wood-remapped stone->boards ramp (p2..p98 anchors), masks vanilla bits
  passthrough. Wired as land variants.transition {overlay_layout, mask_layout};
  empty_transitions DROPPED. First patch pass failed on a non-unique anchor
  (the ford tile carries the same empty_transitions pattern) -> anchor on the
  boards-land-4x4 line.
- Three-way corners: maintainer saw STONE at grass|water|ford corners beside
  boards - the inherited concrete between-set (transitions_between_transitions
  fires where two transition-bearing tiles meet). bake-land-between.py =
  geometry clone of vanilla water-transitions/concrete-transitions.png
  (3072x2368, counts 3/3/3/1/0, band y-fields and gaps verbatim per the v2
  lesson) -> boards-land-between.png; overlay+background wood-painted, mask
  passthrough; wired as land between-set entry 1 (default<->water groups,
  background_enabled + layer offsets + vanilla concrete-mask effect map),
  entries 2+3 = vanilla out-of-map verbatim. check12/check13 clean.
- Empirical: the variant trim does NOT fire at water boundaries (south lip
  identical trim on/off, warm 0.96 both) -> no double edge at the bumper; the
  water edge stays exactly as approved.
- Verification went sideways first: interactive console driving degraded
  (stray keys drove game UIs; maintainer walked the game back to player mode).
  HARDENED console law now script-shaped in tools/paper-pipeline/
  console-help.sh: backtick opens the console, "/c " + command, nothing else
  ever typed; artifacts on disk are the only truth. Final cycle (fresh
  relaunch, paint grass x -22..-14 y -18..-3 + boards x -13..-4 y -14..-7,
  capture {center -10,-10.5}): boards 0.94 warm (all sessions), grass|boards
  boundary column warm 0.70 (trim off) -> 0.77 (final), matching the approved
  trim-on capture (0.80). Maintainer eye-approved: "That looks great. Bake
  this into the mod and commit."

## 2026-10-18 — land->ford transition audit: ship as-is (round-22)
Static audit of the boards-land -> water-ford seam: the land side's bumper
entry fires toward the ford (water_tile_type_names includes water-ford;
the ford joined the water transition group) = lip course on the land tile +
submerged curb beneath the water layer, verbatim the approved water-edge art.
The ford side has no entry toward land - vanilla water has no land-facing
transition to inherit - so the ford deck runs plain piling art to the
boundary. The between-set covers three-ways only.
- Both orientations captured in one frame (provenance
  20261018-005810-land-ford-seam-current.png): boards-land strip x -10..8 at
  y -7..-3 (north variant, directly above ford row y -2 - the maintainer's
  emphasized case) and y 7..11 (south, mirrored), capture {center 0,2.5};
  strips 0.92/0.95 warm, ford edges render warm piling art at both seams.
- Maintainer: "To be honest, that looks great. I can imagine improvements,
  but it will absolutely do for this release." DECISION: no dedicated
  transition art this release - the land-side bumper IS the land->ford seam.
  Parked for a future release: a ford-side receiving edge or a dedicated
  Blender ramp/deck model.

## 2026-10-18 — ford deck pebble+stone ballast doodads (round-23)
The parked ballast item lands as engine-native doODADS, not in-sprite art:
- Audit: TilePrototype.bound_decoratives (SA space-platform-foundation
  precedent, SA tiles.lua L278) binds optimized-decorative prototypes to the
  tile; no control.lua. R11 runtime questions answered by a bench probe with
  the SA platform decoratives bound to water-ford: (1) sprinkles fire on tile
  BUILDS (set_tiles fresh-built patches sprinkle; existing tiles do not
  retro-sprinkle), (2) pieces sit OVER the water veil (maintainer confirmed
  live), (3) SA-Default density too high for the deck (maintainer: overwhelming).
- Factory: blender/ford-stones.blend (new family sibling: PEBBLES 24 frames
  @ 40px + STONES 12 @ 64px, heap-of-stones variations, west key sun -
  shadows east - palette anchored to measured vanilla rock decoratives mean
  [79,56,33]). tools/paper-pipeline/auth-stones.py + bake-stones.py both
  in-repo per maintainer law; sheets packed law-3 (400x120 / 640x128).
- Determinism lesson: Blender 4.3.2 PNGs vary CONTAINER bytes per process
  but pixels are bit-reproducible (proven 36/36 across processes); the prover
  must compare pixel arrays (bake.sh's np.array_equal standard), not file md5.
  Boolean-fcurve flipbooks are unreliable (all keys collapse to the last
  state) - the bake stages hide_render per frame directly.
- Wiring: ford-pebbles (target 120) + ford-stones (target 20) prototypes +
  water-ford tile.bound_decoratives; density knobs commented at the wiring.
- Maintainer feedback v1: density good ("a good density of rocks"), shadows
  cast wrong side (sun tilt sign flipped: light from WEST, shadows EAST),
  heaps wanted (2-3 stones per variation), palette = vanilla umber/brown.
  v2 approved: "That is perfect. Bake that." (bench + 4x crop captures in
  provenance 012953-stones-bench2*). Stones render above the water veil.

## 2026-10-18 — boards-land layer below stone brick (round-24)
Maintainer experimented with other floor tiles vs boards on land: the tile
inherited concrete's layer 13 (ground-artificial), and the stone-brick ITEM
places the stone-path tile at layer 11 - boards were sitting above the brick
floor. Changed land_tile.layer = 10 (free slot just below stone-path;
ground-artificial occupancy 5/11/13/15/17/19/25/70, 0-255 band = room to
spare). Stone paths now draw over boards at shared boundaries. Watch-item:
the water edge's submerged curb rides the tile layer
(offset_background_layer_by_tile_layer) - bench showed the approved bumper
look unchanged. check26 clean. Maintainer: "That looks good to me. Bake that."

## 2026-10-18 — stones waterline: sliced above/below + multiplicative alpha (round-25)
Maintainer commissioned the multiplicative-alpha waterline ("slice the
geometry at a uniform height, above and below water mesh, as we did for the
pilings, and use that to drive the multiplicative alpha channel"):
- Mechanism: Sprite.layers per decorative variation - layer 1 = the dry heap
  art (normal blend), layer 2 = the below-waterline slice with blend_mode
  "multiplicative-with-alpha" (submerged part tints with whatever is under
  it: wet boards inside the deck, water at the edges). Auth splits every
  stone mesh at a uniform waterline plane (true vertex ring, piling GN-cut
  semantics; no object tilt so the cut stays horizontal); the bake renders
  aligned ABOVE + BELOW sheets per family (4 sheets, identical grids).
- THE ROOT-CAUSE LESSON of the whole look saga: Blender new objects default
  to rotation_mode QUATERNION, which SILENTLY IGNORES rotation_euler - the
  v1/v2 sun, fill and camera never rotated (top-down renders, camera-side
  shadows, "light from behind the camera"). Fix = rotation_mode='XYZ' on
  every rotated object; verified live via render asymmetry (W/E 1.30).
  Background-probe matrix_world reads identity for objects outside the
  active view layer - misleading; the render engine's depsgraph is correct.
- Balance: key sun 4.2 (WSW-up, shadows east), south fill 25 (the fill
  carries the visible south faces; too strong reads as backlit). Below-part
  material = washed bright mask - a dark mask under multiplicative blend =
  near-black feet (round-25 bug; the feet were there but crushed).
- Bake hard-checks: scene camera assert (SC_CAM), per-frame distinctness,
  warm-earth palette both passes, bit-equal packing, pixel --twice 72/72.
  check25d clean. ford-stones.blend(.blend1) committed (round-23 miss).
- Maintainer: "That's it. You got it right that time."

## 2026-10-18 — item + tech icons (round-26)
Placeholder flat-square icons replaced with composed top-down swatches, pure
arrangement of committed art (maintainer-sanctioned "just compose and crop
sprites"; no blender scene needed - the first attempt was reverted):
- boards-land-icon.png (128): one boards-land tile cell, verbatim.
- water-ford-icon.png (128): the deck cell over the P1 flat-water base
  (17,114,129 - the deck cells carry transparent water-gaps; the gaps now
  read as water) + three stone-heap sprites pasted at the corners.
- water-ford-tech-icon.png (256): a 2x2 of four deck cells + six stone
  heaps around the edges; icon_size 256 = the game downscales.
- Paste rule learned: Image.paste(im, pos, mask) REPLACES the destination
  RGBA (semi-transparent sprite edges punch holes) - alpha_composite with
  manual clipping is the correct over-composite.
- Recipes need no icons: vanilla recipes display the product item's icon.
- Buttons: make-icons.sh (+ the icons stage in bake.sh's default chain).
  The boards tileset sheets themselves have no build button yet (consumed
  by the trim/between/icon builders) - flagged as a build-code gap rider.
- Maintainer: "I like those icons."

## 2026-10-18 — naming & localisation (round-27)
Audit first, then two shipped units:
1. Descriptions rewritten (34b291b): short tooltip slugs on item/tech
   (maintainer copy, verbatim), expanded copy on the Factoriopedia tile
   pages (item and tile are separate pages — tooltip stays short).
2. Display-name/ID rename (this commit), maintainer-approved with a
   breaking version bump:
   - boards-land -> wooden-flooring, "Wooden Boards" -> "Wooden Flooring"
   - water-ford -> wooden-ford, "Water Ford" -> "Wooden Ford"
   - the TECHNOLOGY keeps id water-ford ("Water Fords"); mod id unchanged.
   Locale keys follow the ids; asset filenames (boards-land.png,
   water-ford-icon.png...) deliberately NOT renamed — assets keep their
   historical names, only in-game identifiers moved. pypp "?" guards
   updated to the new keys. placement-denied message now says Wooden Ford.
   Historical journal/research docs keep the old ids (they were true then).
   info.json 1.0.0 -> 2.0.0 (breaking). Another agent shipped the
   mod-portal thumbnail (ff73498) mid-session; changelog notes it.
   Headless check clean. In-game eye-check = restart, Factoriopedia.

## 2026-10-18 — minimap colors (pre-2.0.0 outstanding work)
Both boards tiles now share ONE map color: ochre #cc7722 (204,119,34).
- Before: wooden-ford had no map_color (inherited deep-water blue from the
  clone -> fords read as open water); wooden-flooring had (140,112,78).
- Method: clustered the shipped sprites (boards deck dominant 145,115,84;
  planks/icon amber ~150,105,60; gen-textures piling ramp dark (70,48,26)
  -> lite (224,186,122), capedge (184,144,90)) and scored candidates
  (CIE76 dE) against every vanilla terrain map color. First pick was the
  ramp midpoint honey (147,117,74) — dE 6 vs dirt-1/sand-1, i.e. nearly
  indistinguishable from desert terrain (vanilla's own floor: dirt-1~sand-1
  = dE 1.2). Maintainer overrode: vicinity of ochre #cc7722, "more distinct
  from the sands and dirts" — measured dE 34 vs dirt-1/sand-1, 38 vs
  red-desert-1, 80 vs water; better separated from vanilla terrain than
  vanilla terrains are from each other. Adopted as-is (any drift toward
  brown/muted only shrinks the margin). Swatch sheets + scoring scripts in
  .cache/water-ford-mapcolor/ (scratch).
- Verification: dlc-smoke load smoke PASS; dump-diff vs fresh pre-change
  baseline = exactly 4 field changes (wooden-ford.map_color added;
  wooden-flooring.map_color r/g/b), nothing else. The stale Oct-15
  baseline (.cache/water-ford-refactor/) predates the 2.0.0 rename and
  diffs as add/remove noise — fresh pre-change dumps via stash-free
  checkout round-trip instead. Sprites untouched (map_color is
  minimap-only, no render impact; no locale check needed).
- In-game minimap eye-check still owed before release (map view, dlc
  install).

## 2026-10-18 — thumbnail adopted + AI-art pipeline formalized (round-28)

- Thumbnail: round-3 candidate 1 (old label "variant 5") adopted as
  `mod/thumbnail.png` @288 (commit ff73498) — engineer wading the submerged
  ford, leaping fish. Feedback trail: round 1 style rejected (planks floated);
  round 2 picked V4's direction (1 square-on, 2 surprised, 3 wharf — all
  rejected); round 3 delivered the keeper.
- **Process lifted to devctl** (tooling unit B2, superproject
  `docs/ai-art-briefs.md`): brief at `assets-src/ai/thumbnail/` — brief.toml +
  prompts + reference copies + decisions.md + committed runs/ (all three
  pre-tooling rounds migrated as reconstructed records, prompt→candidate
  mapping verified by hash) + provenance.json (target sha256 verified against
  the adopted round-3 derivative).
- `devctl mods art generate --count 1` shakedown (run 20261018T190142Z): the
  fresh candidate reproduced the accepted thumbnail **byte-for-byte**
  (determinism re-proven live); idempotent re-adopt left target + provenance
  untouched.
- Old scratch libraries (`shared-assets/to-maintainer/thumbnail-roundN/`,
  `.cache/thumbnail-library/`) are superseded by the committed run records;
  kept as scratch until the next session culls them.

## 2026-10-18 — save migration for the 2.0.0 rename (portal 1.0.0 exists!)
The portal API confirms water-ford 1.0.0 IS published (2026-10-14, 6
downloads) — the rename is not just a dev-round concern. The released
1.0.0 zip contains ONLY the ford triple (item/recipe/tile water-ford) +
tech; boards-land never shipped publicly (1.0.1 dev builds only).
- Mechanic (lua-api 2.1.21 auxiliary/migrations.html + IDType concept):
  migrations/<version>.json rename pairs per prototype class; applied
  during map load, tracked by name (no double-apply); "tile" IS a valid
  IDType. Without a tile migration, placed water-ford cells would fall
  back to the surface default tile on load (ford loss). Tech id unchanged
  (water-ford), so research state carries; recipe resets are automatic.
- Shipped mod/migrations/2.0.0.json: water-ford -> wooden-ford for
  tile/item/recipe, plus dev-era boards-land -> wooden-flooring (no-op
  for public saves, converts the maintainer's own boards-era test saves,
  e.g. testing/scratch/saves/boards-compare-1.zip). JSON has no comments
  — rationale lives here.
- OWED in the play-test session: load an old save against the 2.0.0 zip
  candidate; confirm in the log that the migration applied and placed
  fords survive as wooden-ford.

## 2026-10-18 — release renumber: ships as 1.0.1 (was 2.0.0)
Maintainer decision after the migration route landed: only 1.0.0 is
public (6 downloads), and the engine's only version consumers are portal
ordering and migration filenames. Facts that made the renumber safe:
info.json stayed 1.0.0 through ALL dev rounds (verified at 30a64cd and
1df92dd — the "1.0.1 (unreleased, dev tiles)" changelog entry was
aspirational; no build ever carried it), so every save in existence
records 1.0.0 and a migration named 1.0.1.json covers all lineages — no
version-equality trap, and no tags existed to move. Applied:
info.json 2.0.0 -> 1.0.1; git mv migrations/2.0.0.json -> 1.0.1.json;
changelog merged into one stanzaed 1.0.1 entry (Features/Changes/
Balancing/Locale/Bugfixes/Graphics) with the dev-internal arc detail
(compare tiles, promotion passes) dropped — never user-visible; BREAKING
softened to scripts-only (saves/blueprints auto-convert); README,
info.json description and locale mod-description now mention the
flooring. LESSON for future dev-versioned builds: name migration files
above the highest version any save has ever recorded, not the release
version — the 1.0.1-equality trap we dodged by never bumping info.json
in dev.

2026-10-19 — portal page source seeded (`portal/`, new superproject layout
convention): `description.md` reconstructed from the portal-rendered page
(the markdown source lived only on the portal; table/link rendering is
equivalent — treat this repo copy as source of truth from now on),
`summary.txt` byte-exact from the portal API, `portal/images/` stubbed
(gallery currently empty on the portal). Next parity push happens via the
publish tool (inbox/tool-devctl-mods-publish.md, M3). Also noted: repo
README crafting lines (0.1.x recipe) have drifted from the published 1.0.x
recipes; README refresh is owed on the next README touch.

2026-10-19 — `devctl mods publish` landed (commit 19f5852) and was probed
against this mod, publish-safe by construction (maintainer: do not publish
anything yet). Dry-run plan: release mode auto-selected (portal has 1.0.0;
none of the gates blocked), zip sha1 c4c6d0e9… computed, changelog section
for 1.0.1 present. The `--yes` path was exercised ONLY with an invalid Bearer
key, so the portal rejected at init_upload (HTTP 400 InvalidApiKey) and no
byte could reach the uploader — water-ford remains un-re-released (portal
releases: 1.0.0 only, re-verified after the probes). Evidence:
.cache/publish-probe-{1-dryrun,2-yes-invalid-key,3-mode-404}.log. The real
1.0.1 release upload waits for the human API-key step (blocked ticket
blocked/tool-devctl-mods-publish.md; trigger = key slot non-empty in
devctl.conf). Nothing to do on the portal side until then.

2026-10-19 — publish tooling live-verified via a dedicated deprecated scratch
mod (maintainer-authorized; see inbox/tool-devctl-mods-publish.md): first
publish 0.1.0 and release upload 0.2.0 both sha1-verified against /full, then
deprecated. Water-ford itself remains untouched on the portal (releases:
1.0.0 only) — its 1.0.1 upload and any page polish wait for an explicit
maintainer go per case; the tool will plan them (read-only) on request.
Also caught today: devctl.conf was erroneously TRACKED since the
.env→devctl.conf rename — untracked now with ignore entries (commit
500f0dd); no secrets were ever in its history.

## 2026-10-18 — portal page content for the 1.0.1 publish
description.md + summary.txt rewritten to the maintainer's editorial line:
sell the why only (new decorative tiles; players + biters + py caravans
cross, fish and Cargo Ships unaffected), no in-game-available detail —
recipes, unlock tech, speeds, layering and migration logistics all cut
(migration lives in the changelog; portal shows compatibility itself).
summary.txt 277/500 chars. Verified the publish tool's contract
(lib/portal-publish.py): RELEASE mode ships the zip only — description/
summary/gallery are first-publish-seed or edit_details/images calls the
tool does not implement yet (M3); until then the page updates via the
web UI from these files. Gallery convention documented in
portal/images/README.md (numeric prefix = display order).

## 2026-10-20 — launch failure, asset rename, the load-gate
The audio agent's launch failed: "File __water-ford__/graphics/
wooden-flooring-between.png not found". Root cause: rename commit 349b513
rewired 14 asset references to wooden-flooring-* while the committed files
kept their historical boards-land-* names — violating its own "assets keep
historical names" decision. WHY THE GATES MISSED IT: --dump-data and
dump-diff never validate file existence (data stage carries only path
strings), and the post-rename baselines contain the same broken strings on
both sides. The maintainer had not play-tested since the rename.
- a4963fa: references restored to committed names (staged fix-only via
  hash-object/update-index — the audio session was mid-edit in the same
  file; their diff stayed clean).
- 4775141: MAINTAINER DECISION — assets renamed to in-game identifiers
  (supersedes round-27): boards-land-* -> wooden-flooring-* (17),
  boards-ford* -> wooden-ford-* (3), water-ford-icon -> wooden-ford-icon
  (tech icon keeps water-ford-tech-icon — the tech id IS water-ford).
  Descriptive names stay (pilings-*, ford-decorative-*, planks* sources).
  Tools rewired (gen-branding, bake-land-edge/trim/between, make-icons);
  gen-branding verified pixel-identical regeneration under the new name.
  The audio agent committed their footstep work mid-sequence (c1e00da,
  4a994f2, 58dda88) — 4775141's data-updates delta is provably path-only.
- tools/check-assets.py: the load-gate the data-stage checks lack —
  every graphics/sound reference (incl. sound_variations prefix
  expansion, non-padded) must resolve to a shipped file; flags stray
  shipped assets too. 27 graphics + 23 sound refs, all present. Caught
  the author's own double-dash rename bug on its first run.
- check suite vs pre-rename baseline: 7 field changes, all intentional
  (4 asset-path fields + recycling-icon fallout + 2 walking_sound from
  the audio agent). smoke + locale PASS.
LESSON: "assets keep historical names" + identifier renames = drift by
construction. Asset filenames now track in-game ids.

## 2026-10-20 — footstep audio shipped (six curation rounds, 23 assets)

Ticket `inbox/produce-water-ford-footstep-audio.md` actioned (prerequisite
`docs/how-to-do-audio.md` was complete). Sources: 3 maintainer phone captures
(`assets-src/audio/source/`, 44.1 kHz mono mp3). Curation: Audacity driven via
mod-script-pipe (`/tmp/audacity_script_pipe.{to,from}.$UID`; transport NOT
scriptable; invalid params open a modal that wedges the pipe — restart to
recover), `LabelSounds` auto-segmentation (−25 dB / 0.3 s / 0.1 s) → 25 hits;
maintainer ear-verdicts over six rounds against a local HTTP listen page
(verdict manifests in `.cache/ford-audio-import/`, scratch).

- **Assets**: 13 `flooring-N.ogg` (12 board steps + P1 squeak at 0.3) + 10
  `ford-deck-N.ogg` composites (splash leads the thunk ~120 ms, board 0.85 /
  splash 1.0, splash runs its natural 0.44–0.66 s). Built by
  `tools/build-audio.py` — deterministic, all knobs embedded, idempotent ogg
  writes via decoded-PCM compare (container serials differ per encode).
- **Wiring**: `walking_sound` on both tiles in `data-updates.lua`, clone-source
  volumes (concrete 0.5 / shallow-water 1.0), vanilla cosine fade-in. core
  sound-util defines GLOBALS — `require` returns true, indexing it dies.
- **Root-cause chain** (all in superproject `docs/how-to-do-audio.md` §11):
  the rounds-2–4 "pops" were ONE istft edge-normalization bug (fix = one-frame
  padding); the peak-picker must be pinned to label±0.25 s (it wandered 840 ms
  into house noise); musical-noise taming (median gain filter) ended the
  residual tail ticks; `--dump-data` smoke does NOT load the sound library —
  9 missing oggs passed smoke and failed only at game boot (non-padded
  `-N.ogg` naming was the miss).
- **Verification**: dlc-smoke smoke PASS; dump-diff vs pre-audio baseline =
  exactly the 2 intended `walking_sound` fields, no collateral. Stray tracked
  leak `mod/mods/...` removed (invariant 1).
- **Licensing note**: composites embed vanilla splash audio — permitted as a
  derived work per the Factorio ToS (Wube retains rights/removal right);
  recorded in `tools/build-audio.py` header.
- **Pending**: in-game listening pass (game launched; volume verdicts),
  changelog under 2.0.0, push, ticket removal.

## 2026-10-20 — ford crossing speed 0.9
Audio play-test passed; maintainer's final gameplay tuning: the ford gets
walking_speed_modifier 0.9 — faster than wading shallows (water-shallow
0.8) but slower than dry land (1.0); "a wet deck, not a boardwalk".
Previously absent (= 1.0, inherited from the impassable deep-water clone
that never needed a modifier). wooden-flooring stays 1.1 (D3 band).
Balancing changelog bullet added. Gates: assets OK (27+23), smoke/locale
PASS, dump-diff = exactly tile.wooden-ford.walking_speed_modifier.

## 2026-10-20 — py-closure vs engine 2.1.22: blocked by py, data-stage proven
Fresh env spec envs/py-closure.toml (the v0 env system cannot chase
OPTIONAL deps to install zips — roots are projects only — so the closure
reused the documented hand-assembled .cache/water-ford-refactor/pymods
set: 17 py zips + water-ford link + explicit mod-list, space-age off).
Result on dlc 2.1.22: data stage COMPLETES (checksums for every mod incl.
water-ford; zero water-ford errors; pypp final-fixes ran through the
renamed ids) then the engine dies at entity validation of pyfusionenergy
3.1.5's own gasturbinemk01 (FluidBox min/max_temperature removed in
2.1.22). The Oct-15 closure passed the same set on 2.1.21 — the install
auto-updated since. CONCLUSION: stale py zips vs the new engine, not a
water-ford regression; py users on 2.1.22 are broken regardless. The
1.0.1 py-facing surface (recipe ids, pypp guards) is proven at data
stage, which is everything 1.0.1 touched. Full-closure re-run owed when
the py suite ships 2.1.22-compatible zips (or on a pinned 2.1.21
install).

## 2026-10-20 — 1.0.1 PUBLISHED
devctl mods publish water-ford --yes: release upload verified (portal
sha1 == local 6040fcb5…), page polish completed on retry (--page-only):
edit_details (description 1333 + summary 278) + 3 gallery images in
numeric order (01 criss-cross, 02 biters, 03 cargoship). Two engine bugs
found and fixed by the live run: (1) the splice that added the page
section swallowed wait_and_verify — restored verbatim; (2) images/add's
response carries {"id",…} with no success wrapper — _upload_payload now
accepts an id-bearing dict (allow_id). The sha1-idempotent gallery made
the retry free: the first attempt's partial upload (01) was recognized
and skipped. Portal state verified via /full: 1.0.1 live, sha1 match,
page populated. py-closure caveat stands (data-stage proven; py's own
gasturbinemk01 blocks entity validation on 2.1.22 — py suite issue).

## 2026-10-20 — py-closure CLOSED (updated suite, engine 2.1.23)
Maintainer updated the py suite (pyfusionenergy 3.1.6 — the FluidBox fix
— plus pycoalprocessing 3.1.8; engine now 2.1.23) and confirmed the ford
works with py in-game. Automated closure re-run on the refreshed set:
dump-data exit 0, full dump (69.7MB), ALL invariants verified in py
context — piling rule (2 entries, composite wired), ochre map_color,
0.9 crossing speed, 10 ford footstep variations, py recipe composed
through the RENAMED wooden-flooring item (1 flooring + 1 log + 200
gravel), pypp "?" guard intact, wooden-flooring item+tile present for
pypp's eager lookups, creosote prereq, py flooring recipe (treated-wood
+ iron-stick + bolts). Provenance re-check satisfied by the closure
itself (all py-sourced items resolve); dependency floors stand
(pyalienlife 3.1.8 = newest). Tooling debt noted: devctl mods sync
reported "all up to date" while the portal held pyfusionenergy 3.1.6 —
the superseded check missed it (py-alphabetical neighbours flagged
fine); investigate when next touching lib/mods/sync.

## 2026-10-20 — vehicle-crossing testmod: the ford does NOT block vehicles
Headless scenario harness `testmods/water-ford/` (four lanes: wooden-ford /
water-shallow / landfill control / deepwater; scripted orientation +
per-tick car.speed push — no unit groups, no autopilot mod). Runner exits
0/1/2 (pass/fail/harness-error); results JSON in the scratch
script-output/. **Finding: FAIL — a speed-pushed car drives straight across
the shipped wooden ford** (min_x 4.07 = onto the west island), and across
vanilla water-shallow equally. Deepwater STOPS the car at the shore; the
landfill control crossed. So the engine blocks cars on `player`-layer
water (deepwater mask carries `player`; shallow-family tiles don't) —
`water_tile` in the car's collision mask does NOT gate movement (it gates
placement-type checks). The 1.0 tile comment "water_tile stays [so
vehicles are excluded]" is therefore wrong for movement: the wooden
ford's vehicle exclusion was never engine-enforced. Consequences for the
cobblestone ticket: "IS vehicle-pathable" is free (shallow-like mask);
"NOT player-pathable" is the hard half (needs the player layer or a
custom layer — and the deepwater lane narrows the car-blocker to `item`
or `player`, disambiguation pending); the wooden-ford clause "vehicles
EXCLUDED" is currently false in game and this ticket must own a fix or a
rescission. Harness caveat: scripted speed-push, not a human driver —
worth one manual drive-at-the-ford confirmation on the live install.

## 2026-10-20 — ford-posts cylinder probe ticket retired (maintainer: done)

The Order-1 ticket (superproject `inbox/produce-ford-posts-cylinder.md`) was
retired as complete. The record: the effect-stack arc was executed and
verified in-game 2026-10-16→17 (piling viewer, paper-pipeline consolidation,
shadow layer, Stage B transition swap, shore-rim ladder — "Version D
verified ring-free"), P1 committed as the shipped boundary baseline,
knowledge extracted (`docs/ford-knobs.md`, `docs/shore-rim.md`,
`docs/shadows.md` — route (a): poles stay pure tile art), and the art
shipped in 1.0.1. The ticket's one unrecorded check — the looping-GIF
water-animation review of the rebuilt pipeline's outputs — is **waived by
the maintainer at retirement** (the P1 composite has been the live baseline
since 1.0.1). Order 2 (refined randomized pole) stays open and now points
at this journal instead of the deleted ticket.

## 2026-10-20 — layer grid resolves the crossing mechanic
Harness extended to a 24-lane grid (11 vanilla tiles + 13 synthetic
single-layer `wf-probe-*` tiles from testmod data.lua). Result: a car is
stopped by exactly three tile layers — `player`, `train`, `is_object` —
and crosses tiles carrying only any other layer (item, object,
water_tile, resource, floor, doodad, ground_tile, lava_tile,
is_lower_object, meltable all crossed). So entity-vs-tile movement is NOT
mask intersection (the car mask carries water_tile, yet water_tile tiles
don't stop it): tile masks are mostly PLACEMENT semantics ("water-tile
prevents placing paths"), while ground-movement blocking is governed by a
small engine-side layer set — matching Wube's own comment that the
character collides only with player/train layers. All three vanilla
vanilla crossings now explained: water/deepwater/lava block via `player`;
water-shallow/water-mud/oil-ocean-shallow cross (confirming the 1.1
changelog line, the shallow driving sound, and the oil-ocean comment).
Consequence, now proven rather than inferred: every car-blocking vanilla
layer (player/train/is_object) also blocks the walking character
(character mask = object/train/is_object/is_lower_object; units carry
player/train/is_object) — "car-crossable but player-blocked" is
impossible with vanilla layers. Both the cobble ford (vehicle-open,
player+unit-blocked) and the wooden-ford vehicle exclusion fix (walkable,
vehicle-blocked) require a custom collision layer via collision-mask-util,
patched into the relevant entity masks at data stage.

## 2026-10-20 — resource layer dropped from the ford tile (maintainer order)
tile.collision_mask is now {water_tile, floor} (was +resource, inherited
from the water clone). Maintainer order during the cobblestone ticket
discussion; nothing in the mod or its deps keys on the layer. Diff gate:
exactly one delta (tile.wooden-ford.collision_mask.layers.resource), smoke
PASS. Note for the pump question: a can_place_entity probe mid-bridge
proved invalid for the player placement pathway (edge + orientation +
fluid-offset semantics; creative/scripted placement bypasses it) — the
in-game hand test decides whether pumps still place on the ford; if they
do, the fix path is the control-stage placement guard (invariant 2), not
the mask.

## 2026-10-21 — wooden-ford collision layer: the contract is real
Pond-row hand test (maintainer): pumps place on vanilla water/shallow/
deep AND on a water_tile-masked tile with no fluid and no name-list
membership (mask-only) — pumpability keys on the water_tile MASK layer;
tile.fluid and water_tile_type_names are irrelevant. The ford (same mask
plus the new wooden-ford layer) rejected the pump. One layer, two
consumers implemented in mod/data-final-fixes.lua (oreguard pattern):
collision-layer "wooden-ford" stamped onto the ford tile, all
data.raw["car"] (cars, tanks, modded cars) and all data.raw["offshore-
pump"]. Players/units/ships untouched; spidertron deliberately unstamped
(it walks open water). Diff gate: exactly the four expected deltas plus
the layer prototype. Harness verdict flipped FAIL to PASS: the ford-lane
car stops at the shore (min_x 65.00, the deepwater signature); landfill
control crosses; shallow crosses. Loose ends for 1.1.0: changelog lines;
migration decision for pumps already standing on fords in old saves;
the cobble ford must NOT carry the layer.

## 2026-10-21 — MAINTAINER HAND CONFIRMATION: ford blocks vehicles
Live session, real mod (data-final-fixes stamping), maintainer-driven:
tank drove east into the ford lane's west shore and was stopped by the
deck; the shallow lane let the same vehicle cross in the same session.
Combined with the pond-row pump rejection, both halves of the
wooden-ford contract are maintainer-verified in game. Harness remains
the automated gate (exit 0).

## 2026-10-21 — cobblestone ford Phase A: behaviour green (three-layer split + path oracle)

Ticket `inbox/feature-cobblestone-road-ford.md` (superproject), maintainer
directives same day: spidertron ignored (unstamped everywhere, like the wooden
ford — it walks open water anyway); layer names mod-prefixed.

**The split.** The 1.0.x single `wooden-ford` layer retired for three mod-custom
collision layers (oreguard pattern, `mod/data-final-fixes.lua`): `water-ford`
(BOTH ford tiles + every offshore-pump mask — pump exclusion stamped once for
all fords), `water-ford-vehicle` (wooden tile + every car mask), and
`water-ford-pedestrian` (cobble tile + every character/unit mask). Walker
exclusion cannot use the vanilla `player`/`train`/`is_object` tile layers (they
block cars too — journal 2026-10-20). The cobble tile keeps `water_tile`
(ships/pumps key on it; it keeps paths unplaceable over the deck — paving would
silently reopen the walker contract). Dump-diff vs the pinned pre-change
baseline (`.cache/water-ford-refactor/cobble-phaseA-baseline.json`): 137
expected / 0 unexpected (expect map alongside: layer rename across tile/cars/
pumps, character+unit stamps, land-tile `to_tiles` registration gains,
space-age recycling for the new item).

**The cobble tile** (`mod/data-updates.lua`, new construction — the frozen
wooden config copied by pattern, never mutated): deep-water clone, water
effect + the shallow wash trick (12.5% alpha), layer 9, mask
{water_tile, resource, floor}, `water_tile_type_names` registration, no
piling transition and no bound decoratives. Phase A item exists (place-on-
water-only, stand-in icon; no recipe/technology — the ticket's open questions
are Phase B); `mod/control.lua` revert guard covers it with its own denial
message.

**Stand-in graphics.** refined-hazard-concrete's `variants` do NOT render on a
water clone (`material_background` is the land-floor path — the deck drew as
plain water in-game, the maintainer could not see the bridge), and size-8-only
main records are rejected at load ("missing 1x1 version or material
background"; base ships no 64px hazard cells). Borrow: base **lab-white**
variants (`variants.main`, the shape the water-family renderer honours) with a
stone-path fallback for bases without the lab tiles. Unmistakable bright-white
deck under the wash; Phase B authors real cobble art.

**Harness (testmods/water-ford, all green, exit 0).** Cobble car lane added
(must CROSS). Unit lanes switched from live-walker to a **path-request
oracle**: the engine pathfinder is asked (async `surface.request_path` —
base wave-defense/AII idiom; `on_script_path_request_finished`) for a path
across each bridge with the small-biter's real `collision_box` +
`collision_mask` read from the live prototype; gates = cobble/deepwater yield
no reaching path, wooden/shallow/landfill reach. Two harness lessons, both
expensive:

1. *The harness ate its own subjects.* Biters commanded via script
   (`entity.commandable.set_command`, the py caravan idiom) all vanished at
   tick 241 — one tick after the tick-240 periodic command re-issue — all four
   lanes, both enemy and player force, no death/damage events. Removing the
   re-issue: all survived a full run. (Same symptom class as oreguard's matrix
   whose periodic sweep ate its own construction bots.) Live-walk unit lanes
   are therefore banned; the oracle runs with NO entity walked.
2. *set_tiles vs chunk generation.* A fresh scenario world generates only a
   band around spawn; `set_tiles` silently drops tile changes in
   not-yet-generated chunks (= the maintainer's in-game report: water rect
   ending mid-world, bottom rows on wild terrain, "offset" impression — the
   pond band is deliberately its own row strip). Fix: request +
   `force_generate_chunk_requests()` BEFORE the paint, with a TILE-coord
   position + chunk radius (the first attempt passed an area and a pcall ate
   the error; the second passed a chunk coord as a tile position and stopped
   at y≈456, short of the unit rows).

**The big one: mod-list placement (devctl).** First py-closure smoke on the
dlc env failed in pypostprocessing (space-age gate). The maintainer challenged
the 2026-10-16 gotcha ("data-dir DLC mods always load"): probe runs proved
the provisioner had been writing `mod-list.json` at the env root while the
engine reads `mods/mod-list.json` — the engine found no list, auto-enabled
everything, and wrote an all-true list back (the same artifact that likely
founded the old gotcha). With the list placed correctly the engine honours
`enabled: false` and **no data-dir DLC mod loads** (zero DLC loads, zero
space-age prototypes in the dump). Fixed `lib/envspec.py` (write to
`mods/mod-list.json`) + selftest battery 7c; `devctl repo selftest` green;
superproject docs corrected (data-lifecycle.md, testing.md, py-suite.md) and
`lib/check.py`'s locale scope no longer scans data-dir locales as resolution
sources. The py-closure env spec (`envs/py-closure.toml`) was also repaired to
the documented portal-dep pattern (roots=[] + fetch + pins; the old
`roots=["pyalienlife"]` never resolved) and now runs the chain on the dlc
install at 2.1.23 — the py chain's own floor — with space-age off.

**Verification (2026-10-21, this session).** dlc-smoke smoke/diff/locale PASS;
asset gate OK; harness exit 0 (wooden stops, cobble crosses, controls cross;
oracle: cobble+deepwater no path, wooden/shallow/landfill cross); py-closure
smoke PASS with: py recipe branch composed (treated-wood + boards + bolts),
ford recipe `localised_name` guard present, piling rule intact, all 28 units
incl. both caravan units stamped, cobble item's place_as_tile present with no
pypp crash. MAINTAINER HAND TESTS (in-game, windowed session): offshore pump
refused on the cobble pond; player character blocked from walking onto the
cobble deck; vehicle crosses the cobble ford with and without a player — the
movement contract hand-proven. The dump-diff baseline + expect map live in
`.cache/water-ford-refactor/` (scratch — recreate per this entry).

**Still open (Phase B).** Authored cobble art (the lab-white stand-in must
never ship); transition sprites + border blending; the cobblestone-path
partner tile; item/recipe/technology + locale for the released surface;
changelog lines; seed-pinned visual gates; Cargo Ships sail-over hand check;
1.1.0 release flow.

## 2026-10-21 — cobble Phase B: the mechanical rebuild (prospecting the confused session)

**What was recovered, how.** The previous session's cobble work survived mostly
on disk (`.cache/blender-cobble/auth-cobble-probe.py` + `bake-cobble.py`),
with the session transcript as a backup source. A deterministic extractor
(`.cache/cobble-prospecting/prospect.py`) swept the two session JSONLs without
any transcript entering an agent context: 152 unique payloads → 57 version
chains → manifest. From there, targeted reads only. (Lesson, written down this
time: file-based factory scripts + a manifest beat session archaeology.)

**Where it now lives (committed).** `tools/paper-pipeline/auth-cobble.py`
(full mechanical scene rebuild: superellipse loaf cobbles `dome_bmesh`,
variant fields `layout_field` — 24×24 1×1 base + 2×2 field grid @ (−22,−22) +
4×4 field grid @ (−46,−40), waterbed trim at z=0, WL waterline wet/dry cut
with `in_wet`/`wet_depth` vertex attrs, materials mechanically extracted from
the built blend's node trees, rig as saved) and `tools/paper-pipeline/
bake-cobble.sh` → `bake-cobble.py` (art ladder, alpha + pack gates, --twice).
`blender/ford-cobble.blend` is now a gitignored BUILD OUTPUT (126 MB exceeds
GitHub's 100 MB block; reproducible from script — verified by oracle-dump
fingerprint: mesh hash `a710525c` + 44/44 links + all graphs equal; deltas =
deliberate: M_WATER junk-clone dedupe, COB2/COB4 cams rebuilt ORTHO (the
session had left them PERSP while the bake's REGIONS + 128px/unit math assume
ortho — sq2 mean-L spread was 51-138 through the persp cams, now 126-132)).

**Maintainer rulings applied.** (1) The whole chain regenerates mechanically
from git-tracked scripts; nothing needed for the build lives in .cache.
(2) Artifacts live in the mod tree: sheets at `assets-src/cobble/`.
(3) NO wetness-mask sheets (the wooden ford has none): the wet look lives in
the art pixels — M_COBBLE's WL ramp (WL 0.15 at bake). M_COBBLEMASK remains
in-scene only, now with use_fake_user (a rebuilt blend's zero-user materials
are stripped at load, which would break any future Mask-view-layer bake).

**Baked & shown.** `cobblestone-ford.png` 2048×128 (16 variants),
`cobblestone-ford-2x2.png` 1024² (16 fields), `cobblestone-ford-4x4.png`
2048² (16 fields); mean-L spreads 107-141 / 126-132 / 135-146; alpha 255
everywhere; pack bit-equal. Maintainer viewed in gwenview.

**Open (unfixed by order), for next session.** The `--twice` determinism gate
fails on all three art passes even at 1 fixed thread: prime suspect =
`dither_intensity` 1.0 on art renders (dither noise is unseeded), but note the
recovered crank's mask passes (0-dither, analytic emission) ALSO failed — so
dither explains the art passes at most; the mask non-determinism is still
unexplained. Fixing either changes pixels or the gate semantics ⇒ maintainer
call. Mask-byte fidelity (dry byte lands 165 not 170: double sRGB-encode of
the pre-inverted ramp) is moot while no mask sheets ship, but is recorded
here for when the wet/dry data map is needed (transitions, Phase B item 2).

## 2026-10-21 (later) — cobble feedback round: icons, decoratives, color rig; crank hardening; the visual-review lesson

Maintainer feedback on the wired cobbles: (1) icons needed (same arrangement
recipes as the wooden set: bare cell for the land path, water+deck+stone-heaps
for the ford); (2) the rock decoratives (`ford-pebbles`/`ford-stones`) bound to
`cobblestone-ford` like the wooden ford has; (3) cobble reads too white
in-game — asked for interactive color testing in Blender. (1)+(2) implemented
this session (make-icons.py cobble section + icon wiring + the
`bound_decoratives` line; icons untracked, wiring uncommitted at entry).

(3) got a COLOR RIG, built by the auth (so it regenerates): `COB_TONE` /
`COB_BED_TONE` value-node multipliers on M_COBBLE / M_COBBLEBED between the
palette mix and the Principled Base Color; a compositor `GAME_VEIL` sim
(px' = 0.75·px + 0.25·(51,51,51) — the ford wash law) so F12 previews the
in-game look; scenes saved preview-fast (512², ZOOM/BEAUTY cams; compositing
on). The committed palette state = `TONE_COBBLE` / `TONE_BED` / `VEIL_FAC`
constants in auth-cobble.py; GUI knob edits are scratch until folded back +
re-crank. Blend's saved WL = −1 (dry product state, post-geometry so the
cut keeps its 0.15 build value).

**CRANK HARDENING** (motivated by maintainer's reproducibility complaint —
"each time an agent does it, they get into a mess"; two concrete incidents
this session: an auth crash at the CompositorNodeMixRGB socket rename —
4.3 inputs are Fac/Image/Image_001, not Color1/Color2 — that blender SWALLOWED
(exit 0 by default), so the crank blessed a STALE blend ALL-GREEN; and my own
edit-call failing wholesale, which I then forgot to reapply):
- `bake-cobble.sh` = ONE blender process: `--python auth --python bake`,
  `--python-exit-code 1` (script errors kill the crank), the bake refuses any
  blend whose provenance stamp (auth sha256, mesh-hash oracle a710525c6ee05b1d,
  rig values, generated time) is missing or stale — `bake-cobble.sh --selftest`
  proves the refusal (passing);
- sheets render to .cache staging and get PROMOTED only on pixel change (the
  PNG writer is not byte-stable; a rerun must leave git clean);
- the VERDICT line is grepped from the log as the green authority.

**THE VISUAL-REVIEW LESSON (maintainer, verbatim intent):** the gate said the
new art was "pixel-identical to committed"; it was NOT — the old committed
sheets carry the wet band (pre-revision wet-in-art ruling) and a WHITE DRY BED
was hiding under it. I "diagnosed" the diff from signed pixel statistics alone
(mixture-fit, wet-band story) and was wrong in the way that matters: the
maintainer looked and saw the actual thing in one glance: **the old background
is black, the new one white.** Rule from now on, for this mod and this
pipeline: ANY visual problem or art-affecting change gets pointed at the
maintainer for eyes (gwenview side-by-sides), never resolved by pixel stats
alone; "looks identical" is not a claim an agent gets to make unaided.

Diagnosis after the maintainer's correction: the fresh dry cells and the old
dry cells are byte-equal ⇒ the white dry bed is the AS-EXTRACTED palette
(the old sheets read dark only because their wet band covered most of the
frame) — i.e. the white background predates all of today's tooling changes.
Remedy = the bed tone (and the cobble tone for the in-game wash), which is
the maintainer's interactive call: bed-tone ladder rendered at 1.0/0.55/0.35/
0.22 (gwenview: /tmp/bed-tone-ladder.png), Blender GUI on ford-cobble.blend
for live COB_BED_TONE / COB_TONE turning with F12 preview. NEXT: fold chosen
values into TONE_* constants, re-crank (staged sheets will promote for real:
bed pixels will differ), redeploy mod/graphics, gates, commit — INCLUDING the
uncommitted icons/decoratives and the rig; masks stay unshipped until the
engine wiring (named change).

- Blender 4.3 ships NO node-tree arrange (nice_layout was removed ages ago);
  the mechanical extraction piles every node at (0,0), so the GUI shows one
  heap. Added a deterministic longest-path layout pass (layout_node_tree in
  auth-cobble.py, name-sorted rows, 280/240 steps, frames untouched) + framed/
  parked the TONE knobs left of the palette mix. Ran it live in the shared
  GUI session and saved; the next crank produces the same layout from the
  auth. Maintainer feedback live-lesson recorded earlier stands: every visual
  judgement = their eyes (gwenview/in-GUI), mine = numeric state only; I
  cannot see images (the look tool returns them; my provider omits them).

## 2026-10-21 — sun-key direction transplant (GUI session, live) + tooling ruling

Maintainer ruling: **ALL cobble tooling (auth-cobble.py, bake-cobble.py,
bake-cobble.sh, mesh-hash oracle, provenance stamps) is suspect — nothing
carries into the remake.** Do not fold anything back into auth-cobble.py;
its `build_scenes_and_rig` still authors ONLY the boards point-`KEY`
(1800000 W at (−126,0,126), r=0.1). The GUI-session `FILL`/`SUN_DAY` are
scratch that the remake must re-decide from the reference files, not from
the stale auth.

Lighting review of the four files (dumps: superproject
`.cache/water-ford/dump-ford-{boards,posts,stones}.txt`):
- boards/posts rig (docs/boards-visual-language.md §4): POINT KEY from west,
  45° up (−42,0,42) @40 kW / floor-scaled (−126,0,126) @1.8 MW; world
  (0.55,0.55,0.55)@0.06. Shadows due east.
- stones rig: SUN 4.2 W, angle 0.1745 (10°), rot (0.829,0,−1.1345) — source
  ~42.5° up SSW, shadows ENE; AREA strip 2.0×0.25 @25 W at (0.15,−1.15,0.9)
  rot (0.9425,0,0.1222); NO world (transparent film).
- cobble had the stones skeleton with drift: sun rot (0.9599,0,−2.1817)
  (azimuth MIRRORED across north, shadows ESE) + angle 0.0698 (4°).

FIX applied in the live GUI session, saved to blender/ford-cobble.blend:
- SUN_DAY rot (0.9599,0,−2.1817) → (0.829,0,−1.1345), angle 0.0698 → 0.1745
  (stones KEY_SUN verbatim; SUN direction is scale-free, energy already 4.2).
- BEFORE/AFTER previews (no other change): /tmp/cobble_sun_{ZOOM,FLOOR}_CAM_
  {…_BEFORE,AFTER}.png, side-by-sides /tmp/cobble_sun_{ZOOM,FLOOR}_CAM_SBS.png
  shown to maintainer via gwenview (eyes-on law). Verdict pending eyes.
- Same FILL/SUN_DAY objects link into both cobble scenes → one fix covers
  FLOOR + FORD.

Open knobs for the remake round (deliberately untouched): FILL strip aspect
(56×0.25 = 224:1 vs stones' 8:1) and its relative distance/height
(47/58-stage vs stones' 1.46/0.9-unit ≈ hand-port inconsistency); the
orphaned `KEY` point-light datablock in the blend (unlinked residue).

## 2026-10-21 — GAME_VEIL ABOLISHED (maintainer ruling: "there is no game veil")

The maintainer's repeated removal requests never STUCK because the veil had a
resurrection path: auth-cobble.py build_veil_sim() rebuilt the compositor
sim on every scene build, and bake-cobble.py line 85 then worked AROUND it
("the SAVED rig state carries the veil-sim"). Removing it in the GUI removed
only half the system.

State found this purge: the live blend's FLOOR compositor tree was ALREADY
empty (prior GUI removals had stripped the veil nodes; only the FORD scene
carried a vestigial Render Layers→Composite passthrough). Both scenes now
use_nodes=False, zero compositor nodes, saved to blender/ford-cobble.blend.
Zero-pixel continuity vs the previous review renders (AE=0 on both
ZOOM_CAM/FLOOR_CAM) — earlier side-by-side verdicts stand valid.

Amputation (not salvage) in the condemned toolchain, so no re-crank can
resurrect the veil:
- auth-cobble.py: build_veil_sim → no-op that sets use_nodes=False; VEIL_FAC
  deleted; stamp dict drops 'veil_fac'; py_compile clean.
- bake-cobble.py: the use_compositing=False belt stays, comment updated.
- bake-cobble.sh: header comment updated.
Remaining GAME_VEIL/VEIL_FAC references = comments recording the ruling only.

Maintainability verdict recorded: the unmaintainable pattern = live GUI
state + a suspect regenerator that resurrects removed state + comment-level
awareness that the two contradict. The gut-and-remake (fresh materials,
lighting from stones-verbatim as applied, tooling rebuilt fresh) is the fix;
no further folds-back into auth/bake.

## 2026-10-21 — TEXTURE/COLORING PIPELINE GUTTED + REBUILT (maintainer ruling)

Ruling: "can we get rid of the entire texture/coloring pipeline and start
again" — after the veil unstickability, the answer executed. FIRST brick of
the NEW toolchain: `tools/paper-pipeline/mat-fresh.py` (standalone, no
involvement with auth-cobble/bake, runs in the open session only).

GUTTED (all of it):
- M_COBBLE (31-node toning stack: 6×Math/4×MapRange/3×MixRGB/WL waterline
  window, COB_TONE/COB_BED_TONE knobs) — DELETED.
- M_COBBLEBED (6-node Voronoi bed, WL residue) — DELETED.
- M_COBBLEMASK (WL waterline → gray ramp → Emission; the shader-rendered
  wetness channel) — DELETED (had use_fake_user). The fresh mask pass gets
  rebuilt at the sheet round; wetness data stays a DELIVERY rule (law 2),
  mesh attributes `in_wet`/`wet_depth` left untouched (geometry decision
  pending, no new material references them).

REBUILT — stones convention transplanted (graph verbatim, parameters
re-anchored from .cache/water-ford/mat-stones.txt extraction):
- M_COBBLE: Noise(Scale 1.2, Detail 8, Rough 0.5) → 2-stop ramp →
  Principled(Rough 0.85) = 4 nodes. Scale 1.2 from ~18% relative detail
  (stones: Scale 14 on ~0.35-unit bodies; cobble cells measured 5 units).
  Dry stops: (0.42,0.39,0.36)@0.3 = L101 pocket → (0.64,0.52,0.35)@0.72 =
  L136 ochre-sandy (§3 deck band L120–155, pop band, no true blacks).
- M_COBBLE_WET: SAME graph; wet delta = the measured stones convention
  (ramp stops lifted toward grey (0.53,0.52,0.47), k=0.34). Orphan fixture
  (unassigned) until the twin-object/bake round.
- M_COBBLEBED / M_COBBLEBED_WET: same 4-node shape; stops L39→L72 (joint
  gravel; gap floor law: not black).
- Assignments: COBBLE_FLOOR ← M_COBBLE, JOINTBED ← M_COBBLEBED. Renamed
  off the .001 suffixes; material inventory now exactly the 4 fresh ones.
- Compositor: still OFF both scenes (veil purge holds).
- cobble_seed FACE attribute (0..1, 101 buckets): KEPT as mesh data;
  per-cobble seeded pool variation = available as round 2; deliberately not
  built in this first pass (simplicity = reviewability).

REVIEW: /tmp/cobble_mats_{ZOOM,FLOOR}_CAM_SBS.png (left = condemned toning
stack, right = fresh stones-convention) sent to maintainer via gwenview.
Verdict = maintainer's eyes; my numbers only (L stats above).

## 2026-10-21 rev 2 — WET/DRY = THE MASK PASS (maintainer ruling, piling pattern)

Correction of round 1's read: the wet/dry split is NOT wet art materials.
"We render just the wet/dry out in a separate render to make a wetness mask.
It doesn't affect the render to sprites at all. It is purely used for the
wetness mask render. This is all exactly as for the piling workflow."

- M_COBBLE_WET / M_COBBLEBED_WET (round-1 ramp twins) — REMOVED. Art = dry
  only, forever; wetness never touches sprite renders.
- M_COBBLE_MASK built — the 6-node M_PILING_MASK graph verbatim
  (extract: .cache/water-ford/mat-posts.txt):
    Attribute("in_wet") -> SegmentGray.Fac (0 -> 0.402 linear = gray 170)
    Attribute("wet_depth") -> MapRange(0..1, STEPPED, Steps=4) ->
    WetGrayRamp.Fac (0.0908=85 -> 0.0097=25) -> Emission(1) -> Output.
  (4.3 gotcha: Steps is an input socket visible under STEPPED, not a node
  attribute.) Cobble mesh carries the SAME normalized wetness attributes
  the piling convention uses (in_wet 58.3% >0.5, wet_depth 0..1 mean 0.53).
- Mask view layer "Mask" with material_override=M_COBBLE_MASK on FLOOR+FORD;
  default passes untouched; the runtime pass state (Standard/opaque/world-0/
  dither-0, VL switch) is toggled ONLY during the mask render, as bake-mask.py.
- Mask verification render @512 ZOOM view: PASS — bg opaque black ✓,
  crown-170 = 41499 px, wet-85 = 69347 px, fully-wet-25 = 590 px
  (all three segments present, piling bake-mask thresholds).
  115..165 seam-antialias = 12806 px — piling's 64px bleed cap was 120 px
  (~2 rows × the frame); scaled to this 512 view ≈ 7680; observed 1.7×,
  consistent with the meandering washboard waterline (long boundary), not a
  dry bleed. MAINTAINER'S EYES: /tmp/cobble_mask_SBS.png open (left = art
  render, right = the mask pass).
- Incident: the first mask-pass attempt ABORTED MID-TOGGLES (crash between
  toggles and restore) and left the live session polluted (world 0, dither
  0, default VL off); my restore in the second attempt then read the
  polluted state and "restored" world to 0.0. REPAIRED to the file's
  standard state (0.55 @ 0.06, dither 1.0, Standard, opaque, VLs on), saved;
  art continuity proven ZERO-DIFF vs the round-1 fresh-material render.
- LESSON for the fresh bake (round 3): toggle→render→restore must be
  ALL-OR-NOTHING (try/finally) — the pass toggles are exactly the kind of
  partial state that has burned this session twice now.
- File state: materials = exactly M_COBBLE, M_COBBLEBED, M_COBBLE_MASK; no
  orphans; slots dry-only; compositor still off; saved.

## 2026-10-21 rev 3 — BED KEYING FIX (maintainer's physical model)

Maintainer: the grounding floor plane is logically UNDER WATER; the cobbles
rise up through the water, some breaching the surface (dry tops); as
rendered, the floor exposed between cobbles was keyed DRY — it must key just
as wet as the bottoms of cobbles.

Diagnosis (measured, not guessed): JOINTBED shipped with NO wetness
attributes at all → in the mask pass the attribute nodes defaulted to 0 →
the bed rendered gray-170 (dry). Cobble convention confirmed from the mesh:
wet_depth = 1.0 at z=0 → ~0 at z≈0.15 waterline; the bed plane sits at z=0 =
the same depth as cobble bottoms.

FIX: tools/paper-pipeline/wet-fresh.py (fresh toolchain, DATA round —
owns wetness keying, separate from the materials round): JOINTBED verts now
in_wet=1.0, wet_depth=1.0 (verified exact), saved.

RESULT (mask pass @512 ZOOM, before → after):
- fully-wet gray-25: 590 -> 28,077 px (the bed now fully-wet, same bucket
  as cobble bottoms — "just as wet as the bottoms of cobbles" ✓);
- dry gray-170: 41,499 -> 35,189 px (the removed 6.3k = dry-keyed bed;
  the remainder = genuinely emergent crown tops);
- background opaque black ✓; art continuity: ZERO-DIFF render (the wetness
  data touches only the mask pass, as ruled).
- All-or-nothing toggles (try/finally) this round: restore verified
  (world 0.06, Standard, opaque, dither 1.0).
MAINTAINER REVIEW: /tmp/cobble_maskwet_SBS.png in gwenview (left = art,
right = the fixed mask pass).
Fresh toolchain now: mat-fresh.py (materials incl. M_COBBLE_MASK),
wet-fresh.py (mesh wetness keying).

## 2026-10-21 — recipe round (increment 1+2)

- docs/export-recipe.md: the recipe (game contract = data-updates.lua:
  16 sprites/size, sprite = (128·size)², sheets = 16-sprite row / 4×4 sprite
  grids, 128 px/tile @ scale 0.25; layout law = contiguous areas + in-file
  cams + row-major variant IDs; render + cut + deploy = committed driver;
  gates = contract + --twice pixel-equality + deploy byte-equality +
  maintainer's eyes as the look-approval gate — NOT byte-identity with the
  old sheets, maintainer clarified). Known faults recorded:
  staged-vs-deployed generation drift (measured 230k-4.1M px/sheet), layout
  law unimplemented. NOTE: assets-src/cobble carries ANOTHER session's
  uncommitted mask/icon work — left alone (ownership rule).
- tools/paper-pipeline/bake-ladder.py: the exporter skeleton; bpy imported
  lazily (selftest runs as plain python3); synthetic selftest GREEN:
  cut/arrange preserves windows 1:1; contract_check catches malformed
  sheets; verify_bytes catches tampered copies; row-major origin windows
  verified for sizes 1/2/4. First selftest run caught MY OWN test bug
  (deploy re-copies over the tamper — restructured to a testable
  verify_bytes helper); the gate machinery is honest.
- Stage B (render) deliberately refuses until the Stage-A lattice exists
  (no rendering against an undefined layout).

## 2026-10-21 — boards builder: proof-cell facts + the looking rule

Maintainer (verbatim intent): STOP trying to visually understand renders —
"you are very bad at it. Use my eyes for looking." My output = geometric and
numeric facts only; every visual verdict = theirs (gwenview/in-GUI), for
this mod's Blender work generally. Reinforces the standing eyes-on law.

Proof cell facts (seed 1000, --cells 0): 7 planks — courses 0/2/3 carry
interior butts (x = 0.3856 / 0.6000 / 0.5167), course 1 = one full-cell
plank; plank spans tile the cell exactly (0 gaps in x at every course
midline); arch h=0 at every plank's own ends; butts flush (no z-steps).
Coordination fix applied to build_cell (the previous proof had independent
per-course start jitter + length draws = uncoordinated starts/ends,
maintainer's catch).

Committed so far this round (uncommitted until eyes pass):
tools/paper-pipeline/extract-mplank.py, boards-mplank-spec.json (55-node
M_PLANK + BOLT_METAL + GAP_TONE + 12-entry plank_pool), boards-builder.py
(builder: factory-empty rebuild, blocks = blessed footprints, cams
BLK1/2/4 at ortho 4/8/16 = 512/1024/2048 masters).

Join-decoration law (maintainer 2026-10-21): where planks meet within a
course, the join is decorated with bolts — ONE pair per join (2 bolts at
1/3 and 2/3 across the plank width, at the join x, flush), shared by both
planks, emitted once per join line (left cell edge + interior butts; the
right edge = the neighbor's emit). The old emitter did 2 bolts per plank
end = 4 per join (over-bolted); fixed in boards-builder.py emit_bolts.
Proof cell: 8 join lines / 16 bolts.

Bolt visibility fix (maintainer: "I see no bolts"): (a) the emitted bolt was
a degenerate 1px-tall X-ridge (zero y-extent = invisible regardless of
material) — my geometry bug; (b) the true spec = near-black iron:
BOLT_METAL Base Color (0.0645,0.0645,0.068), Roughness 0.22, Specular 0.7;
the old art's darkness budget = 7.7% of planks-base under L60 (bolts+seams),
p5 = L43. Now the bolt = a 2D low dome (5x5 vertex grid, r2 falloff, peak
+0.014 over the flush join); bolt zones read L 33-51 vs plank 106-128.

Bolt round 3 (maintainer: bolts square + wrongly at the left edge):
(1) the TRUE bolt geometry extracted verbatim from git HEAD's old deck:
462 identical 13-poly/24-vert flat 12-gon washers, 10.2px dia, 1.3px tall —
committed as bolt_template in boards-mplank-spec.json (extract-mplank.py
re-runs against the old file); the builder instantiates the template
(sits +0.004 over the flush join). (2) placement: bolts = ONLY at interior
butts (where two boards meet within a course within a tile) — cell edges
carry no bolts now. Proof: butt bolts read L 13-37 vs plank 110-130; left
edge shows no bolt (min L 51 = edge/cap tone).

Bolt round 4 (maintainer: bolts too close; butts need a gap):
- the pair now spreads by the 1x:2x space law: edge-space g = (w - 4R)/4 =
  0.0185 u (2.4px), between = 2g = 0.037 u; centers at 0.0585/0.1755 across
  the plank width (was the touching-edge 1/3-2/3 pair at 0.078/0.156).
- interior butts now OPEN a gap: BUTT_GAP = 0.008 u (~1px = half the course
  seam) between the meeting board ends; the washers span it as splice
  plates; cell edges stay flush.
- proof: bolt zones L 42-63 (dark discs against ~110-130 plank); the butt
  gap column reads like the seam (min 40.8 vs seam 80-84 hmm the AA band).

Grain round (maintainer: rings traced ACROSS all boards + grain unlike the
original): three WRONG parametrizations in my plank attr emitter, found by
decoding the old deck's attrs (git-HEAD file):
- plank_cx/cy emitted as LOCAL FRACTIONS (0.25..0.75) — the old = the
  plank's WORLD-CENTER x (strip−cx median 0.032) + the center y with an
  OFF-CANVAS pith shift (old cy = −11.5..11.5 over a ±6 deck);
- plank_ringfreq = 0.6..1.4 — the old = 8..16 (med 10; rings ~8-16px).
The local-fraction piths = one near-origin point = the global concentric
rings the maintainer saw; the wrong rf = the too-wide bands. Fixed:
cx = x0+L/2; cy = course center + uniform(-5.5,5.5) pith shift;
ringfreq = uniform(8,16). Verified per-plank (cx = exact plank centers,
cy varied both sides, rf in band). plank_len = shader-dead informational
attr (emitted as L). The old deck's ring arcs = per-plank; ring value =
len(world_pos - pith)·freq + warp/seed phase (13.77·seed) — unchanged
(graph verbatim from spec).

## 2026-10-21 — SESSION STATE: recipe + builder committing; 2x2 next

Committed this round (all mine): docs/export-recipe.md (the 3-stage recipe:
LAYOUT law / RENDER / CUT+deploy+gates; contract = data-updates.lua
16 sprites per size, sprite = (128·size)², 4×4 sprite grids for ALL sizes,
128px/tile, scale 0.25; the strip retires; the lua line_length 16→4 ships
in the same commit as the first replaced 1x1 sheet); the fresh toolchain:
extract-mplank.py + boards-mplank-spec.json (the M_PLANK 55-node grain
shader + BOLT_METAL/GAP_TONE + the 12-entry plank_pool + the VERBATIM
bolt_template washer), boards-builder.py (the factory-empty rebuild:
planks/seams/bolts/blocks/cams/rig from primitives), mat-fresh.py,
wet-fresh.py (cobble materials + wetness keying), bake-ladder.py (the
ladder driver skeleton, selftest = cut/arrange/contract/verify_bytes
GREEN; Stage B refuses until the lattice exists), the veil amputation in
auth-cobble/bake-cobble(+sh), and the REBUILT blender/ford-boards.blend
(+blend1): the builder's output, 16/16 approved-look 1x1 cells, NOTHING
else in the file.

RE-RUN RECIPE: cd mods/water-ford && blender -b blender/ford-boards.blend
--python tools/paper-pipeline/extract-mplank.py (BLEND env optional) —
regenerates the spec from the committed look; blender -b --python
tools/paper-pipeline/boards-builder.py -- --cells all — rebuilds the blend
idempotently; python3 tools/paper-pipeline/bake-ladder.py --selftest.

NEXT (maintainer order): the 2x2 block (16 designs, boards ~2u crossing
the internal 1x1 boundary, bolted interior joins), then 4x4, then Stage
B/C wiring in bake-ladder.py: real renders → identity cut (the blocks =
the sheet shapes now) → contract gate → deploy = byte-verified copy into
mod/graphics + the lua flip. The cobble = the SAME recipe with
--base cobblestone-ford --wetpass (the wetness = the Mask view layer
render per area; bed keyed wet; piling gray language 170/85/0).

NOT committed (other sessions'): mod/data*.lua/info.json/make-icons.py,
assets-src/cobble M-files + untracked masks/icons, palette-ladder-cobble.py.

## 2026-10-21 — PARKED (handoff to next agent) — 2×2 round in flight
Committed here: boards-builder.py extended (blocks 1+2, per-block zoom
cams, census diagnostics in the final print; --cells all = 16+16 cells,
maintainer's visual verdict on 2×2 = "looks OK" + little-things list
pending). Blender file on disk = --cells 0 state — REBUILD FIRST:
cd blender && blender -b --python ../tools/paper-pipeline/boards-builder.py -- --cells all
OPEN (next agent):
1. Maintainer's 2×2 corrections: (a) PER-TILE SHADE must break per
   1×1 tile even under continuing planks (old deployed wooden-flooring.png:
   per-tile mean L 107..131, measured). Mechanism UNIDENTIFIED — M_PLANK
   spec has NO tile branch (attrs consumed = cx/cy/rf/seed/course/rgb
   only); candidates = the LAT_FIX object in the old file (unexamined),
   a per-tile slicing post-process (journal.md:560 "big-floor render +
   per-tile slicing (law-3)"). Maintainer calls it "the every-tile shade
   block" but forgot the name — find the name/mechanism in the old file
   before inventing anything. (b) DOUBLE-HEIGHT planks: old 2×2 tiles had
   SOME 2-course-wide planks (~0.468u); ratio unmeasured — my LAT_BOARDS
   strip-width-histogram attempt failed, rerun empirically.
2. BOLT-VANISH-SAVE BUG: --cells 0 run = 16 bolts in-memory at save;
   reopened file = 0; P-planks survive the same save. strings-probe
   useless (compressed blend). Next = --outfile /tmp isolate +
   collection-membership diff. The on-disk blend = bolt-less regardless.
3. Then: the 4×4 block; Stage B/C wiring in bake-ladder.py (real
   renders → identity cut → contract gate → deploy) + the lua
   line_length 16→4 flip in the same commit; cobble = --base
   cobblestone-ford --wetpass.
RULES: numeric self-checks only (never interpret renders); renders go to
the maintainer's gwenview for the verdict; commit own-work only (the tree
is shared — other sessions' cobble/lua edits are not ours).

## 2026-10-21 (late) — old-deck mechanisms decoded; vertical law fixed; pattern engine live (next agent round 1)

Handoff's first action done: blend rebuilt --cells all (log
.cache/boards-rebuild-cells-all-2346.log). Then the PARKED items 1a/1b:

- **"Every-tile shade block" identified** (old file = git 248d8f3 blend):
  the old file has NO modifiers/drivers/text blocks; LAT_FIX = a 256-face
  missing-strip geometry patcher (atlas_note), NOT the shade block. The
  mechanism lives IN M_PLANK (extracted verbatim in boards-mplank-spec.json):
  (1) per-course tone ramp: plank_course face attr ×0.25 indexes a 4-stop
  ramp T0(dark brown)..T3(pale tan); (2) pin window: fac = 1.0 within ±9px
  of each 1x1 tile's x-edge lines, 0.0 at the tile x-center, linear ramp;
  (3) TWO mixes MULTIPLIED: TPIN = mix(plank_cast → course tone, fac) ×
  GPIN = mix(grain → white, fac) — tile EDGES = flat per-course pinned
  tone (grain fades), interior = free cast + grain. That IS the R10
  "pin the boundary furniture" law, shader-side, keyed by face attrs.
- **Old deck per-tile numbers** (probe-old-deck.py over the geo attrs):
  per-tile cast-mean σ 0.021-0.039 linear (tile means reach 0.11-0.285);
  the new builder's per-tile bias (POOL_W weighted + uniform(-1,1) tilt,
  GAIN 2.4, sim-tuned) realized σ ≈ 0.037 — inside the old band.
- **Vertical law found + fixed** (maintenance catch 2026-10-21: my h=2
  planks extended UPWARD — they flooded the course above):
  OLD DECK law, from 3 measured sources: every plank = [lower line +
  0.016, upper line flush]; the 2px seam hangs just ABOVE each pitch line
  (deployed wooden-flooring.png seam slots at PNG rows 30-32/62-64/94-96
  + the bottom slot 126-128); course attr = the plank's BOTTOM band
  indexed from ITS TILE'S bottom (0..3 bottom-up — LAT_BIG3 contingency
  attr↔band exact 1:1); multi-course planks anchor at pitch lines and
  extend DOWNWARD (doubles measured at internal bottom-up starts 0/1/2/3,
  not only the top pair). Builder now: this phase law on ALL planks,
  tile-anchored multis, course attr = 3-((bc+bh-1)%4), lattice-periodic
  crowns in the pattern path (old z_profile law: A*sin²(π·fract(x)),
  coplanar at every cell edge so crossing planks stay flush), census +
  flush/phase/attr HARD gates: 0 failures on 520 planks.
- **1x1 block vs HEAD**: bit-identical (99 planks, 0 object diffs) BEFORE
  the phase fix; after the fix only Δy=+0.016 (2px) + the course attr
  remap 3-(c%4) — the seam phase = the old art's now; the 16 approved
  cells moved 2px = awaiting maintainer's eyes with the new proofs.
- **Bolt-vanish-save bug (PARKED item 2)**: NOT reproduced across 3
  rebuilds (200/200, then 148/148, 294/294 bolts persist on reopen).
  Isolate recipe preserved in probe-old-deck.py dump-planks mode
  (compare same-name objects across builds).
- **OPEN (next cycles, in order)**: (i) plank-length + butt-density
  calibration to the old macros — measured old: ~1.7 planks/band (2x2-era
  sites), L-mix = ~59% exactly-full-tile + ~31% long runs (1.2-2.4u) +
  few shorts; doubles = 20-24% of planks / 35-59% multi area by site
  pattern, triples 2-11% mostly internal-1 starts — my current build:
  12.6% (2x2)/16.3% (4x4) doubles; "long" mode wrongly emits FULL-design
  planks (old max = 2.4u at 2x2s, the 4.0u only in 4x4s). (ii) the 4x4 +
  Stage B/C wiring in bake-ladder.py + the lua line_length 16→4 flip;
  (iii) cobble pass --base cobblestone-ford --wetpass (other session).
- **Rules kept**: numeric/geometry self-checks only; proofs to gwenview
  for verdicts (/tmp/boards-proof-{1x1,2x2,4x4,zoom,zoom2,zoom4}.png);
  other sessions' files untouched; nothing ephemeral (probe + builder
  committed).

## 2026-10-21 — A/B: per-tile vs per-plank crowns (look-test, uncommitted either way)
Builder gained --crown per-tile|per-plank (default per-tile = the old deck's
l lattice-periodic law) + --proof-tag so A/B renders don't clobber. Same
seeds both sides; B built to /tmp/ford-boards-B.blend (throwaway).
Numeric A/B: 520/520 planks x/y-identical, z-only (max dz 0.014 = amp cap);
393 planks cross an internal 1x1 tile line — surface z AT those lines:
A flush 0.0530..0.0590 (zbase ± jitter = the lattice law), B the plank
arch continuing (up to 0.0729). Gwenview: A/B pairs (2x2+4x4 blocks +
the two zooms; 1x1 unchanged and left out of the A/B).
Verdict = maintainer's eyes; neither committed as the look.

## 2026-10-21 — A/B round 2: pin-window scope (maintainer-corrected)
Terminology settled with the maintainer: the "shade block"/"crowns to move"
= the PIN WINDOW (TPIN tone pin + GPIN grain pin in M_PLANK; the per-course
CRSRAMP tones replace the grain within ±9px of every integer tile edge).
The prior --crown A/B = the geometric arch (kept as a flag + renders, not
the test here). B = --pins per-sprite: per-size M_PLANK variants
(M_PLANK_2/M_PLANK_4 = the SAME spec + an x/side multiply before the pin
FRACT, constants verbatim): internal tile-line windows GONE (grain
continuous inside each design), sprite-edge windows remain. Geometry
verified identical A vs B (0 diffs over all 817 objects; same seeds);
B built to /tmp/ford-boards-B.blend (throwaway until the eyes pick).
NOTE: B's sprite-edge band width = the window shape stretched to the
sprite period (±9px × side: ±18px on 2x2 / ±36px on 4x4); keeping ±9px
= one multiply constant, on request. Gwenview: pairs A/B per block +
zooms. Verdict = maintainer's eyes.

## 2026-10-21 — B pins approved; made the default + recorded
Maintainer: "I like B" (per-sprite pins: internal windows gone, grain
continuous inside each design; sprite-edge bands remain). The builder's
default flipped to --pins per-sprite; the committed blend rebuilt to the
B state and reopen-verified (520 planks / 294 bolts / M_PLANK_2|4
variant materials in-file; gates 0). Material law documented in
export-recipe.md (pin window terminology + the A/B decision record).
The ford/flooring deployed ladder pairs measured byte-identical
(1x1/2x2/4x4) — one staged sheet serves both names.

## 2026-10-21 — pipeline wired end-to-end; B sprites deployed; in-game
bake-ladder.py Stage B (render) is real now: the lattice cams at the
contract depth (128 px/tile) -> committed masters in assets-src/boards/;
--twice = the masters re-rendered + PIXEL-equal (green: deterministic).
Stage C offline (python3, no bpy): identity cut (the Stage-A lattice =
the master window == the sheet), the cut's own twice gate; staged per
name for BOTH shared-art tiles (wooden-ford + wooden-flooring, the
deployed pairs measured byte-identical); deploy = byte-verified copies;
gate = contract (ALL sizes 4x4 grids incl the 1x1 = 512^2 — the strip
retired) + staging==deploy + pair equality: PASS.
The lua contract flip: BOTH tiles' 1x1 line_length 16->4 (the recipe's
same-commit law); staged as MY hunks only (the cobble session's
uncommitted hunks left in the worktree untouched).
In-game: the viewer scenario rewritten to the current names (the old
sculpt still laid pre-2.0.0 water-ford + the retired shore-rim probe
tiles = the load crash; minimal fix = the lake + wooden-ford causeway +
WOODEN-FLOORING pads north + a mid-lake pad, noon-locked, zero Lua on
load). The scratch save flow remained flaky (a stale-window/lock
incident: the view stage reported alive off the OLD process while the
fresh save failed — the standing lesson), so the maintainer asked for
the direct setup: factorio launched on :0 with the DEFAULT install
(live-linked devctl symlink -> the repo deployable, B sheets deployed).
The repro recipe (whole round):
  cd mods/water-ford
  devctl build? no — graphics: blender -b --python tools/paper-pipeline/boards-builder.py -- --cells all
  (cd tools/paper-pipeline && blender -b --python bake-ladder.py -- --blend ../../blender/ford-boards.blend --base wooden-ford --twice)
  python3 tools/paper-pipeline/bake-ladder.py --base wooden-ford --stages cut,deploy,gate
  (the live-factorio run = the maintainer's default install; the scratch
  scenario = baking/qa only)

## 2026-10-22 — the "empty file" GUI incidents: factory Scene root-caused + fixed
Maintainer saw an empty scene TWICE on GUI opens. Root cause (measured in
a fresh headless probe): Blender 4.3 read_factory_settings(use_empty=True)
still births an empty scene "Scene", and scenes.new('FLOOR') does NOT
switch the active scene — so every builder-saved blend carried
['FLOOR'(821 objs), 'Scene'(0, ACTIVE)]. GUI opens land on the empty
scene (the framing was never the problem). Fixes, both committed:
the builder now drops the empty Scene and saves with FLOOR active
(re-verified: FILE_SCENES [(FLOOR, 821, True)] ACTIVE FLOOR); the GUI
poke helper = the load_post-hooked idiom (4.x runs --python scripts
BEFORE the file arg — the old poke framed the factory scene). Live
session fixed in-place via the bridge (ACTIVE FLOOR, Scenes [FLOOR],
821 objects, viewports re-framed material). Maintainer verdict: "this
looks correct... the template geometry for designing tilesets".
Also: pkill -f trick (matched my own shell = exit 143), pattern anchored
to the cmdline tail. The MCP bridge reports via get_scene_info need
content[0].text (not .result), fields whitelist = placement-free.

## 2026-10-22 — round closes: calibration + little-things PASSED by the maintainer; bake.sh ordering fixed
Maintainer accepted item 1 (pattern-rate calibration: NOT applied — the
approved look stands as-is) and item 4 (the 2x2 little-things list: passed).
Item 3 done: the save stage of bake.sh now pkills the previous factorio
before regenerating (the .lock + stale-window incident's fix; mirrors the
view stage). Item 2 (16-distinct gate) = explained, awaiting the go.

## 2026-10-22 — BOARDS ARC WRAP (session handoff: next session = cobble)

End state of the boards tileset arc, all committed:
- Template geometry CONFIRMED by the maintainer ("looks like the geometry
  that we discussed as our template"): blender/ford-boards.blend =
  regenerative output (boards-builder.py -- --cells all): FLOOR-only scene
  (the factory-Scene incident fixed), the Stage-A lattice (AREA_1X1/2X2/4X4,
  16 row-major designs each, cams = the contract depth), 520 planks / 294
  bolts, the approved B materials (M_PLANK + per-size M_PLANK_2/4 with the
  per-sprite pin window).
- All 3 ladder sheets deployed through the wired pipeline (bake-ladder.py:
  render masters + TWICE pixel-repro gate -> identity cut (own twice gate)
  -> byte-verified deploy -> contract gates PASS); 1x1 = 512^2 4x4-grid,
  the strip retired, lua line_length flipped (both tiles) in the same commit.
- In-game CONFIRMED by the maintainer (live-linked factorio on :0).
- Maintainer rulings recorded: the per-tile shade mechanism = the pin
  window (shader-side; export-recipe.md material law); pattern-rate
  calibration = PASSED AS-IS (item 1 accepted); the 2x2 little-things =
  passed (item 4); the 16-distinct gate = SKIPPED (item 2, not a priority).

OUTSTANDING after this wrap (for later sessions, listed in BACKLOG/repo docs):
- the cobble family through this recipe (--base cobblestone-ford --wetpass:
  the lattice re-base + the wetness pass + the drift closing) — THE NEXT
  SESSION'S WORK (the cobble arc; the cobble files = that session's
  in-flight work in the shared tree: mod/data*.lua/info.json,
  assets-src/cobble, make-icons.py, palette-ladder-cobble.py — DO NOT commit
  other sessions' in-flight files).
- the cobble mask wiring (a named change after the art run).
- the release packaging (the version bump + the changelog bullets at release
  time, per the frozen rule).
- housekeeping: .cache quarantine + README reconcile; the BACKLOG's blend
  items 1-3 marked superseded (done this wrap).
- the bolt-vanish-on-save bug = closed not-reproduced (monitored; the
  isolate recipe lives in probe-old-deck.py dump-planks).
## 2026-10-22 (cobble session) — THE COBBLE PURGE + the new process frame (maintainer rulings)

Rulings, in order of arrival this session:
1. **Commit the predecessor's in-flight work** (was the boards-wrap do-not-touch
   list): done — staging+masks (3055f7f), decoratives/icons/1.1.0 (1a40273),
   palette-ladder tool (c769b13), boards blend restored to builder output (cd30819,
   the post-wrap GUI save was UI-state-only: content-verified vs a fresh build,
   GEO_HASH dad240231648c813 equal), old viewer scratch save dropped (a1b3bd2);
   superproject ledger Q1/Q2/Q3 update + pointer (7ac0f2d, 6cc65ec).
2. **No art stand-ins**: planks ≠ cobbles (`boards-visual-language.md` transfers
   only LAWS, never look anchors); stone heaps ≠ cobbles. The boards mirror keeps
   its SHAPE (spec-before-Blender) but loses its object: nothing inherited is a
   look reference.
3. **THE WATER VEIL DOES NOT EXIST** in any actual rendering path (maintainer,
   "I am confident"); the wetness mechanism = the WET/DRY MASK (as for the piling
   workflow). Casualties: palette-ladder-cobble.py's WASHED column (moot — the
   tool is purged below), the prototype's effect_color/secondary (tuned under the
   veil assumption at 12.5% alpha — QUESTION MARK for the wiring round; frozen
   config, untouched).
4. **THE PURGE** ("all the old cobble code and blend gone — it is all cursed"):
   - git-removed: auth-cobble.py, bake-cobble.py, bake-cobble.sh (the condemned
     crank incl. mesh-hash oracle + provenance stamps), mat-fresh.py,
     wet-fresh.py (fresh-toolchain session scripts — no living object once the
     blend dies; the graphs' descriptions survive in the 2026-10-21 entries and
     the spec will re-record what the builder needs), palette-ladder-cobble.py.
   - untracked build-output removed: blender/ford-cobble.blend(+1) (45MB,
     gitignored), __pycache__.
   - kept BY RULING (art, not code/blend): the committed cobble sheet
     generations (assets-src/cobble + mod/graphics deploys) — they retire to
     archive per export-recipe.md at look-approval (maintainer may order them
     purged too if wanted now).
   - comment-only reference fixes (frozen zone, safe): data-updates.lua cobble
     comment now points at export-recipe + the spec; tools README cobble stage
     RETIRED; export-recipe.md purge note; .gitignore cobble-blend entries out.
5. **THE NEW PROCESS** = the boards mirror, corrected frame: spec-before-Blender
   with the waterline physical model FIRST ("we need the wet work, so that
   cobbles can be partially in the water") = docs/cobble-visual-language.md v1.

Next: the spec's decision points (pattern law, tone bands judged DRY, height/
breach law, variant identity) go to the maintainer; then the cobble builder.
## 2026-10-22 (cobble session 2) — spec walkthrough rounds 1–4 + builder v0 (the look round starts)

- Walkthrough rulings (all in the spec, dated): oblong cobbles 3×4/tile,
  merges into large cobbles; edge law = variant-invariant lattice faces,
  small spill allowed (hidden by shadows/neighbours), cobble TOP stays
  entirely within the tile; crown = flattened dome (the loaf archetype:
  irregular rounded corners+edges, inflated top); §3.3 numbers =
  TUNING KNOBS not given constants (heights first, breach follows);
  hard polished slate + speckle/non-reflective pitting (research-not-
  reinvent directive → the researched recipe recorded as §3.2a);
  variants = seeded geometry/packing jiggle (texture jiggle secondary);
  MANDATORY boards scene template (same lights/cams/staging); 2×2/4×4 =
  internal-grid jiggle free, outer edges law-bound; bed = faux
  sand/pebble rubble IN THE SHADER, sandy palette (committed spec).
- cobble-builder.py v0 committed (8b154d0): the boards skeleton with the
  cobble geometry/materials; self-check gates green (0 overlaps, edge
  law tol, heights in band). Ladder lessons: merge law needed
  edge-column members (interior-only rule = 0 merges everywhere); size
  jitter must be shrink-only vs the joint budget; outline excursion
  budget EXCURSION=0.006 (bow 0.025/wiggle 0.0015/ring-off 0.001).
- LOOK LADDER up for the maintainer's eyes (gwenview):
  /tmp/cobble-look-ladder.png (5 material rows, zoom 4×),
  /tmp/cobble-look-ladder-close.png (close ~26×: pits/polish),
  /tmp/cobble-area-survey.png (all 16 designs, 2×: variants + merges
  + edge law in situ). Verdict = the maintainer's.
- Next: rows ruled → fold into TUNE/ROW constants → the full lattice
  (2×2/4×4 + internal jiggle/collision resolve) → save path → wetpass.

## 2026-10-22 — hard reset → superellipsoid rounds (geometry + look)

- HARD RESET executed on the maintainer's order: every ring-ladder/bulge/
  tuck experiment condemned; builder reset to the first working scene
  (byte-identical loaf + the OUTLINK fix), then stones rebuilt on the
  maintainer-sourced SUPERELLIPSOID spec, verbatim: x,y = (extents/2)·
  sgn·|cos|^r with r per-stone in [0.40,0.50] (squircle plan), z =
  (h)·sgn·|sin|^t with t 0.2 top/0.8 bottom, H=2h, centre on the bed
  plane. Renamed: stone_verts_faces/emit_stone (loaf vocabulary gone).
- Rulings, in sequence (each = a build + fresh-window look):
  1. better → "lift": centre raised per-stone ¼–⅓ of full height
     (lift ∈ [0.5, 0.667]·h); crowns 11.9–27.0 px; base still buried.
  2. "cobbles tend to touch" → JOINT 0.012→0.004 first, then "drop the
     joint to 0" (drift/spill kept — sub-pixel position jitter is
     indistinguishable; maintainer confirmed meshes may intersect, and
     the bbox overlap gate I had authored in v0 is DELETED: it was my
     invention, not doc law).
  3. hoops: SUP_NTOP/SUP_NBUT 12/8→24/14, then re-sampled UNIFORM IN Z
     (the s-uniform sampling put ~22 of 23 upper rings on the top face
     and 1 on the wall; now bands at exact z = ±h·j/N — wall carries
     its hoops). 890 verts/stone (37 rings × 24 + poles).
  4. texture: metallic confirmed 0.0 (shine was dielectric specular +
     Standard view clipping); rough 0.35→0.55, rough_break 0.10→0.16
     (matte); base → darker+bluish (0.035,0.038,0.043, ratio R:G:B
     1:1.07:1.23); sand (M_COBBLEBED "bed") := the stone base tone.
- Proof workflow ruling: AREA RENDER ONLY (1024² over the 4×4 deck);
  zoom/close cameras retired from the builder.
- Numbers on the record: census 16 designs/163 stones/29 merges steady
  through every round; edge law + height band green (tol now 0.0045);
  area lum finished at 0.254 mean, max 1.000; renders lit throughout.
- Gates anchor: edge law + height band only (the packing stays
  lattice-anchored; JOINT now 0 → faces meet at lattice midpoints).
- Unresolved: ROW_VARIANTS ladder rows 2–5 awaiting eye rulings; tile
  edges (2×2/4×4) and the wetpass (masks/keying) still to come.

## 2026-10-22 (cobble session 3) — wetpass + Stage-A rulings approved; art masters next

- The wetpass round (session died mid-run last time) re-tabulated: the wetpass
  mask masters (`--wetpass`, WATER_PLANE z = 0.18, sliced stones + 85→25
  ramp, bed all-wet) DID land on disk before the death. Shown to the
  maintainer: **LOOK-APPROVED** (ruling 2026-10-22).
- Stage-A dry look: the three area proofs rendered 11:24–26
  (area-1/2/4_c = AREA_1X1/2X2/4X4, area-render-only ruling honored) shown
  to the maintainer: **"They look fine"** — the ROW_VARIANTS rows 2–5
  unresolved flag from the hard-reset entry CLOSES here; Stage-A eyes done.
- Committed this wrap: cobble-builder (AREA_2X2/4X4 blocks + CAMS roster +
  WATER_PLANE knob at z=0.18), bake-ladder `--wetpass`, ford-cobble.blend(+1),
  the three mask masters.
- Watch item carried to the wiring round (documented, not blocking): the
  wetpass gray ladder (flat-170 dry region, 25–70 ramp stops, 25 bed) has
  not been numerically censused since the pre-approval pixel check; the
  engine keys gray levels, so the wiring round re-verifies the ladder first.
- Next: Stage-B art masters (cobblestone-ford-master-{1x1,2x2,4x4}) from the
  committed cams; then cut --twice → deploy + the size-1 line_length flip.

## 2026-10-22 (cobble session 3 continues) — art masters look-approved; Stage C begins

- The three new-pipeline masters (cobblestone-ford-master-{1x1,2x2,4x4}, rendered
  16:41–44 from the committed blend by the committed driver, contract dims 512²/
  1024²/2048²) shown side-by-side with the old generations: **"The master
  spritesheets look good and they look correct against the wetness mask."**
- RULING: the on-disk wetness masks stand as look-approved FINAL (the §2
  numeric band census is not being re-run; the wiring round keys the gray
  ladder off the approved masks — watch item stands, journal above).
- Committed the masters (recipe: masters committed before any cut).
- bake-ladder offline Stage C gains the cobble branch: staging follows the
  base family (COBBLE_STAGING), no shared-art pairs, mask-sheet presence in
  the gate. Boards machinery untouched (selftest re-proved after the edit).
- Deploy commit carries the sheet+lua pair per recipe law: the size-1
  cobblestone-ford sprite line_length flips 16→4 (both tiles that share
  the art) AT THE SAME COMMIT as the first replaced 512² sheet.

- Stage C executed and gated: cut (twice-gate green) → deployed 3 sheets
  (byte-verified) → GATE PASS. Offline machinery gained the family-aware
  cobble branch (staging=COBBLE_STAGING, no shared-art pairs, mask-sheet
  presence in the gate).
- Lua shipped WITH the sheets (same-commit law): size-1 cobblestone-ford
  sprite line_length 16→4 in BOTH tiles that share the art; comment block
  updated to the current-pipeline state.
- Verification: check-assets OK; dlc-smoke smoke PASS; dump-diff vs a
  baseline re-captured from the pre-change tree = exactly the two expected
  cobble variants.main flips (note for hygiene: the previous :cache
  baseline predated yesterday's boards-wrap + icon-commit — its drift was
  absorbed into the fresh baseline); vehicle/pump harness run.py exit 0;
  py-closure smoke PASS.
- The old generations (strip 2048x128 + the Oct-21 sheets) are now git-
  history archive; staging == deployed from this commit forward.
