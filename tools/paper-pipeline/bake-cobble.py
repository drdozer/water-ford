# bake-cobble: render the cobblestone ladder (1x1 base floor, 2x2 + 4x4 field
# grids) to ART sheets committed under assets-src/cobble/. Maintainer ruling
# 2026-10-21: NO wetness-mask sheets — the wet look lives in the art pixels
# (M_COBBLE's WL ramp, set to WL=0.15 here), as for the wooden ford.
# Art = FLOOR scene ("water must not exist" asserted), 128px per world unit in
# every region; per-cell alpha gate; law-3 slice (SQ1_PICK / field grids);
# bit-equal repack; determinism = every pass rendered twice, PNG bytes compared
# (--twice gate of the stones/boards recipe; single fixed thread).
import bpy, os, sys, math
import numpy as np
from PIL import Image

REGIONS = [
    # (cam, ortho, res_px, frame (x0, y0, w, h), tag, cell_px)
    ('FLOOR_CAM', 24.0, 3072, (-12.0, -12.0, 24.0, 24.0), 'sq1', 128),
    ('COB2_CAM',   8.0, 1024, (-22.0, -22.0,  8.0,  8.0), 'sq2', 256),
    ('COB4_CAM',  16.0, 2048, (-46.0, -40.0, 16.0, 16.0), 'sq4', 512),
]
N_VARIANTS = 16
SQ1_PICK = [(1, 1), (7, 1), (13, 1), (19, 1), (4, 7), (10, 7), (16, 7), (22, 7),
            (1, 13), (7, 13), (13, 13), (19, 13), (4, 19), (10, 19), (16, 19), (22, 19)]
WL = 0.15
MODROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(MODROOT, 'assets-src', 'cobble')
TMPA = os.path.join(MODROOT, '.cache', 'blender-cobble', 'bake')
for d in (OUT, TMPA):
    os.makedirs(d, exist_ok=True)

sc = bpy.data.scenes['FLOOR']
sc.camera = bpy.data.objects['FLOOR_CAM']
sc.cycles.samples = 96
sc.cycles.use_adaptive_sampling = True
sc.cycles.adaptive_threshold = 0.01
sc.cycles.use_denoising = False
sc.cycles.seed = 0
sc.cycles.threads_mode = 'FIXED'
sc.cycles.threads = 1
sc.view_settings.view_transform = 'Standard'
assert not [o for o in sc.collection.all_objects if 'WATER' in o.name], 'water must not exist in FLOOR'
cob = bpy.data.objects['COBBLE_FLOOR']; bed = bpy.data.objects['JOINTBED']

def set_wl(v):
    for mn in ('M_COBBLE', 'M_COBBLEBED'):
        bpy.data.materials[mn].node_tree.nodes['WL'].outputs[0].default_value = v

w0 = sc.world.node_tree.nodes['Background'].inputs[1].default_value
d0 = sc.render.dither_intensity
film0 = sc.render.film_transparent
rt0 = sc.view_settings.view_transform
wl0 = [bpy.data.materials[mn].node_tree.nodes['WL'].outputs[0].default_value
       for mn in ('M_COBBLE', 'M_COBBLEBED')]

set_wl(WL)
for run in (1, 2):
    for cam_name, ortho, res, (x0, y0, w, h), tag, cell in REGIONS:
        sc.camera = bpy.data.objects[cam_name]
        sc.render.resolution_x = res; sc.render.resolution_y = res
        sc.render.film_transparent = False
        art = os.path.join(TMPA, f'art_{tag}_run{run}.png')
        sc.render.filepath = art
        with bpy.context.temp_override(scene=sc):
            bpy.ops.render.render(write_still=True)
        if not os.path.exists(art) or os.path.getsize(art) == 0:
            raise RuntimeError(f'ART {tag} run{run}: wrote nothing')
        print(f'BAKE {tag} run{run} OK', file=sys.stderr)
# restore the knob state read at entry (the bake never saves the blend)
set_wl(wl0[0])
bpy.data.materials['M_COBBLEBED'].node_tree.nodes['WL'].outputs[0].default_value = wl0[1]
sc.camera = bpy.data.objects['FLOOR_CAM']
sc.render.resolution_x, sc.render.resolution_y = 1536, 1536
sc.render.film_transparent = film0
sc.render.dither_intensity = d0
sc.view_settings.view_transform = rt0
sc.world.node_tree.nodes['Background'].inputs[1].default_value = w0

# ---- determinism: byte-compare each pass across runs
det_ok = True
for b in REGIONS:
    p1 = os.path.join(TMPA, f'art_{b[4]}_run1.png')
    p2 = os.path.join(TMPA, f'art_{b[4]}_run2.png')
    if open(p1, 'rb').read() != open(p2, 'rb').read():
        det_ok = False
        print(f'DETERMINISM FAIL art {b[4]}')
print(f'DETERMINISM (run1==run2, all three art passes): {det_ok}')

# ---- slice + gate + pack (pure arrangement, bit-equal per cell)
def variants_for(tag):
    x0, y0, w, h = [v for b in REGIONS if b[4] == tag for v in b[3]]
    res = [b[2] for b in REGIONS if b[4] == tag][0]
    px = 128  # px per world unit (res/ortho)
    out = []
    if tag == 'sq1':
        for (ti, tj) in SQ1_PICK:
            out.append((ti * px, (23 - tj) * px))
    else:
        n = int(w)  # 8 or 16
        for r in range(4):
            for c in range(4):
                cx = x0 + c * (w / 4)
                cy = y0 + r * (h / 4)
                ux = (cx - x0) / w * res
                uy = res - ((cy + h / 4 - y0) / h) * res
                out.append((round(ux), round(uy)))
    return out

report = []
for cam_name, ortho, res, frame, tag, cell in REGIONS:
    art = Image.open(os.path.join(TMPA, f'art_{tag}_run1.png')).convert('RGBA')
    if art.size != (res, res):
        raise RuntimeError(f'ART size wrong for {tag}')
    picks = variants_for(tag)
    sheet_cols = 16 if tag == 'sq1' else 4
    art_sheet = Image.new('RGBA', (sheet_cols * cell, ((len(picks) + sheet_cols - 1) // sheet_cols) * cell), (0, 0, 0, 0))
    allok = True
    means = []
    for i, (ux, uy) in enumerate(picks):
        ac = art.crop((ux, uy, ux + cell, uy + cell))
        art_sheet.paste(ac, ((i % sheet_cols) * cell, (i // sheet_cols) * cell))
        a = np.asarray(ac)
        if a[..., 3].min() != 255:
            allok = False; print(f'ALPHA GATE FAIL {tag} variant {i}: alpha {a[...,3].min()}')
        means.append(float(np.asarray(ac.convert('L')).mean()))
    name = 'cobblestone-ford' if tag == 'sq1' else ('cobblestone-ford-2x2' if tag == 'sq2' else 'cobblestone-ford-4x4')
    ap = os.path.join(OUT, f'{name}.png')
    art_sheet.save(ap)
    back = np.asarray(Image.open(ap).convert('RGBA'))
    if not np.array_equal(back, np.asarray(art_sheet)):
        raise RuntimeError(f'PACK not bit-equal: {ap}')
    report.append(f'{tag}: art {ap} {art_sheet.size} | mean-L spread {min(means):.0f}-{max(means):.0f} | alpha-gate {"OK" if allok else "FAIL"}')
print('\n'.join(report))
print('BAKE COMPLETE')