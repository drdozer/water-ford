# water-ford — agent notes

A walkable ford tile over water: land caravans cross, wooden pilings stand
semi-submerged, ships still sail over it (Cargo Ships waterways).

## Layout

Standard superproject mod layout: `mod/` is the portal-clean deployable (this
is what `devctl mods build water-ford` packs and what the live link points at).
`tools/`, `docs/`, `LICENSE`, `README.md` stay at the repo root and never ship.

## Target

**Factorio 2.1 only** (decision 2026-10-15 — see `docs/dependency-audit.md`).
`factorio_version: "2.1"` + `base >= 2.1.0` are already minimal; the code has no
2.1-only API (2.0.77 loads it with only the info.json lines changed — audit §4).

## Invariants (do not break casually)

1. **`mod/data-final-fixes.lua` tile config is frozen.** The ford = water-shallow
   clone + `effect = "water"` + piling transition rule whose pieces are OPAQUE
   plain-water composites + gray dryness effect map. The "shadow" mechanism took
   13 experiment rounds (`docs/shadow-experiments.md`); every "simplification"
   there was tested and rejected. Comment-only edits are safe.
2. **Control-stage behavior = the placement guard only** (`mod/control.lua`).
   Script-rendered visuals were tried and banned (round 9).
3. **Single-extend rule** in `mod/data.lua`: prototype tables are final before
   `data:extend` — never extend-then-mutate (that bug hid the py recipe for
   three commits, see 019fd2b).
4. **Strings live in `mod/locale/en/locale.cfg` only.** Prototypes carry no
   `localised_*` overrides. The control-stage flying text is the one hardcoded
   English string (deliberate; identical to 1.0.0 output).

## Dependencies (map: docs/dependency-audit.md)

- `? cargo-ships >= 2.1.8` — advisory only, no code references.
- `? pyalienlife >= 3.1.8` — gates recipe/prereq. Item provenance: treated-wood,
  log, gravel + tech `creosote` ← **pycoalprocessing**; `bolts` ←
  **pypetroleumhandling**; both are hard deps of pyalienlife, so the closure is
  sound. If the py suite reorganizes items, re-check audit §5.
- **Known issue (pre-existing in 1.0.0)**: with pypostprocessing installed (it is
  effectively mandatory for the py suite), the game **crashes in data-final-fixes**
  before the ford tile exists — `TILE("water-ford")` errors in pypostprocessing's
  recipe-name fallback. Repro + fix sketches: audit §6. Fixing it changes game
  content, so it is deliberately NOT in the 1.0.0-equivalence refactor; decide
  separately.

## Testing

Hermetic dumps per the superproject's `docs/testing.md` (`--mod-directory` +
`-c` scratch config; `--dump-data` exit code = load smoke). Scratch dirs live
in the superproject's gitignored `.cache/` (e.g. `.cache/water-ford-refactor/`
holds the pre/post-refactor dump evidence for the 1.0.0-equivalence claim).
Runtime placement behavior is unchanged from 1.0.0 — hand place/mine a ford on
the dlc install after any control.lua change.

## Graphics pipeline (standalone, needs PIL + numpy)

- `tools/gen-textures.py` — pilings/mask/planks sheets. Seeded: regenerates the
  shipped files **pixel-identically** (verified in the 1.0.0-equivalence pass).
  Writes only on pixel change; `--force` to rewrite; `--base` for the game
  install's `data/base` dir (default: dlc install or `$FACTORIO_BASE_DIR`).
- `tools/gen-branding.py` — icon (exact 64×64 slice of planks.png;
  pixel-identical) + thumbnail reconstruction (goes to `dist/` scratch; the
  shipped `mod/thumbnail.png` is canonical — its border water matches no base
  crop, see the script header).
- `assets-src/` does not exist yet: all art is generated. If real external art
  ever appears, it belongs there and never in `mod/`.
