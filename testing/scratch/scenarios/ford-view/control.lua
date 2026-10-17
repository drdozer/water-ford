-- ford-view scenario: deterministic, seed-pinned map sculpt used ONLY to view
-- the Blender piling sheet in-game. Carves a lake, lays a ford causeway with
-- the shipped tile art (current pipeline context), scatters 61 viewer pilings
-- (each instance picks a random sheet variation), saves once, exits-friendly.
local R = 24  -- sculpt radius (tiles)

local function sculpt(surface)
  for _, e in pairs(surface.find_entities_filtered{area = {{-R, -R}, {R, R}}}) do
    if e.type ~= "character" then e.destroy() end
  end
  surface.destroy_decoratives{area = {{-R, -R}, {R, R}}}

  local tiles = {}
  for x = -16, 16 do
    for y = -16, 16 do
      tiles[#tiles + 1] = {name = "water", position = {x, y}}
    end
  end
  surface.set_tiles(tiles, true)

  tiles = {}
  for x = -14, 14 do  -- ford causeway (shipped tile = live context)
    for y = -2, 2 do
      tiles[#tiles + 1] = {name = "water-ford", position = {x, y}}
    end
  end
  for x = -14, 14 do  -- south bank for the player to stand on
    for y = 3, 6 do
      tiles[#tiles + 1] = {name = "grass-1", position = {x, y}}
    end
  end
  surface.set_tiles(tiles, true)

  local decs = {}  -- showcase field on open water
  for i = 0, 53 do
    local x = -14 + (i % 27) * 2
    local y = -10 + math.floor(i / 27) * 3
    decs[#decs + 1] = {name = "wf-view-piling", position = {x, y}}
  end
  for x = -13, 13, 4 do  -- tight row against the ford's north edge
    decs[#decs + 1] = {name = "wf-view-piling", position = {x, -4}}
  end
  surface.create_decoratives{check_collision = false, decoratives = decs}
end

script.on_init(function()
  local surface = game.surfaces[1]
  surface.request_to_generate_chunks({0, 0}, 3)
  surface.force_generate_chunk_requests()
  sculpt(surface)
  -- playerless save: whoever opens it spawns on the south bank via the spawn point
  game.forces.player.set_spawn_position({0.5, 4.5}, surface)
end)

script.on_event(defines.events.on_tick, function(e)
  if e.tick == 40 then
    global.saved_at = e.tick
    game.server_save("ford-view-test")
    pcall(game.take_screenshot, {
      position = {0, -2}, resolution = {1920, 1080}, zoom = 0.6,
      path = "ford-view-archive.png", show_entity_info = false,
    })
  end
end)