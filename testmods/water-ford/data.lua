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
