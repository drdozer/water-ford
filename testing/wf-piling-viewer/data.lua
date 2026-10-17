-- wf-piling-viewer: scenario-only viewer mod. The decorative piling prototype
-- was retired (the ford transition now carries the real sprites in-game).

-- Comparator tile (maintainer request, 2026-10-16): raw planks ON LAND,
-- exact same sprite sheet as the ford deck, no water effect — lets the eyes
-- compare the deck under the effect against the art under lighting alone.
data:extend
{
  {
    type = "tile",
    name = "wf-plank-land",
    subgroup = "special-tiles",
    variants =
    {
      main =
      {
        {
          picture = "__water-ford__/graphics/planks.png",
          count = 8,
          size = 1,
          scale = 0.5
        }
      },
      empty_transitions = true
    },
    collision_mask = { layers = { ground_tile = true } },
    layer = 60,
    map_color = { 143, 102, 60 }
  }
}

-- D2/D3/D4: property-bisect probes — each carries ONE MORE of the ford's
-- structural deltas (layer_group / transition_merges / is_foundation),
-- everything else = the bare probe (water-exact tint a=0, dark sheet).
data:extend
{
  {
    type = "tile",
    name = "wf-plank-dark",
    subgroup = "special-tiles",
    effect = "water",
    effect_color = { 21, 147, 167, 0 },
    effect_color_secondary = { 49, 80, 14 },
    variants =
    {
      main =
      {
        {
          picture = "__wf-piling-viewer__/graphics/planks-dark.png",
          count = 8,
          size = 1,
          scale = 0.5
        }
      },
      empty_transitions = true
    },
    is_foundation = true,
    collision_mask = { layers = { water_tile = true, resource = true, floor = true } },
    layer = 9,
    map_color = { 94, 67, 39 }
  },
  {
    type = "tile",
    name = "wf-plank-d2",
    subgroup = "special-tiles",
    effect = "water",
    effect_color = { 21, 147, 167, 0 },
    effect_color_secondary = { 49, 80, 14 },
    variants =
    {
      main =
      {
        {
          picture = "__wf-piling-viewer__/graphics/planks-dark.png",
          count = 8,
          size = 1,
          scale = 0.5
        }
      },
      empty_transitions = true
    },
    is_foundation = true,
    collision_mask = { layers = { water_tile = true, resource = true, floor = true } },
    layer = 9,
    map_color = { 94, 67, 39 },
    layer_group = "water"
  }
}data:extend
{
  {
    type = "tile",
    name = "wf-plank-d3",
    subgroup = "special-tiles",
    effect = "water",
    effect_color = { 21, 147, 167, 0 },
    effect_color_secondary = { 49, 80, 14 },
    variants =
    {
      main =
      {
        {
          picture = "__wf-piling-viewer__/graphics/planks-dark.png",
          count = 8,
          size = 1,
          scale = 0.5
        }
      },
      empty_transitions = true
    },
    is_foundation = true,
    collision_mask = { layers = { water_tile = true, resource = true, floor = true } },
    layer = 9,
    map_color = { 94, 67, 39 },
    layer_group = "water",
    transition_merges_with_tile = "water"
  }
}data:extend
{
  {
    type = "tile",
    name = "wf-plank-d4",
    subgroup = "special-tiles",
    effect = "water",
    effect_color = { 21, 147, 167, 0 },
    effect_color_secondary = { 49, 80, 14 },
    variants =
    {
      main =
      {
        {
          picture = "__wf-piling-viewer__/graphics/planks-dark.png",
          count = 8,
          size = 1,
          scale = 0.5
        }
      },
      empty_transitions = true
    },
    collision_mask = { layers = { water_tile = true, resource = true, floor = true } },
    layer = 9,
    map_color = { 94, 67, 39 },
    layer_group = "water",
    transition_merges_with_tile = "water",
    is_foundation = true
  }
}
-- CHECKER PROBES (maintainer request, 2026-10-16): is_foundation A/B —
-- identical tiles EXCEPT is_foundation; effect omitted; half-tile quadrant
-- checkerboard art (50% alpha-255 planks, 50% alpha-0). Question: does the
-- water beneath render through the transparent pixels (and only when
-- is_foundation is set)?
data:extend
{
  {
    type = "tile",
    name = "wf-checker-f",
    subgroup = "special-tiles",
    is_foundation = true,
    variants =
    {
      main = { { picture = "__wf-piling-viewer__/graphics/planks-checker.png",
                 count = 8, size = 1, scale = 0.5 } },
      empty_transitions = true
    },
    collision_mask = { layers = { water_tile = true, resource = true, floor = true } },
    layer = 9,
    map_color = { 120, 90, 50 }
  },
  {
    type = "tile",
    name = "wf-checker-n",
    subgroup = "special-tiles",
    variants =
    {
      main = { { picture = "__wf-piling-viewer__/graphics/planks-checker.png",
                 count = 8, size = 1, scale = 0.5 } },
      empty_transitions = true
    },
    is_foundation = true,
    collision_mask = { layers = { water_tile = true, resource = true, floor = true } },
    layer = 9,
    map_color = { 120, 90, 50 }
  }
}

-- PLAIN PROBE (maintainer request): the original deck art (bright planks
-- sheet, fully opaque) with the water effect OMITTED — the "no-shader"
-- in-lake reference against the ford (effect on) and the checker tiles.
data:extend
{
  {
    type = "tile",
    name = "wf-plank-plain",
    subgroup = "special-tiles",
    is_foundation = true,
    variants =
    {
      main = { { picture = "__water-ford__/graphics/planks.png",
                 count = 8, size = 1, scale = 0.5 } },
      empty_transitions = true
    },
    collision_mask = { layers = { water_tile = true, resource = true, floor = true } },
    layer = 9,
    map_color = { 143, 102, 60 }
  }
}
