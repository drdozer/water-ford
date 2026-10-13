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
  -- shadow bisect round 4. Round 3 verdict: the shadow follows the piling
  -- rule's existence regardless of mask (B had none) and group (C private:
  -- still shadow). TileRenderLayer doc: pieces in the "water" family render
  -- BELOW the water shaders - the pass pre-darkens their territory. New arms:
  -- A = control; B = pure declaration (blank art, no mask); C = pieces raised
  -- ABOVE the shader pass via overlay_layer_group = "ground-natural".
  {name = "py-ford-flooded",          group = "custom", kind = "flooded", posts = "exp",   masked = false, title = "Ford A", tint = {r = 1, g = 1, b = 1}, above_shader = true},
  {name = "py-ford-exp-1",            group = "custom", kind = "flooded", posts = "exp",   masked = false, title = "Ford B", tint = {r = 1, g = 1, b = 1}, above_shader = true},
  {name = "py-ford-exp-2",            group = "custom", kind = "flooded", posts = "exp",   masked = false, title = "Ford C", tint = {r = 1, g = 1, b = 1}, above_shader = true},
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
