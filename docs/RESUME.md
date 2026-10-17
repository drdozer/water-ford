**SUPERSEDED as of 2026-10-16 evening: the shore-rim investigation lives in docs/shore-rim.md (carried forward, corrected); this file remains the pre-formalization handoff snapshot.**

# RESUME — water-ford session handoff (2026-10-16)

State at handoff: config = deep-water clone, deck restored, pilings entry DISABLED mid-probe.
Game window was live on the last capture (fresh id 0x6200032 — always re-resolve the id).

## THE ONE OPEN QUESTION
Which ford-tile property makes the water effect paint the dark shore rim on the
neighboring water cells? It is NOT the pieces, NOT the gray mask (probes below),
NOT is_foundation (flipped false on the shallow clone: rim persisted).

## Measured chain (all in .cache captures /tmp/ford_*.png)
1. shallow-clone ford, transitions nil, opaque-era: rim dip ~13-16 luma at rim, both edges.
2. is_foundation=false: rim unchanged (72.6 vs 86.9). REVERTED to true.
3. transition_merges_with_tile="water": rim unchanged. KEPT (harmless).
4. Clone source water instead of water-shallow, opaque wash:
   deck buried (effect_color of vanilla water = full alpha, covers tile graphics);
   rim measured ABSENT — ARTIFACT: the full-opacity water hid it (see 7).
5. Translucent wash copied from shallow (effect_color a=12.5% + secondary):
   deck restored (warm planks again). One-variable fix, vanilla-fact based.
6. Pilings entry re-instated on the water clone (same layout/effect_map as
   git-HEAD, sheets = pilings-transition{,-mask}.png, strip-built): pieces
   verified on the rim cells (~6.6k pole px per band).
7. PROBE (final, pieces OFF): rim STILL present: touch 91.1/97.1 vs
   row2 110.1/114.4 (G means, water-only pixels, within-capture).
   => shore rim = the water effect's shore pass around the ford tile;
      earlier "no rim on water clone" was occlusion, not absence.

## Vanilla proto facts (base/prototypes/tile/tiles.lua)
- water: effect "water", effect_color {21,147,167} (opaque), layer_group "water",
  layer 3, variants.main water1/2/4 (count 1), empty_transitions true,
  transitions = {water_to_out_of_map_transition}.
- water-shallow: same effect, effect_color a = 255*0.125 (why shallow shows
  tile graphics), walking_sound/driving_sound shallow, walking_speed_modifier
  0.8, layer 6, collision shallow_water(), variants.main count 8, its own
  transition overlay layout (inner/outer/side count 6).
- Lost by cloning water: wading sounds + 0.8 walk speed. Not yet re-added.

## Current config (mod/data-updates.lua)
- clone = data.raw.tile["water"]; name/subgroup/order/minable standard;
  is_foundation = true; transition_merges_with_tile = "water";
  effect_color pair = shallow's translucent values;
  variants.main = planks.png 8x; empty_transitions = true; variants.transition = nil;
  transitions = nil (the piling entry sits between --[[ ]] guards, ready to
  re-enable: restore `tile.transitions = tile.transitions or {}` and close `]]`);
  layer = 9; collision = water_tile/resource/floor; land-side registration intact.
- pf block present: pilings-transition.png + pilings-transition-mask.png.

## Next bisect (one variable each, rim now VISIBLE and measurable)
Candidates: layer 9 (try 3), is_foundation (try false), collision_mask (try
vanilla water()), subgroup (nauvis-tiles), variants content. Each run: rebuild
save, fresh window id, capture, water-only G means at N touch(556-595)/
row2(512-551)/deep(300-340), S touch(880-919)/row2(924-963)/deep(1050-1090),
strip-mid(700-740).

## BUILD + MEASURE RECIPE
- pkill -x factorio; bake.sh --stages save,view --seed 4242; sleep ~22.
- Resolve the Factorio window id FRESH via xwininfo -root -tree (the id changes
  every relaunch; a stale id silently captures the wrong window — happened 3x).
- Bands are stable (spawn {0.5,4.5}, seed 4242, 2560x1600 window).

## LAWS (violated twice before — binding)
1. The shadow = its own sprites/its own layer, NEVER inside the art pixels
   (CATCHER excluded from the sprite render; shadows64 separate, UNREGISTERED).
2. Wetness = the gray data block only.
3. Paper pixels = Blender output only.
4. Factual answers to factual questions.
5. ONE variable per change.