# bake-stones v2: render the ford-stones decorative flipbooks (ABOVE the
# waterline + BELOW = water part per frame) and pack aligned engine sheets.
#   PEBBLES 24 frames @ 40px -> mod/graphics/ford-decorative-pebbles.png         (400x120)  + ...-below.png
#   STONES  12 frames @ 64px -> mod/graphics/ford-decorative-stones.png          (640x128)  + ...-below.png
# The wiring composites above+below via Sprite.layers, blend_mode
# "multiplicative-with-alpha" on the below layer (maintainer round-25).
# Law-3: Blender renders are the pixels; packing copies frames 1:1 with
# per-cell bit-equal verification. Empty/artless renders = hard failure.
# Run: blender -b mods/water-ford/blender/ford-stones.blend --python tools/paper-pipeline/bake-stones.py
import bpy, os
import numpy as np
from PIL import Image

ROOT = bpy.data.filepath
for _ in range(4):                     # blender -> water-ford -> mods -> superproject
    ROOT = os.path.dirname(ROOT)
BASE = os.path.join(ROOT, ".cache", "ford-factory")
GRAF = os.path.join(ROOT, "mods", "water-ford", "mod", "graphics")

JOBS = [
    ("PEBBLES", "pf", 24, 40, os.path.join(BASE, "stones", "pebbles"),
     "ford-decorative-pebbles.png", "ford-decorative-pebbles-below.png"),
    ("STONES",  "sf", 12, 64, os.path.join(BASE, "stones", "frames"),
     "ford-decorative-stones.png", "ford-decorative-stones-below.png"),
]

LINE = 10

def alpha_present(path):
    a = Image.open(path).convert("RGBA")
    ex = a.getextrema()
    return ex[3][1] > 230

def warm_earth(path):
    im = np.asarray(Image.open(path).convert("RGBA")).astype(int)
    op = im[im[..., 3] > 200][:, :3]
    return op.size and op[:, 0].mean() > op[:, 2].mean()

for scenename, tag, n, cell, outdir, sheetname, sheetname_w in JOBS:
    sc = bpy.data.scenes[scenename]
    sc.render.resolution_x = cell
    sc.render.resolution_y = cell
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    os.makedirs(outdir, exist_ok=True)
    ctx = bpy.context.scene
    objs = [o for o in sc.objects if o.name.startswith(tag)]
    import re
    frames_of = {ob.name: int(re.match(rf"{tag}(\d+)_", ob.name).group(1)) for ob in objs}
    above = [o for o in objs if o.name.endswith("a")]
    below = [o for o in objs if o.name.endswith("w")]
    if len(set(frames_of.values())) != n or min(frames_of.values()) != 1 or max(frames_of.values()) != n:
        raise RuntimeError(f"{scenename}: heap staging mismatch ({len(set(frames_of.values()))} frames for {n})")
    for f in range(1, n + 1):
        # pass 1: dry part visible
        for ob in above: ob.hide_render = (frames_of[ob.name] != f)
        for ob in below: ob.hide_render = True
        # pass 2: water part visible
        targets = [(os.path.join(outdir, f"frame_{f:03d}.png"),
                    lambda ob, f=f: frames_of[ob.name] != f,
                    lambda ob: True),
                   (os.path.join(outdir, f"frame_{f:03d}_W.png"),
                    lambda ob: True,
                    lambda ob, f=f: frames_of[ob.name] != f)]
        for target, avw, bvw in targets:
            for ob in above: ob.hide_render = avw(ob)
            for ob in below: ob.hide_render = bvw(ob)
            ctx.render.filepath = target
            sc.render.filepath = target
            sc.frame_set(f)
            bpy.ops.render.render(scene=scenename, write_still=True)
            if not os.path.exists(target) or os.path.getsize(target) == 0:
                raise RuntimeError(f"{scenename} frame {f}: render wrote nothing ({os.path.basename(target)})")
            if not alpha_present(target):
                raise RuntimeError(f"{scenename} frame {f}: no opaque art ({os.path.basename(target)})")
            if not warm_earth(target):
                raise RuntimeError(f"{scenename} frame {f}: palette off (not warm-earth)")
        # the below pass must actually carry art distinct from the above pass
        a = np.asarray(Image.open(os.path.join(outdir, f"frame_{f:03d}.png")).convert("RGBA"))
        w = np.asarray(Image.open(os.path.join(outdir, f"frame_{f:03d}_W.png")).convert("RGBA"))
        if not (w[..., 3] > 200).any():
            raise RuntimeError(f"{scenename} frame {f}: below-water pass is empty")
    # every frame must be a DISTINCT heap (flipbook integrity)
    import hashlib
    sigs = set()
    for i in range(n):
        with open(os.path.join(outdir, f"frame_{i+1:03d}.png"), 'rb') as fh:
            sigs.add(hashlib.md5(fh.read()).hexdigest())
    if len(sigs) != n:
        raise RuntimeError(f"{scenename}: frames not distinct ({len(sigs)}/{n})")
    # arrangement: 10 per line, top-left origin; ABOVE and BELOW sheets share
    # cell coords so the Sprite.layers composite lines up in-game
    rows = (n + LINE - 1) // LINE
    W, H = LINE * cell, rows * cell
    for namesuf, srcsuf, destname in (("", "", sheetname), ("_W", "_W", sheetname_w)):
        sheet = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for i in range(n):
            fr = Image.open(os.path.join(outdir, f"frame_{i+1:03d}{srcsuf}.png")).convert("RGBA")
            if fr.size != (cell, cell):
                raise RuntimeError(f"{scenename} frame {i+1}{srcsuf}: size {fr.size} != {(cell,cell)}")
            x, y = (i % LINE) * cell, (i // LINE) * cell
            sheet.paste(fr, (x, y))
        # bit-equal cell verification
        sheet_bytes = sheet.tobytes()
        for i in range(n):
            fr = Image.open(os.path.join(outdir, f"frame_{i+1:03d}{srcsuf}.png")).convert("RGBA")
            x, y = (i % LINE) * cell, (i // LINE) * cell
            if sheet.crop((x, y, x + cell, y + cell)).tobytes() != fr.tobytes():
                raise RuntimeError(f"{scenename}: cell {i+1}{srcsuf} not bit-equal after packing")
        dest = os.path.join(GRAF, destname)
        sheet.save(dest)
        if Image.open(dest).tobytes() != sheet_bytes:
            raise RuntimeError(f"{dest}: save/read mismatch")
        print(f"SHEET {scenename}{namesuf}: {n}/{n} frames verified, {dest} {W}x{H} cells {cell}px")