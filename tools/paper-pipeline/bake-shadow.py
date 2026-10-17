# bake-shadow: render the cast-shadow strip - THE SHADOW ONLY, its own sprite.
# The CATCHER object is a Cycles shadow catcher (is_shadow_catcher=True, set in
# the shadow-experiment era): with film-transparent and the piling hidden from
# CAMERA rays (it still casts), the render is transparent everywhere except the
# shadow itself - dark translucent coverage east of the piling.
# Runtime-only: camera linked into FORD, view layers toggled, pole camera
# visibility off, all restored. Never saved from this process.
import bpy, os
import numpy as np
from PIL import Image

ROOT = bpy.data.filepath
for _ in range(4):
    ROOT = os.path.dirname(ROOT)
BASE = os.path.join(ROOT, ".cache", "ford-factory")
shadows_dir = os.path.join(BASE, "shadows64")
os.makedirs(shadows_dir, exist_ok=True)
N = 108

FORD = bpy.data.scenes["FORD"]
ctx = bpy.context.scene
cam = bpy.data.objects["ICON_CAM"]
if cam.name not in FORD.collection.objects:
    FORD.collection.objects.link(cam)
pole = bpy.data.objects["PILING"]
old_cam = FORD.camera
old_res = (FORD.render.resolution_x, FORD.render.resolution_y)
FORD.camera = cam
FORD.render.resolution_x = 64
FORD.render.resolution_y = 64
vl_state = {v.name: v.use for v in FORD.view_layers}
for v in FORD.view_layers:
    v.use = (v.name == 'SHADOW')
pole.visible_camera = False

for f in range(1, N + 1):
    FORD.frame_set(f)
    bpy.ops.render.render()
    sp = os.path.join(shadows_dir, f"frame_{f:03d}.png")
    bpy.data.images["Render Result"].save_render(filepath=sp)
    if not os.path.exists(sp) or os.path.getsize(sp) == 0:
        raise RuntimeError(f"SHADOW frame {f}: save_render wrote nothing")

pole.visible_camera = True
for v in FORD.view_layers:
    v.use = vl_state[v.name]
FORD.camera = old_cam
FORD.render.resolution_x, FORD.render.resolution_y = old_res
FORD.collection.objects.unlink(cam)

# verification: the block is the shadow only - translucent dark coverage lying
# EAST of the piling (the key sits due west; shadows fall due east).
ico_dir = os.path.join(BASE, "icons64-wood")
report = []
for f in range(1, N + 1):
    sp = os.path.join(shadows_dir, f"frame_{f:03d}.png")
    a = np.asarray(Image.open(sp).convert("RGBA")).astype(float)
    alpha = a[..., 3]
    cov = alpha > 10
    if cov.sum() < 200:
        raise RuntimeError(f"SHADOW frame {f}: shadow coverage too small ({int(cov.sum())} px)")
    ic = np.asarray(Image.open(os.path.join(ico_dir, f"frame_{f:03d}.png")).convert("RGBA"))
    m = ic[..., 3] > 230
    pcx = int(np.nonzero(m.any(axis=0))[0].mean())
    cols = np.arange(alpha.shape[1])[None, :] + 0.5
    east_share = float((alpha * (cols >= pcx)).sum() / alpha.sum())
    if east_share < 0.60:
        raise RuntimeError(f"SHADOW frame {f}: shadow not lying east of the piling (east share {east_share:.2f})")
    rgb_mean = float(a[..., :3][cov].mean())
    if rgb_mean > 40:
        raise RuntimeError(f"SHADOW frame {f}: coverage not shadow-dark (rgb mean {rgb_mean:.0f})")
    report.append((int(cov.sum()), round(east_share, 2)))
counts = [r[0] for r in report]
shares = [r[1] for r in report]
print(f"SHADOW STRIP: {N}/{N} rendered")
print(f"shadow coverage px per frame: min {min(counts)} max {max(counts)} | "
      f"east-share min {min(shares)} max {max(shares)}")
print("SHADOW BAKE DONE")