#!/usr/bin/env python3
"""Generates the ford post sheets.

  pilings.png      gold standard art (py-ford-flooded) - DO NOT TUNE, keep byte-stable
  pilings-exp.png  experiment posts (exp-1 and exp-2): 2/3 size, wood rings on the
                   cut faces, softer shading (anti-"barcode"), north-facing posts
                   shifted half a tile south so the tops sit closer to the planks
  pilings-mask.png water-effect strength mask for exp-2: 0 over the post crowns
                   (dry - sprite shows crisp), 170 everywhere else (full water
                   effect; the shader's waterline wraps each post at the crown/foot
                   boundary = lapping). Polarity measured from vanilla's
                   water-dirt-mask: land side ~34 (weak), lap zone ~107, max 170.

Sheet structure (decoded from base): 64px columns = one slot per tile edge;
bands at y 0/576/1152/1728 hold 8 columns x 4 rotation rows of 64x128 pieces;
the o band (y 2304) holds 4 columns x 1 row of 64x64 pieces. The 8 columns are
the engine's randomization slots.

ANCHORING MODEL: the post's BASE is the anchor (it stands at the waterline);
the cap is derived (base - height). Placement tweaks are expressed as per-row
BASE_SHIFT_ROWS adjustments; weathering shortens posts from the cap down.

OPEN GUESSES (flagged for in-game A/B):
  BASE_SHIFT_ROWS = {0} assumes rotation row 0 = north edge (its base sits half
  a tile too far from the planks). If exp-1 shows the wrong side shifted, flip
  to {2}.
"""
from PIL import Image
import numpy as np, random, math

BASE = "/home/nmrp3/.local/share/factorio_2_dlc/data/base/graphics/terrain/water-transitions/"
PANELS = (0, 1088, 2176)
BANDS = [(0, 8, 128, 4), (576, 8, 128, 4), (1152, 8, 128, 4), (1728, 2, 128, 4), (2304, 4, 64, 1)]
BASE_SHIFT_ROWS = {0: 32}  # per-rotation-row base anchor adjustment (base = anchor;
                           # 32px = half a tile on the 2x sheet)

GOLD = dict(w=24, hmin=58, hmax=74, jpos=4, foot=115.0, seed=9000,
            dark=(44, 29, 15), lite=(218, 176, 114), cap=(232, 196, 134), capedge=(168, 128, 76),
            wf=0.18, wfac=0.72, rings=False)
EXP = dict(w=16, hmin=40, hmax=50, jpos=3, foot=115.0, seed=41000,
           dark=(70, 48, 26), lite=(224, 186, 122), cap=(238, 204, 142), capedge=(184, 144, 90),
           wf=0.18, wfac=0.72, rings=True)

FOAM = np.array([205, 226, 232], np.float32)
WATER_VALUE = 170.0   # "full water effect" per vanilla's own mask scale

van = np.asarray(Image.open(BASE + "landfill.png").convert("RGBA")).astype(np.float32)
alpha2 = van[..., 3]

def npv(c): return np.array(c, np.float32)

def draw_foam(cv, cx, cy, rx, ry, a):
    for t in np.linspace(0, 2 * math.pi, 90):
        for th in (0, 1):
            x, y = int(cx + rx * math.cos(t)) + th, int(cy + ry * math.sin(t)) + th
            if 0 <= y < cv.shape[0] and 0 <= x < cv.shape[1] and cv[y, x, 3] < a:
                cv[y, x, :3], cv[y, x, 3] = FOAM, a

