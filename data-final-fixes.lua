-- Builds the ford tiles. Runs after Py Alien Life (data-updates.lua stamps its caravan layers on
-- every water tile) and after Cargo Ships (data-final-fixes.lua), thanks to the hard dependencies.
--
-- Core idea: every ford keeps `water_tile` (so Cargo Ships waterways/buoys, which require it, still
-- work on it) but has NO Py caravan layers (so caravans, whose mask is only
-- `caravan_collision_mask`, can path over it). Only the visuals differ between variants.

local V = require("py-ford-variants")
local cmu = require("__core__/lualib/collision-mask-util")

local G = "__py-caravan-ford__/graphics/"

local shallow = assert(data.raw.tile["water-shallow"], "py-caravan-ford: water-shallow missing")

-- NOTE: collision_mask_util.get_mask() returns the LIVE table, not a copy. 0.1.x edited it in
-- place, which also removed Py's layers from vanilla water-shallow. Always copy first.
local base_mask = table.deepcopy(cmu.get_mask(shallow))
assert(base_mask.layers.water_tile, "py-caravan-ford: water-shallow has no water_tile layer")
base_mask.layers.caravan_collision_mask = nil
base_mask.layers.dingrido_collision_mask = nil   -- remove this line if dingrido creatures should NOT cross

local function finish(tile, v)
  tile.name = v.name
  tile.localised_name = {"", v.title}
  tile.localised_description = nil
  tile.minable = {mining_time = 0.1, result = v.name}
  tile.autoplace = nil
  tile.fluid = nil
  tile.default_cover_tile = nil
  tile.ambient_sounds = nil
  tile.is_foundation = true
  tile.subgroup = "artificial-tiles"
  tile.order = "z[py-ford]-" .. v.name
  tile.collision_mask = table.deepcopy(base_mask)
  if v.next_direction then tile.next_direction = v.next_direction end
  return tile
end

local function scale_alpha(color, factor)
  color = table.deepcopy(color)
  if color.r ~= nil or color.g ~= nil or color.b ~= nil then
    color.a = math.min((color.a or 1) * factor, 1)
  else
    color[4] = math.min((color[4] or 255) * factor, 255)
  end
  return color
end

-- The engine rule: a tile needs a size-1 entry in variants.main OR a variants.material_background,
-- else it is rejected with "missing 1x1 version or material background". Factorio 2.0's concrete
-- family (concrete, refined-concrete, landfill) has NO variants.main; its ground texture lives in
-- variants.material_background. Water-style beds are drawn from `main`, so when a bed only has a
-- material_background we synthesize a size-1 main from it and copy the background through as well.
local function bed_main_and_background(bed, v)
  local bv = bed.variants or {}
  local main, background
  if bv.main then
    main = table.deepcopy(bv.main)
  elseif bv.material_background then
    local mb = bv.material_background
    main = {{picture = mb.picture, count = mb.count or 1, size = 1, scale = mb.scale or 0.5}}
  end
  if bv.material_background then
    background = table.deepcopy(bv.material_background)
  end
  if not main then
    error(string.format(
      "py-caravan-ford: bed tile '%s' (used by variant '%s') has neither variants.main nor variants.material_background",
      bed.name, v.name))
  end
  return main, background
end

local function water_style(v)
  local t = table.deepcopy(shallow)
  t.layer = 9  -- above shallow(6)/mud(7), so its edge overlay is drawn onto them
  if v.bed then
    local main, background = bed_main_and_background(data.raw.tile[v.bed], v)
    t.variants.main = main
    if background then t.variants.material_background = background end
  elseif v.bed_texture then
    t.variants.main = {{picture = v.bed_texture, count = 8, size = 1, scale = 0.5}}
  end
  if v.effect_from then
    local e = data.raw.tile[v.effect_from]
    t.effect = e.effect or t.effect
    if e.effect_color then t.effect_color = table.deepcopy(e.effect_color) end
    if e.effect_color_secondary then t.effect_color_secondary = table.deepcopy(e.effect_color_secondary) end
  end
  if v.effect_scale and t.effect_color then
    t.effect_color = scale_alpha(t.effect_color, v.effect_scale)
  end
  return t
end

local new_tiles, water_type_names = {}, {}

