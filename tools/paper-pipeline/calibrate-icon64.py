# bg-icon64-center: render the ICON scene at 64x64, auto-centering the piling
import bpy, math, os, shutil
from PIL import Image
from mathutils import Vector
import numpy as np

sc = bpy.data.scenes["ICON"]
cam = bpy.data.objects["ICON_CAM"]
OUT = "/home/nmrp3/devel/factorio-mods/mods/water-ford/blender/.png"   # where write_still actually lands
sc.render.resolution_x = 64
sc.render.resolution_y = 64

aim = Vector((0.0, 0.0, 0.4))
dist_dir = Vector((1.0, 1.0, 1.0)).normalized()

def set_cam(scale):
    cam.location = aim + dist_dir * 1.0
    cam.data.ortho_scale = scale

set_cam(0.9)
for attempt in range(4):
    sc.frame_set(27)
    bpy.ops.render.render(scene="ICON", write_still=True)
    im = np.asarray(Image.open(OUT).convert("RGBA"))
    a = im[..., 3] > 8
    ys, xs = np.nonzero(a)
    h = ys.max() - ys.min() + 1
    center = (ys.max() + ys.min()) / 2
    print(f"attempt {attempt}: rows {ys.min()}-{ys.max()} h={h} fill={h/64:.2f} center={center:.1f} scale={cam.data.ortho_scale:.3f}")
    if 0.62 <= h / 64 <= 0.80 and abs(center - 32) <= 2 and ys.min() >= 3:
        break
    u = (cam.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized()
    aim -= u * ((32 - center) / 64.0 * cam.data.ortho_scale)
    set_cam(cam.data.ortho_scale * math.sqrt(max(h, 1) / (0.70 * 64)))

shutil.copy(OUT, "/home/nmrp3/devel/factorio-mods/.cache/ford-factory/icon-frame27-64.png")
os.remove(OUT)   # keep the blend directory clean
print("CAM CONVERGED: loc", tuple(round(v, 3) for v in cam.location), "scale", round(cam.data.ortho_scale, 3))
print("BG ICON64 CENTERED DONE")
