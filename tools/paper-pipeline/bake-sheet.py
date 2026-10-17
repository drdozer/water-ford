#!/usr/bin/env python3
# bake-sheet: repack the verified icon strip into the spritesheet + the
#   12x9 row-major grid of 64px cells: cell (col,row) = frame_(1+row*12+col).
#   companion GRAY WETNESS sheet (separate data block, not the piling alpha).
#   Verification: every cell BIT-EQUAL to its source frame (a pure repack -
#   chart pixels remain Blender output only). Output RGBA (alpha = silhouette).
import numpy as np
from PIL import Image
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
for _ in range(4):                     # paper-pipeline -> tools -> water-ford -> mods -> superproject
    ROOT = os.path.dirname(ROOT)
BASE = os.path.join(ROOT, ".cache", "ford-factory")
out = os.path.join(BASE, "sheet"); os.makedirs(out, exist_ok=True)
COLS, ROWS, CELL, N = 12, 9, 128, 108

sheet = Image.new("RGBA", (COLS * CELL, ROWS * CELL), (0, 0, 0, 0))
frames = []
for i in range(N):
    frames.append(Image.open(os.path.join(BASE, "icons128-wood", f"frame_{i+1:03d}.png")).convert("RGBA"))
for r in range(ROWS):
    for c in range(COLS):
        sheet.paste(frames[r * COLS + c], (c * CELL, r * CELL))
path = os.path.join(out, "piling-sheet-128.png")
sheet.save(path)

# grey wetness mask sheet: SAME grid, SEPARATE block of data (old pilings-mask
# convention: 170 dry crown -> 85 foot, 0 outside). Not an alpha channel.
mask_frames = []
for i in range(N):
    mask_frames.append(Image.open(os.path.join(BASE, "masks64", f"frame_{i+1:03d}.png")).convert("RGBA"))
mask_sheet = Image.new("RGBA", (COLS * CELL, ROWS * CELL), (0, 0, 0, 0))
for r in range(ROWS):
    for c in range(COLS):
        mask_sheet.paste(mask_frames[r * COLS + c], (c * CELL, r * CELL))
mpath = os.path.join(out, "piling-mask-sheet-64.png")
mask_sheet.save(mpath)
mchk = np.asarray(Image.open(mpath).convert("RGBA"))
mok = True
for i in range(N):
    c, r = (i % COLS) * CELL, (i // COLS) * CELL
    cell = mchk[r:r+CELL, c:c+CELL]
    if not np.array_equal(cell, np.asarray(mask_frames[i])):
        mok = False; print(f"MASK CELL MISMATCH row {r} col {c} (frame {i+1})")
print("mask sheet:", mask_sheet.size, "| cells bit-equal to mask frames:", mok,
      "| grays:", sorted({int(v) for v in np.unique(mchk[..., 0])})[:8])

# shadow block: same grid, separate data (the key-light cast shadow east of
# the piling, rendered from the SHADOW view layer through the asset camera).
shadow_frames = []
for i in range(N):
    shadow_frames.append(Image.open(os.path.join(BASE, "shadows64", f"frame_{i+1:03d}.png")).convert("RGBA"))
shadow_sheet = Image.new("RGBA", (COLS * CELL, ROWS * CELL), (0, 0, 0, 0))
for r in range(ROWS):
    for c in range(COLS):
        shadow_sheet.paste(shadow_frames[r * COLS + c], (c * CELL, r * CELL))
spath = os.path.join(out, "piling-shadow-sheet-64.png")
shadow_sheet.save(spath)
s_ok = True
for i in range(N):
    c, r = (i % COLS) * CELL, (i // COLS) * CELL
    cell = shadow_sheet.crop((c, r, c + CELL, r + CELL))
    if not np.array_equal(cell, shadow_frames[i]):
        s_ok = False; print(f"SHADOW CELL MISMATCH row {r} col {c} (frame {i+1})")
print("shadow sheet:", shadow_sheet.size, "| cells bit-equal to shadow frames:", s_ok)

chk = np.asarray(Image.open(path).convert("RGBA"))
ok = True
for i in range(N):
    c, r = (i % COLS) * CELL, (i // COLS) * CELL
    cell = chk[r:r+CELL, c:c+CELL]
    if not np.array_equal(cell, np.asarray(frames[i])):
        ok = False; print(f"CELL MISMATCH row {r} col {c} (frame {i+1})")
print("sheet:", sheet.size, "| RGBA:", Image.open(path).mode, "| cells bit-equal to frames:", ok)
print(f"alpha: min {chk[...,3].min()} max {chk[...,3].max()} | "
      f"cells fully populated: {all((chk[r:r+CELL, c:c+CELL, 3] > 230).any() for r in range(0, ROWS*CELL, CELL) for c in range(0, COLS*CELL, CELL))}")