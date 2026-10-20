# water-ford testmod — ford-vehicle-crossing

Headless scenario harness for the pathing contracts discussed in
`inbox/feature-cobblestone-road-ford.md` (superproject). Not for release.

Run from anywhere:

    devctl python run mods/water-ford/testmods/water-ford/run.py

Exit codes: 0 pass · 1 fail (contract broken) · 2 harness-error.
Results JSON lands in the scratch instance's `script-output/`; the server
log lives beside it under `.cache/water-ford-vehicle-test/`.

Four lanes, one car each, 2-wide bridges between grass islands in a water
moat: `wooden-ford` (the test: car must stop), `water-shallow` and
`deepwater` (vanilla references, informational), `landfill` (control: the
car must cross, else the harness itself is broken). Driving is a scripted
orientation + per-tick `car.speed` push — no unit groups (cars are not
units) and no third-party autopilot (its pathfinder would confound the
result); stopping is attributable to engine vehicle-vs-tile collision alone.
