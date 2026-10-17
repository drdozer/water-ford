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
-- Pyanodon recipe: the ford steps into the wood chain - creosote is the
-- wood-preservative stage, so requiring it gates the ford exactly when the
-- player can first build something meant to live underwater. treated-wood
-- (planks) / iron-stick (stakes and nails) / bolts (fasteners) / log (pilings)
-- / gravel (ballast for the bed, unlocked before creosote).
--
-- Provenance of the py items (see docs/dependency-audit.md §5): treated-wood,
-- log, gravel and the creosote technology are defined by pycoalprocessing;
-- bolts by pypetroleumhandling - both hard dependencies of pyalienlife, so
-- `? pyalienlife` transitively guarantees the whole set.
local INGREDIENTS = py_loaded
    and {
      {type = "item", name = "treated-wood", amount = 2},
      {type = "item", name = "iron-stick",   amount = 1},
      {type = "item", name = "bolts",        amount = 8},
      {type = "item", name = "log",          amount = 1},
      {type = "item", name = "gravel",       amount = 200},  -- ballast: one full stack
    }
    or {
      {type = "item", name = "wood",        amount = 4},
      {type = "item", name = "iron-stick",  amount = 1},
      {type = "item", name = "stone",       amount = 50},
    }

local PREREQUISITES = py_loaded and {"creosote"} or {"concrete"}

-- 1 ford per craft: scarce by design. Tech and item live in distinct
-- data.raw namespaces, so the shared "water-ford" id is legal and keeps the
-- mod's names uniform.
data:extend{
  {
    type = "item",
    name = "water-ford",
    icon = "__water-ford__/graphics/water-ford-icon.png",
    icon_size = 64,
    subgroup = "terrain",
    order = "c[landfill]-a2[water-ford]",
    stack_size = 100,
    place_as_tile = {
      result = "water-ford",
      condition_size = 1,
      condition = {layers = {water_tile = true}},
      invert = true,
    },
  },
  {
    type = "recipe",
    name = "water-ford",
    enabled = false,  -- unlocked by the water-ford technology
    energy_required = 10,
    -- Load-bearing for pypostprocessing compat (docs/dependency-audit.md §6):
    -- pypp's data-final-fixes composes a display name for every single-product
    -- recipe whose item has place_as_tile, eager-TILE()ing the tile — which
    -- only exists in OUR data-final-fixes (we sort after py*). Setting the
    -- name here skips that fallback entirely. Mirrors pypp's own
    -- {"?", recipe-name, item-name} chain; display is identical to the
    -- engine default.
    localised_name = {"?", {"recipe-name.water-ford"}, {"item-name.water-ford"}},
    ingredients = INGREDIENTS,
    results = {{type = "item", name = "water-ford", amount = 1}},
  },
  {
    type = "technology",
    name = "water-ford",
    icon = "__water-ford__/graphics/water-ford-icon.png",
    icon_size = 64,
    effects = {{type = "unlock-recipe", recipe = "water-ford"}},
    unit = {count = 20, ingredients = {{"automation-science-pack", 1}}, time = 10},
    order = "a2[water-ford]",
    prerequisites = PREREQUISITES,
  },
}
