# Ford shadow experiments — tested matrix

The symptom: a soft dark band in the WATER TILES SURROUNDING the ford tiles.
Not painted anywhere; vanishes with debug `show-raw-tile-transitions`.

## Grid (round order)

| # | Change tested                                | Shadow? | Notes |
|---|----------------------------------------------|---------|-------|
| 1 | baseline: rule + mask (else-0)               | YES     | posts above water when mask present |
| - | mask baseline raised to 85 (deck-wide dryness)| YES    | + tile-wide rectangles on neighbours |
| - | tints removed                                | YES     | deck brightness only, shadow unchanged |
| 2 | piling rule REMOVED (B)                      | **NO**  | only round where the shadow ever disappeared |
| 2 | rule present, ford at layer 3 (C)            | YES     | layer exonerated |
| 3 | rule present, NO effect map (B)              | YES     | mask exonerated |
| 3 | rule present, PRIVATE group 40 (C)           | YES     | water-group coupling exonerated |
| 4 | rule present, BLANK art, no mask (B)          | YES     | nothing rendered, still shadow: declaration-independent of content |
| 4 | pieces raised: overlay_layer_group=ground-natural (C) | YES* | round-4 note flagged only the blend; this round: all three identical → STILL SHADOW |
| 1 | is_foundation = false                        | YES     | |
| 1 | inherited variants.transition stripped       | YES     | (needed empty_transitions=true) |
| – | land-side bank rules / between-transition water_patch | (present) | no shadow without the piling rule ⇒ not the source |
| – | **debug show-raw-tile-transitions ON**        | **NO**  | the only switch that has ever removed it |

## Standing conclusions

- The shadow follows the piling rule's EXISTENCE with to_tiles = water tiles.
  Every rule-internal knob is exonerated: art content, effect map, transition
  group, piece layer, piece render slot. Ford tile props exonerated: layer,
  is_foundation, inherited edge overlays, tints.
- The ONE engine behaviour that always correlates: show-raw-tile-transitions
  (skips the water shader's transition passes) removes it.

## New suspect (round 5)

The ford inherited vanilla water-shallow's tile `effect = "water"` with
`effect_color` [7.75, 28.5, 33.25, 31.875] and a secondary colour. Hypothesis:
the engine renders the tile's effect machinery over the transition territory
its rules claim on neighbouring water tiles — soft dark tint band. Fits all
grid rows: plain waters never declare transitions between themselves (no
territory → no shadow); land tiles carry no effect (their bank rules shade
nothing); show-raw skips the effect passes.

Arms: A = control (effect untouched) · B = effect/effect_color/secondary nil'd
· C = effect kept, both colours zeroed.

## Round 5 verdict — mechanism found and fixed

| Ford | Config | Result |
|------|--------|--------|
| A | effect intact | pilings + shadow |
| B | effect nil'd | pilings, **NO shadow** — deck looked dry/above water |
| C | effect kept, colours zeroed | pilings + shadow; degraded edge-only water look |

Mechanism: the tile's inherited `effect = "water"` machinery renders over the
transition territory the piling rule claims on neighbouring water tiles - the
soft dark band. The colours were irrelevant (C). Removing the effect removes
both the shadow and the deck's watery wash, so the submerged look is painted
into the deck art instead: the generator re-washes pristine `planks-base.png`
into `planks.png` (knobs DECK_WASH / DECK_WASH_STRENGTH). Final config on all
three fords: no tile effect, pieces in `ground-natural` (above the shader
pass), painted wet feet, painted underwater deck.
## Round 6 — final architecture

Round-5 B proved the effect = both the deck's water AND the shadow's vehicle;
the painted wash was rejected (hard edges, no real water). Resolution:
- RESTORE the tile effect (effect = "water" inherited): deck under water again.
- REMOVE all water-targeting transitions from the ford (the territory claim
  was the only thing that carried the effect's darkening onto neighbours).
- Pilings = script-placed simple-entity "py-ford-piling" (8 jittered sprites,
  zero collision, non-selectable, destructible=false), placed on water cells
  adjacent to fords by control.lua on player/robot built/mined tile events,
  removed when the adjacent water changes or the ford goes.

Dump-verified: fords carry only the out-of-map rule; effect = water; entity
prototype present with 8 pictures. NOTE: pilings appear only on fords placed
after loading this build (old placements had no entities).

## Round 7 — water-owned rules: shadow dead, pieces buried

Vanilla water tiles gained rules targeting the fords (source = water,
target = ford, pieces on the FORD's rim cells). Result on the user's test:
ALL THREE identical - no shadow anywhere (the vintage, second confirmation:
effect + no water-claiming rules = clean) - but NO pilings: pieces render
at the SOURCE's layer (3), beneath the opaque layer-9 deck. The claim and
the paint work; the painter's floor is too low.

## Round 8 — raising the pieces (control + two tests)

- B (py-ford-exp-1): control, untouched (vintage, no pilings).
- A (py-ford-flooded): masked rule + overlay_layer_offset = 6 - in-family
  raise to deck level; the mask should keep its shader access (crowns lift).
- C (py-ford-exp-2): unmasked rule + overlay_layer_group = "ground-natural"
  - the proven out-of-family move (round 4); masks are inert there.
