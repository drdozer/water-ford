# Ford deck ballast — pebble+stone bound decoratives

Shipped in rounds 23–25 (2026-10-18). The stones = engine-native
`bound_decoratives` (see the generic reference
`docs/factorio-decoratives.md` in the superproject for the system), authored
in a dedicated Blender factory.

## Factory

`blender/ford-stones.blend` — scenes `PEBBLES` (24 frames @ 40 px cells)
and `STONES` (12 frames @ 64 px cells). Each variation = a heap of 2–3
stones; every stone mesh is sliced at the uniform waterline plane z=0 into
an above part (`...a`) and a below part (`...w`), a true vertex ring at the
cut (piling GN-cut semantics, no object tilt so the plane stays horizontal).

- Camera: the posts-rig angle (45° elevation, ortho), re-aimed at heap
  height; ortho scale 0.55 (pebbles) / 0.88 (stones).
- Key sun 4.2 WSW-up (rays east+north+down: shadows east, away from the
  camera); south area-fill 25 W carries the visible faces (too strong reads
  as backlit). AgX, Cycles seed 0, 1 thread fixed, no adaptive sampling.
- Below parts render through washed bright masks (M_PEBBLE_WET /
  M_STONE_WET): under `multiplicative-with-alpha` a bright mask = a gentle
  wet darkening; a dark mask = near-black feet (v1 bug).

## Scripts (buttons)

| Button | Purpose |
|---|---|
| `tools/paper-pipeline/auth-stones.py` | rebuilds the factory file (run in a VISIBLE blender session; rotation_mode law!). Only when the art changes. |
| `tools/paper-pipeline/bake-stones.sh [--twice]` | render + pack the four sheets from the committed factory; `--twice` = pixel-array proof. |
| `tools/paper-pipeline/check.sh [NAME]` | headless zero-error gate. |
| `tools/paper-pipeline/bench.sh SAVE X,Y TAG [--paint LUA]` | scripted console-law in-game verification. |

Outputs: `mod/graphics/ford-decorative-{pebbles,stones}.png` +
`...-below.png` (aligned cell grids: 400×120 @ 40 px, 640×128 @ 64 px,
10 per line).

## Wiring

`mod/data-updates.lua`: prototypes `ford-pebbles` (ground-layer-1,
collision ±0.12, sep 0.12) and `ford-stones` (ground-layer-3, collision
±0.3, sep 0.5), both with layered `pictures`; `tile.bound_decoratives` on
water-ford. **Density knobs**: `target_count` (pebbles 120, stones 20 —
~¼ of the SA-platform effective density the maintainer found overwhelming;
bench-verified live) and the `bound_decoratives` list itself.

Palette: vanilla-anchor umber/brown (measured vanilla rock decoratives
mean [79,56,33], hi [120,96,48]); light stops raised so lit faces read
at/above deck brightness ([132,108,77] rendered mean) — dark stops keep
the umber.

## Runtime facts (benched)

- Sprinkles fire on tile BUILDS only; existing tiles never retro-sprinkle.
- Pieces render above the water veil — the multiplicative below-slice is
  what makes them read as sitting IN the water/wet deck.
- The engine has no decorative wetness mask; `opacity_over_water` exists
  but is decals-layer-only and would mask the whole deck tile uniformly —
  not usable for deck art (details in the superproject reference).
