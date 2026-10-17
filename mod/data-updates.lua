-- Water Ford -- tile definition.
--
-- STAGE: data-updates, chosen by experiment (docs/dependency-audit.md §6).
-- Earliest stage that works, on both axes:
--   * inheritance — this is a deepcopy of water-shallow taken after the stack
--     has mutated it (space-age adds the lava-dirt rule + mech landing sounds
--     in its own data-updates). water-ford sorts after every mutator
--     alphabetically ('w'), so the clone here captures all of them; a data.lua
--     clone was verified to silently drop them.
--   * robustness — the tile exists before EVERY mod's data-final-fixes, so
--     eager name-fallback passes (pypostprocessing TILE()) find it.
-- Seed-pinned screenshot harness: renders pixel-identical to the former
-- data-final-fixes placement.
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
-- SPRITES RE-INSTATED (2026-10-16, maintainer order): the piling transition
-- entry is back, now on the deep-water clone. Measured on this clone: the
-- shallow-inherited shore darkening is ABSENT (rim dip gone), so the pieces'
-- transparent backgrounds sit on clean water. The cast shadow is still only
-- its own strip/sheet (shadows64-) - FORBIDDEN inside art pixels, and its
-- own engine layer remains unresolved.

local pf = {  -- post parameters shared with tools/bake-transition-sheet.py
  sheet    = "__water-ford__/graphics/pilings-composite.png",
  mask     = "__water-ford__/graphics/pilings-transition-mask.png",
}

local tile = table.deepcopy(data.raw.tile["water"])  -- EXPERIMENT 2026-10-16: clone source = deep water (was water-shallow)

-- Name/description come from locale ([tile-name]/[tile-description]) — no
-- localised_* override here (it would dead-string the locale file).
tile.name = "water-ford"
tile.subgroup = "artificial-tiles"
tile.order = "c[landfill]-a2[water-ford]"
tile.minable = {mining_time = 0.1, result = "water-ford"}
tile.autoplace = nil
tile.fluid = nil
tile.default_cover_tile = nil
tile.ambient_sounds = nil
tile.is_foundation = true
tile.transition_merges_with_tile = "water"  -- probe 2026-10-16: bank-shadow candidate (maintainer-found)
-- translucent wash (copied from water-shallow): the plain water effect draws
-- at full opacity and buried the planks deck; at 12.5% alpha the deck shows
-- through the animated water (the shallow's own trick)
tile.effect_color = { 51, 51, 51, 63.75 }  -- committed 2026-10-17: W3 tint on the P1 composite boundary
tile.effect_color_secondary = {r = 0.031, g = 0.129, b = 0.031, a = 0.361}  -- SWEEP P2

tile.variants.main = {{picture = "__water-ford__/graphics/planks.png", count = 8, size = 1, scale = 0.5}}
-- the inherited water-shallow edge overlays produced a pale halo on bordering
-- water and have no mask channel; the piling rule covers these cells instead
tile.variants.empty_transitions = true
tile.variants.transition = nil

tile.transitions[#tile.transitions + 1] = {
  -- water-wube is the Factorio-logo easter-egg tile (base factorio-logo.lua);
  -- present in both 2.0.x and 2.1.x, so it is a real member of the water layer,
  -- not dead config. Full version analysis: docs/dependency-audit.md.
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

-- The land-side registration below stays:
-- LAND side: register the name so vanilla land tiles draw their bank onto the
-- join. The land tiles carry no tile effect, so this produces no darkening.
-- The list is a base global; guard it exactly as the sandbox-era code did.
if water_tile_type_names then
  table.insert(water_tile_type_names, "water-ford")
end

data:extend{tile}