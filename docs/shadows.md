# Shadows & reflections on the ford poles — survey (2026-10-17)

Question (maintainer): the poles look great but want cast shadows and reflections;
use vanilla entities as references, no guessing.

## The two engine mechanisms

### Cast shadows: `draw_as_shadow = true` (sprite-level)
- Property lives on **SpritePrototype / AnimationPrototype** and in the shared
  **SpriteParameters** set (doc-html/prototype-api.json). Boolean; mutually
  exclusive with `draw_as_glow` / `draw_as_light`.
- The engine draws the sprite in a **separate shadow pass** (darkens what is
  beneath); the RenderLayer enum (prototype-api RenderLayer type) has NO shadow
  entry at all — shadows are not a layer, they are a pass. (Evidence of the
  ordering: `lower-object-above-shadow` exists as a layer *above* shadows.)
- Art is always a **separate sheet**; vanilla never bakes a shadow into the
  main sprite.
- Vanilla users: character (`idle_shadow` / `dead_shadow` sheets,
  character-animations.lua:72–87), turrets (turrets.lua:73+), trees
  (entity-util.lua:192 `sprite_load(filepath_shadow, … draw_as_shadow = true)`,
  trees.lua:4839), steam-engine (`steam-engine-V-shadow.png` /
  `steam-engine-H-shadow.png`, entities.lua ~1770+).
- Factorio has **no dynamic sun shadows**: every shadow is static sprite art.

### Reflections: `water_reflection` (entity-level)
- EntityPrototype property, type **WaterReflectionDefinition** =
  `{ pictures (SpriteVariations, a dedicated pre-drawn mirrored/tinted sheet —
  NOT derived from the main art), rotate, orientation_to_variation }`.
- **Only renders for EntityWithHealthPrototype and CorpsePrototype** (API
  description, forum link factorio.com/forums/100703).
- Vanilla users: character (entities.lua:1005, `character-reflection.png`
  13×19), steam-engine (`steam-engine-reflection.png`), boiler
  (`boiler_reflection()`, entities.lua ~1500s), trees (`get_water_reflection =
  tree_NN_reflection`, trees.lua:3759+, `tree-01-reflection.png` 28×40).
- The engine renders the dedicated sheet mirrored/wobbling within the water
  shader, which painted-in art cannot reproduce.

## The reference cases (maintainer's list, all verified)
| Object | Shadows | Reflection | Where |
|---|---|---|---|
| Player | YES — idle/dead shadow sheets | YES | character-animations.lua:72, entities.lua:1005 |
| Steam engine | YES — V/H shadow sheets | YES | entities.lua steam-engine block |
| Trees | YES — entity-util.lua:192 | YES — tree-NN-reflection | trees.lua:4839, 3759+ |
| Turrets | YES (layers) | — | turrets.lua:73+ |

## The tile-side verdict (the parked question, now resolved)
- **TilePrototype property list** (complete, prototype-api): no `shadow`, no
  `reflection`, no draw-flag of any kind. Transitions are
  `TileTransitionsToTiles` arrays. **Tile transition pieces cannot carry
  engine shadows or reflections. There is no tile-side mechanism at all** —
  the parked header's "own engine layer remains unresolved" is answered: no
  such layer exists for tile art.
- SimpleEntityPrototype is a subclass of **EntityWithHealthPrototype**
  ("extremely basic entity… used for minable rocks") — a pole prototype only
  needs `simple-entity` to qualify for `water_reflection` rendering, and any
  of its sprites can carry `draw_as_shadow`.

## Routes for the poles (options, undecided)
- **(a) Tile art only** — no shadows/reflections, forever. Zero work.
- **(b) Pole entities** — simple-entity per pole (or per pole cluster) carrying
  draw_as_shadow shadow sheet + water_reflection reflection sheet. Needs
  placement/lifecycle handling as ford tiles change (event-driven
  place/remove at the boundary); real reflections wobble in the water shader.
  The parked `shadows64-` art reserve maps to the entity's shadow sheet.
- **(c) Painted inside the composite sheet** — static mirrored-post reflection
  in the flat-water background pixels (wobbles only as much as the effect_map
  mask distorts them) + soft under-post shading. Art-only, no entities — but
  touches the parked "shadow forbidden inside art pixels" rule, whose wording
  predates the composite-boundary design. Maintainer must rule.
- **(d) Hybrid** — (c) for the static shadow/shading, (b) only for the
  wobbling reflection.

## DECISION (2026-10-17, maintainer)

**Route (a) — tile art only.** The poles stay as transition-sheet art on the
committed W3+P1 baseline; no engine shadows or reflections for the ford.
The other routes (entities, painted reflections) are recorded above but set
aside — not investigated further. The survey below is preserved as the
reference for the NEXT thing we build graphics for.

## Build-time cheat sheet (what the survey taught, in one glance)

- **Sprite flagged `draw_as_shadow = true`** → drawn in the engine's shadow
  pass, darkening what's beneath (terrain, other tiles, whatever). It is a
  property of sprites/animations (SpriteParameters), NOT of prototypes or
  layers — there is no "shadow" RenderLayer. Keep the shadow as its own
  sheet; never bake shadow pixels into the main art. Shadows are static
  (Factorio has no dynamic sun). Vanilla examples: character idle/dead
  sheets, turrets, trees (entity-util.lua:192), steam-engine V/H sheets.
- **`water_reflection = {pictures, rotate, orientation_to_variation}`** →
  entity-level only; renders ONLY on EntityWithHealthPrototype and
  CorpsePrototype. `pictures` = a dedicated pre-drawn mirrored/tinted sheet
  (do NOT derive it from the main art); the engine wobbles it inside the
  water shader. Simplest qualifying prototype: `simple-entity` (a
  EntityWithHealth subclass). Vanilla examples: character (13×19 sheet),
  boiler/steam-engine, chest, trees (28×40 sheets), robot_reflection helper.
- **Tiles and tile-transition pieces can have NEITHER.** TilePrototype's
  property list has no shadow/reflection/draw-flag; transitions are plain
  art arrays. If a boundary/detail feature needs engine shadows or
  reflections, it must be an entity (simple-entity is enough) placed and
  managed by mod code — not tile art.
- **Water-side rendering niceties learned along the way:**
  `apply_effect_color_to_overlay` on a transitions entry tints the WHOLE
  stamped art (background included); two entries sharing
  transition_group+to_tiles do not stack (last wins); variant-sprite alpha is
  flattened, transition-piece alpha works; a flat opaque water-colored
  background inside stamped frames kills the shore rim (UF0/P1 proof).

## Next
Closed. Any future graphics work that wants shadows/reflections starts here:
pick the entity route (b)/(d) shapes only if the placement/lifecycle cost is
acceptable; painted options (c) remain blocked unless the maintainer updates
the "shadows forbidden inside art pixels" rule.