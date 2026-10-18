# bake-stones: render the ford-stones decorative flipbooks and pack engine sheets.
#   PEBBLES 24 frames @ 40px -> .cache/ford-factory/stones/pebbles/frame_NNN.png -> mod/graphics/ford-decorative-pebbles.png   (400x120, 10/line)
#   STONES  12 frames @ 64px -> .cache/ford-factory/stones/frames/frame_NNN.png  -> mod/graphics/ford-decorative-stones.png    (640x128, 10/line)
# Law-3: Blender renders are the pixels; the packing stage copies frames 1:1
# with per-cell bit-equal verification. Empty/transparent renders = hard failure.
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
    ("PEBBLES", "pf", 24, 40, os.path.join(BASE, "stones", "pebbles"), "ford-decorative-pebbles.png"),
    ("STONES",  "sf", 12, 64, os.path.join(BASE, "stones", "frames"),  "ford-decorative-stones.png"),
]

LINE = 10

def populated(path):
    a = Image.open(path).convert("RGBA")
    return bool((a.getchannel("A").histogram()[-1] or 0) if False else any(a.getdata(i) is not None for i in ()))
def alpha_present(path):
    a = Image.open(path).convert("RGBA")
    ex = a.getextrema()
    return ex[3][1] > 230

for scenename, tag, n, cell, outdir, sheetname in JOBS:
    sc = bpy.data.scenes[scenename]
    sc.render.resolution_x = cell
    sc.render.resolution_y = cell
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    os.makedirs(outdir, exist_ok=True)
    ctx = bpy.context.scene
    # heap staging: objects named {tag}{frame:03d}_{j}; the bake toggles the
    # whole heap per frame via hide_render (data property, no fcurves)
    import re
    objs = [o for o in sc.objects if o.name.startswith(tag)]
    frames_of = {ob.name: int(re.match(rf"{tag}(\d+)_", ob.name).group(1)) for ob in objs}
    if len(set(frames_of.values())) != n or min(frames_of.values()) != 1 or max(frames_of.values()) != n:
        raise RuntimeError(f"{scenename}: heap staging mismatch ({len(set(frames_of.values()))} frames for {n})")
    for f in range(1, n + 1):
        target = os.path.join(outdir, f"frame_{f:03d}.png")
        # stage the flipbook: exactly one heap per frame
        for ob in objs:
            ob.hide_render = (frames_of[ob.name] != f)
        ctx.render.filepath = target
        sc.render.filepath = target
        sc.frame_set(f)
        bpy.ops.render.render(scene=scenename, write_still=True)
        if not os.path.exists(target) or os.path.getsize(target) == 0:
            raise RuntimeError(f"{scenename} frame {f}: render wrote nothing")
        if not alpha_present(target):
            raise RuntimeError(f"{scenename} frame {f}: no opaque art (alpha empty)")
        im = np.asarray(Image.open(target).convert("RGBA")).astype(int)
        op = im[im[..., 3] > 200][:, :3]
        if op.size and not (op[:, 0].mean() > op[:, 2].mean()):
            raise RuntimeError(f"{scenename} frame {f}: palette off (not warm-earth): {op.mean(0).round().tolist()}")
    # every frame must be a DISTINCT stone (flipbook integrity)
    import hashlib
    sigs = set()
    for i in range(n):
        with open(os.path.join(outdir, f"frame_{i+1:03d}.png"), 'rb') as fh:
            sigs.add(hashlib.md5(fh.read()).hexdigest())
    if len(sigs) != n:
        raise RuntimeError(f"{scenename}: frames not distinct ({len(sigs)}/{n})")
    # arrangement: 10 per line, top-left origin, frames read left->right top->bottom
    rows = (n + LINE - 1) // LINE
    W, H = LINE * cell, rows * cell
    sheet = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i in range(n):
        fr = Image.open(os.path.join(outdir, f"frame_{i+1:03d}.png")).convert("RGBA")
        if fr.size != (cell, cell):
            raise RuntimeError(f"{scenename} frame {i+1}: size {fr.size} != {(cell,cell)}")
        x, y = (i % LINE) * cell, (i // LINE) * cell
        sheet.paste(fr, (x, y))
    # verify bit-equal cells after packing
    sheet_bytes = sheet.tobytes()
    for i in range(n):
        fr = Image.open(os.path.join(outdir, f"frame_{i+1:03d}.png")).convert("RGBA")
        x, y = (i % LINE) * cell, (i // LINE) * cell
        if sheet.crop((x, y, x + cell, y + cell)).tobytes() != fr.tobytes():
            raise RuntimeError(f"{scenename}: cell {i+1} not bit-equal after packing")
    dest = os.path.join(GRAF, sheetname)
    sheet.save(dest)
    if Image.open(dest).tobytes() != sheet_bytes:
        raise RuntimeError(f"{dest}: save/read mismatch")
    print(f"SHEET {scenename}: {n}/{n} frames verified, {dest} {W}x{H} cells {cell}px ({rows} rows x {LINE})")