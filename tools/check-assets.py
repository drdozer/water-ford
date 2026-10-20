#!/usr/bin/env python3
"""Fail if any asset referenced from mod/*.lua is missing from the shipped tree.

Why this exists: the data-stage gates (--dump-data, dump-diff) never
validate file existence — a broken reference only surfaces as
"Failed to load mods" at game launch (2026-10-19/20: the identifier
rename rewired 14 graphics references to filenames that were never
renamed). Run this in every verification pass; it is the load-gate for
asset names.

Covers:
- graphics: `__water-ford__/graphics/<file>.png` literals
- sound:    `__water-ford__/sound/...ogg` literals, plus
            sound_variations("__water-ford__/sound/<prefix>", N) expanded
            to <prefix>-1.ogg .. <prefix>-N.ogg (core sound-util
            convention, non-padded)

Stdlib only, standalone (superproject shared venv not required).
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, "mod")
SOUND_PREFIX = "__water-ford__/sound/"

# assets kept for tooling, not referenced by prototypes (icon sources etc.)
ALLOW_UNREFERENCED = {"graphics/planks.png", "graphics/planks-base.png"}


def main():
    wanted = set()  # paths relative to mod/

    def add_graphics(name):
        wanted.add(f"graphics/{name}")

    def add_sound(rel_no_ext):
        wanted.add(f"sound/{rel_no_ext}.ogg")

    for fn in sorted(os.listdir(MOD)):
        if not fn.endswith(".lua"):
            continue
        text = open(os.path.join(MOD, fn), encoding="utf-8").read()
        for m in re.findall(r"__water-ford__/graphics/([A-Za-z0-9_.-]+\.png)", text):
            add_graphics(m)
        for m in re.findall(r"__water-ford__/sound/([A-Za-z0-9_/-]+\.ogg)", text):
            wanted.add(f"sound/{m}")
        # sound_variations("__water-ford__/sound/<prefix>", N, ...) -> <prefix>-1..N.ogg
        for prefix in re.findall(
            r'sound_variations\("(__water-ford__/sound/[A-Za-z0-9_/-]+)",\s*\d+', text
        ):
            rel = prefix[len(SOUND_PREFIX):]
            # count from the same call
            n = int(re.search(
                r'sound_variations\("' + re.escape(prefix) + r'",\s*(\d+)', text
            ).group(1))
            for i in range(1, n + 1):
                add_sound(f"{rel}-{i}")

    on_disk = set()
    for kind in ("graphics", "sound"):
        base = os.path.join(MOD, kind)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirnames, filenames in os.walk(base):
            for f in filenames:
                on_disk.add(os.path.relpath(os.path.join(dirpath, f), MOD))

    missing = sorted(wanted - on_disk)
    stray = sorted(on_disk - wanted - ALLOW_UNREFERENCED)
    for m in missing:
        print(f"MISSING: mod/{m} (referenced but absent)", file=sys.stderr)
    for s in stray:
        print(f"UNREFERENCED: mod/{s} (shipped but unused?)", file=sys.stderr)
    if missing or stray:
        return 1
    n_gfx = sum(1 for w in wanted if w.startswith("graphics/"))
    n_snd = sum(1 for w in wanted if w.startswith("sound/"))
    print(f"assets OK: {n_gfx} graphics + {n_snd} sound references, all present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
