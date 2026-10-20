# bake-land-trim: the wooden-flooring LAND TRIM = vanilla concrete's variant
# transition sheets (the land-to-land edge system, tiles.lua
# concrete.variants.transition) with OUR wood paint on the overlay art and
# the grey/alpha masks passed through bit-identical.
#
# Audit (maintainer round-20/21): the land edges hang off variants.transition
# - overlay_layout + mask_layout, counts 16/8/16/4/4, square 64x64 cells
# (1x1 tile at scale 0.5), 4 rotation rows per sheet (o: 1 row). Sheets are
# perfectly packed (no slack). The promotion pass cleared the variant
# transition (vanilla grey stone trim would be wrong on boards), so boards
# vs grass/dirt/sand currently show a hard cut - this bake + the wiring in
# data-updates.lua is the queued "land TRIM" increment.
#
# Per piece type: __base__/graphics/terrain/concrete/<piece>.png (overlay,
# wood-remapped) + <piece>-mask.png (value map, verbatim). Output 10 files:
# mod/graphics/wooden-flooring-trim-<piece>.png and -mask.png.
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
G = os.path.join(ROOT, "mods", "water-ford", "mod", "graphics")
PROV = os.path.join(ROOT, ".cache", "ford-factory", "provenance")
VAN = "/home/nmrp3/.local/share/factorio_2_dlc/data/base/graphics/terrain/concrete"

# (piece name, count) - vanilla overlay/mask dims are exactly rows x count*64
PIECES = [("inner-corner", 16), ("outer-corner", 8), ("side", 16), ("u", 4), ("o", 4)]

src = np.asarray(Image.open(os.path.join(G, "wooden-flooring.png")).convert("RGB"))
SH = src.reshape(-1, 3)
lp = SH[SH.sum(1) > 30]
Wt = np.array([0.299, 0.587, 0.114], np.float32)

def pct_anchor(px, p):
    l = px.astype(np.float32) @ Wt
    t = np.percentile(l, p)
    sel = np.abs(l - t) < 1.5
    return px[sel].mean(0).astype(np.float32)

lo = pct_anchor(lp, 2); hi = pct_anchor(lp, 98)
lo_l = float(lo @ Wt); hi_l = float(hi @ Wt)
print(f"wood ramp: dark {lo.round(0)} lum {lo_l:.0f} -> light {hi.round(0)} lum {hi_l:.0f}")

n = 0
for piece, count in PIECES:
    ov = np.asarray(Image.open(f"{VAN}/concrete-{piece}.png").convert("RGBA"))
    mk = np.asarray(Image.open(f"{VAN}/concrete-{piece}-mask.png").convert("RGBA"))
    rows = ov.shape[0] // 64
    # verbatim-dims check: cols*64 wide, rows*64 tall, rows = 4 (o: 1)
    assert ov.shape[1] == count * 64, f"{piece}: width {ov.shape[1]} != count*64"
    expect_rows = 1 if piece == "o" else 4
    assert rows == expect_rows, f"{piece}: rows {rows} != {expect_rows}"
    assert mk.shape == ov.shape, f"{piece}: mask dims {mk.shape} != overlay {ov.shape}"
    # wood-remap overlay (same ramp as the bumper edge), alpha bit-exact
    t = np.clip((ov[..., :3].astype(np.float32) @ Wt - 32.0) / 103.2, 0.0, 1.0)[..., None]
    wood = lo[None, None, :] + t * (hi[None, None, :] - lo[None, None, :])
    ov2 = ov.copy()
    ov2[..., :3] = np.clip(wood + 0.5, 0, 255).astype(np.uint8)
    Image.fromarray(ov2, "RGBA").save(f"{G}/wooden-flooring-trim-{piece}.png")
    Image.fromarray(ov2, "RGBA").save(f"{PROV}/wooden-flooring-trim-{piece}.png")
    # mask: pass through bit-identical (functional value map)
    Image.fromarray(mk, "RGBA").save(f"{G}/wooden-flooring-trim-{piece}-mask.png")
    n += 1
    print(f"{piece}: overlay {ov.shape[1]}x{ov.shape[0]} wood-remapped, mask verbatim")
assert n == 5
print(f"TRIM DONE: 5 overlay sheets wood-painted + 5 masks verbatim -> mod/graphics/")