# bake-cobble: render the cobblestone ladder (1x1 base floor, 2x2 + 4x4 field
# grids) to ART sheets + companion WETNESS MASK sheets, per the pilings
# workflow (bake-mask/bake-sheet) and the boards ladder conventions (16
# variants, 128px per world unit in every region). Maintainer ruling
# 2026-10-21 (revised same day): the WET LOOK SHIPS IN THE MASK — art renders
# DRY (WL knob down — in-memory only), the mask (M_COBBLEMASK, its own WL
# knob) carries 170 dry / ramp / 85 hold and is mixed with the water effects
# shader by the engine to submerge cobble bases, exactly as the piling bases.
# Gates: per-cell alpha; mask byte floor/ceiling per the recipe (hard-fail
# only true voids (byte 0, the suppression-black defect) or over-bright
# (>172); the recovered crank treated sub-78 rim bytes as a NOTE — the
# remaining sub-85 bytes here are the corner cells' boundary AA (the field
# stones end exactly ON the cell edge by design — the pinned furniture — so
# the outermost pixel is a partial-coverage blend; the neighbouring tile's
# geometry continues the mosaic in-game); crown/hold byte counters reported.
# Determinism = --twice on PIXELS (the PNG writer is
# not byte-stable run-to-run — encoder noise cost the recovered crank its
# gate; the stones recipe compares pixels for the same reason).
import bpy, os, sys, math
import numpy as np
from PIL import Image

REGIONS = [
    # (cam, ortho, res_px, frame (x0, y0, w, h), tag, cell_px, pad_units)
    # pad_units: extra ortho units rendered around the logical frame; the
    # slice crops interior windows (+pad*128 px) so the sheet never touches
    # the render's outer-edge filter tail (rim bytes dipped to 74 at the
    # sq2/sq4 frame borders without it; sq1's picked cells sit interior and
    # stay pad 0). The px/unit stays 128 everywhere.
    ('FLOOR_CAM', 24.0, 3072, (-12.0, -12.0, 24.0, 24.0), 'sq1', 128, 0),
    ('COB2_CAM',   8.0, 1024, (-22.0, -22.0,  8.0,  8.0), 'sq2', 256, 1),
    ('COB4_CAM',  16.0, 2048, (-46.0, -40.0, 16.0, 16.0), 'sq4', 512, 1),
]
N_VARIANTS = 16
SQ1_PICK = [(1, 1), (7, 1), (13, 1), (19, 1), (4, 7), (10, 7), (16, 7), (22, 7),
            (1, 13), (7, 13), (13, 13), (19, 13), (4, 19), (10, 19), (16, 19), (22, 19)]
WL = 0.15
WET_DRY_ARTRUN_WL = -1.0
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

# dedicated Mask view layer: material_override = M_COBBLEMASK, all linear-exact
# grays (Standard transform, world 0, dither 0)
mask_vl = sc.view_layers.get('Mask') or sc.view_layers.new('Mask')
mask_vl.material_override = bpy.data.materials['M_COBBLEMASK']

# ART renders DRY: WL knob down (the wet look ships in the mask sheets)
set_wl(WET_DRY_ARTRUN_WL)
for run in (1, 2):
    for cam_name, ortho, res, (x0, y0, w, h), tag, cell, pad in REGIONS:
        sc.camera = bpy.data.objects[cam_name]
        # overscan: widen ortho equally; px/unit stays 128 and the logical
        # frame stays centered, so cells shift by exactly pad*128 whole px
        sc.render.resolution_x = res + round(pad * 128 * 2)
        sc.render.resolution_y = sc.render.resolution_x
        cam = bpy.data.objects[cam_name]
        if cam.data.type == 'ORTHO' and pad:
            cam.data.ortho_scale = ortho + pad * 2
        # ART (main view layer, dry deck)
        sc.view_layers[0].use = True
        mask_vl.use = False
        sc.render.film_transparent = False
        art = os.path.join(TMPA, f'art_{tag}_run{run}.png')
        sc.render.filepath = art
        with bpy.context.temp_override(scene=sc):
            bpy.ops.render.render(write_still=True)
        if not os.path.exists(art) or os.path.getsize(art) == 0:
            raise RuntimeError(f'ART {tag} run{run}: wrote nothing')
        # MASK (override view layer, linear-exact grays)
        sc.view_layers[0].use = False
        mask_vl.use = True
        sc.view_settings.view_transform = 'Standard'
        sc.render.film_transparent = False
        sc.world.node_tree.nodes['Background'].inputs[1].default_value = 0.0
        sc.render.dither_intensity = 0.0
        msk = os.path.join(TMPA, f'mask_{tag}_run{run}.png')
        sc.render.filepath = msk
        with bpy.context.temp_override(scene=sc):
            bpy.ops.render.render(write_still=True)
        sc.view_layers[0].use = True
        mask_vl.use = False
        sc.world.node_tree.nodes['Background'].inputs[1].default_value = w0
        sc.render.dither_intensity = d0
        sc.render.film_transparent = film0
        sc.view_settings.view_transform = rt0
        if not os.path.exists(msk) or os.path.getsize(msk) == 0:
            raise RuntimeError(f'MASK {tag} run{run}: wrote nothing')
        print(f'BAKE {tag} run{run} OK', file=sys.stderr)
# restore the knob state read at entry (the bake never saves the blend)
set_wl(wl0[0])
bpy.data.materials['M_COBBLEBED'].node_tree.nodes['WL'].outputs[0].default_value = wl0[1]
sc.camera = bpy.data.objects['FLOOR_CAM']
sc.render.resolution_x, sc.render.resolution_y = 1536, 1536
sc.world.node_tree.nodes['Background'].inputs[1].default_value = w0