for _, v in ipairs(V.list) do
  if V.enabled(v) then
    local t
    if v.kind == "clone" then
      t = table.deepcopy(data.raw.tile[v.src])
    elseif v.kind == "planks-land" then
      t = table.deepcopy(data.raw.tile["landfill"])
      -- Vanilla material_background frames are 8x8-tile (512x512 px) sheets; our generated textures
      -- are 1x1-tile (64x64 px) strips. Claiming them as material_background makes the atlas
      -- builder read 512x512 out of a 512x64 file. Render them as a `main` set instead (as water
      -- tiles do) and drop landfill's dirt material_background.
      t.variants.main = {{picture = v.texture, count = 8, size = 1, scale = 0.5}}
      t.variants.material_background = nil
    elseif v.kind == "flooded" then
      -- water-shallow clone: lives in the water layer group, so it renders at water
      -- height with the water shader (like planks-under), not at landfill height.
      -- WATER side (both variants): a rule draws post pilings onto adjacent water -
      -- synthesized cylinders (solid crown, translucent foot, painted foam rings,
      -- one post per tile edge, jittered per slot). to_tiles is a FROZEN vanilla-water
      -- list so the rule never targets fords themselves. NO effect map: the water-dirt
      -- mask's splash anchors one tile south on north/south edges (unresolved), so the
      -- lapping is painted into the sprite instead.
      t = table.deepcopy(data.raw.tile["water-shallow"])
      t.variants.main = {{picture = G .. "planks.png", count = 8, size = 1, scale = 0.5}}
      t.layer = 9  -- match planks-under: above shallow(6)/mud(7) so edge overlays draw onto them

      local piling_rule = {
        to_tiles = {"water", "deepwater", "water-green", "deepwater-green", "water-shallow", "water-mud", "water-wube"},
        transition_group = (water_transition_group_id or 1),
        spritesheet = G .. "pilings.png",
        background_enabled = false,
        layout = {
          scale = 0.5,
          inner_corner_count = 8, outer_corner_count = 8, side_count = 8,
          u_transition_count = 2, o_transition_count = 4,
          inner_corner_y = 0, outer_corner_y = 576, side_y = 1152,
          u_transition_y = 1728, o_transition_y = 2304,
          inner_corner_tile_height = 2, outer_corner_tile_height = 2,
          side_tile_height = 2, u_transition_tile_height = 2,
          overlay = {x_offset = 0}, mask = {x_offset = 2176}, background = {x_offset = 1088},
        },
      }
      t.transitions = t.transitions or {}
      t.transitions[#t.transitions + 1] = piling_rule

      if v.wood_join then
        -- LAND side, wood-join variant: land tiles draw a solid wood edge band onto
        -- this tile. transition_group stays OUT of the water group (0/default): the
        -- engine merges same-group rules at render time, which made the land tiles'
        -- own shore sheets (bank/stone) bleed onto the planks. No effect map - hard
        -- cut, no blending, no bank. The variant stays OUT of water_tile_type_names.
        local land_rule = {
          to_tiles = {v.name},
          transition_group = (default_transition_group_id or 0),
          spritesheet = G .. "ramp.png",
          background_enabled = false,
          layout = {
            scale = 0.5,
            inner_corner_count = 8, outer_corner_count = 8, side_count = 8,
            u_transition_count = 2, o_transition_count = 4,
            inner_corner_y = 0, outer_corner_y = 576, side_y = 1152,
            u_transition_y = 1728, o_transition_y = 2304,
            inner_corner_tile_height = 2, outer_corner_tile_height = 2,
            side_tile_height = 2, u_transition_tile_height = 2,
            overlay = {x_offset = 0}, mask = {x_offset = 2176}, background = {x_offset = 1088},
          },
        }
        for _, land_name in ipairs({"landfill", "stone-path", "concrete", "refined-concrete"}) do
          local land = data.raw.tile[land_name]
          if land then
            land.transitions = land.transitions or {}
            table.insert(land.transitions, table.deepcopy(land_rule))
          end
        end
      else
        -- LAND side, bank-join variant: register in water_tile_type_names so the land
        -- tiles draw their vanilla dirt bank onto it (the planks-under look).
        water_type_names[#water_type_names + 1] = v.name
      end
    elseif v.kind == "water" then
      t = water_style(v)
      -- shore = false opts a variant out of water_tile_type_names, so LAND tiles draw their
      -- normal land-style edge transitions onto it instead of their waterfront cliff overlay.
      if v.shore ~= false then
        water_type_names[#water_type_names + 1] = v.name
      end
    end
    t = finish(t, v)
    -- Sandbox safety net: apply the engine's own rule here so a bad variant fails with a message
    -- naming the variant, instead of the engine aborting the whole load on a generic error.
    local has_1x1 = t.variants and t.variants.material_background ~= nil
    for _, entry in ipairs(t.variants and t.variants.main or {}) do
      if (entry.size or 1) == 1 then has_1x1 = true end
    end
    if not has_1x1 then
      error(string.format(
        "py-caravan-ford: variant '%s' (kind '%s') produced a tile with no size-1 main and no material_background",
        v.name, v.kind))
    end
    new_tiles[#new_tiles + 1] = t
  end
end

if #new_tiles > 0 then
  data:extend(new_tiles)
  -- Land tiles' shoreline transitions use `to_tiles = water_tile_type_names` (a shared global list in
  -- base). Registering water-style fords there lets land edges draw towards them. Done after cloning
  -- so land-style fords don't pick the names up.
  if water_tile_type_names then
    for _, name in ipairs(water_type_names) do table.insert(water_tile_type_names, name) end
  end
  log("py-caravan-ford: created " .. #new_tiles .. " ford tiles")
end
