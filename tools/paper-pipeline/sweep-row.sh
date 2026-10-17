#!/usr/bin/env bash
# One run of the #7 effect_color sweep (mods/water-ford/docs/shore-rim.md).
#   usage: sweep-row.sh R0..R6
# Applies the row's effect_color pair (restore-from-snapshot then patch),
# rebakes save+view (seed 4242), captures the window (maintainer view) and an
# ABSOLUTE-coordinate screenshot via a one-shot console command (zoom=1,
# 32 px/tile, centered {0,2.5}, no HUD), then measures both bases.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROW="${1:?usage: sweep-row.sh R0..R6}"
WD="$HERE/../../testing/scratch"
PROV="$HERE/../../../../.cache/ford-factory/provenance"
mkdir -p "$PROV"
# provenance law: unique, never-overwritten capture names, referenced from
# the investigation file's result rows (maintainer rule 2026-10-16)
STAMP=$(date +%Y%m%d-%H%M%S)
WIN="$PROV/${STAMP}-${ROW}-win.png"
ABS="$PROV/${STAMP}-${ROW}-abs.png"
[[ -e "$WIN" || -e "$ABS" ]] && { echo "capture name collision, abort"; exit 1; }
GAMEABS="ford-abs-${ROW}.png"

cd "$HERE/../../mod"
cp data-updates.lua.parked data-updates.lua
python3 - "$ROW" <<'EOF'
import sys, re
row = sys.argv[1]
p = "data-updates.lua"; s = open(p).read()
EC = "{ 21, 147, 167, 255 * 0.125 }"; EC50 = "{ 21, 147, 167, 127.5 }"
ECO = "{ 21, 147, 167 }"; SEC = "{r = 0.031, g = 0.129, b = 0.031, a = 0.361}"
SECV = "{ 49, 80, 14 }"
LG = { "L1": True }.get(row, False)
ec, sec, tag = {
  "R0": ("{ 31 * 0.25, 114 * 0.25, 133 * 0.25, 255 * 0.125 }", SEC, "parked reference"),
  "R1": (EC, SEC, "water rgb a=12.5% parked-sec"),
  "R2": (EC50, SEC, "water rgb a=50% parked-sec"),
  "R3": (ECO, SEC, "water rgb opaque parked-sec"),
  "R4": (ECO, SECV, "water pair wholesale (opaque)"),
  "R5": (EC, SECV, "water rgb a=12.5% water-sec"),
  "R6": (EC50, SECV, "water rgb a=50% water-sec"),
  "E1": ("{ 21, 147, 167, 6.4 }", SECV, "water rgb a=2.5% water-sec"),
  "E2": ("{ 21, 147, 167, 12.75 }", SECV, "water rgb a=5% water-sec"),
  "E3": ("{ 21, 147, 167, 25.5 }", SECV, "water rgb a=10% water-sec"),
  "E4": ("{ 21, 147, 167, 51 }", SECV, "water rgb a=20% water-sec"),
  "E5": ("{ 21, 147, 167, 102 }", SECV, "water rgb a=40% water-sec"),
  "E6": ("{ 21, 147, 167, 153 }", SECV, "water rgb a=60% water-sec"),
  "E7": ("{ 21, 147, 167, 204 }", SECV, "water rgb a=80% water-sec"),
  "G1": ("{ 21, 147, 167, 5.1 }", SECV, "water rgb a=2% water-sec"),
  "G2": ("{ 21, 147, 167, 3.8 }", SECV, "water rgb a=1.5% water-sec"),
  "G3": ("{ 21, 147, 167, 2.55 }", SECV, "water rgb a=1% water-sec"),
  "G4": ("{ 21, 147, 167, 1.275 }", SECV, "water rgb a=0.5% water-sec"),
  "G5": ("{ 21, 147, 167, 0.51 }", SECV, "water rgb a=0.2% water-sec"),
  "G6": ("{ 21, 147, 167, 0.255 }", SECV, "water rgb a=0.1% water-sec"),
  "F0":  ("{ 21, 147, 167, 51 }", "{ 49, 80, 14, 0 }",   "a=20% sec a=0%"),
  "F20": ("{ 21, 147, 167, 51 }", "{ 49, 80, 14, 51 }",  "a=20% sec a=20%"),
  "F40": ("{ 21, 147, 167, 51 }", "{ 49, 80, 14, 102 }", "a=20% sec a=40%"),
  "F60": ("{ 21, 147, 167, 51 }", "{ 49, 80, 14, 153 }", "a=20% sec a=60%"),
  "F80": ("{ 21, 147, 167, 51 }", "{ 49, 80, 14, 204 }", "a=20% sec a=80%"),
  "A00":   ("{ 21, 147, 167, 0 }",    "{ 49, 80, 14, 0 }",    "p0% s0%"),
  "A100":  ("{ 21, 147, 167, 25.5 }", "{ 49, 80, 14, 0 }",    "p10% s0%"),
  "A010":  ("{ 21, 147, 167, 0 }",    "{ 49, 80, 14, 25.5 }", "p0% s10%"),
  "A55":   ("{ 21, 147, 167, 12.75 }","{ 49, 80, 14, 12.75 }","p5% s5%"),
  "A1010": ("{ 21, 147, 167, 25.5 }","{ 49, 80, 14, 25.5 }", "p10% s10%"),
  "C90": ("{ 18.9, 132.3, 150.3, 31.875 }", "{ 49, 80, 14 }", "water x0.9 a12.5%"),
  "C80": ("{ 16.8, 117.6, 133.6, 31.875 }", "{ 49, 80, 14 }", "water x0.8 a12.5%"),
  "C50": ("{ 10.5, 73.5, 83.5, 31.875 }",   "{ 49, 80, 14 }", "water x0.5 a12.5%"),
  "C20": ("{ 4.2, 29.4, 33.4, 31.875 }",    "{ 49, 80, 14 }", "water x0.2 a12.5%"),
  "L1": ("PARKED", "PARKED", "parked tint + layer_group=nil"),
  "L2": ("{ 4.2, 29.4, 33.4, 31.875 }", "{ 49, 80, 14 }", "water x0.2 a12.5% + layer_group=nil"),
  "L3": ("{ 21, 147, 167, 31.875 }",    "{ 49, 80, 14 }", "water exact a12.5% + layer_group=nil"),
  "T1": ("{ 0, 0, 0, 255 * 0.125 }", SEC, "black tint a12.5% -- boards-visible ladder"),
  "T2": ("{ 0, 0, 0, 12.75 }",     SEC, "black tint a5%"),
  "T3": ("{ 0, 0, 0, 63.75 }",     SEC, "black tint a25%"),
  "TB": ("{ 0, 0, 0, 12.75 }",     SEC, "T2 base (black a5%) + vanilla shallow overlay edges"),
  "U1": ("{ 25.5, 25.5, 25.5, 12.75 }",  SEC, "grey 10% @ a5% -- under-water ladder"),
  "U2": ("{ 51, 51, 51, 12.75 }",       SEC, "grey 20% @ a5%"),
  "U3": ("{ 89.25, 89.25, 89.25, 12.75 }", SEC, "grey 35% @ a5%"),
  "TC": ("{ 0, 0, 0, 12.75 }",     SEC, "T2 base (black a5%) + pilings transition re-enabled"),
  "UF0": ("{ 0, 0, 0, 12.75 }",    SEC, "T2 base + flat-water cover on outward entry (mechanics proof)"),
  "V1": ("{ 0, 0, 0, 31.875 }",    SEC, "black a12.5% + cover"),
  "V2": ("{ 0, 0, 0, 63.75 }",     SEC, "black a25% + cover"),
  "V3": ("{ 0, 0, 0, 102 }",       SEC, "black a40% + cover"),
  "W1": ("{ 25.5, 25.5, 25.5, 63.75 }", SEC, "grey 10% a25% + cover"),
  "W2": ("{ 38.25, 38.25, 38.25, 63.75 }", SEC, "grey 15% a25% + cover"),
  "W3": ("{ 51, 51, 51, 63.75 }",  SEC, "grey 20% a25% + cover"),
  "X1": ("{ 51, 51, 51, 63.75 }",  SEC, "W3 + piling entry stacked (option 1)"),
  "X2": ("{ 51, 51, 51, 63.75 }",  SEC, "X1 + apply_effect_color_to_overlay on piling entry"),
  "P1": ("{ 51, 51, 51, 63.75 }",  SEC, "W3 + composite sheet (flat-water bg under piling frames)"),
  "P2": ("{ 51, 51, 51, 63.75 }",  SEC, "P1 + apply_effect_color_to_overlay on the composite entry"),
}[row]
s = s.replace("{ 31 * 0.25, 114 * 0.25, 133 * 0.25, 255 * 0.125 }",
              f"{ec}  -- SWEEP {row}: {tag}")
