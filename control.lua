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
-- Round 9: pilings as script-rendered sprites. ONE per water cell adjacent to
-- a ford. Ford A (py-ford-flooded) = centred on the water cell; Ford C
-- (py-ford-exp-2) = snugged toward the ford edge. Ford B = control (none).
-- Render objects vanish on save/load, so on_load redraws from storage.
-- Runs after the placement guard handlers (same file, later registration).
-- ---------------------------------------------------------------------------

local pilings_styles = {
  ["py-ford-flooded"] = "centred",
  ["py-ford-exp-2"] = "snug",
}

local function pilings_table(surface)
  storage.pilings = storage.pilings or {}
  local k = surface.index or 1
  storage.pilings[k] = storage.pilings[k] or {}
  return storage.pilings[k]
end

-- returns the style + offset toward the adjacent ford, or nil
local function piling_wanted(surface, x, y)
  local t = surface.get_tile(x, y)
  if not t or not water_names[t.name] then return nil end
  for dx = -1, 1 do
    for dy = -1, 1 do
      if not (dx == 0 and dy == 0) then
        local n = surface.get_tile(x + dx, y + dy)
        local style = n and pilings_styles[n.name]
        if style then
          if style == "centred" then return "centred", {x = 0, y = 0} end
          return "snug", {x = dx * 0.35, y = dy * 0.35}
        end
      end
    end
  end
  return nil
end

local function refresh_cell(surface, x, y)
  local table_ = pilings_table(surface)
  local key = x .. "," .. y
  local old = table_[key]
  if old then
    if old.id then rendering.destroy(old.id) end
    table_[key] = nil
  end
  local style, offset = piling_wanted(surface, x, y)
  if not style then return end
  local target = {x + 0.5 + offset.x, y + 0.5 + offset.y}
  local variant = math.random(0, 7)
  local id = rendering.draw_sprite{
    sprite = "py-ford-piling-" .. variant,
    target = target,
    surface = surface,
  }
  -- store everything the redraw needs: render objects die on save/load
  table_[key] = {id = id, variant = variant, target = target, surface = surface.index}
end

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

local function piling_events(event)
  local surface = game.surfaces[event.surface_index]
  if not surface then return end
  local positions = {}
  for _, t in ipairs(event.tiles or {}) do positions[#positions + 1] = t.position end
  for _, p in ipairs(event.positions or {}) do positions[#positions + 1] = p end
  if #positions > 0 then refresh_around(surface, positions) end
end

for _, ev in ipairs{"on_player_built_tile", "on_robot_built_tile", "on_player_mined_tile", "on_robot_mined_tile"} do
  script.on_event(defines.events[ev], piling_events)
end

script.on_init(function() storage.pilings = storage.pilings or {} end)
script.on_load(function()
  -- render objects do not survive save/load: redraw every stored piling
  storage.pilings = storage.pilings or {}
  for surface_index, by_cell in pairs(storage.pilings) do
    local surface = game.get_surface(surface_index) or game.surfaces.nauvis
    for _, entry in pairs(by_cell) do
      if entry and entry.target then
        entry.id = rendering.draw_sprite{
          sprite = "py-ford-piling-" .. entry.variant,
          target = entry.target,
          surface = surface,
        }
      end
    end
  end
end)
