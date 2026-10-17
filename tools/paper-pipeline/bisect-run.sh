#!/usr/bin/env bash
# One bisect run cycle: clean shutdown -> rebake save+view -> fresh capture.
# The headless save stage needs the scratch dir's exclusive lock; a still-running
# or still-exiting windowed game holds it ("scenario save did not appear").
# So: pkill, then WAIT until the factorio process AND the .lock are gone.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SEED="${SEED:-4242}"
OUT="${1:-/tmp/ford_run.png}"

pkill -x factorio 2>/dev/null || true
for i in $(seq 1 40); do
  pgrep -x factorio >/dev/null || break
  sleep 1
done
pgrep -x factorio >/dev/null && { echo "factorio would not die" >&2; exit 1; }
LOCK="$HERE/../../testing/scratch/.lock"
while lsof "$LOCK" >/dev/null 2>&1; do sleep 1; done

"$HERE/bake.sh" --stages save,view --seed "$SEED" 2>&1 | tail -6
"$HERE/capture-view.sh" "$OUT"