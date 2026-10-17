-- Control-stage guard for Water Ford tile placement.
--
-- In 2.0 the tile placement rules consult the tile stack, and water stays
-- hidden under landfill. Since the ford tile keeps the water_tile collision
-- layer (Cargo Ships waterways, offshore pumps), the engine sees "water" under
-- landfill and allows fords over it. No data-stage place_as_tile config can
-- distinguish "landfill with hidden water" from plain water, so the rule is
-- enforced here: any ford placed over a non-water tile is reverted in the same
-- tick and the items are refunded.

local ford_names = {
  ["water-ford"] = true,
}

local not_water_names = {["out-of-map"] = true, ["empty-space"] = true}

local function is_waterish(tile_prototype)
  if not_water_names[tile_prototype.name] then return false end
  local layers = tile_prototype.collision_mask and tile_prototype.collision_mask.layers
  return layers ~= nil and layers.water_tile == true
end

local function on_built(event)
  if not ford_names[event.tile.name] then return end

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
        text = {"water-ford-messages.placement-denied"},
        position = revert[1].position,
      }
    end
  end
end

script.on_event(defines.events.on_player_built_tile, on_built)
script.on_event(defines.events.on_robot_built_tile, on_built)
