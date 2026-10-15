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
