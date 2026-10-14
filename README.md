# Water Ford

A walkable ford tile over water for Factorio 2.1: land caravans cross it,
wooden pilings stand semi-submerged in animated water at the rims, and ships
still sail over it — fords keep the `water_tile` collision layer, so Cargo
Ships waterways stay navigable.

- Without [Pyanodon Alien Life](https://mods.factorio.com/mod/pyalienlife):
  unlocked by the concrete tech; 4 wood + 1 iron stick + 50 stone per ford.
- With Pyanodon Alien Life: unlocked after creosote; crafted from treated-wood,
  iron sticks, bolts, a log and 200 gravel (bed ballast).

Fords can only be placed on water — illegal placements are reverted in the same
tick and refunded. Fords are intentionally scarce: one per craft, 10 s craft
time.

## For players

Install from the mod portal (Factorio 2.1.x), or drop
`dist/water-ford_<version>.zip` into your mods directory.

## For developers

Layout follows the superproject convention — `mod/` is the portal-clean
deployable, everything else is scaffolding:

```sh
devctl mods build water-ford     # zip from committed mod/ content -> dist/
devctl mods link water-ford      # live-link for in-game testing
python3 tools/gen-textures.py    # regenerate pilings/mask/planks (seeded)
python3 tools/gen-branding.py    # regenerate icon; thumbnail -> dist/ scratch
```

Agent-facing notes and invariants: [AGENTS.md](AGENTS.md).
Design history: [docs/shadow-experiments.md](docs/shadow-experiments.md) (the
13-round water-shadow investigation), [docs/dependency-audit.md](docs/dependency-audit.md)
(version floors, verified empirically), [docs/refactor-plan.md](docs/refactor-plan.md).

## License

MIT — see [LICENSE](LICENSE).