s = s.replace(SEC, f"{sec}  -- SWEEP {row}")
if LG:
    s = s.replace("data:extend{tile}",
        "tile.layer_group = nil  -- L-ROW: layer_group dropped\ndata:extend{tile}")
if row == "TB":
    s = s.replace(
"""tile.variants.empty_transitions = true
tile.variants.transition = nil""",
"""-- TB ROW: vanilla water-shallow overlay edges (the shallow approach)
tile.variants.transition =
{
  overlay_layout =
  {
    inner_corner = { spritesheet = "__base__/graphics/terrain/water-shallow/water-shallow-inner-corner.png", count = 6, scale = 0.5 },
    outer_corner = { spritesheet = "__base__/graphics/terrain/water-shallow/water-shallow-outer-corner.png", count = 6, scale = 0.5 },
    side         = { spritesheet = "__base__/graphics/terrain/water-shallow/water-shallow-side.png",         count = 6, scale = 0.5 },
    u_transition = { spritesheet = "__base__/graphics/terrain/water-shallow/water-shallow-u.png",            count = 1, scale = 0.5 },
    o_transition = { spritesheet = "__base__/graphics/terrain/water-shallow/water-shallow-o.png",            count = 1, scale = 0.5 }
  }
}""")
    assert "overlay_layout" in s, "TB patch failed"
