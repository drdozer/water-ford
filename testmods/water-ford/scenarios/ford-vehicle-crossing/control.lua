-- Scenario: ford-vehicle-crossing — layer-by-layer vehicle crossing grid.
--
-- Carves a water moat with one east-west lane per probed tile (16-tile
-- spacing): two grass islands linked by a 2-wide bridge of the tile under
-- test (bridge tiles span y = cy-1, cy; car centre y = cy so the car's
-- 1.4-wide box stays inside the bridge). One car per lane, pushed west by
-- scripted orientation + per-tick car.speed — zero intelligence between
-- command and physics, so "stopped at the shore" is attributable to engine
-- vehicle-vs-tile collision alone.
--
-- Lane groups:
--   * vanilla tiles — wooden-ford (THE TEST: car must stop), water-shallow,
--     water-mud, water, deepwater, lava, oil-ocean-shallow, stone-path,
--     concrete, grass-1, landfill (control: MUST cross, else harness-error).
--   * wf-probe-<layer> — synthetic single-layer tiles from data.lua; each
--     answers "does this collision layer stop a car".
--
-- Results: script-output/ford-vehicle-crossing-results.json
--   overall = "pass"           runner exit 0
--             "fail"           runner exit 1  (ford car crossed)
--             "harness-error"  runner exit 2  (control failed / never moved)

local VANILLA_LANES = {
  { key = "wooden-ford",       bridge = "wooden-ford" },
  { key = "water-shallow",     bridge = "water-shallow" },
  { key = "water-mud",         bridge = "water-mud" },
  { key = "water",             bridge = "water" },
  { key = "deepwater",         bridge = "deepwater" },
  { key = "lava",              bridge = "lava" },
  { key = "oil-ocean-shallow", bridge = "oil-ocean-shallow" },
  { key = "stone-path",        bridge = "stone-path" },
  { key = "concrete",          bridge = "concrete" },
  { key = "grass-1",           bridge = "grass-1" },
  { key = "landfill",          bridge = "landfill" },
}
local PROBE_LAYERS = {
  "player", "item", "object", "water_tile", "resource", "floor", "doodad",
  "train", "ground_tile", "lava_tile", "is_object", "is_lower_object", "meltable",
}

