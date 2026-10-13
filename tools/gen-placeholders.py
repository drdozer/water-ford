#!/usr/bin/env python3
"""Regenerates the placeholder pilings sheet (graphics/pilings.png).

One post per 64px sheet column (= one post per tile edge), anchored to the
vanilla landfill shore silhouette for position only. Each post: elliptical cut
face (~45 deg downward projection), cylinder-shaded body, solid crown fading to
a translucent foot (the water beneath shows through), painted foam rings at the
base for the lapping look. Posts are stamped into all three panels
(overlay/background/mask) at the same coordinates.

The land-side band and palisade generators from earlier iterations are in git
history (see commits cbcd366, 6e0d8d5, a4a34bc).

Knobs (all in one place):
  POST_W, H range, JITTER, foot alpha, foam radii - see constants below.
Known wanted tweaks, deferred to Blender-era modelling:
  - posts ~2/3 the current size
  - wood-ring texture on the cut faces
  - north-facing posts shifted ~half a tile south (tops closer to the planks)
  - softer contact shadow (current hard base shading reads as a "barcode")
  - chain from posts down to planks; bolts/rivets on the planks
"""
from PIL import Image
import numpy as np, random, math

BASE = "/home/nmrp3/.local/share/factorio_2_dlc/data/base/graphics/terrain/water-transitions/"
OUT = "pilings.png"
PANELS = (0, 1088, 2176)                       # overlay/background/mask panel x-offsets
BANDS = [(0, 8, 128, 4), (576, 8, 128, 4), (1152, 8, 128, 4),
         (1728, 2, 128, 4), (2304, 4, 64, 1)]  # (band y, columns, cell h, rotation rows)

POST_W = 24            # px on the 2x sheet (12 screen px)
H_MIN, H_MAX = 58, 74  # post body height range before weathering
JITTER_POS, JITTER_H = 4, 2
FOOT_ALPHA = 115.0     # opacity at the submerged foot (255 = fully solid crown)
WEATHERED_CHANCE, WEATHERED_FACTOR = 0.18, 0.72

DARK = np.array([44, 29, 15], np.float32); LITE = np.array([218, 176, 114], np.float32)
CAP = np.array([232, 196, 134], np.float32); CAPEDGE = np.array([168, 128, 76], np.float32)
FOAM = np.array([205, 226, 232], np.float32)

van = np.asarray(Image.open(BASE + "landfill.png").convert("RGBA")).astype(np.float32)
alpha2 = van[..., 3]
cv = np.zeros((2368, 3200, 4), np.float32)

def ripple(cx, cy, rx, ry, a):
    for t in np.linspace(0, 2 * math.pi, 90):
        for th in (0, 1):
            x, y = int(cx + rx * math.cos(t)) + th, int(cy + ry * math.sin(t)) + th
            if 0 <= y < 2368 and 0 <= x < 3200 and cv[y, x, 3] < a:
                cv[y, x, :3], cv[y, x, 3] = FOAM, a

def post(px, base_y, y_min, h, w):
    rx = w / 2.0
    ry = max(int(rx * 0.55), 3)                      # foreshortened cut face (~45 deg)
    cy_cap = max(int(base_y - h), y_min) + ry
    x0 = int(px - rx)
    for x in range(x0, x0 + w):                      # body below the cap
        t = (x - x0 + 0.5) / w
        col = DARK + (LITE - DARK) * ((1 - abs(t - 0.5) * 2) ** 0.7)
        for y in range(int(cy_cap), int(base_y)):
            frac = (y - y_min) / max(base_y - y_min, 1)
            a = 255.0 if frac < 0.5 else 255.0 - (frac - 0.5) / 0.5 * (255.0 - FOOT_ALPHA)
            cv[y, x, :3], cv[y, x, 3] = col, a
    for dy in range(-ry, ry + 1):                    # elliptical cut face
        hw = rx * math.sqrt(max(1.0 - (dy / ry) ** 2, 0.0))
        xa, xb = int(px - hw), int(px + hw)
        cv[cy_cap + dy, xa:xb + 1, :3] = CAP + (CAPEDGE - CAP) * (abs(dy) / ry)
        cv[cy_cap + dy, xa:xb + 1, 3] = 255.0

n = 0
for y0, cols, ch, rows in BANDS:
    for r in range(rows):
        ry0 = y0 + r * 128
        for c in range(cols):
            cx0 = c * 64
            rng = random.Random(9000 + y0 * 31 + r * 7 + c)
            ca = alpha2[ry0:ry0 + ch, cx0:cx0 + 64]
            ys, xs = np.nonzero(ca > 128)
            if len(ys) == 0: continue
            px_rel = min(max(int(xs.mean()) + rng.randint(-JITTER_POS, JITTER_POS), 14), 50)
            col_a = ca[:, px_rel]
            base_rel = min(int(np.nonzero(col_a > 128)[0].max()) + 1 + rng.randint(-JITTER_H, JITTER_H), ch - 2)
            w = POST_W + rng.randint(-2, 2)
            h = min(rng.randint(H_MIN, H_MAX), base_rel - 10)
            if rng.random() < WEATHERED_CHANCE: h = int(h * WEATHERED_FACTOR)
            bx, by = cx0 + px_rel, ry0 + base_rel
            for dx in PANELS:
                ripple(bx + dx, by, 22, 9, 70); ripple(bx + dx, by, 14, 6, 110)
                post(bx + dx, by, ry0, h, w)
            n += 1

Image.fromarray(cv.clip(0, 255).astype(np.uint8), "RGBA").save(OUT)
print(f"{OUT}: {n} posts written")
