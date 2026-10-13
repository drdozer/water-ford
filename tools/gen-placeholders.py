#!/usr/bin/env python3
"""Generates the ford post sheets.

  pilings-exp.png   THE post sheet (arms A and B): 2/3-size posts, wood rings on
                    the cut faces, softer shading, north-facing posts' bases
                    shifted half a tile south. Contains ONLY the pilings - no
                    painted foam (foam belongs in a layer the water shader
                    interacts with; revisit once basic visuals are correct).
  pilings-mask.png  the known-good gray dryness mask (304df33 form, in-game
                    A/B'd): crowns 170 (dry, renders above water); the foot ramps
                    to 50% dryness (85) over ~12px below the waterline and HOLDS
                    to the base - the post grounds in the water bottom instead of
                    fading out; 0 outside the posts (water renders normally).
                    All three channels equal. HISTORY: v1 inverted (170 everywhere
                    = black tile); channel-split and Wube-format variants rendered
                    posts submerged - the dryness signal empirically follows the
                    uniform gray level. Vanilla's exact channel semantics remain
                    unknown (posila: effect maps are interpreted per-shader).
  pilings-blank.png fully transparent sheet (same dimensions) - arm C (mask only)
                    uses it as its spritesheet so the water-shader reaction to
                    the mask renders with NO post sprites at all.

Sheet structure (decoded from base): 64px columns = one slot per tile edge;
bands at y 0/576/1152/1728 hold 8 columns x 4 rotation rows of 64x128 pieces;
the o band (y 2304) holds 4 columns x 1 row of 64x64 pieces. The 8 columns are
the engine's randomization slots.

ANCHORING MODEL: the post's BASE is the anchor (it stands at the waterline);
the cap is derived (base - height). Placement tweaks are expressed as per-row
BASE_SHIFT_ROWS adjustments; weathering shortens posts from the cap down.

PANELS: overlay only. Stamping the background (x 1088) and mask (x 2176) panels
caused circles/zig-zag artifacts (the mask panel drives terrain-blend;
mask_enabled defaults true). Vanilla's water-shallow transition proves
overlay-only is valid; isolation arm C confirmed the artifacts live in the art
panels.

OPEN GUESSES (flagged for in-game A/B):
  BASE_SHIFT_ROWS = {0: 32} assumes rotation row 0 = north edge. If the wrong
  side shifted, flip to {2: 32}.
"""
from PIL import Image
import numpy as np, random, math

BASE = "/home/nmrp3/.local/share/factorio_2_dlc/data/base/graphics/terrain/water-transitions/"
PANELS = (0,)  # overlay panel ONLY (see docstring)
BANDS = [(0, 8, 128, 4), (576, 8, 128, 4), (1152, 8, 128, 4), (1728, 2, 128, 4), (2304, 4, 64, 1)]
BASE_SHIFT_ROWS = {0: 32}  # per-rotation-row base anchor adjustment (base = anchor;
                           # 32px = half a tile on the 2x sheet)

P = dict(w=16, hmin=40, hmax=50, jpos=3, foot=115.0, seed=41000,
         dark=(70, 48, 26), lite=(224, 186, 122), cap=(238, 204, 142), capedge=(184, 144, 90),
         wf=0.18, wfac=0.72, rings=True)

DRY = 170.0       # mask gray dryness: 170 = dry (empirically the working form)
FOOT_DRY = 0.5    # foot holds at 50% dryness - grounds the post in the water bottom
FOOT_RAMP = 12    # px over which the dryness ramps 170 -> 50% below the waterline

van = np.asarray(Image.open(BASE + "landfill.png").convert("RGBA")).astype(np.float32)
alpha2 = van[..., 3]

def npv(c): return np.array(c, np.float32)

