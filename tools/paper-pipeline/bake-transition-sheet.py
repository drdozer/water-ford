# bake-transition-sheet: the ford transition asset = OUR frames, pasted.
#
# 2026-10-17 density pass (maintainer order): the strip is re-rendered at
# 128px cells (2x the 64px era) and the sheets move onto TIGHT canvases -
# every pixel outside the engine's piece windows is dropped. The canvas
# geometry follows from the layout numbers in data-updates.lua:
#   art window  = 128x128 (scale 0.25 -> 32 world px, double the old density)
#   band y (art):    inner 0, outer 512, side 1024, u 1536, o 2048  (4 rot rows)
#   art canvas:      1024x2176 (o band = 4 cols x 1 rot row)
#   mask window = 64x64 (scale 0.5 - wetness granularity UNCHANGED)
#   band y (mask):   inner 0, outer 256, side 512, u 768, o 1024
#   mask canvas:     512x1088
# Piece order = the gen-textures loop order (frame k -> cell k). Slack inside
# the art canvas (x past the count windows in the u/o bands) stays fully
# transparent: the engine never samples it (proven: the 512-wide mask has
# always anchored identically to the 3200-wide visual sheet).
#
# Art sheet (transparent poles)      -> .cache/ford-factory/intermediates/
# Composite sheet (P1, LIVE)         -> mod/graphics/pilings-composite.png
#   P1 recipe bit-verified against the live 64px composite:
#   cell = alpha_composite(flat water (17,114,129,255), icon frame) - the
#   flat-water cover hides the engine's shore pre-darkening (the round-12
#   lesson, maintainer-committed as P1).
# Mask sheet (LIVE)                  -> mod/graphics/pilings-transition-mask.png
#   bit-copied masks64 frames (64px, spec dryness, else-region 0 = black,
#   the state reverted to after the else-170 black-cell incident).
# The cast-shadow sheet is retired (background_enabled=false, route (a)):
# the last shadow artifact is the moved .cache/intermediates copy.
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
BASE = os.path.join(ROOT, ".cache", "ford-factory")
G = os.path.join(ROOT, "mods", "water-ford", "mod", "graphics")
INTER = os.path.join(BASE, "intermediates")
os.makedirs(INTER, exist_ok=True)

N = 108
CELL_A = 128          # art window at the new density
CELL_M = 64           # mask window (wetness granularity unchanged)
WATER = (17, 114, 129, 255)

# (band y, cols, rot rows) in ART px and MASK px
BANDS_A = [(0, 8, 4), (512, 8, 4), (1024, 8, 4), (1536, 2, 4), (2048, 4, 1)]
BANDS_M = [(0, 8, 4), (256, 8, 4), (512, 8, 4), (768, 2, 4), (1024, 4, 1)]

ART_W, ART_H = 1024, 2176
MSK_W, MSK_H = 512, 1088

art = np.zeros((ART_H, ART_W, 4), np.uint8)                 # transparent pieces
comp = np.zeros((ART_H, ART_W, 4), np.uint8)                # P1 composite
msk = np.zeros((MSK_H, MSK_W, 4), np.uint8)                 # spec mask, else black
msk[..., 3] = 255

water = Image.new("RGBA", (CELL_A, CELL_A), WATER)


def load(path, shape):
    a = np.asarray(Image.open(path).convert("RGBA"))
    if a.shape != shape:
        raise RuntimeError(f"{os.path.basename(path)}: wrong size {a.shape} (want {shape})")
    return a


k = 0
for (y0, cols, rows), (my0, _, _) in zip(BANDS_A, BANDS_M):
    for r in range(rows):
        wy = y0 + r * CELL_A
        mwy = my0 + r * CELL_M
        for c in range(cols):
            k += 1
            fa = load(os.path.join(BASE, "icons128-wood", f"frame_{k:03d}.png"), (CELL_A, CELL_A, 4))
            fm = load(os.path.join(BASE, "masks64", f"frame_{k:03d}.png"), (CELL_M, CELL_M, 4))
            art[wy:wy + CELL_A, c * CELL_A:(c + 1) * CELL_A] = fa
            msk[mwy:mwy + CELL_M, c * CELL_M:(c + 1) * CELL_M, :3] = fm[..., :3]
            comp_img = Image.alpha_composite(water, Image.fromarray(fa, "RGBA"))
            comp[wy:wy + CELL_A, c * CELL_A:(c + 1) * CELL_A] = np.asarray(comp_img, np.uint8)
assert k == N, f"pasted {k} pieces, expected {N}"

Image.fromarray(art, "RGBA").save(os.path.join(INTER, "pilings-transition.png"))
Image.fromarray(comp, "RGBA").save(os.path.join(G, "pilings-composite.png"))
Image.fromarray(msk, "RGBA").save(os.path.join(G, "pilings-transition-mask.png"))
print(f"DEPLOY DONE: {N} pieces pasted; art {ART_W}x{ART_H} (slack alpha 0) -> intermediates;")
print(f" composite -> {G}/pilings-composite.png ; mask {MSK_W}x{MSK_H} -> {G}/pilings-transition-mask.png")