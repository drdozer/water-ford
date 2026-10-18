#!/usr/bin/env bash
# One-button icon build: compose the water-ford item/tech icons from
# committed sheet cells (pure arrangement: crops + alpha-over pastes, no
# value changes; the game downscales via icon_size).
#   make-icons.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/make-icons.py"