if row in ("UF0", "V1", "V2", "V3", "W1", "W2", "W3"):
    s = s.replace("tile.transitions = nil  -- PROBE 2026-10-16: pilings transition disabled (darkening discriminator)\n", "")
    i = s.index("--[[\ntile.transitions[#tile.transitions + 1] = {")
    j = s.index("]]", i)
    s = s[:i] + s[i+4:j] + s[j+2:]
    s = s.replace('sheet    = "__water-ford__/graphics/pilings-transition.png",',
                  'sheet    = "__wf-piling-viewer__/graphics/wf-cover-flat.png",')
    s = re.sub(r"\n  effect_map_layout = \{.*?\n  \},", "", s, count=1, flags=re.S)
    assert "wf-cover-flat" in s and "effect_map_layout" not in s, "UF0 patch failed"
if row in ("X1", "X2"):
    s = s.replace("tile.transitions = nil  -- PROBE 2026-10-16: pilings transition disabled (darkening discriminator)\n", "")
    i = s.index("--[[\ntile.transitions[#tile.transitions + 1] = {")
    j = s.index("]]", i)
    piling_entry = s[i+4:j]
    s = s[:i] + s[i+4:j] + s[j+2:]
    s = s.replace('sheet    = "__water-ford__/graphics/pilings-transition.png",',
                  'sheet    = "__wf-piling-viewer__/graphics/wf-cover-flat.png",')
    s = re.sub(r"\n  effect_map_layout = \{.*?\n  \},", "", s, count=1, flags=re.S)
    pe = piling_entry.replace("spritesheet = pf.sheet,",
        'spritesheet = "__water-ford__/graphics/pilings-transition.png",')
    pe = pe.replace("spritesheet = pf.mask,",
        'spritesheet = "__water-ford__/graphics/pilings-transition-mask.png",')
    if row == "X2":
        pe = pe.replace("transition_group = (water_transition_group_id or 1),",
            "transition_group = (water_transition_group_id or 1),\n  apply_effect_color_to_overlay = true,")
    # insert at a stable anchor: the pe text is a complete statement; splice it
    # right before data:extend (the old j+2 index went stale after the strip
    # and once corrupted collision_mask - 2026-10-17 lesson: never reuse
    # indices into a rebuilt string; anchor on text, always)
    assert "data:extend{tile}" in s
    s = s.replace("data:extend{tile}", pe + "data:extend{tile}", 1)
    assert s.count("tile.transitions[#tile.transitions + 1] = {") == 2, "X stack failed"
    assert "pilings-transition-mask.png" in pe, "mask wiring failed"
    assert ("apply_effect_color_to_overlay" in pe) == (row == "X2"), "flag wiring failed"
