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
--   * vanilla tiles — wooden-ford (car must STOP), cobblestone-ford (the
--     1.1.0 road ford: car must CROSS), water-shallow, water-mud, water,
--     deepwater, lava, oil-ocean-shallow, stone-path, concrete, grass-1,
--     landfill (control: MUST cross, else harness-error).
--   * wf-probe-<layer> — synthetic single-layer tiles from data.lua; each
--     answers "does this collision layer stop a car".
--   * unit-* lanes — PATH-REQUEST oracle per bridge tile (cobblestone-ford,
--     wooden-ford, water-shallow, landfill + a deepwater negative control):
--     the real pathfinder is asked, asynchronously, for a path from the east
--     island to the west island with the small-biter's collision box and
--     mask; no entity is walked. Biters commanded from script proved hostile
--     to the harness — all vanished together at tick 241, one tick after a
--     periodic command re-issue, with no died/damaged events; with the
--     re-issue removed they all survived a full run (same symptom class as
--     oreguard's matrix, whose periodic sweep ate its own bots). No units
--     exist for anything to eat.
--
-- Results: script-output/ford-vehicle-crossing-results.json
--   overall = "pass"           runner exit 0
--             "fail"           runner exit 1  (a contract gate violated)
--             "harness-error"  runner exit 2  (control failed / never moved)

local VANILLA_LANES = {
  { key = "wooden-ford",       bridge = "wooden-ford" },
  { key = "cobblestone-ford",  bridge = "cobblestone-ford" },
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
-- unit lanes (1.1.0 cobble contract): real-pathfinder walkers on the same
-- bridge geometry. Unlike the speed-driven cars, units PATH — so on_init
-- paints the moat far beyond the lane rows (±96) and no detour exists within
-- the eval budget.
local UNIT_BRIDGES = { "cobblestone-ford", "wooden-ford", "water-shallow", "landfill", "deepwater" }
local unit_base = #LANES
for i, bridge in ipairs(UNIT_BRIDGES) do
  LANES[#LANES + 1] = { key = "unit-" .. bridge, bridge = bridge,
    cy = 10 + (unit_base + i - 1) * LANE_SPACING, unit = true }
end
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
local EVAL_TICK = 1200             -- cars need ~600 ticks; path requests finish in seconds

local cars, min_x = {}, {}
-- path-request oracle state (request id -> lane key; results per lane)
local path_requests, path_results, path_retries = {}, {}, {}
local unit_bounding_box, unit_collision_mask
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
  if lane.unit then return end -- unit lanes carry path results, not movers
  local mover = cars[lane.key]
  local r = {
    bridge = lane.bridge,
    probe_layer = lane.probe,
    min_x = min_x[lane.key],
    final_x = (mover and mover.valid) and mover.position.x or nil,
    mover_valid = (mover and mover.valid) or false,
    crossed = min_x[lane.key] < CROSS_X,
    reached_shore = min_x[lane.key] < SHORE_X,
  }
  results.lanes[lane.key] = r
  return r
end

-- PATH-REQUEST ORACLE: ask the engine pathfinder for a unit path across
-- each bridge geometry (base wave-defense / aai-vehicles idiom). A path is
-- "reaching" when it lands within 4 tiles of the west-island goal — a mere
-- shore-approaching partial path does not count.
local function request_unit_path(lane)
  local rid = game.surfaces[1].request_path{
    start = { CAR_START_X, lane.cy },
    goal = { WEST_X0 + 2, lane.cy },
    bounding_box = unit_bounding_box,
    collision_mask = unit_collision_mask,
    force = "enemy",
    radius = 2,
  }
  if rid then path_requests[rid] = lane.key end
  log(string.format("PATH-REQUEST %s rid=%s", lane.key, tostring(rid)))
end

script.on_event(defines.events.on_script_path_request_finished, function(e)
  local key = path_requests[e.id]
  if not key then return end
  path_requests[e.id] = nil
  local lane = lane_by_key[key]
  if e.try_again_later then
    -- pathfinder busy (8 simultaneous requests at init): re-request, bounded
    path_retries[key] = (path_retries[key] or 0) + 1
    if path_retries[key] <= 10 and lane then
      request_unit_path(lane)
      return
    end
  end
  local reached, n = false, e.path and #e.path or 0
  if e.distance_to_goal ~= nil then
    reached = e.distance_to_goal < 4
  elseif n > 0 and lane then
    local last = e.path[n]
    log(string.format("PATH-SHAPE first=%s last=%s",
      helpers.table_to_json(e.path[1]), helpers.table_to_json(last)))
    local ok, value = pcall(function()
      local lx = last.x or (last.position and last.position.x) or last[1]
      local ly = last.y or (last.position and last.position.y) or last[2]
      return math.abs(lx - (WEST_X0 + 2)) < 4 and math.abs(ly - lane.cy) < 4
    end)
    reached = ok and value or false
  end
  log(string.format("PATH-RESULT %s len=%d reached=%s try_again=%s",
    key, n, reached, tostring(e.try_again_later)))
  path_results[key] = { reached = reached, path_len = n,
    try_again_later = e.try_again_later or false }
end)

script.on_init(function()
  local surface = game.surfaces[1]
  pcall(function() surface.peaceful_mode = true end)
  game.map_settings.enemy_expansion.enabled = false

  -- clear the lab area, then carve: water moat, islands, bridges, pond row
  -- (the moat/grass apron is painted ±96 rows beyond the lane grid so the
  -- pathfinding unit lanes cannot detour around the painted moat)
  for _, e in pairs(surface.find_entities_filtered{area = {{0, -96}, {140, Y_MAX + 96}}}) do
    if e.type ~= "character" then e.destroy() end -- keep the (windowed-session) player alive
  end
  -- FORCE-GENERATE THE WHOLE LAB BEFORE PAINTING. set_tiles silently drops
  -- tile changes in not-yet-generated chunks (2026-10-21 in-game session:
  -- everything south of the spawn-generation band painted to nothing and
  -- later chunk-generated as wild terrain). The idiom (mferrari-lib):
  -- request_to_generate_chunks takes a CHUNK-COORD position + radius, then
  -- force_generate_chunk_requests generates them synchronously. Chunk (2,8)
  -- radius 14 covers tiles x -384..544, y -192..736 — the whole lab incl.
  -- the ±96 anti-detour buffers.
  do
    local ok, err = pcall(function()
      -- request_to_generate_chunks takes a TILE-COORD position + a
      -- CHUNK-COORD radius (2026-10-21: passing chunk (2,8) as the position
      -- generated only to tile y ≈456, just short of the unit rows at
      -- 474+). Center on the lab (70, 270), radius 14 chunks → tiles y
      -- -178..718 ✓ the whole lab.
      surface.request_to_generate_chunks({ x = 70, y = 270 }, 14)
      surface.force_generate_chunk_requests()
    end)
    log(string.format("CHUNK-GEN ok=%s err=%s south-chunk-generated=%s",
      tostring(ok), tostring(err),
      tostring(surface.is_chunk_generated({ x = 2, y = 17 })))) -- y 544-576: bottom buffer
  end
  local tiles = {}
  for y = -96, Y_MAX + 96 do
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
    { key = "wooden-ford",         x0 = 95 }, -- carries the water-ford layers (data-updates stamp)
    { key = "cobblestone-ford",    x0 = 95 }, -- the road ford: pumps must be rejected here too
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
  game.forces.player.chart(surface, {{0, -96}, {140, Y_MAX + 96}})
  local placements = {}
  pcall(function()
    local p = game.players[1]
    p.insert{ name = "offshore-pump", count = 20 }
    p.insert{ name = "landfill", count = 100 }
    p.insert{ name = "car", count = 1 }
    p.insert{ name = "tank", count = 1 }
    p.insert{ name = "wood", count = 200 }
    p.insert{ name = "wooden-ford", count = 100 }
    p.insert{ name = "cobblestone-ford", count = 100 }
    p.cheat_mode = true
    placements["player kit"] = "pumps + landfill + car + tank + wood + both ford items given to player 1"
  end)
  probe_placements = placements

  -- unit lanes need no entities: read the small-biter's collision shape
  -- and ask the pathfinder across each bridge geometry. Chunk generation
  -- was force-completed above, before the paint (the pathfinder cannot
  -- path through non-generated chunks, and set_tiles only lands on
  -- generated chunks).
  pcall(function()
    local proto = prototypes.entity["small-biter"]
    unit_bounding_box = proto.collision_box
    unit_collision_mask = proto.collision_mask
    log("UNIT-SHAPE small-biter box=" .. helpers.table_to_json(unit_bounding_box)
      .. " mask=" .. helpers.table_to_json(unit_collision_mask))
  end)
  for _, lane in ipairs(LANES) do
    if lane.unit then
      request_unit_path(lane)
    else
      min_x[lane.key] = CAR_START_X
      local car = surface.create_entity{ name = "car", position = { CAR_START_X, lane.cy }, force = "player" }
      car.insert{ name = "wood", count = 50 }
      car.orientation = 0.75 -- west
      cars[lane.key] = car
    end
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
    snap("cobble-crossing", { x = 40, y = 26 }, 2)     -- road ford car mid-bridge
    snap("landfill-crossing", { x = 40, y = 170 }, 1)  -- control car mid-bridge
  end
  if e.tick >= EVAL_TICK then
    finished = true
    script.on_nth_tick(1, nil)

    local results = { eval_tick = e.tick, lanes = {}, overall = "pass",
      placement = probe_placements }
    for _, lane in ipairs(LANES) do record(results, lane) end

    -- GATES. Cars: the wooden ford must stop the car; the cobblestone ford
    -- (the 1.1.0 road ford) must be crossed; landfill is the control.
    -- Units: biters cross the cobblestone ford (balance ruling 2026-10-22:
    -- paving must not become a free, impenetrable biter barrier — units are
    -- unstamped, the feet exclusion is players only); deepwater is the
    -- negative control; wooden/shallow/landfill stay the unit controls.
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

    local cobble = results.lanes["cobblestone-ford"]
    if cobble.crossed then
      cobble.verdict = "PASS - car crossed the cobblestone ford (road ford open)"
    elseif cobble.reached_shore then
      cobble.verdict = "FAIL - car stopped at the cobblestone ford"
      results.overall = "fail"
    else
      cobble.verdict = "HARNESS-ERROR - cobble car never approached the shore"
      if results.overall == "pass" then results.overall = "harness-error" end
    end

    local control = results.lanes["landfill"]
    if not control.crossed then
      control.verdict = "HARNESS-ERROR - control car failed to cross the landfill bridge"
      if results.overall == "pass" then results.overall = "harness-error" end
    else
      control.verdict = "control ok - car crossed the landfill bridge"
    end

    -- UNIT PATH-REQUEST GATES: deep water is the oracle's negative control
    -- (no crossing path); a reaching path on cobblestone/wooden shallows and
    -- landfill (the unit-side controls — cobble crossable as of the
    -- 2026-10-22 balance ruling).
    local must_not_cross = { ["unit-deepwater"] = true }
    for _, lane in ipairs(LANES) do
      if lane.unit then
        local pr = path_results[lane.key]
        if not pr then
          results.lanes[lane.key] = { bridge = lane.bridge,
            verdict = "HARNESS-ERROR - path request never finished (" .. lane.key .. ")" }
          if results.overall == "pass" then results.overall = "harness-error" end
        else
          results.lanes[lane.key] = { bridge = lane.bridge,
            path_found = pr.path_len > 0, reached = pr.reached }
          if pr.reached and must_not_cross[lane.key] then
            results.lanes[lane.key].verdict = "FAIL - pathfinder found a crossing path: " .. lane.key
            results.overall = "fail"
          elseif must_not_cross[lane.key] then
            results.lanes[lane.key].verdict = "PASS - no crossing path (unit-blocked)"
          elseif pr.reached then
            results.lanes[lane.key].verdict = "control ok - pathfinder crossed " .. lane.key
          else
            results.lanes[lane.key].verdict = "HARNESS-ERROR - unit control found no path: " .. lane.key
            if results.overall == "pass" then results.overall = "harness-error" end
          end
        end
      end
    end

    -- everything else: informational
    for _, lane in ipairs(LANES) do
      if not (lane.key == "wooden-ford" or lane.key == "landfill"
          or lane.key == "cobblestone-ford" or lane.unit) then
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
    snap("final-upper", { x = 40, y = 42 }, 0.5)   -- ford/cobble/shallow/mud/water/deep end states in one frame
    snap("final-landfill", { x = 40, y = 170 }, 0.5) -- control car on the far island
    log("FORD-VEHICLE-TEST DONE overall=" .. results.overall)
  end
end)
