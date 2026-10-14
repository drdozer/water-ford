-- Water Ford -- items, recipes. Tile built in data-final-fixes.lua.
--
-- Standalone mod; the Pyanodon integration will be revisited deliberately.
-- Until then the recipe is vanilla-only and enabled from the start.

local function water_ford_item()
  return {
    {
      type = "item",
      name = "water-ford",
      localised_name = {"", "Water Ford"},
      localised_description = {"", "A walkable ford over water: land caravans cross it, wooden pilings stand in the shallows, ships still sail over it."},
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
      energy_required = 1,
      ingredients = {
        {type = "item", name = "wood",        amount = 4},
        {type = "item", name = "iron-stick",  amount = 2},
      },
      results = {{type = "item", name = "water-ford", amount = 1}},
    },
  }
end

data:extend(water_ford_item())

-- Tech and item live in distinct data.raw namespaces, so the shared
-- "water-ford" id is legal and keeps the mod's names uniform.
--
-- Pyanodon integration: when pyalienlife is loaded the ford steps into the
-- wood chain - creosote is the wood-preservative stage, so requiring it gates
-- the ford exactly when the player can first build something meant to live
-- underwater - and the recipe switches to py materials.
local py_loaded = mods["pyalienlife"] ~= nil

local recipe = water_ford_item()[2]
if py_loaded then
  -- treated-wood (planks) / iron-plate (edge strapping) / bolts (fasteners) /
  -- log (pilings). NOTE: no "iron-bar" item exists in the loaded mod set;
  -- iron-plate is the substitution.
  recipe.ingredients = {
    {type = "item", name = "treated-wood", amount = 2},
    {type = "item", name = "iron-plate",   amount = 1},
    {type = "item", name = "bolts",        amount = 8},
    {type = "item", name = "log",          amount = 1},
  }
end

local tech = {
  {
    type = "technology",
    name = "water-ford",
    localised_name = {"", "Water Fords"},
    icon = "__water-ford__/graphics/water-ford-icon.png",
    icon_size = 64,
    effects = {{type = "unlock-recipe", recipe = "water-ford"}},
    unit = {count = 20, ingredients = {{"automation-science-pack", 1}}, time = 10},
    order = "a2[water-ford]",
  },
}
if py_loaded then
  tech[1].prerequisites = {"creosote"}
end

data:extend(water_ford_item())
data:extend(tech)