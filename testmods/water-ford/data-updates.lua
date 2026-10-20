-- Harness validation of the one-layer-two-consumers design:
--   * a "wooden-ford" collision layer (oreguard pattern: collision-layer
--     prototype + mask stamp) goes onto the wooden-ford TILE,
--   * ...into every car's mask (blocks vehicles from driving across —
--     already proven by the wf-probe-custom lane), and
--   * ...into every offshore-pump's mask (blocks pump PLACEMENT on the
--     ford — measured here through the real player build path).
-- Cars are NOT stamped with this layer, so the wooden-ford movement lane
-- doubles as the proof that adding the layer to the tile does not
-- accidentally stop vehicles.
-- Live-mod change is nil: this stamping exists only while the testmod
-- loads. The real implementation would live in the mod's data-final-fixes.
local maskutil = require("collision-mask-util")
data:extend{ { type = "collision-layer", name = "wooden-ford" } }

local ford = data.raw.tile["wooden-ford"]
ford.collision_mask.layers["wooden-ford"] = true

for _, pump in pairs(data.raw["offshore-pump"]) do
  local mask = maskutil.get_mask(pump)
  mask.layers["wooden-ford"] = true
  pump.collision_mask = mask
end
