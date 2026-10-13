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
  -- Final architecture (round 6, docs/shadow-experiments.md): the tile effect
  -- is RESTORED (it is the water over the deck) and the piling transitions are
  -- GONE (they were what invited the effect's dark band onto neighbour water).
  -- Pilings are script-placed entities on adjacent water cells (control.lua).
  {name = "py-ford-flooded",          group = "custom", kind = "flooded", posts = "exp", masked = true,  title = "Ford A: emerging posts (mask)",    tint = {r = 1, g = 1, b = 1}},
  {name = "py-ford-exp-1",            group = "custom", kind = "flooded", posts = "water", masked = false, title = "Ford B: CONTROL (covered, no pilings)", tint = {r = 1, g = 1, b = 1}},
  {name = "py-ford-exp-2",            group = "custom", kind = "flooded", posts = "exp", masked = false, title = "Ford C: submerged posts (no mask)", tint = {r = 1, g = 1, b = 1}},
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
