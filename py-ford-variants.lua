-- Shared list of ford variants. Used by data.lua (items/recipes/tech) and
-- data-final-fixes.lua (tiles), so both stages always agree on what exists.
--
-- groups (each can be switched off in startup settings if one group fails to load):
--   land   : whole vanilla artificial tile cloned (keeps its land/shore transitions)
--   water  : water-shallow clone (real water shader) with another tile's texture as the bed
--   custom : uses textures generated into graphics/ (planks, pontoon)
--
-- kinds:
--   clone       src = vanilla tile to clone entirely
--   planks-land landfill clone with the generated planks texture as its material
--   water       water-shallow clone; bed = vanilla tile whose `main` textures are used,
--               or bed_texture = our own strip; effect_scale multiplies the water alpha;
--               effect_from = copy water colours from another water tile
local M = {}

M.water_tile_names = {"water", "deepwater", "water-green", "deepwater-green", "water-shallow", "water-mud"}

local G = "__py-caravan-ford__/graphics/"

M.list = {
  -- ===== land-style =====
  {name = "py-ford",                  group = "land", kind = "clone", src = "landfill",        title = "Ford: landfill (baseline)",    tint = {r = 0.75, g = 0.55, b = 0.30}},
  {name = "py-ford-stone-path",       group = "land", kind = "clone", src = "stone-path",      title = "Ford: stone path",             tint = {r = 0.65, g = 0.65, b = 0.65}},
  {name = "py-ford-concrete",         group = "land", kind = "clone", src = "concrete",        title = "Ford: concrete",               tint = {r = 0.70, g = 0.70, b = 0.75}},
  {name = "py-ford-refined-concrete", group = "land", kind = "clone", src = "refined-concrete", title = "Ford: refined concrete",       tint = {r = 0.45, g = 0.55, b = 0.75}},
  {name = "py-ford-sandbar",          group = "land", kind = "clone", src = "sand-1",          title = "Ford: sandbar",                tint = {r = 0.95, g = 0.85, b = 0.50}},

  -- ===== water-style: texture under the real water shader =====
  {name = "py-ford-stone-under",      group = "water", kind = "water", bed = "stone-path",      title = "Ford: stone path under shallow water", tint = {r = 0.40, g = 0.65, b = 0.75}},
  {name = "py-ford-concrete-under",   group = "water", kind = "water", bed = "concrete",        title = "Ford: concrete under shallow water",   tint = {r = 0.45, g = 0.60, b = 0.85}},
  {name = "py-ford-refined-under",    group = "water", kind = "water", bed = "refined-concrete", title = "Ford: refined concrete under shallow water", tint = {r = 0.35, g = 0.50, b = 0.95}},
  {name = "py-ford-stone-clear",      group = "water", kind = "water", bed = "stone-path", effect_scale = 0.35, title = "Ford: stone path, very clear water", tint = {r = 0.70, g = 0.90, b = 1.00}},
  {name = "py-ford-stone-murky",      group = "water", kind = "water", bed = "stone-path", effect_scale = 2.5,  title = "Ford: stone path, murky water",     tint = {r = 0.35, g = 0.55, b = 0.35}},
  {name = "py-ford-stone-deep",       group = "water", kind = "water", bed = "stone-path", effect_from = "deepwater",   title = "Ford: stone path, deep-water colours",  tint = {r = 0.15, g = 0.30, b = 0.60}},
  {name = "py-ford-stone-green",      group = "water", kind = "water", bed = "stone-path", effect_from = "water-green", title = "Ford: stone path, green water",        tint = {r = 0.30, g = 0.70, b = 0.40}},

  -- ===== custom textures (generated planks / pontoon) =====
  {name = "py-ford-planks",           group = "custom", kind = "planks-land", texture = G .. "planks.png",            title = "Ford: planks (land-style)",                 tint = {r = 0.85, g = 0.55, b = 0.25}, next_direction = "py-ford-planks-ns"},
  {name = "py-ford-planks-ns",        group = "custom", kind = "planks-land", texture = G .. "planks-ns.png",         title = "Ford: planks (land-style, N-S)",            tint = {r = 0.85, g = 0.55, b = 0.25}, next_direction = "py-ford-planks"},
  {name = "py-ford-planks-under",     group = "custom", kind = "water", bed_texture = G .. "planks.png",              title = "Ford: planks under shallow water",          tint = {r = 0.55, g = 0.50, b = 0.45}, next_direction = "py-ford-planks-under-ns"},
  {name = "py-ford-planks-under-ns",  group = "custom", kind = "water", bed_texture = G .. "planks-ns.png",           title = "Ford: planks under shallow water (N-S)",    tint = {r = 0.55, g = 0.50, b = 0.45}, next_direction = "py-ford-planks-under"},
  {name = "py-ford-planks-under-blend", group = "custom", kind = "water", bed_texture = G .. "planks.png",            title = "Ford: planks under water, land-style shore (EXPERIMENT)", tint = {r = 0.50, g = 0.65, b = 0.45}, shore = false},
  {name = "py-ford-pontoon-baked",    group = "custom", kind = "water", bed_texture = G .. "pontoon-baked.png",       title = "Ford: pontoon (gaps show baked-in water bed)", tint = {r = 0.30, g = 0.60, b = 0.60}},
  {name = "py-ford-pontoon-alpha",    group = "custom", kind = "water", bed_texture = G .. "pontoon-alpha.png",       title = "Ford: pontoon (transparent gaps, EXPERIMENT)", tint = {r = 0.20, g = 0.45, b = 0.60}},
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
