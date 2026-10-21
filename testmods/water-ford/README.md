# water-ford testmod — ford-vehicle-crossing

Headless scenario harness for the ford pathing contracts
(`inbox/feature-cobblestone-road-ford.md`, superproject). Not for release.

Run from anywhere:

    devctl python run mods/water-ford/testmods/water-ford/run.py

Exit codes: 0 pass · 1 fail (contract broken) · 2 harness-error.
Results JSON lands in the scratch instance's `script-output/`; the server
log lives beside it under `.cache/water-ford-vehicle-test/`.

Lane groups (2-wide bridges between grass islands in a water moat, one
scripted car per car lane, pushed west by orientation + per-tick
`car.speed` — stopping is attributable to engine vehicle-vs-tile collision
alone):

- `wooden-ford` (car must STOP — the 1.0 contract, kept as regression gate),
  `cobblestone-ford` (the 1.1 road ford: car must CROSS), `water-shallow`
  … `landfill` (vanilla references + `landfill` control: must cross, else
  harness-error), 13 `wf-probe-<layer>` single-layer tiles (the vanilla
  layer grid), `wf-probe-custom` (custom-layer movement probe) and three
  pump-ablation lanes (2×2 water_tile-mask × name-list evidence).
- Unit lanes (`unit-*`): a **path-request oracle** — no entity walks
  (biters commanded from script die at command re-issue — journal
  2026-10-21); the engine pathfinder is asked asynchronously
  (`surface.request_path` + `on_script_path_request_finished`) across each
  bridge with the small-biter's real collision box + mask: cobble and
  deepwater must yield NO reaching path; wooden/shallow/landfill must reach.

Chunk generation is force-completed before the paint (`set_tiles` silently
drops tiles in ungenerated chunks) — the launch order lives in
`scenarios/ford-vehicle-crossing/control.lua`.