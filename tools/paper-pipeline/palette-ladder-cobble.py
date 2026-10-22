# palette-ladder-cobble: the maintainer's color-decision aid, NO BLENDER NEEDED.
#
# Renders a numbered contact sheet of candidate looks straight from the SHIPPED
# art (assets-src/cobble 1x1 ladder, cell 0) using the wetness-mask sheet as
# the stone/bed pixel selector (weight = smoothstep of the mask ramp 85..170),
# so the stones and the grout bed can be toned independently. Every candidate
# row shows DRY (what a sheet cell holds) and WASHED (the ford's in-game veil
# sim: px' = 0.75*px + 0.25*(51,51,51), the effect_color mixing law) so the
# picker judges the look the game will actually show. A vanilla stone-path
# reference panel sits on top as the brightness anchor.
#
# The pick ("row N", optionally per sheet) is folded into the committed
# TONE_* constants in auth-cobble.py; the crank then re-renders the ladder
# sheets for real and the maintainer confirms visually before shipping.
# (2026-10-21: the maintainer found the live node route unworkable —
# "I can't see what is going on or how to adjust it" — this is the
# alternative: one image, one number.)
#
# Usage: devctl python run tools/paper-pipeline/palette-ladder-cobble.py
# Outputs (transient, .cache): .cache/palette-ladder/ladder-stone.png,
#                               .cache/palette-ladder/ladder-bed.png
import os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
MODROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
GRAF = os.path.join(MODROOT, 'assets-src', 'cobble')
OUT = os.path.join(MODROOT, '.cache', 'palette-ladder')
VANILLA = '/home/nmrp3/.local/share/factorio_2_dlc/data/base/graphics/terrain/stone-path/stone-path-1.png'
CELL = 128          # 1x1 sheet cell px
ZOOM = 2            # panels are CELL*ZOOM squares
PANEL = CELL * ZOOM
GUTTER = 110
PAD = 8
ROWH = PANEL + 2 * PAD
STONE_TONES = (1.00, 0.90, 0.80, 0.72, 0.65, 0.58, 0.50, 0.42)
BED_TONES = (1.00, 0.90, 0.80, 0.72, 0.65, 0.58, 0.50, 0.42)
VEIL = 51.0         # the ford wash veil (51,51,51), 25% mix
MASK_LO, MASK_HI = 85.0, 170.0   # the wetness ramp bytes (hold..crown)

os.makedirs(OUT, exist_ok=True)
# base = the CURRENT-TRUTH render (the crank's staged sheets: dry art) when
# present; otherwise the committed shipped sheets (pre-ruling, wet-in-art) —
# the ladder labels state which one it is. --source shipped|stage|auto.
STAGE = os.path.join(MODROOT, '.cache', 'blender-cobble', 'bake', 'stage')
_src = 'auto'
if '--source' in sys.argv:
    _src = sys.argv[sys.argv.index('--source') + 1]
_use = _src
if _use == 'auto':
    _use = 'stage' if os.path.exists(os.path.join(STAGE, 'cobblestone-ford.png')) else 'shipped'
ARTDIR = STAGE if _use == 'stage' else GRAF
print('LADDER BASE:', _use, ARTDIR)
art = Image.open(os.path.join(ARTDIR, 'cobblestone-ford.png')).convert('RGBA')
mask = Image.open(os.path.join(ARTDIR, 'cobblestone-ford-mask.png')).convert('RGBA')
cell = np.asarray(art.crop((0, 0, CELL, CELL)), dtype=float)
mcell = np.asarray(mask.crop((0, 0, CELL, CELL)).convert('L'), dtype=float)
w = np.clip((mcell - MASK_LO) / (MASK_HI - MASK_LO), 0, 1)  # 1 = stone, 0 = bed
rgb = cell[..., :3]
mean_stone = float(rgb[w > 0.5].mean())
mean_bed = float(rgb[w < 0.5].mean())
washed = lambda a: 0.75 * a + 0.25 * VEIL
def panel(a):
    a = np.clip(a, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([a, np.full(a.shape[:2], 255, np.uint8)]), 'RGBA').resize((PANEL, PANEL), Image.NEAREST)

van = np.asarray(Image.open(VANILLA).convert('RGBA').crop((0, 0, 64, 64)), dtype=float)[:3]
van_mean = float(van.mean())

def ladder(title, tones, which):
    n = len(tones)
    H = ROWH * (n + 2) + 28
    W = GUTTER + 2 * (PANEL + PAD) + PAD + 260
    im = Image.new('RGB', (W, H), (22, 22, 24))
    d = ImageDraw.Draw(im)
    d.text((10, 8), title, fill=(255, 210, 80))
    # reference row: shipped-as-is (DRY) and its WASHED look, then vanilla
    y = 28
    d.text((6, y + PANEL // 2 - 6), 'row 0\nSHIPPED\n(as-is)', fill=(255, 255, 255))
    im.paste(panel(rgb), (GUTTER, y))
    im.paste(panel(washed(rgb)), (GUTTER + PANEL + PAD, y))
    d.text((GUTTER + 2 * (PANEL + PAD) + 12, y + 8), 'WASHED = the ford\nlook in game',
           fill=(150, 200, 255))
    y += ROWH
    d.text((6, y + PANEL // 2 - 12), 'ANCHOR\nVANILLA\nstone-path\nmean L %.0f' % van_mean,
           fill=(120, 220, 255))
    im.paste(panel(van), (GUTTER, y))
    d.text((GUTTER + PANEL + PAD + 12, y + 8), 'vanilla: no wash\n(game shows it dry)',
           fill=(150, 200, 255))
    y += ROWH
    for i, t in enumerate(tones, start=1):
        toned = rgb * (1 + w[..., None] * (t - 1)) if which == 'stone' else \
                rgb * (1 + (1 - w)[..., None] * (t - 1))
        d.text((6, y + PANEL // 2 - 6), 'row %d\ntone\n%.2f' % (i, t), fill=(255, 210, 80))
        im.paste(panel(toned), (GUTTER, y))
        im.paste(panel(washed(toned)), (GUTTER + PANEL + PAD, y))
        d.text((GUTTER + 2 * (PANEL + PAD) + 12, y + 8),
               '%s tone %.2f\ndry mean L %.0f | washed %.0f'
               % (which, t, float(toned.mean()), float(washed(toned).mean())),
               fill=(200, 200, 200))
        y += ROWH
    p = os.path.join(OUT, 'ladder-%s.png' % which)
    im.save(p)
    print('SAVED', p, im.size)

print('shipped stone mean L %.1f | bed mean L %.1f | vanilla stone-path mean L %.1f'
      % (mean_stone, mean_bed, van_mean))
ladder('COBBLE STONES — tone ladder (pick one row)', STONE_TONES, 'stone')
ladder('COBBLE BED (the grout between stones) — tone ladder (pick one row)', BED_TONES, 'bed')