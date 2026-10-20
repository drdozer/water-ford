#!/usr/bin/env python3
"""Fail if any graphics file referenced from mod/*.lua is missing from mod/graphics/.

Why this exists: the data-stage gates (--dump-data, dump-diff) never
validate sprite paths — a broken reference only surfaces as
"Failed to load mods" at game launch (2026-10-19: the identifier rename
rewired 14 references to filenames that were never renamed). Run this in
every verification pass; it is the load-gate for asset names.

Stdlib only, standalone (superproject shared venv not required).
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, "mod")
GFX = os.path.join(MOD, "graphics")

# assets kept for tooling, not referenced by prototypes (icon sources etc.)
ALLOW_UNREFERENCED = {"planks.png", "planks-base.png"}


def main():
    refs = set()
    for fn in sorted(os.listdir(MOD)):
        if fn.endswith(".lua"):
            text = open(os.path.join(MOD, fn), encoding="utf-8").read()
            refs.update(re.findall(r"__water-ford__/graphics/([A-Za-z0-9_.-]+\.png)", text))
            refs.update(re.findall(r'"graphics/([A-Za-z0-9_.-]+\.png)"', text))
    on_disk = set(os.listdir(GFX)) if os.path.isdir(GFX) else set()
    missing = sorted(refs - on_disk)
    stray = sorted(on_disk - refs - ALLOW_UNREFERENCED)
    for m in missing:
        print(f"MISSING: mod/graphics/{m} (referenced but absent)", file=sys.stderr)
    for s in stray:
        print(f"UNREFERENCED: mod/graphics/{s} (shipped but unused?)", file=sys.stderr)
    if missing or stray:
        return 1
    print(f"graphics OK: {len(refs)} references, all present "
          f"({len(ALLOW_UNREFERENCED)} allowed icon sources)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
