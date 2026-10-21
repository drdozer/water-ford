-- Water Ford -- items, recipes, technology. Tile built in data-updates.lua
-- (stage experiment verdict, docs/dependency-audit.md §6: earliest stage that
-- both renders identically and inherits the stack's water-shallow mutations —
-- see the stage note in data-updates.lua).
--
-- Standalone mod; the Pyanodon integration is gated on pyalienlife. Names and
-- descriptions come from locale/en/locale.cfg ([item-name], [item-description],
-- [technology-name], [technology-description]) — prototypes deliberately carry
-- no localised_* overrides, so the locale file is the single place strings live.
--
-- The vanilla and py variants are SELECTED here and extended once: every
-- prototype table is final before data:extend. (The earlier extend-then-mutate
-- shape was the bug that hid the py recipe for three commits until the dump
-- caught it — 019fd2b.)

local py_loaded = mods["pyalienlife"] ~= nil

-- Vanilla recipe: cheap tile-tier inputs, in the band established by vanilla
-- landfill (1 stone + 2 sand -> 2 landfill). Enabled from the start is NOT
-- wanted: the water-ford technology gates it.
--
-- Pyanodon recipe: the floor board steps into the wood chain - creosote is
-- the wood-preservative stage, so the shared technology gates both boards
-- exactly when the player can first build something meant to live
-- underwater. The floor board carries treated-wood (planks) / iron-stick
-- (stakes and nails) / bolts (fasteners); the ford board adds log (pilings)
-- and gravel (ballast for the bed).
--
-- Provenance of the py items (see docs/dependency-audit.md §5): treated-wood,
-- log, gravel and the creosote technology are defined by pycoalprocessing;
-- bolts by pypetroleumhandling - both hard dependencies of pyalienlife, so
-- `? pyalienlife` transitively guarantees the whole set.
-- The ford board is composed: it consumes a wooden floor board plus the bed
-- material. Vanilla carries the bed as stone; py carries a real ballast bed
-- (gravel) plus a log for the pilings. One ford per craft, scarce by design
-- (a full stack of bed material per crossing).
local INGREDIENTS = py_loaded
    and {
      {type = "item", name = "wooden-flooring", amount = 1},
      {type = "item", name = "log",         amount = 1},
      {type = "item", name = "gravel",      amount = 200},
    }
    or {
      {type = "item", name = "wooden-flooring", amount = 1},
      {type = "item", name = "wood",        amount = 2},
      {type = "item", name = "stone",       amount = 100},
    }

local PREREQUISITES = py_loaded and {"creosote"} or {"concrete"}

-- 1 ford per craft: scarce by design. Tech and item live in distinct
-- data.raw namespaces. The tile/item/recipe are "wooden-ford" (the technology
-- mod's names uniform.
data:extend{
  {
    type = "item",
    name = "wooden-ford",
    icon = "__water-ford__/graphics/wooden-ford-icon.png",
    icon_size = 128,
    subgroup = "terrain",
    order = "c[landfill]-a2[water-ford]",
    stack_size = 100,
    place_as_tile = {
      result = "wooden-ford",
      condition_size = 1,
      condition = {layers = {water_tile = true}},
      invert = true,
    },
  },
  {
    type = "recipe",
    name = "wooden-ford",
    enabled = false,  -- unlocked by the water-ford technology
    energy_required = 10,
    -- Load-bearing for pypostprocessing compat (docs/dependency-audit.md §6):
    -- pypp's data-final-fixes composes a display name for every single-product
    -- recipe whose item has place_as_tile, eager-TILE()ing the tile — which
    -- only exists in OUR data-final-fixes (we sort after py*). Setting the
    -- name here skips that fallback entirely. Mirrors pypp's own
    -- {"?", recipe-name, item-name} chain; display is identical to the
    -- engine default.
    localised_name = {"?", {"recipe-name.wooden-ford"}, {"item-name.wooden-ford"}},
    ingredients = INGREDIENTS,
    results = {{type = "item", name = "wooden-ford", amount = 1}},
  },
  {
    type = "technology",
    name = "water-ford",
    icon = "__water-ford__/graphics/water-ford-tech-icon.png",
    icon_size = 256,
    effects = {
      {type = "unlock-recipe", recipe = "wooden-flooring"},
      {type = "unlock-recipe", recipe = "wooden-ford"},
    },
    unit = {count = 20, ingredients = {{"automation-science-pack", 1}}, time = 10},
    order = "a2[water-ford]",
    prerequisites = PREREQUISITES,
  },
}

-- Cobblestone ford item (1.1.0 Phase A): exists so the Phase A tile is
-- minable/placeable for the harness kit and the windowed hand tests. No
-- recipe/technology yet — the ticket's tech/recipe open questions are
-- Phase B. Stand-in icon references base art (__base__ path — nothing
-- copied); Phase B replaces it. Same place-on-water-only rule as the
-- wooden ford (inverted water_tile condition) and the same control-stage
-- revert guard (control.lua ford_names).
data:extend{
  {
    type = "item",
    name = "cobblestone-ford",
    icon = "__base__/graphics/icons/refined-hazard-concrete.png",
    icon_size = 64,
    subgroup = "terrain",
    order = "c[landfill]-a3[cobblestone-ford]",
    stack_size = 100,
    place_as_tile = {
      result = "cobblestone-ford",
      condition_size = 1,
      condition = {layers = {water_tile = true}},
      invert = true,
    },
  },
}