if row in ("P1", "P2"):
    s = s.replace("tile.transitions = nil  -- PROBE 2026-10-16: pilings transition disabled (darkening discriminator)\n", "")
    i = s.index("--[[\ntile.transitions[#tile.transitions + 1] = {")
    j = s.index("]]", i)
    s = s[:i] + s[i+4:j] + s[j+2:]
    s = s.replace('sheet    = "__water-ford__/graphics/pilings-transition.png",',
                  'sheet    = "__water-ford__/graphics/pilings-composite.png",')
    if row == "P2":
        s = s.replace("transition_group = (water_transition_group_id or 1),",
            "transition_group = (water_transition_group_id or 1),\n  apply_effect_color_to_overlay = true,", 1)
    assert "pilings-composite.png" in s
    assert s.count("tile.transitions[#tile.transitions + 1] = {") == 1
    assert ("apply_effect_color_to_overlay" in s) == (row == "P2")
if row == "TC":
    s = s.replace("tile.transitions = nil  -- PROBE 2026-10-16: pilings transition disabled (darkening discriminator)\n", "")
    i = s.index("--[[\ntile.transitions[#tile.transitions + 1] = {")
    j = s.index("]]", i)
    s = s[:i] + s[i+4:j] + s[j+2:]
    assert 'to_tiles = {"water", "deepwater"' in s, "TC patch failed"
assert "-- SWEEP" in s
open(p, "w").write(s); print(f"row {row}: ec={tag}")
EOF

"$HERE/bisect-run.sh" "$WIN" 2>&1 | tail -2 || { echo "$ROW: bake/capture failed" >&2; exit 1; }

WID=$(xwininfo -root -tree 2>/dev/null | grep ' "Factorio' | head -1 | awk '{print $1}')
DISPLAY=:0 xdotool windowactivate --sync "$WID"; sleep 1
DISPLAY=:0 xdotool key --window "$WID" grave; sleep 1
CMD="/c game.take_screenshot{position={0,2.5},zoom=1,resolution={2560,1600},show_gui=false,path=\"ford-abs-${ROW}.png\"}"
DISPLAY=:0 xdotool type --window "$WID" --delay 25 "$CMD" 
DISPLAY=:0 xdotool key --window "$WID" Return; sleep 3
if [[ ! -f "$WD/script-output/$GAMEABS" ]]; then   # console raced the fresh relaunch
  sleep 2; DISPLAY=:0 xdotool windowactivate --sync "$WID"
  sleep 1; DISPLAY=:0 xdotool key --window "$WID" grave; sleep 1
  DISPLAY=:0 xdotool type --window "$WID" --delay 25 "$CMD"
  DISPLAY=:0 xdotool key --window "$WID" Return; sleep 5
fi
cp "$WD/script-output/$GAMEABS" "$ABS"
[[ -f "$ABS" ]] || { echo "$ROW: absolute capture missing after retry" >&2; exit 1; }

echo "== $ROW =="
python3 "$HERE/measure-rim.py" "$ABS" --abs
python3 "$HERE/measure-rim.py" "$WIN" | grep rim