#!/usr/bin/env python3
"""Band measurement for the ford shore-rim bisection.

Recipe from docs/RESUME.md (bands are stable for seed 4242, spawn {0.5,4.5},
2560x1600 window): water-only G means in N and S bands one and two tile rows
from the ford edge, plus deep water far from the ford and the deck's mid strip.

Metric per capture:
  - G means of water-classified pixels per band (water = teal-blue class).
  - rim dip = row2_G - touch_G per side (the shore rim shows as touch darker).
Decision rule: a candidate property is ACQUITTED when the dip persists
(~13-16 G at day brightness); it is the CULPRIT when the dip collapses to
noise (~<4). Always compare within one capture (water animation varies).

usage: measure-rim.py capture.png [capture.png ...]
"""
import sys
import numpy as np
from PIL import Image

# y-ranges: (label, y0, y1). x is full width; the classifier excludes HUD.
BANDS = [
    ("Ndeep",  300, 340),
    ("Nrow2",  512, 551),
    ("Ntouch", 556, 595),
    ("Sdeep", 1050, 1090),
    ("Srow2",  924, 963),
    ("Stouch", 880, 919),
    ("mid",    700, 740),   # ford deck strip (deck pixels are NOT water-class)
]

# ABSOLUTE-coordinate basis (game.take_screenshot, zoom=1 -> 32 px/tile,
# resolution 2560x1600 at position {0,2.5}; show_gui=false, no HUD):
# py = 800 + (world_y - 2.5) * 32
BANDS_ABS = [
    ("Ndeep",  432, 463),   # world y -11..-10
    ("Nrow2",  592, 623),   # y -4..-3
    ("Ntouch", 624, 655),   # y -3..-2
    ("Stouch", 944, 975),   # y  7..8
    ("Srow2",  976, 1007),  # y  8..9
    ("Sdeep", 1040, 1071),  # y 10..11
    ("mid",    688, 752),   # world y -0.5..1.5 (deck rows; warm count, not water G)
]

def water_mask(rgb):
    """Teal/blue water class: blue and green both above red by a margin."""
    r = rgb[..., 0].astype(int); g = rgb[..., 1].astype(int); b = rgb[..., 2].astype(int)
    return (b > r + 15) & (g > r + 15) & (g < 180)

def measure(path, bands):
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    wm = water_mask(a)
    warm = (a[..., 0] > a[..., 2] + 10) & (a[..., 0] > 60)
    out = {}
    for label, y0, y1 in bands:
        band = wm[y0:y1 + 1]
        sel = band.any(axis=0)
        px = a[y0:y1 + 1][sel if False else band]
        if label == "mid":
            out[label] = (int(warm[y0:y1 + 1].sum()),)
        else:
            out[label] = (px[:, 1].mean() if px.size else float("nan"),
                          px.shape[0])
    return out, int(wm.sum())

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--abs"]
    bands = BANDS_ABS if "--abs" in sys.argv else BANDS
    for path in args:
        out, total = measure(path, bands)
        means = "  ".join(f"{l}={v[0]:6.1f}" for l, v in out.items())
        print(f"{path}\n  water px {total:8d}  {means}")
        ndip = out["Nrow2"][0] - out["Ntouch"][0]
        sdip = out["Srow2"][0] - out["Stouch"][0]
        print(f"  rim dip N={ndip:6.1f}  S={sdip:6.1f}")