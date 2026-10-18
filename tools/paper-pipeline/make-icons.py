# make-icons.py — compose the water-ford item/tech icons from committed art.
# Pure ARRANGEMENT (maintainer-sanctioned 2026-10-18): crops of committed
# sheet cells + alpha-over pastes of committed stone cells. No value
# changes, no resampling — sizes are native (128px tile cells, 64px stone
# cells); the game downscales via icon_size.
#   outputs: mod/graphics/boards-land-icon.png     (128, 1 land tile cell)
#            mod/graphics/water-ford-icon.png      (128, deck cell + stones)
#            mod/graphics/water-ford-tech-icon.png (256, 2x2 deck + stones)
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
GRAF = os.path.join(HERE, "..", "..", "mod", "graphics")

land_sheet = Image.open(os.path.join(GRAF, "boards-land.png")).convert("RGBA")
ford_sheet = Image.open(os.path.join(GRAF, "boards-ford.png")).convert("RGBA")
stone_sheet = Image.open(os.path.join(GRAF, "ford-decorative-stones.png")).convert("RGBA")

def cell(sheet, idx, size):
    x, y = (idx % 10) * size, (idx // 10) * size
    c = sheet.crop((x, y, x + size, y + size))
    ref = sheet.crop((x, y, x + size, y + size))
    assert c.tobytes() == ref.tobytes()  # crop is 1:1
    return c

def paste_over(dst, src, px, py):
    """proper alpha-over with edge clipping (paste+mask would REPLACE the
    destination RGBA, punching holes where the sprite is semi-transparent)"""
    x0, y0 = max(0, px), max(0, py)
    x1, y1 = min(dst.width, px + src.width), min(dst.height, py + src.height)
    if x1 <= x0 or y1 <= y0: return
    region = dst.crop((x0, y0, x1, y1))
    region.alpha_composite(src.crop((x0 - px, y0 - py, x1 - px, y1 - py)))
    dst.paste(region, (x0, y0))

def opaque_frac(im):
    a = im.getchannel("A")
    h = a.histogram()
    return (sum(h[200:]) / max(1, im.width * im.height))

# --- boards-land item icon: one land tile cell, verbatim
land_icon = cell(land_sheet, 0, 128)
assert opaque_frac(land_icon) > 0.9, "land icon not a full tile"
land_icon.save(os.path.join(GRAF, "boards-land-icon.png"))

# the deck cells carry transparent water-gaps between planks (the tile sits
# on the engine's water); the icon base = the P1 flat-water constant from the
# piling pipeline so the gaps read as water in the inventory
P1_WATER = (17, 114, 129, 255)

# --- water-ford item icon: water base + deck cell + stone heaps at corners
ford_icon = Image.new("RGBA", (128, 128), P1_WATER)
ford_icon.alpha_composite(cell(ford_sheet, 0, 128))
for sidx, (px, py) in [(0, (86, -16)), (5, (-18, 82)), (2, (80, 82))]:
    s = cell(stone_sheet, sidx, 64)
    paste_over(ford_icon, s, px, py)  # alpha-over; edge clips are intentional
assert 0.5 < opaque_frac(ford_icon) <= 1.0
ford_icon.save(os.path.join(GRAF, "water-ford-icon.png"))

# --- water-ford tech icon: 2x2 deck cells + stones at the corners/edges
tech = Image.new("RGBA", (256, 256), P1_WATER)
for i, cidx in enumerate((0, 5, 9, 13)):
    c = cell(ford_sheet, cidx, 128)
    tech.alpha_composite(c, ((i % 2) * 128, (i // 2) * 128))
for sidx, (px, py) in [(0, (188, -18)), (5, (-16, 190)), (2, (196, 192)),
                       (7, (-14, -16)), (9, (118, -12)), (11, (114, 200))]:
    s = cell(stone_sheet, sidx, 64)
    paste_over(tech, s, px, py)
tech.save(os.path.join(GRAF, "water-ford-tech-icon.png"))

for nm in ("boards-land-icon.png", "water-ford-icon.png", "water-ford-tech-icon.png"):
    im = Image.open(os.path.join(GRAF, nm))
    print(f"ICON {nm}: {im.size} mode={im.mode} opaque={opaque_frac(im):.2f}")
print("MAKE-ICONS-DONE")