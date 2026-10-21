#!/usr/bin/env bash
# cobblestone crank: ONE blender process runs auth (mechanically rebuild the
# scene: tools/paper-pipeline/auth-cobble.py) then bake (art ladder + wetness
# masks: bake-cobble.py) against the just-built in-memory state.
#
# Why single process (2026-10-21, "the agents keep getting into a mess"): the
# old two-invocation crank had a stale-blind spot — the auth crashed, blender
# swallowed the script exit (default exit code 0 without --python-exit-code),
# the shell proceeded, and the bake re-rendered the PREVIOUS blend while the
# gate blessed it ALL-GREEN. A gate that doesn't know what it gated isn't a
# gate. Now:
#   * one process: the bake cannot see any blend but the one this run built;
#   * --python-exit-code 1: script failures kill the crank (no swallowing);
#   * the bake independently refuses an unstamped/stale blend (provenance
#     stamp written into the .blend by the auth: script sha, mesh-hash oracle,
#     rig values) — belt for anyone invoking the bake standalone;
#   * sheets render to .cache staging and get PROMOTED to assets-src/cobble/
#     only when pixels actually change (the PNG writer is not byte-stable
#     run-to-run; rerunning the crank must leave git clean unless art moved);
#   * the authority for green = the VERDICT line grepped from the log.
# Sheets land in assets-src/cobble/ (committed artifacts). The blend is a
# build output (gitignored: exceeds GitHub's 100 MB block) and doubles as
# the maintainer's COLOR RIG surface (M_COBBLE's COB_TONE / COB_BED_TONE
# knobs; TONE_* constants in auth-cobble.py are the committed state).
# NOTE (2026-10-21): the maintainer ruled the ENTIRE cobble toolchain
# suspect — the compositor GAME_VEIL is ABOLISHED (no veil anywhere,
# auth no longer builds it); nothing further is folded back into this tooling
# pending the gut-and-remake.
set -euo pipefail
MOD=$(cd "$(dirname "$0")/../.." && pwd)
PP="$MOD/tools/paper-pipeline"
AUTH="$PP/auth-cobble.py"
BAKE="$PP/bake-cobble.py"
BLEND="$MOD/blender/ford-cobble.blend"
LOG="$MOD/.cache/blender-cobble/run.log"
mkdir -p "$MOD/.cache/blender-cobble"
exec > >(stdbuf -oL tee "$LOG") 2>&1

if [[ "${1:-}" == "--selftest" ]]; then
  # Prove the refusal: strip the stamp from a copy of the current blend and
  # expect the standalone bake to die loudly with the marker, nonzero exit.
  S="$MOD/.cache/blender-cobble/selftest"
  mkdir -p "$S"
  echo "== crank selftest: the bake must REFUSE an unstamped (stale) blend =="
  blender -b "$BLEND" --python-expr "
import bpy
sc = bpy.data.scenes['FLOOR']
if 'cobble_auth' in sc:
    del sc['cobble_auth']
bpy.ops.wm.save_as_mainfile(filepath='$S/stale.blend', compress=True)
print('SELFTEST STRIP OK')" > "$S/strip.log" 2>&1
  grep -q "SELFTEST STRIP OK" "$S/strip.log" \
    || { cat "$S/strip.log"; echo "CRANK SELFTEST FAIL (strip stage)"; exit 2; }
  if blender -b "$S/stale.blend" --python-exit-code 1 -P "$BAKE" > "$S/refuse.log" 2>&1; then
    echo "CRANK SELFTEST FAIL: the bake RAN on a stale blend"
    tail -20 "$S/refuse.log"; exit 2
  fi
  # the auth script in the same dir differs from the specimen? not relevant:
  # the specimen was STAMPED-current minus the stamp, so the refusal must be
  # the missing-marker one either way.
  grep -q "COBBLE STALE-BLEND REFUSAL" "$S/refuse.log" \
    || { echo "CRANK SELFTEST FAIL: refused, but without the marker:"
         tail -20 "$S/refuse.log"; exit 2; }
  echo "CRANK SELFTEST OK: stale blend refused (marker + nonzero exit)"
  exit 0
fi

echo "== cobble crank: auth → bake in ONE blender process =="
blender -b --python-exit-code 1 --python "$AUTH" --python "$BAKE" -- "$BLEND"
grep -q "VERDICT ALL-GREEN" "$LOG" \
  || { echo "CRANK NOT GREEN — refusing to call it done (log: $LOG)"; exit 3; }
grep -q "STAMP VERIFIED" "$LOG" \
  || { echo "CRANK WITHOUT A VERIFIED STAMP — refusing (log: $LOG)"; exit 3; }
echo "CRANK OK (green, stamped; log: $LOG)"