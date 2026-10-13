-- Shared list of ford variants. Used by data.lua (items/recipes/tech) and
-- data-final-fixes.lua (tiles), so both stages always agree on what exists.
--
-- Design round: the experimental library has been culled to the planks family
-- plus two prototypes for the "flooded planks" concept (landfill clone wearing
-- the water shader). The full 0.2.0 library (stone/concrete/sand/pontoon/
-- shore-blend variants) is preserved in git history and in the parked
-- py-caravan-ford_0.2.0.zip.bak.
--
-- groups (each can be switched off in startup settings):
--   land   : whole vanilla artificial tile cloned (keeps its land/shore transitions)
--   custom : planks / flooded designs
--
-- kinds:
--   clone       src = vanilla tile to clone entirely
--   planks-land landfill clone with a generated strip texture as its main
--   water       water-shallow clone; bed_texture = our own strip;
--               effect_scale multiplies the water alpha;
--               effect_from = copy water colours from another water tile
--   flooded     landfill clone + water-shallow's water shader + planks main;
--               the inherited waterfront rule is re-sprited with pilings.png;
--               ramp = true additionally adds a custom ramp-to-land rule
--               (tile sits above landfill so its own sprites render onto it)
--
-- flags:
--   next_direction : R-rotation partner tile (in-hand rotation)
--   shore          : false = keep out of water_tile_type_names (land-style shore edges)
--   ramp           : flooded only - add the ramp-to-land transition rule

local M = {}

M.water_tile_names = {"water", "deepwater", "water-green", "deepwater-green", "water-shallow", "water-mud"}

local G = "__py-caravan-ford__/graphics/"

M.list = {
  -- ===== baseline (regression reference: the original ford tile) =====
  {name = "py-ford",                  group = "land", kind = "clone", src = "landfill",        title = "Ford: landfill (baseline)",    tint = {r = 0.75, g = 0.55, b = 0.30}},

  -- ===== design: planks (R rotates EW <-> NS in hand) =====
  {name = "py-ford-planks",           group = "custom", kind = "planks-land", texture = G .. "planks.png",    title = "Ford: planks (land-style)",                 tint = {r = 0.85, g = 0.55, b = 0.25}, next_direction = "py-ford-planks-ns"},
  {name = "py-ford-planks-ns",        group = "custom", kind = "planks-land", texture = G .. "planks-ns.png", title = "Ford: planks (land-style, N-S)",            tint = {r = 0.85, g = 0.55, b = 0.25}, next_direction = "py-ford-planks"},
  {name = "py-ford-planks-under",     group = "custom", kind = "water", bed_texture = G .. "planks.png",              title = "Ford: planks under shallow water",          tint = {r = 0.55, g = 0.50, b = 0.45}, next_direction = "py-ford-planks-under-ns"},
  {name = "py-ford-planks-under-ns",  group = "custom", kind = "water", bed_texture = G .. "planks-ns.png",           title = "Ford: planks under shallow water (N-S)",    tint = {r = 0.55, g = 0.50, b = 0.45}, next_direction = "py-ford-planks-under"},

  -- ===== flooded prototypes: landfill clone wearing the water shader =====
  {name = "py-ford-flooded",          group = "custom", kind = "flooded",                    title = "Ford: flooded planks (pilings, inherited land seam)", tint = {r = 0.60, g = 0.55, b = 0.35}},
  {name = "py-ford-flooded-ramp",     group = "custom", kind = "flooded", ramp = true,       title = "Ford: flooded planks (pilings + ramp to land)",       tint = {r = 0.55, g = 0.60, b = 0.30}},
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