local LANE_SPACING = 16
local LANES = {}
for i, lane in ipairs(VANILLA_LANES) do
  LANES[#LANES + 1] = { key = lane.key, bridge = lane.bridge, cy = 10 + (i - 1) * LANE_SPACING }
end
for i, layer in ipairs(PROBE_LAYERS) do
  local name = "wf-probe-" .. layer:gsub("_", "-")
  LANES[#LANES + 1] = { key = name, bridge = name, cy = 10 + (#VANILLA_LANES + i - 1) * LANE_SPACING, probe = layer }
end
-- custom-layer movement probe lane: the testmod stamps wf-test-block into
-- every car's mask, so this lane answers "do custom layers block movement"
LANES[#LANES + 1] = { key = "wf-probe-custom", bridge = "wf-probe-custom",
  cy = 10 + #LANES * LANE_SPACING, probe = "wf-test-block (custom)" }
-- pump-lever ablation lanes (see data.lua: 2x2 mask-layer x name-list)
LANES[#LANES + 1] = { key = "wf-ablate-mask-only", bridge = "wf-ablate-mask-only", cy = 10 + #LANES * LANE_SPACING }
LANES[#LANES + 1] = { key = "wf-ablate-list-only", bridge = "wf-ablate-list-only", cy = 10 + #LANES * LANE_SPACING }
LANES[#LANES + 1] = { key = "wf-ablate-neither",   bridge = "wf-ablate-neither",   cy = 10 + #LANES * LANE_SPACING }
local Y_MAX = 10 + (#LANES - 1) * LANE_SPACING + 8

local lane_by_key = {}
for _, lane in ipairs(LANES) do lane_by_key[lane.key] = lane end

local WEST_X0, WEST_X1 = 4, 15     -- west island tiles (world x span [4,16))
local BRIDGE_X0, BRIDGE_X1 = 16, 64
local EAST_X0, EAST_X1 = 65, 76
local CAR_START_X = 73.5
local CROSS_X = 16                 -- car centre west of this = crossed the bridge
local SHORE_X = 67                 -- car reached the east shore if min_x < this
local DRIVE_SPEED = 0.1            -- tiles/tick, re-asserted every tick
local EVAL_TICK = 1200

local cars, min_x = {}, {}
local probe_placements = {}
local finished = false

-- In-game evidence captures (absolute positions, §12 console-law protocol).
-- pcall: take_screenshot is client-side; headless runs skip it silently.
local function snap(tag, center, zoom)
  pcall(function()
    game.take_screenshot{ position = center, zoom = zoom,
      resolution = {2560, 1600}, show_gui = false,
      path = "ford-crossing-" .. tag .. ".png" }
  end)
end

local function record(results, lane)
  local car = cars[lane.key]
  local r = {
    bridge = lane.bridge,
    probe_layer = lane.probe,
    min_x = min_x[lane.key],
    final_x = (car and car.valid) and car.position.x or nil,
    car_valid = (car and car.valid) or false,
    crossed = min_x[lane.key] < CROSS_X,
    reached_shore = min_x[lane.key] < SHORE_X,
  }
  results.lanes[lane.key] = r
  return r
end

script.on_init(function()
  local surface = game.surfaces[1]
  pcall(function() surface.peaceful_mode = true end)
  game.map_settings.enemy_expansion.enabled = false

  -- clear the lab area, then carve: water moat, islands, bridges, pond row
  for _, e in pairs(surface.find_entities_filtered{area = {{0, 0}, {140, Y_MAX}}}) do
    if e.type ~= "character" then e.destroy() end -- keep the (windowed-session) player alive
  end
  local tiles = {}
  for y = 0, Y_MAX do
    for x = 0, 89 do
      tiles[#tiles + 1] = { name = "water", position = { x, y } }
    end
    for x = 90, 139 do
      tiles[#tiles + 1] = { name = "grass-1", position = { x, y } }
    end
  end
  for _, lane in ipairs(LANES) do
    local cy = lane.cy
    for y = cy - 6, cy + 6 do
      for x = WEST_X0, WEST_X1 do tiles[#tiles+1] = { name = "grass-1", position = { x, y } } end
      for x = EAST_X0, EAST_X1 do tiles[#tiles+1] = { name = "grass-1", position = { x, y } } end
    end
    for x = BRIDGE_X0, BRIDGE_X1 do
      tiles[#tiles+1] = { name = lane.bridge, position = { x, cy - 1 } }
      tiles[#tiles+1] = { name = lane.bridge, position = { x, cy } }
    end
  end
  -- ponds: 12x12 patches of each probed tile in the grass apron (x>=90) —
  -- vanilla shore geometry (land behind, pond in front) for the pump probes
  local ponds = {
    { key = "water",               x0 = 95 }, -- vanilla positive control
    { key = "wooden-ford",         x0 = 95 }, -- carries the wooden-ford layer (data-updates stamp)
    { key = "wf-ablate-mask-only", x0 = 95 },
    { key = "wf-ablate-list-only", x0 = 95 },
    { key = "wf-ablate-neither",   x0 = 95 },
    { key = "water-shallow",       x0 = 95 },
    { key = "deepwater",           x0 = 95 },
  }
  for i, pd in ipairs(ponds) do pd.cy = 10 + (i - 1) * LANE_SPACING end
  for _, pd in ipairs(ponds) do
    for y = pd.cy - 6, pd.cy + 5 do
      for x = pd.x0, pd.x0 + 11 do
        tiles[#tiles + 1] = { name = pd.key, position = { x, y } }
      end
    end
  end
  surface.set_tiles(tiles, true)

  -- pump-lever ablation oracle = the maintainer's hands: can_place_entity
  -- does not model the player pathway (true on grass, false on water), and
  -- game.create_player no longer exists in 2.1, so the pond row is painted
  -- for a windowed hand test. Kit the (windowed) player if one exists.
  game.forces.player.chart(surface, {{0, 0}, {140, Y_MAX}})
  local placements = {}
  pcall(function()
    local p = game.players[1]
    p.insert{ name = "offshore-pump", count = 20 }
    p.insert{ name = "landfill", count = 100 }
    p.insert{ name = "car", count = 1 }
    p.insert{ name = "tank", count = 1 }
    p.insert{ name = "wood", count = 200 }
    p.cheat_mode = true
    placements["player kit"] = "pumps + landfill + car + tank + wood given to player 1"
  end)
  probe_placements = placements

  for _, lane in ipairs(LANES) do
    local car = surface.create_entity{ name = "car", position = { CAR_START_X, lane.cy }, force = "player" }
    car.insert{ name = "wood", count = 50 }
    car.orientation = 0.75 -- west
    cars[lane.key] = car
    min_x[lane.key] = CAR_START_X
  end
  log("FORD-VEHICLE-TEST initialised: " .. #LANES .. " lanes, Y_MAX=" .. Y_MAX)
end)

script.on_nth_tick(1, function(e)
  if finished then return end
  for key, car in pairs(cars) do
    if car.valid then
      car.speed = DRIVE_SPEED
      if car.position.x < min_x[key] then min_x[key] = car.position.x end
    end
  end
  if e.tick == 340 then
    snap("ford-shore-blocked", { x = 55, y = 10 }, 2)  -- ford car parked at the shore
    snap("landfill-crossing", { x = 40, y = 170 }, 1)  -- control car mid-bridge
  end
  if e.tick >= EVAL_TICK then
    finished = true
    script.on_nth_tick(1, nil)

    local results = { eval_tick = e.tick, lanes = {}, overall = "pass",
      placement = probe_placements }
    for _, lane in ipairs(LANES) do record(results, lane) end

    -- THE TEST: wooden ford must stop the car
    local ford = results.lanes["wooden-ford"]
    if ford.crossed then
      ford.verdict = "FAIL - car crossed the wooden ford"
      results.overall = "fail"
    elseif not ford.reached_shore then
      ford.verdict = "HARNESS-ERROR - car never approached the shore"
      results.overall = "harness-error"
    else
      ford.verdict = "PASS - car stopped at the shore"
    end

    -- control: landfill must let the car through
    local control = results.lanes["landfill"]
    if not control.crossed then
      control.verdict = "HARNESS-ERROR - control car failed to cross the landfill bridge"
      if results.overall == "pass" then results.overall = "harness-error" end
    else
      control.verdict = "control ok - car crossed the landfill bridge"
    end

    -- everything else: informational
    for _, lane in ipairs(LANES) do
      if lane.key ~= "wooden-ford" and lane.key ~= "landfill" then
        local r = results.lanes[lane.key]
        r.informational = true
        if r.crossed then
          r.verdict = "car crossed"
        elseif r.car_valid then
          r.verdict = "car stopped at shore (min_x " .. string.format("%.2f", r.min_x) .. ")"
        else
          r.verdict = "car destroyed en route (min_x " .. string.format("%.2f", r.min_x) .. ")"
        end
      end
    end

    helpers.write_file("ford-vehicle-crossing-results.json",
      helpers.table_to_json(results) .. "\n", false, 0)
    snap("final-upper", { x = 40, y = 42 }, 0.5)   -- ford/shallow/mud/water/deep end states in one frame
    snap("final-landfill", { x = 40, y = 170 }, 0.5) -- control car on the far island
    log("FORD-VEHICLE-TEST DONE overall=" .. results.overall)
  end
end)
