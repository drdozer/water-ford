#!/usr/bin/env bash
# One-button stones bake: render + pack the ford-stones decorative sheets
# (pebbles/stones, above-waterline + below-waterline pairs).
#
#   bake-stones.sh            # bake once (hard-fails on any verification)
#   bake-stones.sh --twice    # bake, stash pixels, re-bake, pixel-array proof
#
# Law-2: opens the COMMITTED blender/ford-stones.blend; never rebuilds
# scenes. Factory edits happen in a visible session via auth-stones.py.
# Determinism law: pixel arrays are bit-reproducible across processes; PNG
# container bytes are not - the --twice proof compares np.array_equal(RGBA).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BLEND="$HERE/../../blender/ford-stones.blend"
CACHE="$HERE/../../../../.cache/ford-factory"
TWICE=0
[[ "${1:-}" == "--twice" ]] && TWICE=1

run_bake () {
  blender -b "$BLEND" --python "$HERE/bake-stones.py" 2>&1 | grep -E "SHEET|RuntimeError|Error"
}

if [[ "$TWICE" == "1" ]]; then
  STASH="$CACHE/.stones-stash"
  rm -rf "$STASH"; mkdir -p "$STASH/pebbles" "$STASH/frames"
  mv "$CACHE/stones/pebbles/"*.png "$STASH/pebbles/" 2>/dev/null || true
  mv "$CACHE/stones/frames/"*.png  "$STASH/frames/"  2>/dev/null || true
  run_bake
  python3 - "$STASH" "$CACHE/stones" <<'EOF'
import os, sys, numpy as np
from PIL import Image
stash, fresh = sys.argv[1], sys.argv[2]
bad, n = [], 0
for sub in ("pebbles", "frames"):
    d0, d1 = os.path.join(stash, sub), os.path.join(fresh, sub)
    for f in sorted(os.listdir(d0)):
        if not f.endswith(".png"): continue
        a = np.asarray(Image.open(os.path.join(d0, f)).convert("RGBA"))
        b = np.asarray(Image.open(os.path.join(d1, f)).convert("RGBA"))
        n += 1
        if not np.array_equal(a, b): bad.append(f"{sub}/{f}")
print("PIXEL --TWICE:", f"BIT-REPRODUCIBLE - {n}/{n} frames pixel-identical" if not bad
      else f"NO: {len(bad)} differ ({bad[:5]})")
sys.exit(1 if bad else 0)
EOF
else
  run_bake
fi
