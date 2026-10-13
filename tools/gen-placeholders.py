#!/usr/bin/env python3
"""Generates the ford post sheets - SQUARE 64x64 transition pieces.

  pilings-exp.png   THE post sheet (arms A and B): 2/3-size posts, wood rings on
                    the cut faces, softer shading. Contains ONLY the pilings - no
                    painted foam (foam belongs in a layer the water shader
                    interacts with; revisit once basic visuals are correct).
  pilings-mask.png  the gray dryness mask, same 64x64 piece grid: crowns 170 (dry,
                    renders above water); the foot ramps to 50% dryness (85) over
                    ~12px below the waterline and HOLDS to the base - the post
                    grounds in the water bottom; 0 outside the posts.
  pilings-blank.png fully transparent sheet - arm C (mask only).

SQUARE PIECES (user decision after the tall-piece placement experiments):
tile_height defaults to 1, so every piece is 64x64 = exactly one water tile.
One post per piece, drawn base-near-the-cell-bottom, crown filling the cell
upward - fully contained, so nothing can be clipped by neighbouring pieces and
no two-tile extension ambiguity exists. The four rotation rows stride 64px
within each band; each direction's POSITION ANCHOR still comes from the vanilla
shore art row at y0 + r*128 (the 128px-stride rows), while the post is DRAWN
into the 64px window at y0 + r*64 that the engine reads for that direction.

Sheet structure: 64px columns = one slot per tile edge (8 = randomization
slots; 2 for u; 4 for o). Bands at y 0/576/1152/1728 (4 direction windows of
64px each) and y 2304 (1 window, o). The mask sheet is 512 wide - one copy of
the grid, aligned piece-for-piece with the art's overlay panel (the art sheet
is overlay-panel ONLY: stamping the background/mask panels caused blend
artifacts, and vanilla's water-shallow transition is overlay-only too).
"""
from PIL import Image
import numpy as np, random, math

BASE = "/home/nmrp3/.local/share/factorio_2_dlc/data/base/graphics/terrain/water-transitions/"
BANDS = [(0, 8, 4), (576, 8, 4), (1152, 8, 4), (1728, 2, 4), (2304, 4, 1)]  # (band y, columns, direction rows)
CELL = 64          # square piece, px on the 2x sheet (= 1 water tile)

P = dict(w=16, hmin=38, hmax=46, jpos=3, foot=115.0, seed=41000,
         dark=(70, 48, 26), lite=(224, 186, 122), cap=(238, 204, 142), capedge=(184, 144, 90),
         wf=0.18, wfac=0.72, rings=True)

DRY = 170.0        # mask gray dryness: 170 = dry (empirically the working form)
FOOT_DRY = 0.5     # foot holds at 50% dryness - grounds the post in the water bottom
FOOT_RAMP = 12     # px over which the dryness ramps 170 -> 50% below the waterline
DECK_DRY = 85.0    # baseline dryness AWAY from the posts (else-0 rendered the water
                   # surface pass at full density over the whole deck = the "ford
                   # shadow"); 85 = the held-foot value = shallow half-density water
                   # over the bed. Feet ramp down to this instead of to 0.

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
mask = np.full((2368, 512), DECK_DRY, np.float32)
n = 0
for y0, cols, rows in BANDS:
    for r in range(rows):
        anchor_y = y0 + r * 128                        # vanilla art row for this direction
        win_y = y0 + r * CELL                          # the 64px window the engine reads
        for c in range(cols):
            cx0 = c * 64
            rng = random.Random(P["seed"] + y0 * 31 + r * 7 + c)
            ca = alpha2[anchor_y:anchor_y + 64, cx0:cx0 + 64]
            ys, xs = np.nonzero(ca > 128)
            if len(ys) == 0: continue
            px_rel = min(max(int(xs.mean()) + rng.randint(-P["jpos"], P["jpos"]), 14), 50)
            base_rel = CELL - 8 + rng.randint(-2, 2)   # base near the window bottom
            w = P["w"] + rng.randint(-2, 2)
            h = min(rng.randint(P["hmin"], P["hmax"]), base_rel - 12)
            if rng.random() < P["wf"]: h = int(h * P["wfac"])
            bx, by = cx0 + px_rel, win_y + base_rel
            draw_post(art, bx, by, win_y, h, w, P)
            # mask: crown fully dry; foot ramps to 50% dryness and HOLDS to the base
            rx = w / 2.0; ry = max(int(rx * 0.55), 3)
            cy_cap = max(int(by - h), win_y) + ry
            xa, xb = max(bx - int(rx), 0), min(bx + int(rx) + 1, 512)
            for dy in range(-ry, ry + 1):
                hw = int(rx * math.sqrt(max(1.0 - (dy / ry) ** 2, 0.0)))
                mask[cy_cap + dy, max(bx - hw, 0):min(bx + hw + 1, 512)] = DRY
            mid = int(by - h * 0.5)
            mask[cy_cap:mid, xa:xb] = DRY
            for i, y in enumerate(range(mid, int(by))):
                f = min(1.0, (i + 1) / FOOT_RAMP)
                mask[y, xa:xb] = DECK_DRY + (DRY - DECK_DRY) * (1.0 - FOOT_DRY * f)
            n += 1

Image.fromarray(art.clip(0, 255).astype(np.uint8), "RGBA").save("pilings-exp.png")
m = np.zeros((2368, 512, 4), np.float32)
m[..., 0] = m[..., 1] = m[..., 2] = mask
m[..., 3] = 255.0
Image.fromarray(m.clip(0, 255).astype(np.uint8), "RGBA").save("pilings-mask.png")
Image.new("RGBA", (3200, 2368), (0, 0, 0, 0)).save("pilings-blank.png")
print(f"pilings-exp.png: {n} posts in 64x64 pieces; pilings-mask.png (gray, foot holds at "
      f"{int(DRY * (1 - FOOT_DRY))}); pilings-blank.png")
