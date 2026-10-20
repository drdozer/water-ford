-- Per-layer probe tiles: grass-1 clones carrying exactly ONE collision layer
-- each. The vehicle-crossing scenario drives a car across a bridge of each;
-- the run's table answers "which collision layer stops a car" empirically
-- instead of by inference from multi-layer vanilla masks.
-- (Existing vanilla layer names only — no collision-mask-util registration.)
local probe_layers = {
  "player", "item", "object", "water_tile", "resource", "floor", "doodad",
  "train", "ground_tile", "lava_tile", "is_object", "is_lower_object", "meltable",
}
for _, layer in ipairs(probe_layers) do
  local t = table.deepcopy(data.raw.tile["grass-1"])
  t.name = "wf-probe-" .. layer:gsub("_", "-")
  t.autoplace = nil
  t.collision_mask = { layers = { [layer] = true } }
  data:extend{ t }  -- single-extend rule: table is final before extend
end

-- Custom-layer MOVEMENT probe (the oreguard pattern, applied to a TILE +
-- car masks): does a brand-new collision layer stop a car when it sits on
-- the tile AND in the car's mask? Entity-vs-tile movement was proven NOT to
-- be plain mask intersection, so this must be measured, not assumed. The
-- wooden-ford vehicle-exclusion design depends on the answer.
local maskutil = require("collision-mask-util")
data:extend{ { type = "collision-layer", name = "wf-test-block" } }
do
  local t = table.deepcopy(data.raw.tile["grass-1"])
  t.name = "wf-probe-custom"
  t.autoplace = nil
  t.collision_mask = { layers = { ["wf-test-block"] = true } }
  data:extend{ t }
end
for _, car in pairs(data.raw["car"]) do
  local mask = maskutil.get_mask(car)  -- copies the shared default when absent
  mask.layers["wf-test-block"] = true
  car.collision_mask = mask
end

-- Pump-lever ablation (2x2 factorial). The wooden ford has BOTH the
-- water_tile mask layer AND membership in the base global
-- water_tile_type_names; vanilla water has both too; the ford's fluid is
-- already nil and pumps place on it regardless (maintainer hand test).
-- These clones isolate which signal the offshore-pump placement check
-- consults: B mask only, C name-list only, D neither. Visual sources
-- differ (sand / red desert / dirt) so the hand-test ponds are
-- distinguishable at a glance.
local function ablate(name, mask_layers, in_name_list, visual)
  local t = table.deepcopy(data.raw.tile[visual])
  t.name = name
  t.autoplace = nil
  t.collision_mask = { layers = mask_layers or {} }
  data:extend{ t }
  if in_name_list and water_tile_type_names then
    table.insert(water_tile_type_names, name)
  end
end
ablate("wf-ablate-mask-only", { water_tile = true }, false, "sand-1")
ablate("wf-ablate-list-only", {}, true, "red-desert-1")
ablate("wf-ablate-neither", {}, false, "dirt-1")
