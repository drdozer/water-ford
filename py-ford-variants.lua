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
--   posts          : "exp" = experiment post sheet; "blank" = fully transparent
--                    sheet (mask-only arm renders no post sprites)
--   masked         : add the gray crown dryness mask (pilings-mask.png, the
--                    known-good 304df33 form)
--   next_direction : R-rotation partner tile (in-hand rotation)
--   shore          : false = keep out of water_tile_type_names (land-style shore edges)

local M = {}

M.water_tile_names = {"water", "deepwater", "water-green", "deepwater-green", "water-shallow", "water-mud"}

local G = "__py-caravan-ford__/graphics/"

M.list = {
  -- ===== isolation experiment A/B/C - names fixed, contents are the three arms =====
  {name = "py-ford-flooded",          group = "custom", kind = "flooded", posts = "exp",   masked = true,  title = "Ford A: posts + mask (known good)", tint = {r = 0.60, g = 0.55, b = 0.35}},
  {name = "py-ford-exp-1",            group = "custom", kind = "flooded", posts = "exp",   masked = false, title = "Ford B: posts only (no mask)",      tint = {r = 0.55, g = 0.58, b = 0.32}},
  {name = "py-ford-exp-2",            group = "custom", kind = "flooded", posts = "blank", masked = true,  title = "Ford C: mask only (no posts)",      tint = {r = 0.50, g = 0.60, b = 0.30}},
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
