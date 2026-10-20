#!/usr/bin/env python3
"""Generates the ford's branding art — portal thumbnail reconstruction.

  thumbnail.png        the mod-portal thumbnail (358x114): a 64px row of plank
                       tiles (planks.png column 0) across the middle band
                       (y=25..89, tiled every 64px, last tile cropped), over a
                       water border (25px top / 25px bottom) — the composition
                       of commit c4033c5 ("tiled boarding art over water"; the
                       water frame was palette-mode on the first attempt).

The SHIPPED thumbnail.png is the canonical artifact: its exact border water
could not be reverse-engineered from base art (it does not match any raw crop
or plain scaling of water1.png), so this script's thumbnail output is a
best-effort reconstruction and is written to a scratch path by default. Run
with --check to compare against the shipped file; only --write-thumbnail
replaces it (deliberately discouraged).

Usage (standalone; needs PIL + numpy):
  tools/gen-branding.py [--out DIR] [--scratch DIR] [--base DIR]
                        [--check] [--write-thumbnail]
    --out      graphics dir holding planks.png / wooden-ford-icon.png
               (default: <repo>/mod/graphics)
    --scratch  where the reconstructed thumbnail is written
               (default: <repo>/dist/thumbnail.reconstructed.png)
    --base     the game install's data/base dir (water border source)
"""
import argparse
import os
from pathlib import Path

import numpy as np
from PIL import Image

DEFAULT_BASE = os.environ.get(
    "FACTORIO_BASE_DIR",
    os.path.expanduser("~/.local/share/factorio_2_dlc/data/base"),
)
REPO = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO / "mod" / "graphics"

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument("--out", default=str(DEFAULT_OUT), help="mod graphics dir")
ap.add_argument("--scratch", default=None, help="reconstructed-thumbnail output path")
ap.add_argument("--base", default=DEFAULT_BASE, help="game install data/base dir")
ap.add_argument("--check", action="store_true", help="compare regenerated art with shipped files")
ap.add_argument("--write-thumbnail", action="store_true",
                help="replace the shipped thumbnail.png with the reconstruction (discouraged)")
args = ap.parse_args()

OUT = Path(args.out)
MOD = OUT.parent                       # zip root: holds thumbnail.png
SCRATCH = Path(args.scratch) if args.scratch else REPO / "dist" / "thumbnail.reconstructed.png"
TH_W, TH_H, BORDER, TILE = 358, 114, 25, 64


def decoded(path):
    return np.asarray(Image.open(path).convert("RGBA"))


def report_pixel_match(new_arr, path):
    if not Path(path).exists():
        print(f"{Path(path).name}: (no shipped file to compare)")
        return False
    same = np.array_equal(decoded(path), new_arr)
    print(f"{Path(path).name}: pixels {'IDENTICAL' if same else 'DIFFER'} vs shipped")
    return same


# --- icon: RETIRED -----------------------------------------------------------
# The 1.0.0 icon (64x64 planks slice, commit a020dad) was superseded in the
# boards rounds by tools/paper-pipeline/make-icons.py (128px deck-cell +
# stones). This script no longer writes the icon — running the old writer
# here would clobber the shipped 128px icon with a 64px 1.0.0 slice.

# --- thumbnail: plank row over a water border --------------------------------
planks = decoded(OUT / "planks.png")            # sheet still feeds the thumbnail row
water = Image.open(Path(args.base) / "graphics" / "terrain" / "water" / "water1.png").convert("RGBA")
frame = np.asarray(water.crop((0, 0, 64, 64)))

th = np.zeros((TH_H, TH_W, 4), np.uint8)
water_row = np.tile(frame, (1, TH_W // 64 + 1, 1))[:, :TH_W]   # 64px water tiled across
th[:BORDER] = water_row[:BORDER]                   # top border (stand-in water)
th[TH_H - BORDER:] = water_row[64 - BORDER:]       # bottom border (stand-in water)
col0 = planks[:, 0:64]                             # plank tile: sheet column 0
x = 0
while x < TH_W:
    w = min(TILE, TH_W - x)
    th[BORDER:BORDER + TILE, x:x + w] = col0[:, :w]
    x += TILE

if args.write_thumbnail:
    Image.fromarray(th, "RGBA").save(MOD / "thumbnail.png")
    print(f"thumbnail.png REPLACED ({MOD / 'thumbnail.png'})")
else:
    SCRATCH.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(th, "RGBA").save(SCRATCH)
    print(f"reconstructed thumbnail written to {SCRATCH} (shipped thumbnail untouched)")
    if args.check:
        report_pixel_match(th, MOD / "thumbnail.png")
