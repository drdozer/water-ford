-- Items, recipes and technology for every enabled ford variant.
-- All variants share the same PLACEHOLDER recipe (see `ingredients` below) and one tech.
-- The tiles themselves are built in data-final-fixes.lua.

local V = require("py-ford-variants")

local ingredients = {
  {type = "item", name = "treated-wood", amount = 2},
  {type = "item", name = "iron-stick",   amount = 2},
}

local recipe_names = {}
for i, v in ipairs(V.list) do
  if V.enabled(v) then
    data:extend{
      {
        type = "item",
        name = v.name,
        localised_name = {"", v.title},
        localised_description = {"", "Experimental walkable ford tile. Place on water. Caravans can cross it; Cargo Ships waterways still work on it."},
        icons = {{icon = "__base__/graphics/icons/landfill.png", icon_size = 64, tint = v.tint}},
        subgroup = "terrain",
        order = string.format("c[landfill]-z[py-ford]-%02d", i),
        stack_size = 100,
        -- `invert` flips the condition from a conflict mask into a permission mask:
        -- placeable ONLY where the existing tile carries the water_tile layer (vanilla +
        -- modded waters), so it cannot be built over landfill or any other land tile.
        place_as_tile = {
          result = v.name,
          condition_size = 1,
          condition = {layers = {water_tile = true}},
          invert = true,
        },
      },
      {
        type = "recipe",
        name = v.name,
        enabled = false,
        energy_required = 1,
        ingredients = ingredients,
        results = {{type = "item", name = v.name, amount = 2}},
      },
    }
    recipe_names[#recipe_names + 1] = v.name
  end
end

local prereqs = {}
for _, name in pairs{"zoology", "creosote"} do
  if data.raw.technology[name] then prereqs[#prereqs + 1] = name end
end

local effects = {}
for _, name in ipairs(recipe_names) do
  effects[#effects + 1] = {type = "unlock-recipe", recipe = name}
end

if #effects > 0 then
  data:extend{{
    type = "technology",
    name = "py-caravan-ford",
    icon = "__base__/graphics/technology/landfill.png",
    icon_size = 256,
    prerequisites = prereqs,
    effects = effects,
    unit = {count = 50, ingredients = {{"automation-science-pack", 1}}, time = 30},
  }}
end

-- The piling entity: script-placed (control.lua) on water cells adjacent to ford
-- tiles. It deliberately is NOT a tile transition - transitions from a ford onto
-- water claim territory that the deck's water effect then darkens (the shadow).
-- 8 jittered sprite variants (the art sheet's row 0, 64x64 pieces at scale 0.5).
local piling_sprites = {}
for i = 0, 7 do
  piling_sprites[#piling_sprites + 1] = {
    filename = "__py-caravan-ford__/graphics/pilings-entity.png",
    priority = "extra-high",
    x = i * 64, y = 0,
    width = 64, height = 64,
    scale = 0.5,
  }
end

data:extend{
  {
    type = "simple-entity",
    name = "py-ford-piling",
    flags = {"placeable-neutral"},
    pictures = piling_sprites,
    collision_box = {{0, 0}, {0, 0}},
    -- no selection_box: posts are not selectable, bots ignore them,
    -- destructible defaults false so nothing removes them but the manager.
  },
}
