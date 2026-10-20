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

-- FOOTSTEP AUDIO (2026-10-18): maintainer-recorded board steps, six curation
-- rounds (docs/journal.md); assets rebuilt by tools/build-audio.py from
-- assets-src/audio/source/. Volumes start at the clone sources' values
-- (concrete 0.5 / shallow-water 1.0) — tune by ear in-game, never re-master.
require("__core__.lualib.sound-util")  -- defines global sound_variations()/default_tile_sounds_advanced_volume_control() (no module return — base calls them as globals)
local ford_steps = sound_variations("__water-ford__/sound/walking/ford-deck", 10, 1.0)

local tile = table.deepcopy(data.raw.tile["water"])  -- EXPERIMENT 2026-10-16: clone source = deep water (was water-shallow)

-- Name/description come from locale ([tile-name]/[tile-description]) — no
-- localised_* override here (it would dead-string the locale file).
tile.name = "wooden-ford"
tile.subgroup = "artificial-tiles"
tile.order = "c[landfill]-a2[wooden-ford]"
tile.minable = {mining_time = 0.1, result = "wooden-ford"}
tile.autoplace = nil
tile.fluid = nil
tile.default_cover_tile = nil
tile.ambient_sounds = nil
-- walk-on-ford audio: pre-mixed board+splash composites (splash leads the thunk
-- by ~120 ms -- foot breaks water, then loads the deck; maintainer-approved
-- character, six curation rounds). Vanilla shallow-water's volume (1.0).
tile.walking_sound =
{
  variations = ford_steps,
  advanced_volume_control = default_tile_sounds_advanced_volume_control(),
}
tile.is_foundation = true
tile.transition_merges_with_tile = "water"  -- probe 2026-10-16: bank-shadow candidate (maintainer-found)
-- translucent wash (copied from water-shallow): the plain water effect draws
-- at full opacity and buried the planks deck; at 12.5% alpha the deck shows
-- through the animated water (the shallow's own trick)
tile.effect_color = { 51, 51, 51, 63.75 }  -- committed 2026-10-17: W3 tint on the P1 composite boundary
tile.effect_color_secondary = {r = 0.031, g = 0.129, b = 0.031, a = 0.361}  -- SWEEP P2
-- Minimap: shared wood color (2026-10-18) — both boards tiles carry the SAME
-- map color: ochre #cc7722, the amber hue-anchor of the art ramp
-- (tools/gen-textures.py P: dark (70,48,26) -> lite (224,186,122), capedge
-- (184,144,90); #cc7722 sits on that hue line, chosen brighter than the deck's
-- dominant honey (145,115,84) for map legibility — map colors are stylized,
-- not a swatch of the art). Without this the ford inherits the deep-water
-- clone's blue and reads as open water on the map. Measured (CIE76 dE):
-- nearest vanilla terrain dirt-1/sand-1 = 34 (vanilla's own terrain floor is
-- dirt-1~sand-1 = 1.2), red-desert-1 = 38, water/deepwater = 80 — the boards
-- separate from every vanilla terrain better than vanilla terrains separate
-- from each other. A literal-art honey (147,117,74) measured dE 6 vs dirt-1
-- and was rejected (maintainer: must not read as sands/dirts).
tile.map_color = {r = 204, g = 119, b = 34}

tile.variants.main = {{picture = "__water-ford__/graphics/wooden-ford.png", count = 16, size = 1, y = 0, scale = 0.25, line_length = 16}, {picture = "__water-ford__/graphics/wooden-ford-2x2.png", count = 16, size = 2, y = 0, scale = 0.25, probability = 1, line_length = 4}, {picture = "__water-ford__/graphics/wooden-ford-4x4.png", count = 16, size = 4, y = 0, scale = 0.25, probability = 1, line_length = 4}}
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
    -- 2026-10-17 density pass: pieces re-rendered at 128px cells (2x the 64px
    -- era), scale 0.25 -> same 32 world px; canvases TIGHT (art 1024x2176,
    -- mask 512x1088) - every band y below matches the bake, slack unindexed.
    scale = 0.25,
    inner_corner_count = 8, outer_corner_count = 8, side_count = 8,
    u_transition_count = 2, o_transition_count = 4,
    inner_corner_y = 0, outer_corner_y = 512, side_y = 1024,
    u_transition_y = 1536, o_transition_y = 2048,
    inner_corner_tile_height = 1, outer_corner_tile_height = 1,
    side_tile_height = 1, u_transition_tile_height = 1,
    overlay = {x_offset = 0},
  },
  effect_map_layout = {
    spritesheet = pf.mask,
    -- mask keeps its 64px windows at scale 0.5: wetness granularity unchanged
    scale = 0.5,
    inner_corner_count = 8, outer_corner_count = 8, side_count = 8,
    u_transition_count = 2, o_transition_count = 4,
    inner_corner_y = 0, outer_corner_y = 256, side_y = 512,
    u_transition_y = 768, o_transition_y = 1024,
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
-- crossing speed (2026-10-20, maintainer): 0.9 — faster than wading the
-- shallows (water-shallow 0.8) but still slower than dry land (1.0); a wet
-- deck, not a boardwalk
tile.walking_speed_modifier = 0.9
-- `resource`: dropped then reinstated same day (maintainer order 2026-10-21:
-- "just in case it is needed for something else"). Hand test showed pumps
-- place on the ford with AND without it — not the pump lever.
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
  table.insert(water_tile_type_names, "wooden-ford")
end

data:extend{tile}

---------------------------------------------------------------------------------------------------
-- PEBBLE+STONE BALLAST DOODADS (round-23): engine-native bound decoratives
-- (TilePrototype.bound_decoratives, SA space-platform precedent). Art =
-- blender/ford-stones.blend scenes PEBBLES (24 @ 40px cells) and STONES
-- (12 @ 64px cells) rendered by tools/paper-pipeline/bake-stones.py (pixel-
-- proven --twice); sheets packed law-3 10-per-line. Density knobs below are
-- the live-tunable surface (maintainer: ~1/4 of the SA effective density).
-- Round-25: layered variations: layer 1 = the dry (above-waterline) heap art,
-- layer 2 = the below-waterline slice composited with
-- "multiplicative-with-alpha" so the submerged part tints with whatever is
-- under it (wet deck boards inside the deck, water at the edges) - the
-- piling-style waterline, driven by a uniform-height mesh slice.
local function wf_layered_variations(count, cols, w, h, above, below)
  local out = {}
  for i = 1, count do
    local x = ((i - 1) % cols) * w
    local y = math.floor((i - 1) / cols) * h
    out[i] = {
      layers =
      {
        {
          filename = above,
          priority = "extra-high",
          width = w, height = h, scale = 0.5,
          x = x, y = y,
        },
        {
          filename = below,
          priority = "extra-high",
          width = w, height = h, scale = 0.5,
          x = x, y = y,
          blend_mode = "multiplicative-with-alpha",
        },
      },
    }
  end
  return out
end
data:extend
{
  {
    type = "optimized-decorative",
    name = "ford-pebbles",
    order = "b[decorative]-z[wooden-ford]-a[pebbles]",
    collision_box = {{-0.12, -0.12}, {0.12, 0.12}},
    minimal_separation = 0.12,
    target_count = 120,          -- DENSITY KNOB: pebble grit on the deck
    render_layer = "ground-layer-1",  -- grit sits lowest, under the big stones
    pictures = wf_layered_variations(24, 10, 40, 40,
      "__water-ford__/graphics/ford-decorative-pebbles.png",
      "__water-ford__/graphics/ford-decorative-pebbles-below.png"),
  },
  {
    type = "optimized-decorative",
    name = "ford-stones",
    order = "b[decorative]-z[wooden-ford]-b[stones]",
    collision_box = {{-0.3, -0.3}, {0.3, 0.3}},
    minimal_separation = 0.5,
    target_count = 20,           -- DENSITY KNOB: bigger stones
    render_layer = "ground-layer-3",
    pictures = wf_layered_variations(12, 10, 64, 64,
      "__water-ford__/graphics/ford-decorative-stones.png",
      "__water-ford__/graphics/ford-decorative-stones-below.png"),
  },
}
tile.bound_decoratives = {"ford-pebbles", "ford-stones"} -- DENSITY KNOB: which families bind to the ford deck
---------------------------------------------------------------------------------------------------
-- WOODEN BOARDS LAND (2026-10-17): single promoted land tileset. Was the
-- wooden-flooring-a/b/c dev compare; the C depth won and the family collapsed
-- to one tile per the maintainer order. The ford side lives in the real
-- wooden-ford tile above, now unfrozen onto the boards-ford ladder. Restore
-- point: testing/testing-mods/2026-10-17-boards-16-16-16/.

local land_tile = table.deepcopy(data.raw.tile["concrete"])
land_tile.name = "wooden-flooring"
land_tile.order = "b[terrain]-zz[wooden-flooring]"
land_tile.autoplace = nil -- never in generated terrain
land_tile.minable = {mining_time = 0.1, result = "wooden-flooring"}
land_tile.walking_speed_modifier = 1.1 -- D3 band 1.0-1.1 (concrete 1.4 too fast)
-- Layer: concrete's deepcopy = 13. Maintainer round-24: boards must sit BELOW
-- stone brick (the stone-brick item places stone-path = layer 11) so stone
-- paths draw over boards at their boundary. 10 = free slot just below.
land_tile.layer = 10
-- Same ochre #cc7722 as the ford tile (see its map_color note above): one
-- color for the whole boards family on the minimap.
land_tile.map_color = {r = 204, g = 119, b = 34}
land_tile.variants =
{
  main =
  {
    {picture = "__water-ford__/graphics/wooden-flooring.png", count = 16, size = 1, y = 0, scale = 0.25, line_length = 16},
    {picture = "__water-ford__/graphics/wooden-flooring-2x2.png", count = 16, size = 2, y = 0, scale = 0.25, probability = 1, line_length = 4},
    {picture = "__water-ford__/graphics/wooden-flooring-4x4.png", count = 16, size = 4, y = 0, scale = 0.25, probability = 1, line_length = 4},
  },
  -- LAND TRIM (2026-10-18, round-21): wooden variant-transition edges - the
  -- land-to-land system vanilla wires as concrete.variants.transition (the
  -- "first block" of edge sprites the maintainer pointed at). Square 64x64
  -- cells, counts 16/8/16/4/4, 4 rotation rows (o: 1); overlay art = the
  -- wood-remapped clone of vanilla's concrete-* sheets (tools/paper-pipeline/
  -- bake-land-trim.py), masks = vanilla value maps passed through verbatim.
  -- empty_transitions dropped: the tile ships variant transition pieces now.
  transition =
  {
    overlay_layout =
    {
      inner_corner = { spritesheet = "__water-ford__/graphics/wooden-flooring-trim-inner-corner.png", count = 16, scale = 0.5 },
      outer_corner = { spritesheet = "__water-ford__/graphics/wooden-flooring-trim-outer-corner.png", count = 8,  scale = 0.5 },
      side         = { spritesheet = "__water-ford__/graphics/wooden-flooring-trim-side.png",         count = 16, scale = 0.5 },
      u_transition = { spritesheet = "__water-ford__/graphics/wooden-flooring-trim-u.png",            count = 4,  scale = 0.5 },
      o_transition = { spritesheet = "__water-ford__/graphics/wooden-flooring-trim-o.png",            count = 4,  scale = 0.5 },
    },
    mask_layout =
    {
      inner_corner = { spritesheet = "__water-ford__/graphics/wooden-flooring-trim-inner-corner-mask.png", count = 16, scale = 0.5 },
      outer_corner = { spritesheet = "__water-ford__/graphics/wooden-flooring-trim-outer-corner-mask.png", count = 8,  scale = 0.5 },
      side         = { spritesheet = "__water-ford__/graphics/wooden-flooring-trim-side-mask.png",         count = 16, scale = 0.5 },
      u_transition = { spritesheet = "__water-ford__/graphics/wooden-flooring-trim-u-mask.png",            count = 4,  scale = 0.5 },
      o_transition = { spritesheet = "__water-ford__/graphics/wooden-flooring-trim-o-mask.png",            count = 4,  scale = 0.5 },
    },
  },
}

