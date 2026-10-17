#!/usr/bin/env bash
# console-help.sh — the ONLY sanctioned way to drive the factorio dev console
# (maintainer law 2026-10-18: "You use backtick to open the console. Then /c
# followed by a space, then your command." — no other keys are ever sent.)
#
# Usage: console-help.sh 'LUA CMD'      (command body WITHOUT "/c")
#   console-help.sh --check             state report only
# Requires: the map view visible; aborts loudly if the console/menu state is
# not verifiable. Every artifact the caller checks afterwards = the truth.
set -uo pipefail
CMDBODY="${1:-}"

WID=$(xwininfo -root -tree 2>/dev/null | grep ' "Factorio' | head -1 | awk '{print $1}')
NAME=$(xdotool getwindowname "$WID" 2>/dev/null || echo MISSING)
[[ "$NAME" == *Factorio* ]] || { echo "WINDOW-GONE: '$NAME'"; exit 2; }
eval "$(xdotool getwindowgeometry --shell "$WID")"

export DISPLAY=:0
cat > /tmp/consdet.py <<'PYEOF'
import sys, os, subprocess, numpy as np
from PIL import Image
WID, X, Y = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
subprocess.run(["import", "-window", "root", "/tmp/sd.png"],
               env=dict(os.environ, DISPLAY=":0"), check=True)
im = np.asarray(Image.open("/tmp/sd.png").convert("L"))
crop = im[Y + 10:Y + 70, X + 40:X + 1400]
print(f"{(crop < 60).mean():.2f}")
PYEOF
cat > /tmp/mapdet.py <<'PYEOF'
import os, subprocess, numpy as np
from PIL import Image
subprocess.run(["import", "-window", "root", "/tmp/md.png"],
               env=dict(os.environ, DISPLAY=":0"), check=True)
im = np.asarray(Image.open("/tmp/md.png").convert("RGB"))
h, w, _ = im.shape
c = im[h//2-300:h//2+300, 3840+600:3840+2000].astype(int)
r, g, b = c[..., 0], c[..., 1], c[..., 2]
print(f"{((b>g)&(g>r)&(b>80)).mean():.3f} {((r>g)&(g>b)&(r-b>12)).mean():.3f}")
PYEOF
consdet () { python3 /tmp/consdet.py "$WID" "$X" "$Y"; }

# menu walkout: verify map visible, else Escape and re-verify
for i in 1 2 3; do
  MAP=$(python3 /tmp/mapdet.py)
  Teal=$(echo "$MAP" | cut -d' ' -f1)
  python3 -c "import sys; sys.exit(0 if float('$Teal')>0.08 else 1)" && break
  echo "map not visible (teal=$Teal) - Escape and re-check"
  xdotool key --window "$WID" Escape; sleep 2
done
MAP=$(python3 /tmp/mapdet.py); echo "state: map-teal=$(echo $MAP|cut -d' ' -f1) map-warm=$(echo $MAP|cut -d' ' -f2)"

if [[ "$CMDBODY" == "--check" ]]; then
  ST=$(consdet); echo "console-darkness=$ST"; exit 0
fi
[[ -z "$CMDBODY" ]] && { echo "usage: console-help.sh 'LUA CMD'"; exit 2; }

# open console: grave, then VERIFY the console band appeared
xdotool key --window "$WID" grave; sleep 1
ST=$(consdet)
python3 -c "import sys; sys.exit(0 if float('$ST')>0.6 else 1)" || { echo "CONSOLE-FAILED-TO-OPEN"; exit 3; }
# clear any stale input line (we are INSIDE a verified console now)
xdotool key --window "$WID" End
for i in $(seq 1 40); do xdotool key --window "$WID" BackSpace; done
# type the /c command and execute
xdotool type --window "$WID" --delay 15 "/c $CMDBODY"
sleep 1
xdotool key --window "$WID" Return
sleep 3
# close the console if it stayed open
ST2=$(consdet)
if python3 -c "import sys; sys.exit(0 if float('$ST2')>0.6 else 1)"; then
  xdotool key --window "$WID" grave; sleep 1
fi
echo "OK"