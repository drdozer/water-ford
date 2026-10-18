#!/usr/bin/env bash
# One-button in-game verification bench (the console law, scripted).
#
#   bench.sh SAVE_NAME POSITION_X,POSITION_Y CAPTURE_TAG [--paint 'LUA...']
#
# Example (stones bench on the viewer save):
#   bench.sh ford-view-test 0,2.5 stones-bal \
#     --paint 'local s=game.player.surface local t={} for x=-14,14 do for y=-2,6 do t[#t+1]={name="water-ford",position={x,y}} end end s.set_tiles(t)'
#
# THE CONSOLE LAW (maintainer, 2026-10-18, verbatim):
#   "You use backtick to open the console. Then /c followed by a space, then
#   your command."  - backtick opens the console; "/c " + command + Return.
#   NOTHING else is ever typed at the game. No raw letters (they drive the
#   character / open train views). Verify effects by ARTIFACT FILES ON DISK
#   (script-output/), never by assumption. The console closes after each
#   Return: every command needs its own backtick.
set -uo pipefail
SAVE="${1:?usage: bench.sh SAVE X,Y TAG [--paint LUA]}"
POS="${2:?usage: bench.sh SAVE X,Y TAG [--paint LUA]}"
TAG="${3:?usage: bench.sh SAVE X,Y TAG [--paint LUA]}"
PAINT=""
[[ "${1:-}" == "--paint" ]] && { echo "usage: bench.sh SAVE X,Y TAG [--paint LUA]"; exit 2; }
if [[ "${4:-}" == "--paint" ]]; then PAINT="${5:?--paint needs the lua command}"; fi

HERE="$(cd "$(dirname "$0")" && pwd)"
SCRATCH="$HERE/../../testing/scratch"
PROV="$HERE/../../../../.cache/ford-factory/provenance"
GAMEABS="bench-${TAG}.png"
CX="${POS%,*}"; CY="${POS#*,}"
STAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p "$PROV"

# fresh relaunch (tiles painted via set_tiles do not persist across sessions)
pkill -x factorio 2>/dev/null; sleep 2
DISPLAY=:0 nohup "$HOME/.local/share/factorio_2_dlc/bin/x64/factorio" \
  -c "$SCRATCH/config/config.ini" --mod-directory "$SCRATCH/mods" \
  --load-game "$SCRATCH/saves/$SAVE.zip" > "$SCRATCH/windowed.log" 2>&1 &
sleep 27
pgrep -x factorio >/dev/null || { echo "LAUNCH-FAILED"; exit 1; }
WID=$(xwininfo -root -tree 2>/dev/null | grep ' "Factorio' | head -1 | awk '{print $1}')
[[ "$(DISPLAY=:0 xdotool getwindowname "$WID" 2>/dev/null)" == *Factorio* ]] || { echo "WINDOW-GONE"; exit 1; }
DISPLAY=:0 xdotool windowactivate --sync "$WID"; sleep 2

conscmd () {  # $1 = lua body (without /c) - grave, type, Return, retry-once
  local CMD="/c $1" OUT="$1"
  rm -f "$SCRATCH/script-output/$GAMEABS"
  DISPLAY=:0 xdotool key --window "$WID" grave; sleep 1
  DISPLAY=:0 xdotool type --window "$WID" --delay 25 "$CMD"
  DISPLAY=:0 xdotool key --window "$WID" Return; sleep 2
}
[[ -n "$PAINT" ]] && conscmd "$PAINT"

DISPLAY=:0 xdotool key --window "$WID" grave; sleep 1
DISPLAY=:0 xdotool type --window "$WID" --delay 25 \
  "/c game.take_screenshot{position={$CX,$CY},zoom=1,resolution={2560,1600},show_gui=false,path=\"$GAMEABS\"}"
DISPLAY=:0 xdotool key --window "$WID" Return; sleep 4
if [[ ! -f "$SCRATCH/script-output/$GAMEABS" ]]; then  # console raced the relaunch
  sleep 2; DISPLAY=:0 xdotool windowactivate --sync "$WID"; sleep 1
  DISPLAY=:0 xdotool key --window "$WID" grave; sleep 1
  DISPLAY=:0 xdotool type --window "$WID" --delay 25 \
    "/c game.take_screenshot{position={$CX,$CY},zoom=1,resolution={2560,1600},show_gui=false,path=\"$GAMEABS\"}"
  DISPLAY=:0 xdotool key --window "$WID" Return; sleep 5
fi
[[ -f "$SCRATCH/script-output/$GAMEABS" ]] || { echo "CAPTURE-MISSING"; exit 1; }

DEST="$PROV/${STAMP}-${TAG}.png"
cp "$SCRATCH/script-output/$GAMEABS" "$DEST"
echo "SAVED $DEST"
# pixel↔tile mapping for a 2560x1600 capture centered at (CX,CY), zoom 1:
#   px = 1280 + (tx-CX)*32   py = 800 + (ty-CY)*32
DISPLAY=:0 nohup gwenview "$DEST" >/dev/null 2>&1 &
