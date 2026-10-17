-- ford-view scenario: deterministic, seed-pinned map sculpt used to view the
-- ford IN GAME: carves a lake and lays the ford across it (causeway + the
-- south strip, so the player spawns on the ford itself - no land island in
-- the water). The tile's own transitions carry the real piling sprites.
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
  for x = -14, 14 do  -- the ford: causeway + the strip the bank used to be
    for y = -2, 6 do
      tiles[#tiles + 1] = {name = "water-ford", position = {x, y}}
    end
  end
  surface.set_tiles(tiles, true)
  -- comparator block: raw planks on land, near the ford, three water columns
  -- of gap from the ford edge so nothing touches (maintainer request)
  tiles = {}
  for x = 18, 26 do
    for y = -2, 5 do
      tiles[#tiles + 1] = {name = "wf-plank-land", position = {x, y}}
    end
  end
  surface.set_tiles(tiles, true)
  -- art-dependence probe block: darkened sheet through the water effect,
  -- water-exact tint at alpha 0; placed clear of every measurement band
  -- (its own shore rims fall on y -9 and y -5, outside N deep(-11..-10),
  -- N row2(-4..-3), N touch(-3..-2), S touch/row2/deep)
  tiles = {}
  for x = -12, -4 do
    for y = -8, -6 do
      tiles[#tiles + 1] = {name = "wf-plank-dark", position = {x, y}}
    end
  end
  for x = 2, 10 do
    for y = -8, -6 do
      tiles[#tiles + 1] = {name = "wf-plank-d2", position = {x, y}}
    end
  end
  for x = -12, -4 do
    for y = -14, -12 do
      tiles[#tiles + 1] = {name = "wf-plank-d3", position = {x, y}}
    end
  end
  for x = 2, 10 do
    for y = -14, -12 do
      tiles[#tiles + 1] = {name = "wf-plank-d4", position = {x, y}}
    end
  end
  tiles = {}
  for x = -10, -2 do
    for y = 12, 15 do
      tiles[#tiles + 1] = {name = "wf-checker-f", position = {x, y}}
    end
  end
  for x = 2, 10 do
    for y = 12, 15 do
      tiles[#tiles + 1] = {name = "wf-checker-n", position = {x, y}}
    end
  end
  for x = 2, 10 do
    for y = 18, 20 do
      tiles[#tiles + 1] = {name = "wf-plank-plain", position = {x, y}}
    end
  end
  surface.set_tiles(tiles, true)
  -- no showcase decoratives: the ford's own transition pieces are the show
end

script.on_init(function()
  local surface = game.surfaces[1]
  -- test-world lighting locked to noon (maintainer, 2026-10-16): captures
  -- stay day-bright and cross-row comparable; no runtime Lua needed on load
  surface.always_day = true
  surface.daytime = 0
  surface.request_to_generate_chunks({0, 0}, 3)
  surface.force_generate_chunk_requests()
  sculpt(surface)
  -- playerless save: whoever opens it spawns on the south bank via the spawn point
  game.forces.player.set_spawn_position({0.5, 4.5}, surface)
-- Archive shot best-effort (headless servers may refuse without a player view).
pcall(game.take_screenshot, {
  position = {0, -2}, resolution = {1920, 1080}, zoom = 0.6,
  path = "ford-view-archive.png", show_entity_info = false,
})
end)
