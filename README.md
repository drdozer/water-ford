# Water Ford

A walkable ford tile over water for Factorio 2.1: land caravans cross it,
wooden pilings stand semi-submerged in animated water at the rims, and ships
still sail over it — fords keep the `water_tile` collision layer, so Cargo
Ships waterways stay navigable. Vehicles keep out: cars and tanks are
stopped at the shore (the ford is a footpath, not a road), and offshore
pumps can no longer be placed on it.

- Without [Pyanodon Alien Life](https://mods.factorio.com/mod/pyalienlife):
  unlocked by the concrete tech; a Wooden Flooring is 2 wood + 1 iron stick,
  and a ford is 1 flooring + 2 wood + 100 stone.
- With Pyanodon Alien Life: unlocked after creosote; a Wooden Flooring is 2
  treated-wood + 1 iron-stick + 8 bolts, and a ford is 1 flooring + 1 log +
  200 gravel (bed ballast).

## Cobblestone Ford (1.1.0)

The road crossing: **vehicles drive across** while players, land caravans
and enemies are stopped at the shore. Hand-laid cobblestones rise through
the water — some crowns breach the surface, joints stay dark, everything
below reads submerged. Ships still sail over it; offshore pumps are
refused. Placeable on water only, like the wooden ford.

- Recipe: 1 Cobblestone Path + 100 stone (bed ballast — a crossing's worth
  of material per ford).
- With Pyanodon Alien Life: 1 path + 200 gravel.

## Cobblestone Path (1.1.0)

The land partner: grey-blue cobbles for roads and yards, reading as one
family with the ford's deck. Slightly faster walking than bare land
(1.1; the cobble ford runs 0.9). Not placeable over water — the ford is
the crossing.

- Recipe: 2 stone + 1 stone brick.
- With Pyanodon Alien Life: 10 sand + 1 stone brick.

## Wooden Flooring

The matching land tile: honey-toned plank boards with a wooden bumper edge
at the waterline and a wooden trim against other terrain. Fords carry
land caravans across water; flooring is for camps, yards and walkways.
Not placeable over water — use the Wooden Ford or the Cobblestone Ford for
a crossing.

Fords can only be placed on water — illegal placements are reverted in the same
tick and refunded. Boards (and cobbles) are intentionally scarce: one per
craft; the cobble ford carries a full bed of ballast per crossing.

## For players

Install from the mod portal (Factorio 2.1.x), or drop
`dist/water-ford_<version>.zip` into your mods directory.

## For developers

Layout follows the superproject convention — `mod/` is the portal-clean
deployable, everything else is scaffolding:

```sh
devctl mods build water-ford     # zip from committed mod/ content -> dist/
devctl mods link water-ford      # live-link for in-game testing
devctl python run testmods/water-ford/run.py   # pathing-contract harness (exit 0)
python3 tools/gen-textures.py    # regenerate pilings/mask/planks (seeded)
python3 tools/gen-branding.py    # regenerate icon; thumbnail -> dist/ scratch
```

Agent-facing notes and invariants: [AGENTS.md](AGENTS.md).
Design history: [docs/shadow-experiments.md](docs/shadow-experiments.md) (the
13-round water-shadow investigation), [docs/dependency-audit.md](docs/dependency-audit.md)
(version floors, verified empirically), [docs/refactor-plan.md](docs/refactor-plan.md).

## License

MIT — see [LICENSE](LICENSE).
