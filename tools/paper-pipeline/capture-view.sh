#!/usr/bin/env bash
# Capture the live Factorio window by FRESHLY resolving its id, and WAIT for
# the simulated scene (game finished loading) before returning.
#
# Traps guarded against here:
#  1. Stale/wrong window: id is resolved fresh each call; ids DO get reused
#     across relaunches — same id is not proof of staleness either way.
#  2. Loading screen: "VIEW WINDOW ALIVE" only proves the process; the map
#     may still be loading. The captured SCENE is validated (water in the S
#     bands) before this script succeeds.
# NOTE: absolute-coordinate screenshots (the measurement basis) are taken by
# sweep-row.sh via a one-shot console command into the game itself; this
# script remains the window/view recorder.
set -uo pipefail
OUT="${1:?usage: capture-view.sh out.png}"

SCENE_CHECK() {
python3 - "$1" <<'PYEOF'
import sys
from PIL import Image
import numpy as np
a = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(int)
r,g,b = a[...,0],a[...,1],a[...,2]
wm = (b > r + 15) & (g > r + 15) & (g < 180)
s_band = int(wm[880:920+1].sum())
total  = int(wm.sum())
ok = s_band > 5000 and total > 650000
print(f"scene-check: total_water={total} s_band={s_band} state={'OK' if ok else 'NOT-LOADED'}", file=sys.stderr)
sys.exit(0 if ok else 1)
PYEOF
}

for i in $(seq 1 12); do
  sleep "${FORD_SETTLE:-4}"
  ID=$(xwininfo -root -tree 2>/dev/null | grep ' "Factorio' | head -1 | awk '{print $1}')
  if [[ -z "$ID" ]]; then echo "no Factorio window found, retry $i" >&2; continue; fi
  echo "capturing window $ID"
  DISPLAY="${DISPLAY:-:0}" import -window "$ID" "$OUT" 2>/dev/null || { echo "import failed, retry" >&2; continue; }
  if SCENE_CHECK "$OUT"; then
    echo "capture ok: $OUT (attempt $i)"; exit 0
  fi
done
echo "ERROR: scene never looked loaded (12 attempts)" >&2
exit 1