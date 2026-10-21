#!/usr/bin/env bash
# cobblestone ladder chain: auth (mechanically rebuild blender/ford-cobble.blend
# from tools/paper-pipeline/auth-cobble.py) → bake (art ladder + wet/dry-in-art
# WL ramp; NO mask sheets — maintainer ruling 2026-10-21). Every stage
# idempotent; determinism gate = byte-compare of two full crank runs.
# Sheets land in assets-src/cobble/ (committed artifacts, law-3 packed).
# The blend is a build output (gitignored: exceeds GitHub's 100 MB block).
set -euo pipefail
MOD=$(cd "$(dirname "$0")/../.." && pwd)
BLEND="$MOD/blender/ford-cobble.blend"
LOG="$MOD/.cache/blender-cobble/run.log"
mkdir -p "$MOD/.cache/blender-cobble"
exec > >(stdbuf -oL tee "$LOG") 2>&1

echo "== auth-cobble: rebuild $BLEND =="
blender -b --python "$MOD/tools/paper-pipeline/auth-cobble.py" -- "$BLEND"

echo "== bake-cobble: art ladder (x2 determinism) =="
blender -b "$BLEND" -P "$MOD/tools/paper-pipeline/bake-cobble.py"