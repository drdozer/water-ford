-- The wooden-ford collision layer: the deck blocks what is stamped into.
--
-- One layer, two consumers (both empirically validated 2026-10-21 via
-- testmods/water-ford — the 24-lane layer grid, and the maintainer's hand
-- test on the pond row):
--   * vehicles (type "car": cars, tanks, modded cars) — stopped at the
--     ford's shore. A custom layer present in BOTH tile and entity masks
--     blocks movement; vanilla water_tile does not (cars are stopped only
--     by player/train/is_object tile layers — see the mod journal).
--   * offshore pumps (all data.raw["offshore-pump"], incl. modded) —
--     placement on the ford rejected through the real player placement
--     pathway. (Pumpability itself keys on the water_tile mask layer, not
--     fluid or water_tile_type_names — hence this layer, not a mask edit.)
-- Players, units and Cargo Ships ships carry no such layer: the ford stays
-- walkable and sailable. Spidertron is deliberately unstamped — it already
-- walks on open water. The cobblestone road ford (1.1.0) must NOT carry
-- this layer: vehicles are supposed to cross it
-- (inbox/feature-cobblestone-road-ford.md, task 10).
local maskutil = require("collision-mask-util")

data:extend({
  { type = "collision-layer", name = "wooden-ford" },
})

local function stamp(prototype)
  local mask = maskutil.get_mask(prototype)
  mask.layers["wooden-ford"] = true
  prototype.collision_mask = mask
end

local ford = data.raw.tile["wooden-ford"]
if ford then stamp(ford) end

for _, vehicle in pairs(data.raw["car"]) do stamp(vehicle) end
for _, pump in pairs(data.raw["offshore-pump"]) do stamp(pump) end
