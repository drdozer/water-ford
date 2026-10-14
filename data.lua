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
      enabled = true,
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