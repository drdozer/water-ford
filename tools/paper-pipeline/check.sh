#!/usr/bin/env bash
# One-button headless load smoke (the zero-error gate).
#   check.sh [NAME]    # NAME = /tmp/wf-devcheck/<NAME>.zip, default "check"
# Run from anywhere. Exit 0 = clean (zero error/failed lines), 1 = dirty.
set -uo pipefail
NAME="${1:-check}"
GAME="${FACTORIO_BIN:-$HOME/.local/share/factorio_2_dlc/bin/x64/factorio}"
HERE="$(cd "$(dirname "$0")" && pwd)"
MODS="$HERE/../../testing/scratch/mods"
mkdir -p /tmp/wf-devcheck
timeout 90 "$GAME" -c /tmp/wf-devcheck/config.ini --mod-directory "$MODS" \
  --create "/tmp/wf-devcheck/$NAME.zip" --disable-audio 2>&1 \
  | tee /tmp/wf-devcheck/$NAME.log | grep -ciE 'error|failed' >/dev/null
if grep -qiE 'error|failed' /tmp/wf-devcheck/$NAME.log; then
  echo "CHECK $NAME: DIRTY"; grep -iE 'error|failed' /tmp/wf-devcheck/$NAME.log | head -5
  exit 1
fi
echo "CHECK $NAME: CLEAN"
