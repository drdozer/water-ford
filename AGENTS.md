# water-ford — agent notes

A walkable ford tile over water: land caravans cross, wooden pilings stand
semi-submerged, ships still sail over it (Cargo Ships waterways). **Target:
Factorio 2.1 only** (decision 2026-10-15 — `docs/dependency-audit.md`).

All-mods procedures live in the superproject `AGENTS.md` + `docs/`; this file
holds only what is specific to this mod. Session history:
`docs/journal.md`.

## Layout

Superproject standard: `mod/` is the portal-clean deployable (what
`devctl mods build water-ford` packs and what the live link points at);
`tools/`, `docs/`, `LICENSE`, `README.md` stay at the repo root and never ship.
Generative-art briefs (AI-art prompts + committed candidate runs) live in
`assets-src/ai/<brief>/` — process: superproject `docs/ai-art-briefs.md`.

## Invariants (each has its reason documented — follow the pointer)

1. **Tile config in `mod/data-updates.lua` is frozen**, and the **stage is
   load-bearing**: water-shallow clone + `effect = "water"` + opaque-composite
   piling rule + dryness effect map. 13 experiment rounds say every
   "simplification" was tested and rejected (`docs/shadow-experiments.md`);
   the stage choice (data-updates, not data.lua/final-fixes) is the experiment
   verdict in `docs/dependency-audit.md` §6. Comment-only edits are safe.
2. **Control-stage behavior = the placement guard only** (`mod/control.lua`).
   Script-rendered visuals were tried and banned (round 9).
3. **Single-extend rule** in `mod/data.lua`: prototype tables are final before
   `data:extend` — never extend-then-mutate (that bug hid the py recipe for
   three commits, `019fd2b`).
4. **Strings live in `mod/locale/en/locale.cfg`** — hooks cover item, recipe,
   technology, tile, mod title/description, and the placement-denied flying
   text. The **recipe's `localised_name` is load-bearing** (pypostprocessing
   compat — do not remove; `docs/dependency-audit.md` §6).

## Dependencies

- `? cargo-ships >= 2.1.8` — advisory only, no code references.
- `? pyalienlife >= 3.1.8` — gates recipe/prereq. Item provenance:
  treated-wood/log/gravel + tech `creosote` ← **pycoalprocessing**; `bolts` ←
  **pypetroleumhandling**; both hard deps of pyalienlife. **Re-check provenance
  whenever the py suite updates** — method and map:
  `docs/dependency-audit.md` §5; suite behaviour: superproject
  `docs/py-suite.md`.

## Verification quick recipe (details in superproject docs)

- Asset gate: `python3 tools/check-assets.py` — every graphics/sound
  reference must resolve to a shipped file. Run after ANY asset or
  reference change; the data-stage checks cannot catch a missing file.
- Load smoke + dump-diff: hermetic `--dump-data` in a pinned set; compare the
  `water-ford` item/recipe/technology/tile subtrees against the baseline
  (superproject `docs/data-lifecycle.md`). Baselines live in
  `.cache/water-ford-refactor/` (scratch — recreate from the docs).
- py branch: real-closure run (symlink the py zips, disable
  space-age/quality/elevated-rails) — must exit 0 with the piling rule intact.
- Visual: seed-pinned scenario harness (superproject `docs/visual-testing.md`;
  harness in `.cache/stage-exp/`, one-off). The critical arrangements are
  open-water rims, ford/shallow border, ford/land border — and the absence of
  the neighbour-shadow band.
- Runtime placement: unchanged since 1.0.0 — hand place/mine one ford on the
  dlc install after any `control.lua` change.

## Tools (standalone; PIL + numpy)

These inherit the **superproject shared venv** via walk-up discovery
(superproject `docs/python-env.md`): prefer `devctl python run
tools/gen-textures.py` for the pinned interpreter + dependency set. The
plain shebangs keep them runnable standalone (system python3 + apt
PIL/numpy as the fallback). Do **not** vendor a venv in this repo.

- `tools/gen-textures.py` — pilings/mask/planks sheets; seeded → regenerates
  the shipped files pixel-identically; writes only on pixel change.
- `tools/gen-branding.py` — thumbnail reconstruction → `dist/` scratch (shipped
  `mod/thumbnail.png` is canonical — its border water matches no base crop).
- `tools/build-audio.py` — footstep audio: rebuilds `mod/sound/walking/` +
  `assets-src/audio/masters/` deterministically from the recorded sources in
  `assets-src/audio/source/` (every curation knob embedded; ffmpeg on PATH).
  Story + lessons: `docs/journal.md` 2026-10-20 and superproject
  `docs/how-to-do-audio.md` §11.
  Its 1.0.0 icon writer is retired: the item icon belongs to
  `tools/paper-pipeline/make-icons.py` (128px deck-cell + stones).
- `tools/check-assets.py` — the launch-time asset gate: every graphics/sound
  reference in `mod/*.lua` must resolve to a shipped file (incl.
  `sound_variations` prefix expansion). The data-stage checks never validate
  file existence — run this in every verification pass.
- `assets-src/ai/` (generative art briefs) and `assets-src/audio/`
  (recorded sources + curated masters) hold real external assets — never in
  `mod/`.

## Docs index

- `docs/dependency-audit.md` — version floors (empirical), py item provenance,
  the pypostprocessing crash + stage experiment
- `docs/shadow-experiments.md` — the 13-round water-shadow investigation
  (pre-1.0.0; the reason the tile config is frozen)
- `docs/refactor-plan.md` — executed refactor plan (provenance)
- `docs/ford-knobs.md` — the ford's measured parameter space (knobs and
  pulleys): tint/alpha response surface, halo law, boundary stamp systems,
  frozen settings
- `docs/shadows.md` — shadows & reflections reference: draw_as_shadow
  (sprite-level, shadow pass) vs water_reflection (entity-level,
  EntityWithHealth/Corpse only); tiles have NO shadow/reflection mechanism;
  DECISION: ford poles stay pure tile art (route a); build-time cheat sheet
- `docs/journal.md` — session work log
