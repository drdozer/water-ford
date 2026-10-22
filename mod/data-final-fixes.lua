-- The ford collision layers: a deck blocks exactly what is stamped into it.
--
-- THREE mod-custom layers (oreguard pattern), superseding the 1.0.x single
-- "wooden-ford" layer (2026-10-21 split —
-- inbox/feature-cobblestone-road-ford.md). Empirical mechanics:
-- docs/collision-layers.md — a custom layer blocks movement only when
-- present in BOTH the tile's and the entity's mask (rule 2); the vanilla
-- player/train/is_object tile layers block CARS too (rule 1), so walker
-- exclusion must not use them.
--   * water-ford            — generic ford-ness: carried by BOTH ford tiles,
--                             stamped into every "offshore-pump" prototype.
--                             No pump on any ford, stamped once (rule 4:
--                             pumpability keys on the water_tile mask layer,
--                             so the exclusion has to be a layer, not a
--                             mask edit).
--   * water-ford-vehicle    — wheels exclusion: carried by the wooden ford
--                             ONLY, stamped into every "car" prototype
--                             (cars, tanks, modded cars).
--   * water-ford-pedestrian — feet exclusion: carried by the cobblestone
--                             ford ONLY, stamped into every "character"
--                             prototype: players on foot are stopped at the
--                             shore. Balance ruling 2026-10-22 (maintainer):
--                             UNITS ARE UNSTAMPED — biters and other units
--                             (py caravans/dingridos) walk across like on
--                             any land tile; stamping them would make cobble
--                             paving a free, impenetrable biter barrier
--                             ("would not be balanced").
-- Deliberately unstamped consumers: ships (sail over both fords),
-- spidertron (ignored by maintainer decision 2026-10-21 — it walks open
-- water regardless), trains (no rail ford). water_tile stays in both ford
-- tile masks: it is what keeps Cargo Ships treating the decks as water, what
-- offshore-pump placement keys on, and what keeps paths unplaceable over the
-- decks (paving would silently swap a deck for an empty-mask tile and reopen
-- the walker contract).
-- Naming: mod-prefixed per docs/collision-layers.md ("keep per-mod layer
-- names"; sign-off 2026-10-21). The retired "wooden-ford" layer name was
-- internal-only; collision masks rebuild from data on load, so saves need
-- no migration.
local maskutil = require("collision-mask-util")

data:extend({
  { type = "collision-layer", name = "water-ford" },
  { type = "collision-layer", name = "water-ford-vehicle" },
  { type = "collision-layer", name = "water-ford-pedestrian" },
})

local function stamp(prototype, layer)
  local mask = maskutil.get_mask(prototype)
  mask.layers[layer] = true
  prototype.collision_mask = mask
end

local wooden_ford = data.raw.tile["wooden-ford"]
if wooden_ford then
  stamp(wooden_ford, "water-ford")
  stamp(wooden_ford, "water-ford-vehicle")
end

local cobblestone_ford = data.raw.tile["cobblestone-ford"]
if cobblestone_ford then
  stamp(cobblestone_ford, "water-ford")
  stamp(cobblestone_ford, "water-ford-pedestrian")
end

for _, vehicle in pairs(data.raw["car"]) do stamp(vehicle, "water-ford-vehicle") end
for _, pump in pairs(data.raw["offshore-pump"]) do stamp(pump, "water-ford") end
for _, walker in pairs(data.raw["character"]) do stamp(walker, "water-ford-pedestrian") end
-- units NOT stamped (balance ruling 2026-10-22: the biter-barrier exploit —
-- paving as a free impenetrable wall — is why biters and other units cross;
-- players on foot remain the one feet exclusion)
-- Ticket record: balance ruling Q1a in inbox/feature-cobblestone-road-ford.md;
-- harness oracle flipped the same wrap (cobble = unit crossing control).
