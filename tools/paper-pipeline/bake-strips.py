# bake-strips: render both flipbook strips from ford-posts.blend, verified.
#   icon strip   -> .cache/ford-factory/icons64-wood/frame_NNN.png  (ICON scene, 128px, direct write)
#   sprite strip -> .cache/ford-factory/frames64/frame_NNN.png      (context scene, save_render)
# Identical output every run (bit-reproducible; proven by bake.sh --twice).
# Empty or unwritten renders are HARD FAILURES - the old stale-copy fallback is gone.
# Run: blender -b mods/water-ford/blender/ford-posts.blend --python tools/paper-pipeline/bake-strips.py
import bpy, os
import numpy as np
from PIL import Image

ROOT = bpy.data.filepath
for _ in range(4):                     # .../blender -> water-ford -> mods -> superproject
    ROOT = os.path.dirname(ROOT)
BASE = os.path.join(ROOT, ".cache", "ford-factory")
icons_dir = os.path.join(BASE, "icons128-wood")
sprites_dir = os.path.join(BASE, "frames128")
os.makedirs(icons_dir, exist_ok=True)
os.makedirs(sprites_dir, exist_ok=True)
N = 108

ICON = bpy.data.scenes["ICON"]
FORD = bpy.data.scenes["FORD"]
ctx = bpy.context.scene              # write_still takes the CONTEXT scene's filepath
ICON.render.resolution_x = 128
ICON.render.resolution_y = 128

def cap_verify(path):
    im = np.asarray(Image.open(path).convert("RGB"), dtype=float)
    a = np.asarray(Image.open(path).convert("RGBA")).astype(int)
    ys, xs = np.nonzero(a[..., 3] > 230)
    cap = im[ys.min():ys.min() + (ys.max() - ys.min()) // 3 + 1,
             max(xs.min(), int(xs.mean()) - 7):int(xs.mean()) + 7]
    # empty renders must FAIL the warm check hard (a [0,0,0]-type mean would pseudo-pass R>=B)
    return cap.reshape(-1, 3).mean(0) if cap.size else np.array([1., 1., 2.])

def populated(path):
    a = np.asarray(Image.open(path).convert("RGBA"))
    return bool((a[..., 3] > 230).any())

# 1) icon strip: direct-write per frame (both scenes get the path)
for f in range(1, N + 1):
    target = os.path.join(icons_dir, f"frame_{f:03d}.png")
    ctx.render.filepath = target
    ICON.render.filepath = target
    FORD.frame_set(f); ICON.frame_set(f)
    bpy.ops.render.render(scene="ICON", write_still=True)
    if not os.path.exists(target) or os.path.getsize(target) == 0:
        raise RuntimeError(f"ICON frame {f}: render wrote nothing (intermittent empty-write bug)")
    m = cap_verify(target)
    if not (m[0] >= m[2]) or not populated(target):
        raise RuntimeError(f"ICON frame {f}: empty/warm-fail render")
print(f"ICON STRIP: 108/108 verified frames")

# 2) sprite strip: the FORD context (water level/bed) rendered THROUGH the asset
#    camera (ICON_CAM) at 128px, so the context view aligns pixel-for-pixel with
#    the icon and mask cells (crank-runtime only: camera/res set + restored).
#    NOTE: the CATCHER stays EXCLUDED (shadow = its own sprites, never baked
#    into the art pixels - the blocks stay separate).
ICON_CAM = bpy.data.objects["ICON_CAM"]
if ICON_CAM.name not in FORD.collection.objects:
    FORD.collection.objects.link(ICON_CAM)
old_cam = FORD.camera
old_res = (FORD.render.resolution_x, FORD.render.resolution_y)
FORD.camera = ICON_CAM
FORD.render.resolution_x = 128
FORD.render.resolution_y = 128
ctx.render.filepath = ""
for f in range(1, N + 1):
    FORD.frame_set(f)
    bpy.ops.render.render()
    sp = os.path.join(sprites_dir, f"frame_{f:03d}.png")
    bpy.data.images["Render Result"].save_render(filepath=sp)
    if not os.path.exists(sp) or os.path.getsize(sp) == 0:
        raise RuntimeError(f"SPRITE frame {f}: save_render wrote nothing")
    m = cap_verify(sp)
    if not (m[0] >= m[2]) or not populated(sp):
        raise RuntimeError(f"SPRITE frame {f}: empty/warm-fail render")
FORD.camera = old_cam
FORD.render.resolution_x, FORD.render.resolution_y = old_res
FORD.collection.objects.unlink(ICON_CAM)
print("sprite strip: context through ICON_CAM at 128px (aligned framing)")
print(f"SPRITE STRIP: 108/108 verified frames")

# 3) strip metrics (was a retyped bash heredoc every cycle; merged to one truth)
cx, cy, probs = [], [], []
lum_all = []
for f in range(1, N + 1):
    p = os.path.join(icons_dir, f"frame_{f:03d}.png")
    a = np.asarray(Image.open(p).convert("RGBA"))
    m = a[..., 3] > 230
    if not m.any():
        probs.append((f, "EMPTY")); continue
    ys, xs = np.nonzero(m)
    cx.append(xs.mean()); cy.append(ys.mean())
    if m[0, :].any() or m[-1, :].any() or m[:, 0].any() or m[:, -1].any():
        probs.append((f, "border"))
    lum_all.append(0.2126 * a[..., 0][m] + 0.7152 * a[..., 1][m] + 0.0722 * a[..., 2][m])
L = np.concatenate(lum_all)
import statistics
print(f"METRICS: centroid sigma X {statistics.pstdev(cx):.1f}px / Y {statistics.pstdev(cy):.1f}px | "
      f"problems: {probs or 'none'}")
print(f"METRICS: piling luma mean {L.mean():.0f} | p50 {np.percentile(L, 50):.0f} | "
      f"p90 {np.percentile(L, 90):.0f} | min {L.min():.0f}")
print("REMAKE DONE")