-- WOODEN BUMPER EDGE (2026-10-17, round-20): wooden-flooring inherits concrete's
-- water transitions verbatim from the deepcopy - the stone curb at the
-- waterline. Replaced with our own edge sheet: a GEOMETRY-CLONE of vanilla's
-- concrete.png (same canvas, band y-fields, channel x-slabs and gaps; cells
-- 64x128 art; counts 16/8/16/4/4; alpha bit-exact) with overlay+background
-- stone colors remapped onto the boards palette by tools/paper-pipeline/
-- bake-land-edge.py ("side-on boards, looking very much like the stone trim";
-- the background channel is neutral grey in vanilla - no water color-matching
-- to copy, the engine shades it). Mask channel = vanilla grey value maps,
-- passed through bit-identical. v2's tightened band spacing broke rows 2/3
-- of every band in-game (N/W/SW/SE edges) -> v3 is a verbatim-geometry clone;
-- tightening returns later only with proven row semantics. Three-way corners
-- (transitions_between_transitions) stay concrete's for now - deferred with
-- the future land-to-ford transition join.
land_tile.transitions =
{
  { -- flags mirror vanilla concrete's water entry; y-fields tightened
    to_tiles = water_tile_type_names,
    transition_group = water_transition_group_id,
    spritesheet = "__water-ford__/graphics/wooden-flooring-edge.png",
    layout =
    {
      scale = 0.5,
      inner_corner_count = 16, outer_corner_count = 8, side_count = 16,
      u_transition_count = 4, o_transition_count = 4,
      inner_corner_y = 0, outer_corner_y = 576, side_y = 1152,
      u_transition_y = 1728, o_transition_y = 2304,
      inner_corner_tile_height = 2, outer_corner_tile_height = 2,
      side_tile_height = 2, u_transition_tile_height = 2,
      overlay    = { x_offset = 0 },
      mask       = { x_offset = 2048 },
      background = { x_offset = 1024 },
    },
    background_enabled = true,
    background_layer_offset = 1,
    offset_background_layer_by_tile_layer = true,
    effect_map_layout =
    {
      spritesheet = "__base__/graphics/terrain/effect-maps/concrete-mask.png",
      inner_corner_count = 1, outer_corner_count = 1, side_count = 1,
      u_transition_count = 1, o_transition_count = 1
    },
  },
  {
    to_tiles = out_of_map_tile_type_names,  -- vanilla concrete's entry verbatim
    transition_group = out_of_map_transition_group_id,
    background_layer_offset = 1,
    background_layer_group = "zero",
    offset_background_layer_by_tile_layer = true,
    spritesheet = "__base__/graphics/terrain/out-of-map-transition/concrete-out-of-map-transition.png",
    -- inline expansion of vanilla tile_spritesheet_layout.concrete_layout(false,true,false)
    -- (base-local there, nil in our stage - check11 lesson)
    layout =
    {
      scale = 0.5,
      inner_corner_count = 16, outer_corner_count = 8, side_count = 16,
      u_transition_count = 4, o_transition_count = 4,
      inner_corner_y = 0, outer_corner_y = 768, side_y = 1280,
      u_transition_y = 1792, o_transition_y = 2304,
      inner_corner_tile_height = 3, outer_corner_tile_height = 2,
      side_tile_height = 2, u_transition_tile_height = 2,
      overlay = { x_offset = 0 },
      mask = { x_offset = 2048 },
      background = { x_offset = 1024 },
    },
  },
}
-- THREE-WAY CORNERS (2026-10-18, round-21): the between-transitions set.
-- The deepcopy carries concrete_transitions_between_transitions (STONE) whose
-- default-group-to-water-group entry fires at grass|water (and ford) corners
-- next to our boards - the maintainer spotted it in-game. Entry 1 becomes our
-- wooden clone (source concrete-transitions.png, counts 3/3/3/1/0, wood-painted
-- overlay+background, grey masks passthrough, verbatim geometry); the out-of-
-- map entries stay vanilla verbatim (map edges, never wooden ground).
land_tile.transitions_between_transitions =
{
  {
    transition_group1 = default_transition_group_id,
    transition_group2 = water_transition_group_id,
    spritesheet = "__water-ford__/graphics/wooden-flooring-between.png",
    layout =
    {
      scale = 0.5,
      inner_corner_count = 3, outer_corner_count = 3, side_count = 3,
      u_transition_count = 1, o_transition_count = 0,
      inner_corner_y = 0, outer_corner_y = 576, side_y = 1152,
      u_transition_y = 1728, o_transition_y = 2304,
      inner_corner_tile_height = 2, outer_corner_tile_height = 2,
      side_tile_height = 2, u_transition_tile_height = 2,
      overlay    = { x_offset = 0 },
      mask       = { x_offset = 2048 },
      background = { x_offset = 1024 },
    },
    background_enabled = true,
    background_layer_offset = 1,
    offset_background_layer_by_tile_layer = true,
    effect_map_layout =
    {
      spritesheet = "__base__/graphics/terrain/effect-maps/concrete-mask.png",
      inner_corner_count = 1, outer_corner_count = 1, side_count = 1,
      u_transition_count = 1, o_transition_count = 1
    },
  },
  {
    transition_group1 = default_transition_group_id,
    transition_group2 = out_of_map_transition_group_id,
    background_layer_offset = 1,
    background_layer_group = "zero",
    offset_background_layer_by_tile_layer = true,
    spritesheet = "__base__/graphics/terrain/out-of-map-transition/concrete-out-of-map-transition-b.png",
    layout =
    {
      scale = 0.5,
      inner_corner_count = 3, outer_corner_count = 3, side_count = 3,
      u_transition_count = 1, o_transition_count = 0,
      inner_corner_y = 0, outer_corner_y = 768, side_y = 1280,
      u_transition_y = 1792, o_transition_y = 2304,
      inner_corner_tile_height = 3, outer_corner_tile_height = 2,
      side_tile_height = 2, u_transition_tile_height = 2,
      overlay    = { x_offset = 0 },
      mask = { x_offset = 2048 },
      background = { x_offset = 1024 },
    },
  },
  {
    transition_group1 = water_transition_group_id,
    transition_group2 = out_of_map_transition_group_id,
    background_layer_offset = 1,
    background_layer_group = "zero",
    offset_background_layer_by_tile_layer = true,
    spritesheet = "__base__/graphics/terrain/out-of-map-transition/concrete-shore-out-of-map-transition.png",
    layout =
    {
      scale = 0.5,
      inner_corner_count = 3, outer_corner_count = 3, side_count = 3,
      u_transition_count = 1, o_transition_count = 0,
      inner_corner_y = 0, outer_corner_y = 768, side_y = 1280,
      u_transition_y = 1792, o_transition_y = 2304,
      inner_corner_tile_height = 3, outer_corner_tile_height = 2,
      side_tile_height = 2, u_transition_tile_height = 2,
      overlay    = { x_offset = 0 },
      mask = { x_offset = 2048 },
      background = { x_offset = 1024 },
    },
  },
}
-- 12 uniform board steps + 1 pure squeak at reduced volume (variations carry
-- their own volume; the helper builds the uniform 12, the squeak is appended)
local land_steps = sound_variations("__water-ford__/sound/walking/flooring", 12, 0.5)
land_steps[13] = { filename = "__water-ford__/sound/walking/flooring-13.ogg", volume = 0.3 }
land_tile.walking_sound =
{
  variations = land_steps,
  advanced_volume_control = default_tile_sounds_advanced_volume_control(),
}
data:extend{land_tile}

