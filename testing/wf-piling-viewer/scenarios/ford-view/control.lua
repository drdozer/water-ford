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

  -- 2026-10-21 rewrite: the retired shore-rim probe tiles are gone; the
  -- view = the boards ladder's approved B look (wooden-ford under the
  -- tile's veil + wooden-flooring pads so the edge/trim art forms).
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
      tiles[#tiles + 1] = {name = "wooden-ford", position = {x, y}}
    end
  end
  -- wooden-flooring pads flanking north (land/edge/trim boundaries form
  -- where they meet the ford and the water edge)
  for x = -14, -7 do
    for y = 8, 13 do
      tiles[#tiles + 1] = {name = "wooden-flooring", position = {x, y}}
    end
  end
  for x = 6, 13 do
    for y = 8, 13 do
      tiles[#tiles + 1] = {name = "wooden-flooring", position = {x, y}}
    end
  end
  -- a small mid-lake flooring pad, clear of both banks
  for x = -3, 2 do
    for y = 12, 15 do
      tiles[#tiles + 1] = {name = "wooden-flooring", position = {x, y}}
    end
  end
  surface.set_tiles(tiles, true)
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
