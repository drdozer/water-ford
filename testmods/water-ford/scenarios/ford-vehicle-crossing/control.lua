-- Scenario: ford-vehicle-crossing — wooden-ford vehicle-exclusion contract.
--
-- Carves a water moat with three east-west lanes, each two islands linked by
-- a 2-wide bridge (bridge tiles span y = cy-1, cy; car centre y = cy so the
-- car's 1.4-wide box stays inside the bridge):
--
--   wooden-ford   (y=20)  THE TEST: a vehicle must be stopped at the shore.
--   water-shallow (y=40)  vanilla reference (informational).
--   landfill      (y=60)  control: the car MUST cross, else the harness itself
--                         is broken (verdict harness-error, runner exit 2).
--   deepwater     (y=70)  vanilla reference (informational): does ANY water
--                         tile stop a car in 2.1?
--
-- Driving mechanism: no unit-group (cars are not units) and no third-party
-- autopilot (its pathfinder would refuse narrow bridges for its own reasons).
-- The harness sets car.orientation west once and pushes car.speed every tick —
-- zero intelligence between command and physics, so "stopped at the shore" is
-- attributable to engine vehicle-vs-tile collision alone.
--
-- Results: script-output/ford-vehicle-crossing-results.json
--   overall = "pass"           runner exit 0
--             "fail"           runner exit 1  (ford car crossed)
--             "harness-error"  runner exit 2  (control car failed / never moved)

local LANES = {
  { key = "wooden-ford",   cy = 20, bridge = "wooden-ford" },
  { key = "water-shallow", cy = 40, bridge = "water-shallow" },
  { key = "landfill",      cy = 60, bridge = "landfill" },
  { key = "deepwater",     cy = 70, bridge = "deepwater" },
}

local WEST_X0, WEST_X1 = 4, 15     -- west island tiles (world x span [4,16))
local BRIDGE_X0, BRIDGE_X1 = 16, 64
local EAST_X0, EAST_X1 = 65, 76
local CAR_START_X = 73.5
local CROSS_X = 16                 -- car centre west of this = crossed the ford
local SHORE_X = 67                 -- car reached the east shore if min_x < this
local DRIVE_SPEED = 0.1            -- tiles/tick, re-asserted every tick
local EVAL_TICK = 1200

local cars, min_x = {}, {}
local finished = false

local function record(results, lane, verdict)
  local car = cars[lane.key]
  local r = {
    bridge = lane.bridge,
    min_x = min_x[lane.key],
    final_x = (car and car.valid) and car.position.x or nil,
    crossed = min_x[lane.key] < CROSS_X,
    reached_shore = min_x[lane.key] < SHORE_X,
    verdict = verdict,
  }
  results.lanes[lane.key] = r
  return r
end

script.on_init(function()
  local surface = game.surfaces[1]
  pcall(function() surface.peaceful_mode = true end)
  game.map_settings.enemy_expansion.enabled = false

  -- clear the lab area, then carve: water moat, islands, bridges
  for _, e in pairs(surface.find_entities_filtered{area = {{0, 0}, {90, 80}}}) do
    e.destroy()
  end
  local tiles = {}
  for y = 0, 79 do
    for x = 0, 89 do
      tiles[#tiles + 1] = { name = "water", position = { x, y } }
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
  surface.set_tiles(tiles, true)

  for _, lane in ipairs(LANES) do
    local car = surface.create_entity{ name = "car", position = { CAR_START_X, lane.cy }, force = "player" }
    car.insert{ name = "wood", count = 50 }
    car.orientation = 0.75 -- west
    cars[lane.key] = car
    min_x[lane.key] = CAR_START_X
  end
  log("FORD-VEHICLE-TEST initialised: " .. #LANES .. " lanes")
end)

script.on_nth_tick(1, function(e)
  if finished then return end
  for key, car in pairs(cars) do
    if car.valid then
      car.speed = DRIVE_SPEED
      if car.position.x < min_x[key] then min_x[key] = car.position.x end
    end
  end
  if e.tick >= EVAL_TICK then
    finished = true
    script.on_nth_tick(1, nil)

    local results = { eval_tick = e.tick, lanes = {}, overall = "pass" }

    local ford = record(results, LANES[1], nil)
    if ford.crossed then
      ford.verdict = "FAIL - car crossed the wooden ford"
      results.overall = "fail"
    elseif not ford.reached_shore then
      ford.verdict = "HARNESS-ERROR - car never approached the shore"
      results.overall = "harness-error"
    else
      ford.verdict = "PASS - car stopped at the shore"
    end

    for _, ref_lane in ipairs({ LANES[2], LANES[4] }) do
      local ref = record(results, ref_lane, nil)
      ref.informational = true
      ref.verdict = ref.crossed
        and ("informational - vanilla " .. ref_lane.key .. " is car-crossable")
        or  ("informational - vanilla " .. ref_lane.key .. " stops the car")
    end

    local control = record(results, LANES[3], nil)
    if not control.crossed then
      control.verdict = "HARNESS-ERROR - control car failed to cross the landfill bridge"
      if results.overall == "pass" then results.overall = "harness-error" end
    else
      control.verdict = "control ok - car crossed the landfill bridge"
    end

    helpers.write_file("ford-vehicle-crossing-results.json",
      helpers.table_to_json(results) .. "\n", false, 0)
    log("FORD-VEHICLE-TEST DONE overall=" .. results.overall)
  end
end)