local land_item =
{
  type = "item",
  name = "wooden-flooring",
  icon = "__water-ford__/graphics/wooden-flooring-icon.png",
  icon_size = 128,
  subgroup = "terrain",
  order = "b[terrain]-zz[wooden-flooring-item]",
  stack_size = 100,
  -- land pattern (cf. stone-brick/concrete items): condition names water_tile
  -- with no invert = the target must NOT carry the water_tile layer, so this
  -- can never be placed over water. Ford items keep the inverted condition.
  place_as_tile =
  {
    result = "wooden-flooring",
    condition_size = 1,
    condition = {layers = {water_tile = true}},
  },
}
local py_loaded = mods["pyalienlife"] ~= nil
local boards_ingredients = py_loaded
    and {
      {type = "item", name = "treated-wood", amount = 2},
      {type = "item", name = "iron-stick",   amount = 1},
      {type = "item", name = "bolts",        amount = 8},
    }
    or {
      {type = "item", name = "wood",         amount = 2},
      {type = "item", name = "iron-stick",   amount = 1},
    }

local land_recipe =
{
  type = "recipe",
  name = "wooden-flooring",
  localised_name = {"?", {"recipe-name.wooden-flooring"}, {"item-name.wooden-flooring"}}, -- pypp eager-tiling guard, same chain as the ford recipe
  enabled = false, -- both boards unlock with the water-ford technology
  energy_required = 0.5,
  ingredients = boards_ingredients,
  results = {{type = "item", name = "wooden-flooring", amount = 1}},
}
data:extend{land_item, land_recipe}
