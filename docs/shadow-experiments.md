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