# ---- determinism: pixel-compare each pass across runs (byte-compare would
# trip on the PNG writer's own nondeterminism; the stones gate is pixel-based)
gates = {'det': True, 'alpha': True, 'mask': True}
for b in REGIONS:
    for kind in ('art', 'mask'):
        p1 = os.path.join(TMPA, f'{kind}_{b[4]}_run1.png')
        p2 = os.path.join(TMPA, f'{kind}_{b[4]}_run2.png')
        same = np.array_equal(np.asarray(Image.open(p1).convert('RGBA')),
                              np.asarray(Image.open(p2).convert('RGBA')))
        byte_same = open(p1, 'rb').read() == open(p2, 'rb').read()
        print(f'DETERMINISM pixels {kind} {b[4]}: {"OK" if same else "FAIL"} (png-bytes {"identical" if byte_same else "writer-noted"})')
        if not same:
            gates['det'] = False

# ---- slice + gate + pack (law-3 arrangement: every cell bit-equal to source)
def variants_for(tag):
    b = [bb for bb in REGIONS if bb[4] == tag][0]
    _, _, _, (x0, y0, w, h), _, cell, pad = b
    res = {"sq1": 3072, "sq2": 1024, "sq4": 2048}[tag]
    px = 128  # px per world unit (res/ortho)
    shift = pad * px
    out = []
    if tag == 'sq1':
        for (ti, tj) in SQ1_PICK:
            out.append((ti * px, (23 - tj) * px))
    else:
        for r in range(4):
            for c in range(4):
                cx = x0 + c * (w / 4)
                cy = y0 + r * (h / 4)
                ux = shift + round((cx - x0) / w * res)
                uy = shift + round(res - ((cy + w / 4 - y0) / h) * res)
                out.append((ux, uy))
    return out

report = []
for cam_name, ortho, res, frame, tag, cell, pad in REGIONS:
    art = Image.open(os.path.join(TMPA, f'art_{tag}_run1.png')).convert('RGBA')
    msk = Image.open(os.path.join(TMPA, f'mask_{tag}_run1.png')).convert('RGBA')
    if art.size != (res + pad * 256,) * 2 or msk.size != (res + pad * 256,) * 2:
        raise RuntimeError(f'SIZE wrong for {tag}')
    picks = variants_for(tag)
    sheet_cols = 16 if tag == 'sq1' else 4
    rows = (len(picks) + sheet_cols - 1) // sheet_cols
    art_sheet = Image.new('RGBA', (sheet_cols * cell, rows * cell), (0, 0, 0, 0))
    mask_sheet = Image.new('RGBA', art_sheet.size, (0, 0, 0, 0))
    ok_al, ok_mk = True, True
    means, crowns, holds, lows, highs = [], 0, 0, 2**30, 0
    for i, (ux, uy) in enumerate(picks):
        ac = art.crop((ux, uy, ux + cell, uy + cell))
        mc = msk.crop((ux, uy, ux + cell, uy + cell))
        art_sheet.paste(ac, ((i % sheet_cols) * cell, (i // sheet_cols) * cell))
        mask_sheet.paste(mc, ((i % sheet_cols) * cell, (i // sheet_cols) * cell))
        a = np.asarray(ac)
        if a[..., 3].min() != 255:
            ok_al = False; print(f'ALPHA GATE FAIL {tag} variant {i}: alpha {a[...,3].min()}')
        means.append(float(np.asarray(ac.convert('L')).mean()))
        m = np.asarray(mc.convert('L'), dtype=int)
        lows = min(lows, int(m.min())); highs = max(highs, int(m.max()))
        crowns += int(((m >= 168) & (m <= 172)).sum())
        holds += int(((m >= 83) & (m <= 87)).sum())
        if (m < 1).any() or (m > 172).any():
            ok_mk = False
            if (m < 1).any():
                print(f'MASK GATE FAIL {tag} variant {i}: void pixels present')
            if (m > 172).any():
                print(f'MASK GATE FAIL {tag} variant {i}: max-byte {int(m.max())}')
        else:
            lows, highs = lows, highs  # informational byte range already tracked
    name = 'cobblestone-ford' if tag == 'sq1' else ('cobblestone-ford-2x2' if tag == 'sq2' else 'cobblestone-ford-4x4')
    ap = os.path.join(OUT, f'{name}.png'); mp = os.path.join(OUT, f'{name}-mask.png')
    art_sheet.save(ap); mask_sheet.save(mp)
    for src_im, path in ((art_sheet, ap), (mask_sheet, mp)):
        back = np.asarray(Image.open(path).convert('RGBA'))
        if not np.array_equal(back, np.asarray(src_im)):
            raise RuntimeError(f'PACK not bit-equal: {path}')
    gates['alpha'] &= ok_al; gates['mask'] &= ok_mk
    report.append(f'{tag}: art {os.path.relpath(ap, MODROOT)} + mask {os.path.relpath(mp, MODROOT)} {art_sheet.size} | art mean-L {min(means):.0f}-{max(means):.0f} | mask bytes [{lows}..{highs}] crowns/hold-px {crowns}/{holds}')
print('\n'.join(report))
verdict = all(gates.values())
print('GATES', gates, 'VERDICT', 'ALL-GREEN' if verdict else 'RED — see FAIL lines; sheets are current-truth regardless')
sys.exit(0 if verdict else 3)