def draw_post(cv, px, base_y, y_min, h, w, p):
    rx = w / 2.0
    ry = max(int(rx * 0.55), 3)
    cy_cap = max(int(base_y - h), y_min) + ry
    x0 = int(px - rx)
    for x in range(x0, x0 + w):                        # body below the cap
        t = (x - x0 + 0.5) / w
        col = npv(p["dark"]) + (npv(p["lite"]) - npv(p["dark"])) * ((1 - abs(t - 0.5) * 2) ** 0.7)
        for y in range(int(cy_cap), int(base_y)):
            frac = (y - y_min) / max(base_y - y_min, 1)
            a = 255.0 if frac < 0.5 else 255.0 - (frac - 0.5) / 0.5 * (255.0 - p["foot"])
            cv[y, x, :3], cv[y, x, 3] = col, a
    for dy in range(-ry, ry + 1):                      # elliptical cut face
        hw = rx * math.sqrt(max(1.0 - (dy / ry) ** 2, 0.0))
        xa, xb = int(px - hw), int(px + hw)
        cv[cy_cap + dy, xa:xb + 1, :3] = npv(p["cap"]) + (npv(p["capedge"]) - npv(p["cap"])) * (abs(dy) / ry)
        cv[cy_cap + dy, xa:xb + 1, 3] = 255.0
    if p["rings"]:                                     # wood rings on the cut face
        for fr in (0.55, 0.28):
            ring = npv(p["capedge"]) * 0.75
            for t in np.linspace(0, 2 * math.pi, 48):
                x, y = int(px + fr * rx * math.cos(t)), int(cy_cap + fr * ry * math.sin(t))
                if 0 <= y < cv.shape[0] and 0 <= x < cv.shape[1]:
                    cv[y, x, :3] = ring

art = np.zeros((2368, 3200, 4), np.float32)
mask = np.zeros((2368, 512), np.float32)
n = 0
for y0, cols, ch, rows in BANDS:
    for r in range(rows):
        ry0 = y0 + r * 128
        for c in range(cols):
            cx0 = c * 64
            rng = random.Random(P["seed"] + y0 * 31 + r * 7 + c)
            ca = alpha2[ry0:ry0 + ch, cx0:cx0 + 64]
            ys, xs = np.nonzero(ca > 128)
            if len(ys) == 0: continue
            px_rel = min(max(int(xs.mean()) + rng.randint(-P["jpos"], P["jpos"]), 14), 50)
            col_a = ca[:, px_rel]
            base_rel = min(int(np.nonzero(col_a > 128)[0].max()) + 1 + rng.randint(-2, 2), ch - 2)
            base_rel = min(base_rel + BASE_SHIFT_ROWS.get(r, 0), ch - 2)
            w = P["w"] + rng.randint(-2, 2)
            h = min(rng.randint(P["hmin"], P["hmax"]), base_rel - 10)
            if rng.random() < P["wf"]: h = int(h * P["wfac"])
            bx, by = cx0 + px_rel, ry0 + base_rel
            draw_post(art, bx, by, ry0, h, w, P)
            # mask: crown fully dry; foot ramps to 50% dryness and HOLDS to the
            # base (the post grounds in the water bottom, never fades to zero)
            rx = w / 2.0; ry = max(int(rx * 0.55), 3)
            cy_cap = max(int(by - h), ry0) + ry
            xa, xb = max(bx - int(rx), 0), min(bx + int(rx) + 1, 512)
            for dy in range(-ry, ry + 1):
                hw = int(rx * math.sqrt(max(1.0 - (dy / ry) ** 2, 0.0)))
                mask[cy_cap + dy, max(bx - hw, 0):min(bx + hw + 1, 512)] = DRY
            top = max(int(by - h), ry0)
            mid = int(by - h * 0.5)
            mask[top + ry:mid, xa:xb] = DRY
            for i, y in enumerate(range(mid, int(by))):
                f = min(1.0, (i + 1) / FOOT_RAMP)
                mask[y, xa:xb] = DRY * (1.0 - FOOT_DRY * f)
            n += 1

Image.fromarray(art.clip(0, 255).astype(np.uint8), "RGBA").save("pilings-exp.png")
m = np.zeros((2368, 512, 4), np.float32)
m[..., 0] = m[..., 1] = m[..., 2] = mask
m[..., 3] = 255.0
Image.fromarray(m.clip(0, 255).astype(np.uint8), "RGBA").save("pilings-mask.png")
Image.new("RGBA", (3200, 2368), (0, 0, 0, 0)).save("pilings-blank.png")
print(f"pilings-exp.png: {n} posts (pilings only, no foam); "
      f"pilings-mask.png: gray, foot holds at {int(DRY * (1 - FOOT_DRY))}; pilings-blank.png")
