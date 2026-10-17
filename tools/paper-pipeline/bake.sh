#!/usr/bin/env bash
# paper-pipeline - deterministic bake chain for the ford piling sprites.
#   usage: bake.sh [--stages strips,sheet,deploy,save,view] [--twice] [--seed N]
#   default stages: strips -> sheet -> deploy -> save -> view
#   --twice: run the strip stage a second time and bit-compare all 108 frames
#            (the crank's reproducibility proof).
# Invariants (see README.md): paper pixels = Blender output only; hard-fail on
# empty/unwritten frames; sheet cells bit-equal to frames; seed-pinned saves.
set -euo pipefail

STAGES="strips,sheet,deploy,save,view"
TWICE=0; SEED=4242
while [[ $# -gt 0 ]]; do
  case "$1" in
    --stages) STAGES="$2"; shift 2;;
    --twice) TWICE=1; shift;;
    --seed) SEED="$2"; shift 2;;
    *) echo "unknown flag $1" >&2; exit 2;;
  esac
done

HERE="$(cd "$(dirname "$0")" && pwd)"
BLEND="$HERE/../../blender/ford-posts.blend"           # blender/ holds the project file
CACHE="$HERE/../../../../.cache/ford-factory"          # superproject .cache (4 ups)
SCRATCH="$HERE/../../testing/scratch"
FACTORIO="${FACTORIO_BIN:-$HOME/.local/share/factorio_2_dlc/bin/x64/factorio}"
has() { [[ ",$STAGES," == *",$1,"* ]]; }

run_stage() { echo "== stage: $1 =="; }

if has strips; then
  run_stage strips
  blender -b "$BLEND" --python "$HERE/bake-strips.py" 2>&1 | grep -E "STRIP|METRICS|DONE|RuntimeError|Error"
  if [[ $TWICE == 1 ]]; then
    STASH="$CACHE/.twice-stash"
    rm -rf "$STASH"; mkdir -p "$STASH"
    mv "$CACHE/icons64-wood"/*.png "$STASH/"
    blender -b "$BLEND" --python "$HERE/bake-strips.py" 2>&1 | grep -E "STRIP|DONE|RuntimeError|Error"
    python3 - "$STASH" <<'EOF'
import os, sys
import numpy as np
from PIL import Image
stash, fresh = sys.argv[1], os.path.join(os.path.dirname(sys.argv[1]), "icons64-wood")
bad = [f for f in sorted(os.listdir(fresh)) if not np.array_equal(
    np.asarray(Image.open(os.path.join(fresh, f)).convert("RGBA")),
    np.asarray(Image.open(os.path.join(stash, f)).convert("RGBA")))]
print("BIT-REPRODUCIBLE:", "yes - all frames identical across runs" if not bad else f"NO: {len(bad)} differ ({bad[:5]})")
if bad: sys.exit(1)
EOF
    rm -rf "$STASH"
  fi
fi

if has shadow; then
  run_stage shadow
  blender -b "$BLEND" --python "$HERE/bake-shadow.py" 2>&1 | grep -E "SHADOW|DONE|RuntimeError|Error"
fi

if has mask; then
  run_stage mask
  blender -b "$BLEND" --python "$HERE/bake-mask.py" 2>&1 | grep -E "MASK|DONE|RuntimeError|Error"
fi

if has sheet; then
  run_stage sheet
  python3 "$HERE/bake-sheet.py"
fi

if has deploy; then
  run_stage deploy
  python3 "$HERE/bake-transition-sheet.py"
fi

if has save; then
  run_stage save
  python3 "$HERE/bake-save.py" --seed "$SEED"
fi

if has view; then
  run_stage view
  pkill -x factorio 2>/dev/null || true; sleep 2
  DISPLAY="${DISPLAY:-:0}" nohup "$FACTORIO" \
    -c "$SCRATCH/config/config.ini" --mod-directory "$SCRATCH/mods" \
    --load-game "$SCRATCH/saves/ford-view-test.zip" \
    > "$SCRATCH/windowed.log" 2>&1 &
  sleep 26
  pgrep -x factorio > /dev/null && echo "VIEW WINDOW ALIVE" || { echo "view window died"; exit 1; }
fi

echo "BAKE COMPLETE ($STAGES)"