def draw_post(cv, px, base_y, y_min, h, w, p):
    rx = w / 2.0
    ry = max(int(rx * 0.55), 3)
    cy_cap = max(int(base_y - h), y_min) + ry
    x0 = int(px - rx)
    for x in range(x0, x0 + w):
        t = (x - x0 + 0.5) / w
        col = npv(p["dark"]) + (npv(p["lite"]) - npv(p["dark"])) * ((1 - abs(t - 0.5) * 2) ** 0.7)
        for y in range(int(cy_cap), int(base_y)):
            frac = (y - y_min) / max(base_y - y_min, 1)
            a = 255.0 if frac < 0.5 else 255.0 - (frac - 0.5) / 0.5 * (255.0 - p["foot"])
            cv[y, x, :3], cv[y, x, 3] = col, a
    for dy in range(-ry, ry + 1):  # elliptical cut face
        hw = rx * math.sqrt(max(1.0 - (dy / ry) ** 2, 0.0))
        xa, xb = int(px - hw), int(px + hw)
        cv[cy_cap + dy, xa:xb + 1, :3] = npv(p["cap"]) + (npv(p["capedge"]) - npv(p["cap"])) * (abs(dy) / ry)
        cv[cy_cap + dy, xa:xb + 1, 3] = 255.0
    if p["rings"]:  # wood rings on the cut face
        for fr in (0.55, 0.28):
            ring = npv(p["capedge"]) * 0.75
            for t in np.linspace(0, 2 * math.pi, 48):
                x, y = int(px + fr * rx * math.cos(t)), int(cy_cap + fr * ry * math.sin(t))
                if 0 <= y < cv.shape[0] and 0 <= x < cv.shape[1]:
                    cv[y, x, :3] = ring

def gen(p, out, mask_out=None):
    art = np.zeros((2368, 3200, 4), np.float32)
    mask = np.full((2368, 512), WATER_VALUE, np.float32) if mask_out else None
    n = 0
    for y0, cols, ch, rows in BANDS:
        for r in range(rows):
            ry0 = y0 + r * 128
            for c in range(cols):
                cx0 = c * 64
                rng = random.Random(p["seed"] + y0 * 31 + r * 7 + c)
                ca = alpha2[ry0:ry0 + ch, cx0:cx0 + 64]
                ys, xs = np.nonzero(ca > 128)
                if len(ys) == 0: continue
                px_rel = min(max(int(xs.mean()) + rng.randint(-p["jpos"], p["jpos"]), 14), 50)
                col_a = ca[:, px_rel]
                base_rel = min(int(np.nonzero(col_a > 128)[0].max()) + 1 + rng.randint(-2, 2), ch - 2)
                base_rel = min(base_rel + BASE_SHIFT_ROWS.get(r, 0), ch - 2)
                w = p["w"] + rng.randint(-2, 2)
                h = min(rng.randint(p["hmin"], p["hmax"]), base_rel - 10)
                if rng.random() < p["wf"]: h = int(h * p["wfac"])
                bx, by = cx0 + px_rel, ry0 + base_rel
                top = max(int(by - h), ry0)
                for dx in PANELS:
                    draw_foam(art, bx + dx, by, 22, 9, 70); draw_foam(art, bx + dx, by, 14, 6, 110)
                    draw_post(art, bx + dx, by, ry0, h, w, p)
                if mask is not None:  # crown = dry, foot = water (single-panel sheet)
                    mid = int(by - h * 0.5)
                    rx = w / 2.0; ry = max(int(rx * 0.55), 3)
                    cy_cap = top + ry
                    for dy in range(-ry, ry + 1):
                        hw = int(rx * math.sqrt(max(1.0 - (dy / ry) ** 2, 0.0)))
                        mask[cy_cap + dy, max(bx - hw, 0):min(bx + hw + 1, 512)] = 0.0
                    mask[mid:int(by), max(bx - int(rx), 0):min(bx + int(rx) + 1, 512)] = 0.0
                n += 1
    Image.fromarray(art.clip(0, 255).astype(np.uint8), "RGBA").save(out)
    if mask is not None:
        m = np.zeros((2368, 512, 4), np.float32)
        m[..., 0] = m[..., 1] = m[..., 2] = mask
        m[..., 3] = 255.0
        Image.fromarray(m.clip(0, 255).astype(np.uint8), "RGBA").save(mask_out)
    print(f"{out}: {n} posts" + (f" (+ {mask_out})" if mask_out else ""))

gen(GOLD, "pilings.png")
gen(EXP, "pilings-exp.png", mask_out="pilings-mask.png")
