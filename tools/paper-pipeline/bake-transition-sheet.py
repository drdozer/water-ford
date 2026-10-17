# bake-transition-sheet: the ford transition asset = OUR 64x64 frames, pasted.
# Art sheet  = icons64-wood frames pasted 1:1 into the 108 transition cells
#              (inner@0 8x4, outer@576 8x4, side@1152 8x4, u@1728 2x4, o@2304 4x1;
#              cell k of the gen-textures loop order takes frame k). The POLE
#              ONLY - the cast shadow is NEVER baked into the art pixels; it
#              lives only in its own strip/sheet.
# Mask sheet = masks64 frames pasted at the same cells (the gray dryness data -
#              the engine consumes art and dryness map as two separate files).
# Shadow sheet = shadows64 frames pasted at the same cells (the cast shadow as
#              its own sprites; NOT registered in the game - awaiting a proper
#              own-layer mechanism).
# Pure arrangement: bit-copies, no filtering, no compositing, no value edits.
import os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
BASE = os.path.join(ROOT, ".cache", "ford-factory")
G = os.path.join(ROOT, "mods", "water-ford", "mod", "graphics")
# the visual + shadow sheets are bake intermediates; only the transition MASK
# is a live mod asset and keeps writing into mod/graphics.
INTER = os.path.join(ROOT, ".cache", "ford-factory", "intermediates")
os.makedirs(INTER, exist_ok=True)

BANDS = [(0, 8, 4), (576, 8, 4), (1152, 8, 4), (1728, 2, 4), (2304, 4, 1)]
N = 108
CELL = 64

art = np.zeros((2368, 3200, 4), np.uint8)
msk = np.zeros((2368, 512, 4), np.uint8)
shd = np.zeros((2368, 3200, 4), np.uint8)
msk[..., 3] = 255

k = 0
for y0, cols, rows in BANDS:
    for r in range(rows):
        win_y = y0 + r * CELL
        for c in range(cols):
            k += 1
            cx0 = c * CELL
            fa = np.asarray(Image.open(os.path.join(BASE, "icons64-wood", f"frame_{k:03d}.png")).convert("RGBA"))
            fm = np.asarray(Image.open(os.path.join(BASE, "masks64", f"frame_{k:03d}.png")).convert("RGBA"))
            if fa.shape != (CELL, CELL, 4) or fm.shape != (CELL, CELL, 4):
                raise RuntimeError(f"frame {k}: wrong size {fa.shape}")
            art[win_y:win_y + CELL, cx0:cx0 + CELL] = fa
            msk[win_y:win_y + CELL, cx0:cx0 + CELL, :3] = fm[..., :3]
            fs = np.asarray(Image.open(os.path.join(BASE, "shadows64", f"frame_{k:03d}.png")).convert("RGBA"))
            if fs.shape != (CELL, CELL, 4):
                raise RuntimeError(f"shadow frame {k}: wrong size {fs.shape}")
            shd[win_y:win_y + CELL, cx0:cx0 + CELL] = fs
if k != N:
    raise RuntimeError(f"pasted {k} pieces, expected {N}")

a_out = os.path.join(INTER, "pilings-transition.png")
m_out = os.path.join(G, "pilings-transition-mask.png")
s_out = os.path.join(INTER, "pilings-transition-shadow.png")
Image.fromarray(art, "RGBA").save(a_out)
Image.fromarray(msk, "RGBA").save(m_out)
Image.fromarray(shd, "RGBA").save(s_out)

# verification: every occupied cell region bit-equal to its source frame;
# every empty region exactly zero (art alpha 0 / mask gray 0).
bad = []
for y0, cols, rows in BANDS:
    for r in range(rows):
        win_y = y0 + r * CELL
        for c in range(cols):
            cx0 = c * CELL
            kk = sum(bc * br for (by, bc, br) in BANDS[:BANDS.index((y0, cols, rows))]) + r * cols + c + 1
            fa = np.asarray(Image.open(os.path.join(BASE, "icons64-wood", f"frame_{kk:03d}.png")).convert("RGBA"))
            fm = np.asarray(Image.open(os.path.join(BASE, "masks64", f"frame_{kk:03d}.png")).convert("RGBA"))
            if not np.array_equal(art[win_y:win_y + CELL, cx0:cx0 + CELL], fa):
                bad.append(("art", kk))
            fs = np.asarray(Image.open(os.path.join(BASE, "shadows64", f"frame_{kk:03d}.png")).convert("RGBA"))
            if not np.array_equal(shd[win_y:win_y + CELL, cx0:cx0 + CELL], fs):
                bad.append(("shadow", kk))
            mc = msk[win_y:win_y + CELL, cx0:cx0 + CELL, 0]
            if not (np.array_equal(mc, fm[..., 0]) and np.array_equal(msk[win_y:win_y + CELL, cx0:cx0 + CELL, 1], fm[..., 0])
                    and np.array_equal(msk[win_y:win_y + CELL, cx0:cx0 + CELL, 2], fm[..., 0])):
                bad.append(("mask", kk))
if bad:
    raise RuntimeError(f"cell mismatch: {bad[:5]}")
# the unused sheet area must be all-zero
rest = art.copy()
srest = shd.copy()
for y0, cols, rows in BANDS:
    for r in range(rows):
        rest[y0 + r * CELL:y0 + r * CELL + CELL, 0:cols * CELL] = 0
        srest[y0 + r * CELL:y0 + r * CELL + CELL, 0:cols * CELL] = 0
if rest.any() or srest.any():
    raise RuntimeError("art/shadow sheets have stray pixels outside the transition cells")
print(f"TRANSITION SHEETS: art {art.shape[1]}x{art.shape[0]} mask {msk.shape[1]}x{msk.shape[0]} shadow {shd.shape[1]}x{shd.shape[0]}")
print(f"{N}/{N} cells bit-equal to frames (art + mask); unused area clean")
print("TRANSITION BAKE DONE")