-- Water Ford -- tile definition.
--
-- ONE tile, straight-line construction, no variant machinery. Config is the
-- former "Ford A" gold standard, proven across the rounds documented in
-- docs/shadow-experiments.md:
--   * water-shallow clone so the tile lives in the water layer group and the
--     "water" tile effect renders animated water OVER the planks deck;
--   * no water-targeting transition claims beyond the piling rule, and its
--     pieces are OPAQUE plain-water composites so the engine's shore
--     pre-darkening never shows (that was the "shadow");
--   * the gray effect map lifts the post crowns above the waterline while
--     their feet stay semi-submerged;
--   * no variant edge overlays (their pale halo on bordering water was
--     rejected); land tiles still draw their vanilla bank onto the join.

local pf = {  -- post parameters shared with tools/gen-placeholders.py
  sheet    = "__water-ford__/graphics/pilings-exp.png",
  mask     = "__water-ford__/graphics/pilings-mask.png",
}

local tile = table.deepcopy(data.raw.tile["water-shallow"])

tile.name = "water-ford"
tile.localised_name = {"", "Water Ford"}
tile.localised_description = {"", "A walkable ford over water: land caravans cross it, wooden pilings stand in the shallows, ships still sail over it."}
tile.subgroup = "artificial-tiles"
tile.order = "c[landfill]-a2[water-ford]"
tile.minable = {mining_time = 0.1, result = "water-ford"}
tile.autoplace = nil
tile.fluid = nil
tile.default_cover_tile = nil
tile.ambient_sounds = nil
tile.is_foundation = true

tile.variants.main = {{picture = "__water-ford__/graphics/planks.png", count = 8, size = 1, scale = 0.5}}
-- the inherited water-shallow edge overlays produced a pale halo on bordering
-- water and have no mask channel; the piling rule covers these cells instead
tile.variants.empty_transitions = true
tile.variants.transition = nil

-- above shallow(6)/mud(7) so the piling pieces on the water side render above
-- shallow-water neighbours (the planks-under convention)
tile.layer = 9

-- walkable: the caravan/dingrido collision layers from water-shallow are not
-- wanted (land caravans must cross); water_tile stays so Cargo Ships and
-- offshore pumps treat the ford as water
tile.collision_mask = {
  layers = {
    water_tile = true,
    resource = true,
    floor = true,
  }
}

-- ---------------------------------------------------------------------------
-- Piling transition: pieces render on the water cells adjacent to the ford.
-- The sheets are opaque plain-water composites (posts over a water frame), so
-- the engine's shore pre-darkening beneath them is covered - the shadow that
-- cost twelve rounds is the space those cells would otherwise show.
-- The effect map is the gray dryness mask: crowns 170 (above the waterline),
-- feet ramping to 50% dryness and holding - the semi-submerged look.
-- ---------------------------------------------------------------------------
tile.transitions = tile.transitions or {}
tile.transitions[#tile.transitions + 1] = {
  to_tiles = {"water", "deepwater", "water-green", "deepwater-green", "water-shallow", "water-mud", "water-wube"},
  transition_group = (water_transition_group_id or 1),
  spritesheet = pf.sheet,
  background_enabled = false,
  mask_enabled = false,
  layout = {
    scale = 0.5,
    inner_corner_count = 8, outer_corner_count = 8, side_count = 8,
    u_transition_count = 2, o_transition_count = 4,
    inner_corner_y = 0, outer_corner_y = 576, side_y = 1152,
    u_transition_y = 1728, o_transition_y = 2304,
    inner_corner_tile_height = 1, outer_corner_tile_height = 1,
    side_tile_height = 1, u_transition_tile_height = 1,
    overlay = {x_offset = 0},
  },
  effect_map_layout = {
    spritesheet = pf.mask,
    scale = 0.5,
    inner_corner_count = 8, outer_corner_count = 8, side_count = 8,
    u_transition_count = 2, o_transition_count = 4,
    inner_corner_y = 0, outer_corner_y = 576, side_y = 1152,
    u_transition_y = 1728, o_transition_y = 2304,
    inner_corner_tile_height = 1, outer_corner_tile_height = 1,
    side_tile_height = 1, u_transition_tile_height = 1,
  },
}

-- LAND side: register the name so vanilla land tiles draw their bank onto the
-- join. The land tiles carry no tile effect, so this produces no darkening.
-- The list is a base global; guard it exactly as the sandbox-era code did.
if water_tile_type_names then
  table.insert(water_tile_type_names, "water-ford")
end

data:extend{tile}