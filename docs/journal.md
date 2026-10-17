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
