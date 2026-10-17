# bake-mask: render the wetness mask strip (a SEPARATE gray data block, never
# an alpha rider on the piling pixels) - mirrors tools/gen-textures.py's
# pilings-mask.png conventions exactly:
#   gray 170 = dry (crown, above the waterline z=0.25)
#   ramp 170 -> 85 (50% dryness) over the first wet_depth 0..0.6 (12px band)
#   hold 85 to the base; 0 outside the silhouette
# Rendered via an emission material override on a dedicated view layer.
# Paper pixels: the gray values are linear-exact (Standard view transform,
# world strength 0, film opacity restored) - all toggles are runtime-only.
import bpy, os
import numpy as np
from PIL import Image

ROOT = bpy.data.filepath
for _ in range(4):
    ROOT = os.path.dirname(ROOT)
BASE = os.path.join(ROOT, ".cache", "ford-factory")
masks_dir = os.path.join(BASE, "masks64")
os.makedirs(masks_dir, exist_ok=True)
N = 108

ICON = bpy.data.scenes["ICON"]
FORD = bpy.data.scenes["FORD"]
ctx = bpy.context.scene
ICON.render.resolution_x = 64
ICON.render.resolution_y = 64

# runtime pass state (restored at the end)
vf = ICON.view_settings.view_transform
film = ICON.render.film_transparent
world = bpy.data.worlds.get("FORD_WORLD")
bg_node = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
w_strength = bg_node.inputs[1].default_value
dither = ICON.render.dither_intensity

default_vl = ICON.view_layers[0]
mask_vl = ICON.view_layers.get("Mask") or ICON.view_layers.new("Mask")
mask_mat = bpy.data.materials["M_PILING_MASK"]

mask_vl.material_override = mask_mat

def set_mask_pass(on):
    default_vl.use = not on
    mask_vl.use = on
    ICON.view_settings.view_transform = 'Standard' if on else vf
    ICON.render.film_transparent = False if on else film
    bg_node.inputs[1].default_value = 0.0 if on else w_strength
    ICON.render.dither_intensity = 0.0 if on else dither

brows = []
bad = 0
set_mask_pass(True)
for f in range(1, N + 1):
    target = os.path.join(masks_dir, f"frame_{f:03d}.png")
    ctx.render.filepath = target
    ICON.render.filepath = target
    FORD.frame_set(f); ICON.frame_set(f)
    bpy.ops.render.render(scene="ICON", write_still=True)
    if not os.path.exists(target) or os.path.getsize(target) == 0:
        raise RuntimeError(f"MASK frame {f}: render wrote nothing")
    a = np.asarray(Image.open(target).convert("RGBA"))
    g = a[..., 0].astype(int)
    if a[..., 3].min() != 255 or a[0, 0, 0] != 0:
        raise RuntimeError(f"MASK frame {f}: background must be gray 0 / alpha 255")
    crown = ((g >= 168) & (g <= 172)).sum()          # completely dry above
    top = ((g >= 78) & (g <= 110)).sum()              # top of wet ramp (sRGB-curved)
    fully = ((g >= 20) & (g <= 30)).sum()             # fully wet at base
    # seam antialiasing between dry-170 and wet-~95 legitimately spans the 115..164
    # bytes within ~2 rows of the waterline; a real dry bleed would be much larger
    bleed = ((g > 115) & (g < 165)).sum()
    if crown < 100 or top < 4 or fully < 2:
        raise RuntimeError(f"MASK frame {f}: bad segments (dry {crown}, ramp-top {top}, fully {fully})")
    if bleed > 120:
        raise RuntimeError(f"MASK frame {f}: dry-gray bleed into wet zone ({bleed} px)")
    rows_g = np.nonzero((g >= 150).any(axis=1))[0]   # dry crown band rows
    rows_any = np.nonzero((g > 0).any(axis=1))[0]    # piling silhouette rows
    brows.append(int(rows_g.max() - rows_any.max())) # wet band size in px (waterline..base)
set_mask_pass(False)
print("MASK STRIP: 108/108 rendered")
print(f"MASK wet-band size (px): min {min(brows)} max {max(brows)} (fixed 0.25 world ~= 11px, must hold ±2)")
if max(brows) - min(brows) > 2:
    raise RuntimeError("wet band size varies beyond jitter tolerance - the fixed-depth model broke")
print("MASK BAKE DONE")