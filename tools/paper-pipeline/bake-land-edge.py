# bake-land-edge: the boards-land WATER EDGE = vanilla concrete's shore-piece
# LAYOUT (read straight off tiles.lua's concrete_transitions + concrete_layout)
# with OUR wood paint in the two picture channels (maintainer direction:
# "basically copy that but with wood boards where the concrete is", "side-on
# boards, looking very much like the stone trim"; "if the concrete doesn't do
# any heroics trying to color match the water, you don't need to" - verified:
# the background channel is neutral grey, the merge into water is pure alpha).
#
# The Lua's pixel map (concrete_layout(false,false,false), all shared by the
# three x-regions of the sheet):
#   overlay   x_offset    0 : the lip ON our tile - single course + halo
#                             blending up onto the land tile
#   background x_offset 1024 : the curb continuing UNDER the water line -
#                             double course + alpha slide-off drawn on the
#                             layer below so the water shades it
#   mask      x_offset 2048 : flat grey value zones (255/0/44...) - shore
#                             contour/darkening value maps (functional data,
#                             passed through bit-identical, never wood-painted)
#   cells 64 wide x 128 tall (1 tile wide x 2 tiles tall at scale 0.5);
#   bands (count, vanilla y): inner 16@0, outer 8@576, side 16@1152,
#   u 4@1728, o 4@2304; each band = count cols x 4 rows (o: 1 row).
# Output: mod/graphics/boards-land-edge.png 3072x2176 (tight band y
#   0/512/1024/1536/2048, slack alpha exactly 0; o band cells 64 tall).
# Alpha is preserved BIT-EXACT in every channel; only overlay+background RGB
# is remapped stone->wood through the boards-land palette.
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
G = os.path.join(ROOT, "mods", "water-ford", "mod", "graphics")
PROV = os.path.join(ROOT, ".cache", "ford-factory", "provenance")
VAN = "/home/nmrp3/.local/share/factorio_2_dlc/data/base/graphics/terrain/water-transitions/concrete.png"

CELL_W, CELL_H = 64, 128
# (vanilla band y, count, rot rows) -> our tight band y
BANDS = [(0, 16, 4), (576, 8, 4), (1152, 16, 4), (1728, 4, 4), (2304, 4, 1)]
# v3: GEOMETRY-CLONE of the vanilla sheet - identical canvas, identical band
# y-fields and inter-band gaps (the tight 512/128 spacing of v2 is the prime
# suspect for the rows-2/3 direction breakage the maintainer saw); tighten
# later only with proven row semantics.
OURS_Y = [0, 576, 1152, 1728, 2304]
# channels: (vanilla x_offset, ours x_offset, paint?) - mask never painted
CHANNELS = [(0, 0, True), (1024, 1024, True), (2048, 2048, False)]
CANV_W, CANV_H = 3072, 2368

src = np.asarray(Image.open(VAN).convert("RGBA"))
land = np.asarray(Image.open(os.path.join(G, "boards-land.png")).convert("RGB"))

# --- wood ramp: stone range -> our INTERIOR plank range (percentile means,
# not the extremes: p100 highlight / p0 shadow pixels would crush the tone) ---
Wt = np.array([0.299, 0.587, 0.114], np.float32)

def pct_anchor(px, p):
    l = px.astype(np.float32) @ Wt
    t = np.percentile(l, p)
    sel = np.abs(l - t) < 1.5
    return px[sel].mean(0).astype(np.float32)

SH = land.reshape(-1, 3)
lp = SH[SH.sum(1) > 30]
stone = src[:2304, :1024, :3][src[:2304, :1024, 3] == 255]   # overlay channel only
lo = pct_anchor(lp, 2); hi = pct_anchor(lp, 98)
slo = pct_anchor(stone, 2); shi = pct_anchor(stone, 98)
lo_l = float(lo @ Wt); hi_l = float(hi @ Wt)
slo_l = float(slo @ Wt); shi_l = float(shi @ Wt)
print(f"wood ramp: dark {lo.round(0)} lum {lo_l:.0f} -> light {hi.round(0)} lum {hi_l:.0f}")
print(f"stone overlay range mapped: lum {slo_l:.1f} -> {shi_l:.1f}")

out = np.zeros((CANV_H, CANV_W, 4), np.uint8)
n = 0
alpha_drift = 0
wood_drift = 0
for (vy, count, rows), oy in zip(BANDS, OURS_Y):
    for vx, ox, paint in CHANNELS:
        for r in range(rows):
            sy = vy + r * CELL_H
            dy = oy + r * CELL_H
            for c in range(count):
                cell = src[sy:sy + CELL_H, vx + c * CELL_W:vx + (c + 1) * CELL_W]
                if cell.shape[0] < CELL_H:
                    # o band: vanilla rows are 64 tall (tile_height default 1);
                    # clone verbatim height - no synthetic padding
                    pass
                cell2 = np.zeros_like(cell)
                if paint:
                    t = np.clip((cell[..., :3].astype(np.float32) @ Wt - slo_l) / (shi_l - slo_l), 0.0, 1.0)[..., None]
                    wood = lo[None, None, :] + t * (hi[None, None, :] - lo[None, None, :])
                    cell2[..., :3] = np.clip(wood + 0.5, 0, 255).astype(np.uint8)
                    wd = int(np.abs(cell2[..., :3].astype(int) - cell[..., :3].astype(int)).mean())
                    wood_drift = max(wood_drift, wd)
                else:
                    cell2[..., :3] = cell[..., :3]          # grey value maps, bit-identical
                cell2[..., 3] = cell[..., 3]                # alpha bit-exact
                out[dy:dy + CELL_H, ox + c * CELL_W:ox + (c + 1) * CELL_W] = cell2
                n += 1
                alpha_drift = max(alpha_drift, int(np.abs(cell2[..., 3].astype(int) - cell[..., 3].astype(int)).max()))
expect = (sum(c * r for _, c, r in BANDS)) * 3
print(f"pieces written: {n} (expect {expect}) alpha drift: {alpha_drift} wood drift(painted): {wood_drift}")

img = Image.fromarray(out, "RGBA")
img.save(os.path.join(G, "boards-land-edge.png"))
img.save(os.path.join(PROV, "boards-land-edge-sheet.png"))
# slack = everything outside the count x rot-row windows must be alpha 0
# (keep = UNION over all bands - a per-band keep would count the other bands'
# content as slack and false-report 255)
keep = np.zeros((CANV_H, CANV_W), bool)
for (vy, count, rows), oy in zip(BANDS, OURS_Y):
    for vx, ox, paint in CHANNELS:
        for r in range(rows):
            keep[oy + r * CELL_H:oy + (r + 1) * CELL_H, ox:ox + count * CELL_W] = True
m = out[..., 3][~keep]
slack = int(m.max()) if m.size else 0
# piece-window sanity: each art band must carry content in its windows
for (vy, count, rows), oy in zip(BANDS, OURS_Y):
    win = np.zeros((CANV_H, CANV_W), bool)
    for vx, ox, paint in CHANNELS:
        if not paint:
            continue
        for r in range(rows):
            win[oy + r * CELL_H:oy + (r + 1) * CELL_H, ox:ox + count * CELL_W] = True
    a = out[..., 3][win]
    if a.size and int(a.max()) == 0:
        raise RuntimeError(f"art band at our y{oy} has no content - bake broken")
print("slack alpha max:", slack, "(0 expected = engine-never-sampled pixels empty)")
print("canvas:", CANV_W, "x", CANV_H, "=", CANV_W * CANV_H * 4 // 1024 // 1024, "MB RGBA")