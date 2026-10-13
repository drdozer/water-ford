-- Control-stage guard for ford tile placement.
--
-- Why this exists: in 2.0 the tile placement rules consult the tile stack, and water stays
-- hidden under landfill. Since ford tiles must keep the water_tile collision layer (Cargo
-- Ships waterways, offshore pumps), the engine sees "water" under landfill and allows fords
-- (and landfill!) over it. No data-stage place_as_tile config can distinguish "landfill with
-- hidden water" from plain water, so we enforce the rule here instead: any ford tile placed
-- over a non-water tile is reverted in the same tick and the items are refunded.

local V = require("py-ford-variants")

local ford_tiles = {}
for _, v in ipairs(V.list) do ford_tiles[v.name] = true end

-- Tiles that carry the water_tile layer but are not water you may build on.
local not_water_names = {["out-of-map"] = true, ["empty-space"] = true}

local function is_waterish(tile_prototype)
  if not_water_names[tile_prototype.name] then return false end
  local layers = tile_prototype.collision_mask and tile_prototype.collision_mask.layers
  return layers ~= nil and layers.water_tile == true
end

local function on_built(event)
  if not ford_tiles[event.tile.name] then return end

  local surface = game.surfaces[event.surface_index]
  if not surface then return end

  local revert, count = {}, 0
  for _, t in ipairs(event.tiles) do
    if t.old_tile and not is_waterish(t.old_tile) then
      count = count + 1
      revert[#revert + 1] = {name = t.old_tile.name, position = t.position}
    end
  end
  if count == 0 then return end

  surface.set_tiles(revert, true)

  if event.player_index then
    local player = game.get_player(event.player_index)
    if player and player.valid then
      if event.item then
        player.insert{
          name = event.item.name,
          count = count,
          quality = event.quality and event.quality.name or "normal",
        }
      end
      player.create_local_flying_text{
        text = "Ford tiles can only be placed on water",
        position = revert[1].position,
      }
    end
  end
end

script.on_event(defines.events.on_player_built_tile, on_built)
script.on_event(defines.events.on_robot_built_tile, on_built)

-- ---------------------------------------------------------------------------
-- Piling entities: one per water cell adjacent to a ford tile. Restores the
-- standing-pilings look WITHOUT water-targeting transition rules (which made
-- the deck's water effect darken the neighbouring water tiles - see
-- docs/shadow-experiments.md). Runs after the placement guard handlers so a
-- reverted illegal placement already reads as water again.
-- ---------------------------------------------------------------------------

local water_names = {
  ["water"] = true, ["deepwater"] = true, ["water-green"] = true, ["deepwater-green"] = true,
  ["water-shallow"] = true, ["water-mud"] = true, ["water-wube"] = true,
}

-- storage.pilings: [surfacename?] -> { [ "x,y" ] = LuaEntity }
local function pilings_for(surface)
  storage.pilings = storage.pilings or {}
  local k = surface.index or 1
  storage.pilings[k] = storage.pilings[k] or {}
  return storage.pilings[k]
end

local function cell_wants_piling(surface, x, y)
  local t = surface.get_tile(x, y)
  if not t or not water_names[t.name] then return false end
  for dx = -1, 1 do
    for dy = -1, 1 do
      if not (dx == 0 and dy == 0) then
        local n = surface.get_tile(x + dx, y + dy)
        if n and ford_tiles[n.name] then return true end
      end
    end
  end
  return false
end

local function refresh_cell(surface, x, y)
  local table_ = pilings_for(surface)
  local key = x .. "," .. y
  local old = table_[key]
  if old then
    if old.valid and old.name == "py-ford-piling" then old.destroy() end
    table_[key] = nil
  end
  if cell_wants_piling(surface, x, y) then
    local e = surface.create_entity{
      name = "py-ford-piling",
      position = {x + 0.5, y + 0.5},
      force = "neutral",
    }
    if e then table_[key] = e end
  end
end

-- a tile change at (x, y) can create/kill pilings on that cell and its 8 neighbours
local function refresh_around(surface, positions)
  for _, pos in ipairs(positions) do
    local x, y = math.floor(pos.x), math.floor(pos.y)
    refresh_cell(surface, x, y)
    for dx = -1, 1 do
      for dy = -1, 1 do
        if not (dx == 0 and dy == 0) then refresh_cell(surface, x + dx, y + dy) end
      end
    end
  end
end

local function built_tiles(event)
  local surface = game.surfaces[event.surface_index]
  if not surface then return end
  local positions = {}
  for _, t in ipairs(event.tiles or {}) do positions[#positions + 1] = t.position end
  for _, p in ipairs(event.positions or {}) do positions[#positions + 1] = p end
  if #positions > 0 then refresh_around(surface, positions) end
end

script.on_event(defines.events.on_player_built_tile, built_tiles)
script.on_event(defines.events.on_robot_built_tile, built_tiles)
script.on_event(defines.events.on_player_mined_tile, built_tiles)
script.on_event(defines.events.on_robot_mined_tile, built_tiles)

script.on_init(function()
  storage.pilings = storage.pilings or {}
end)
