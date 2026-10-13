-- Shared list of ford variants. Used by data.lua (items/recipes/tech) and
-- data-final-fixes.lua (tiles), so both stages always agree on what exists.
--
-- Structure: ONE gold-standard tile (do not change) plus up to three experiment
-- slots. Anything retired lives in git history; the mod is unreleased, so
-- breaking renames/culls here are fine.
--
-- groups (each can be switched off in startup settings):
--   custom : all current fords (planks / flooded family)
--
-- kinds:
--   flooded     water-shallow clone with planks main, layer 9 (renders at water
--               height with the water shader); registered in water_tile_type_names
--               so land tiles draw their vanilla dirt bank onto the join; draws
--               post pilings onto adjacent water (synthesized cylinders with
--               translucent feet and painted foam rings; one post per tile edge,
--               jittered)
--
-- flags:
--   posts          : "exp" = use the experiment post sheet (pilings-exp.png)
--   masked         : add the crown water-effect mask (pilings-mask.png): crowns
--                    render out of the water, shader laps around the feet
--   next_direction : R-rotation partner tile (in-hand rotation)
--   shore          : false = keep out of water_tile_type_names (land-style shore edges)

local M = {}

M.water_tile_names = {"water", "deepwater", "water-green", "deepwater-green", "water-shallow", "water-mud"}

local G = "__py-caravan-ford__/graphics/"

M.list = {
  -- ===== gold standard - do not change =====
  {name = "py-ford-flooded",          group = "custom", kind = "flooded",                    title = "Ford: flooded planks",                 tint = {r = 0.60, g = 0.55, b = 0.35}},

  -- ===== experiment slots (up to 3; one free) =====
  {name = "py-ford-exp-1",            group = "custom", kind = "flooded", posts = "exp",     title = "Ford experiment: posts v2",            tint = {r = 0.55, g = 0.58, b = 0.32}},
  {name = "py-ford-exp-2",            group = "custom", kind = "flooded", posts = "exp", masked = true, title = "Ford experiment: shader-lapped posts", tint = {r = 0.50, g = 0.60, b = 0.30}},
}

-- A variant is available if the vanilla tiles it depends on exist.
function M.available(v)
  if v.src and not data.raw.tile[v.src] then return false end
  if v.bed and not data.raw.tile[v.bed] then return false end
  if v.effect_from and not data.raw.tile[v.effect_from] then return false end
  return true
end

function M.enabled(v)
  return settings.startup["py-ford-group-" .. v.group].value and M.available(v)
end

return M
