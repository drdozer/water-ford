# cobble-builder.py — builds ford-cobble.blend FROM PRIMITIVES (cobble recipe Stage A)
#
# docs/cobble-visual-language.md = the look spec; docs/export-recipe.md =
# the ladder contract. The boards mirror (mandatory scene template, spec
# §3.5): this file = the cobble generator; the .blend is BUILD OUTPUT
# (factory-empty, seeded, idempotent, FLOOR-only — the factory-Scene
# idiom from boards-builder.py). v0 scope = the LOOK ROUND: packing +
# loaf geometry + the §3.2a polished-slate stone + §3.2 sand/pebble-rubble
# bed (shader faux texture, sandy palette) with --row/--tune overrides;
# proof renders + contact ladders for the maintainer's eyes. The full
# block roster + save path + --wetpass land after the look rules settle.
#
#   blender -b --python cobble-builder.py -- [--no-save] [--row N]
#     [--tune k=v,...] [--proof-tag TAG] [--samples N] [--outfile PATH]
#
# Rulings encoded (spec §3, dated there):
#   §3.1  oblong cobbles packed 3×4 per 1×1 tile; occasional x-adjacent
#         MERGES into large cobbles (interior stones only; a merge
#         absorbs both sub-cells' stones into one big oblong);
#   §3.1  EDGE LAW: outermost stones' outer faces sit INSIDE the tile
#         edge by JOINT/2 (variant-invariant — neighbours' joints line
#         up); a seeded outward slide ≤ SPILL = the allowed small spill
#         (hidden by shadows/neighbours); interior drift = joint-scale in
#         v0 — internal-tile crossing jiggle for 2×2/4×4 lands with the
#         collision-resolve pass (v1); per-stone geometry jiggle = sizes,
#         heights, outline bow, p-exponent, merges, z-noise (position
#         jiggle is constrained by the no-overlap + thin-joint law);
#   §3.2a polished slate stones: low base roughness + low-contrast
#         roughness breakup (never flat = never plastic); fleck speckle
#         into Base Color at low factor (tonal variety, zero metallic);
#         smooth-Voronoi pitting = low-amplitude bump + pit roughness
#         lift (matte pit catchers, never shiny dimples); per-stone
#         seeded texture pans (cobble_off attrs);
#   §3.2  bed = FAUX sand/pebble rubble IN THE SHADER, sandy palette
#         (no extra geometry): two Voronoi pebble scales + fines noise;
#         per-pebble tint jitter; bump relief matte-bumpy; recessed
#         joint shading comes from geometry (joints), not a black tone;
#   §3.3  shadow law: everything casts+catches (nothing disabled); bed =
#         real plane at z=0, stones start z=0 (contact), crowns inflate
#         above (flattened dome: plateau inside ρ≤0.35, smooth knee to
#         the skirt line — the loaf archetype);
#   §3.3  heights = U(HMIN, HMAX) tuning knobs; the wet mapping lands
#         with the wetpass round (§2).
import bpy
import math
import os
import sys
import random

HERE = os.path.dirname(os.path.abspath(__file__))

U_PX = 128                 # 1 unit = 1 game tile = 128 px (contract)
COLS, ROWS = 3, 4          # the packing per 1×1 tile (§3.1)
JOINT = 0.012              # joint width u (~1.5 px) — thin joints
WIGGLE = 0.0015            # plan jitter (the excursion budget: see §3.1 law comment)
SPILL = 0.004              # max edge-stone outward slide past lattice
EXCURSION = 0.006          # outline bow+jitter+ring-off budget (bow amp 0.025)
HMIN, HMAX = 0.06, 0.13    # crown height tuning band (§3.3 knobs)
ZSKIRT = 0.010             # outline-ring height (the loaf's rounded knee)
MERGE_P = 0.22             # neighbour-merge probability per candidate pair
SEEDBASE = 1000
RING_R = (1.0, 0.82, 0.60, 0.38, 0.18)   # loaf rings (plan-outward first)
OUT_K = 24                 # outline verts per loaf
DRIFT = 0.0015             # max interior position drift (no-overlap-safe)
SIZE_J = (0.94, 0.99)      # per-stone size jitter: shrink-only (keeps joints)

TUNE_DEFAULTS = {
    "base": (0.082, 0.088, 0.101),      # slate candidate (~L85)
    "bed":  (0.297, 0.237, 0.169),      # sandy anchor (warm tan, ~L110 linear-ish)
    "mottle_s": 0.9, "mottle_light": 1.5,
    "rough": 0.35, "rough_break": 0.10, "rough_s": 20.0,
    "speck_s": 14.0, "speck_fac": 0.15, "speck_light": 1.8,
    "pit_s": 28.0, "pit_bump": 0.7, "pit_dist": 0.010, "pit_rough": 0.08,
    "bed_rough": 0.8,
    "peb_mid": 55.0, "peb_fine": 110.0, "peb_tint": 0.18, "peb_bump": 0.55,
    "peb_dist": 0.008,
}
# the FIRST look ladder: same geometry (seed chain ignores the tune),
# material variants only — rows the maintainer looks at and numbers
ROW_VARIANTS = {
    1: {"label": "slate L85 + sandy bed (defaults)"},
    2: {"label": "less shiny", "rough": 0.45, "rough_break": 0.06},
    3: {"label": "darker slate", "base": (0.047, 0.051, 0.060)},
    4: {"label": "coarse sparse flecks", "speck_s": 7.0, "speck_fac": 0.22},
    5: {"label": "strong pitting", "pit_bump": 1.3, "pit_dist": 0.016,
        "rough_break": 0.14},
}

BLOCKS = {"AREA_1X1": (-2.0, 2.0, -2.0, 2.0)}
CAM1 = ("BLK1_CAM", 0.0, 0.0, 4.0)


# ------------------------------------------------------------------ materials
def mat_nodes(nt, spec):
    made = {}
    for nd in spec:
        n = nt.nodes.new(nd[0])
        n.name = nd[1]
        if len(nd) > 2 and nd[2]:
            n.location = nd[2]
        if len(nd) > 3:
            for k, v in nd[3].items():
                try:
                    setattr(n, k, v)
                except Exception:
                    pass
        if len(nd) > 4:
            for k, v in nd[4].items():
                sock = n.inputs.get(k)
                if sock is not None and hasattr(sock, "default_value"):
                    try:
                        sock.default_value = v
                    except Exception:
                        pass
        made[nd[1]] = n
    return made


def set_ramp(node, stops):
    while len(node.color_ramp.elements) > 1:
        node.color_ramp.elements.remove(node.color_ramp.elements[-1])
    e = node.color_ramp.elements[0]
    e.position = stops[0][0]
    e.color = stops[0][1]
    for pos, col in stops[1:]:
        e = node.color_ramp.elements.new(pos)
        e.color = col


def build_m_cobble(tune):
    """§3.2a polished stone. Vectors = Object coords + the per-stone pan
    attr (cobble_off) so every stone gets its own pan of a global field."""
    m = bpy.data.materials.new("M_COBBLE")
    m.use_nodes = True
    nt = m.node_tree
    for n_ in list(nt.nodes):
        nt.nodes.remove(n_)
    n = mat_nodes(nt, [
        ("ShaderNodeTexCoord", "TX", (-560, 150)),
        ("ShaderNodeAttribute", "ATTR_OFF", (-560, -170), {"attribute_name": "cobble_off"}),
        ("ShaderNodeCombineXYZ", "OFF", (-380, -170)),
        ("ShaderNodeVectorMath", "VEC", (-160, 60), {"operation": "ADD"}),
        ("ShaderNodeTexNoise", "MOTTLE", (60, -60), {"noise_dimensions": "3D"}),
        ("ShaderNodeValToRGB", "R_BASE", (300, -60)),
        ("ShaderNodeTexVoronoi", "SPECK", (60, 240), {"feature": "F1"}),
        ("ShaderNodeValToRGB", "R_SPECK", (300, 280)),
        ("ShaderNodeMixRGB", "MIX_SPECK", (560, 60), {"blend_type": "MIX"}),
        ("ShaderNodeTexVoronoi", "PITS", (60, -320), {"feature": "F1"}),
        ("ShaderNodeMapRange", "R_PITR", (300, -340), {"clamp": True}),
        ("ShaderNodeTexNoise", "RBREAK", (60, -160), {"noise_dimensions": "3D"}),
        ("ShaderNodeMapRange", "R_BRK", (300, -220), {"clamp": True}),
        ("ShaderNodeMath", "ADD_BRK", (520, -180), {"operation": "ADD"}),
        ("ShaderNodeMath", "ADD_PIT", (700, -220), {"operation": "ADD"}),
        ("ShaderNodeMapRange", "R_ROUGH", (880, -200), {"clamp": True}),
        ("ShaderNodeBump", "BUMP", (420, -430)),
        ("ShaderNodeBsdfPrincipled", "BSDF", (1120, 40)),
        ("ShaderNodeOutputMaterial", "OUT", (1360, 40)),
    ])
    base = tune["base"]
    set_ramp(n["R_BASE"], [(0.0, (base[0], base[1], base[2], 1.0)),
                           (1.0, (min(1.0, base[0] * tune["mottle_light"]),
                                  min(1.0, base[1] * tune["mottle_light"]),
                                  min(1.0, base[2] * tune["mottle_light"]), 1.0))])
    fl = min(1.0, base[0] * tune["speck_light"])
    set_ramp(n["R_SPECK"], [(0.30, (0.0, 0.0, 0.0, 1.0)), (0.34, (fl, fl, fl, 1.0))])
    nt.links.new(n["TX"].outputs["Object"], n["VEC"].inputs[0])
    nt.links.new(n["ATTR_OFF"].outputs["Color"], n["OFF"].inputs[0])
    nt.links.new(n["OFF"].outputs[0], n["VEC"].inputs[1])
    for tex in ("MOTTLE", "SPECK", "PITS", "RBREAK"):
        nt.links.new(n["VEC"].outputs["Vector"], n[tex].inputs["Vector"])
    nt.links.new(n["MOTTLE"].outputs["Fac"], n["R_BASE"].inputs["Fac"])
    nt.links.new(n["SPECK"].outputs["Distance"], n["R_SPECK"].inputs["Fac"])
    nt.links.new(n["R_BASE"].outputs["Color"], n["MIX_SPECK"].inputs["Color1"])
    nt.links.new(n["R_SPECK"].outputs["Color"], n["MIX_SPECK"].inputs["Color2"])
    nt.links.new(n["MIX_SPECK"].outputs["Color"], n["BSDF"].inputs["Base Color"])
    n["MIX_SPECK"].inputs["Fac"].default_value = tune["speck_fac"]
    # roughness = base + breakup(±rough_break) + pit lift, clamped 0.12..0.9
    nt.links.new(n["RBREAK"].outputs["Fac"], n["R_BRK"].inputs["Value"])
    brk = n["R_BRK"]
    brk.inputs["From Min"].default_value = 0.35
    brk.inputs["From Max"].default_value = 0.65
    brk.inputs["To Min"].default_value = -tune["rough_break"]
    brk.inputs["To Max"].default_value = tune["rough_break"]
    n["ADD_BRK"].inputs[0].default_value = tune["rough"]
    nt.links.new(n["R_BRK"].outputs[0], n["ADD_BRK"].inputs[1])
    nt.links.new(n["PITS"].outputs["Distance"], n["R_PITR"].inputs["Value"])
    pr = n["R_PITR"]
    pr.inputs["From Min"].default_value = 0.05
    pr.inputs["From Max"].default_value = 0.30
    pr.inputs["To Min"].default_value = 0.0
    pr.inputs["To Max"].default_value = tune["pit_rough"]
    n["ADD_PIT"].inputs[0].default_value = 0.0
    nt.links.new(n["R_PITR"].outputs[0], n["ADD_PIT"].inputs[1])
    nt.links.new(n["ADD_BRK"].outputs[0], n["ADD_PIT"].inputs[0])
    nt.links.new(n["ADD_PIT"].outputs[0], n["R_ROUGH"].inputs["Value"])
    rr = n["R_ROUGH"]
    rr.inputs["From Min"].default_value = 0.0
    rr.inputs["From Max"].default_value = 2.0
    rr.inputs["To Min"].default_value = 0.12
    rr.inputs["To Max"].default_value = 0.9
    nt.links.new(n["R_ROUGH"].outputs[0], n["BSDF"].inputs["Roughness"])
    # pits = low-amplitude bump (non-reflective: matte pits + rough lift)
    nt.links.new(n["PITS"].outputs["Distance"], n["BUMP"].inputs["Height"])
    nt.links.new(n["BUMP"].outputs["Normal"], n["BSDF"].inputs["Normal"])
    n["BUMP"].inputs["Strength"].default_value = tune["pit_bump"]
    n["BUMP"].inputs["Distance"].default_value = tune["pit_dist"]
    n["SPECK"].inputs["Scale"].default_value = tune["speck_s"]
    n["PITS"].inputs["Scale"].default_value = tune["pit_s"]
    n["MOTTLE"].inputs["Scale"].default_value = tune["mottle_s"]
    n["RBREAK"].inputs["Scale"].default_value = tune["rough_s"]
    return m


def build_m_cobblebed(tune):
    """§3.2 bed ruling: FAUX sand/pebble rubble in the shader, sandy
    palette. Two Voronoi pebble scales (mid pebbles + fines) drive: a
    step ramp (pebble separation: darker crevice edges / lighter crowns),
    a per-pebble tint jitter (the Color output ramped), and a low bump;
    fine-value noise rides under everything (sand grain)."""
    m = bpy.data.materials.new("M_COBBLEBED")
    m.use_nodes = True
    nt = m.node_tree
    for n_ in list(nt.nodes):
        nt.nodes.remove(n_)
    n = mat_nodes(nt, [
        ("ShaderNodeTexCoord", "TX", (-900, 0)),
        ("ShaderNodeTexVoronoi", "PEB", (-700, 160), {"feature": "F1"}),
        ("ShaderNodeValToRGB", "R_PEBSEP", (-500, 160)),
        ("ShaderNodeTexVoronoi", "TINTV", (-700, -40), {"feature": "F1"}),
        ("ShaderNodeValToRGB", "R_TINT", (-500, -40)),
        ("ShaderNodeMixRGB", "MIX_TINT", (-260, 40), {"blend_type": "MIX"}),
        ("ShaderNodeTexNoise", "FINES", (-700, -240), {"noise_dimensions": "3D"}),
        ("ShaderNodeValToRGB", "R_FRIN", (-500, -240)),
        # crevice darkening: pebble separation ramp also as a multiply
        ("ShaderNodeMixRGB", "MIX_CRV", (-60, 0), {"blend_type": "MULTIPLY"}),
        ("ShaderNodeBsdfPrincipled", "BSDF", (160, -60)),
        ("ShaderNodeOutputMaterial", "OUT", (420, -60)),
        ("ShaderNodeBump", "BUMP", (260, -420)),
    ])
    bed = tune["bed"]
    nt.links.new(n["TX"].outputs["Object"], n["PEB"].inputs["Vector"])
    nt.links.new(n["TX"].outputs["Object"], n["TINTV"].inputs["Vector"])
    nt.links.new(n["TX"].outputs["Object"], n["FINES"].inputs["Vector"])
    # pebble separation: F1 distance low near pebble centers (lighter),
    # high at crevices (darker) — CONVEX contrast step ramp
    set_ramp(n["R_PEBSEP"], [(0.00, tuple(bed) + (1.0,)),
                             (0.55, tuple(c * 1.22 for c in bed) + (1.0,)),
                             (1.00, tuple(c * 0.55 for c in bed) + (1.0,))])
    # per-pebble tint: the Voronoi Color output = per-cell random; ramp it
    # into a sandy jitter family
    tint_lo = tuple(max(0.02, c * 0.82) for c in bed)
    tint_hi = tuple(min(1.0, c * 1.18) for c in bed)
    set_ramp(n["R_TINT"], [(0.0, tint_lo + (1.0,)), (1.0, tint_hi + (1.0,))])
    nt.links.new(n["TINTV"].outputs["Color"], n["R_TINT"].inputs["Fac"])
    # fines noise: subtle value micro-variation over the whole bed
    set_ramp(n["R_FRIN"], [(0.35, (1.0, 1.0, 1.0, 1.0)),
                           (0.65, (0.88, 0.88, 0.88, 1.0))])
    nt.links.new(n["FINES"].outputs["Fac"], n["R_FRIN"].inputs["Fac"])
    # MIX_TINT: base = pebsep color, factor = per-pebble tint amount
    nt.links.new(n["PEB"].outputs["Distance"], n["R_PEBSEP"].inputs["Fac"])
    nt.links.new(n["R_PEBSEP"].outputs["Color"], n["MIX_TINT"].inputs["Color1"])
    nt.links.new(n["R_TINT"].outputs["Color"], n["MIX_TINT"].inputs["Color2"])
    n["MIX_TINT"].inputs["Fac"].default_value = tune["peb_tint"]
    nt.links.new(n["FINES"].outputs["Fac"], n["R_FRIN"].inputs["Fac"])
    nt.links.new(n["MIX_TINT"].outputs["Color"], n["MIX_CRV"].inputs["Color1"])
    nt.links.new(n["R_FRIN"].outputs["Color"], n["MIX_CRV"].inputs["Color2"])
    nt.links.new(n["MIX_CRV"].outputs["Color"], n["BSDF"].inputs["Base Color"])
    nt.links.new(n["PEB"].outputs["Distance"], n["BUMP"].inputs["Height"])
    nt.links.new(n["BUMP"].outputs["Normal"], n["BSDF"].inputs["Normal"])
    n["BUMP"].inputs["Strength"].default_value = tune["peb_bump"]
    n["BUMP"].inputs["Distance"].default_value = tune["peb_dist"]
    n["PEB"].inputs["Scale"].default_value = tune["peb_mid"]
    n["TINTV"].inputs["Scale"].default_value = tune["peb_mid"]
    n["FINES"].inputs["Scale"].default_value = tune["peb_fine"]
    n["BSDF"].inputs["Roughness"].default_value = tune["bed_rough"]
    return m


# ----------------------------------------------------------------- geometry
def _sstep01(r):
    """0 at r<=0.35 (top plateau), 1 at r>=0.95 (the rounded knee)."""
    t = min(max((r - 0.35) / (0.95 - 0.35), 0.0), 1.0)
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def loaf_verts_faces(rng, cx, cy, ax, ay, h):
    """Loaf: rounded-rect oblong plan (per-stone superellipse exponent p),
    irregular edges (outline jitter + 3-lobe bow), flattened dome z
    (plateau inside ρ≤0.35, smooth knee to the skirt line), base ring at
    z=0 (bed contact). One shared outline per stone keeps the vertical
    bands coherent."""
    p = rng.uniform(2.8, 4.2)
    phase = rng.uniform(0.0, 2.0 * math.pi)
    # the caller's (ax, ay) = the stone's FINAL plan half-extents (already
    # joint-aware + size-jittered); the outline budget (wiggle excursion)
    # must fit inside the joint: WIGGLE + DRIFT <= JOINT/2 (§3.1 law).
    outline = []
    for i in range(OUT_K):
        th = 2.0 * math.pi * i / OUT_K
        c, s = math.cos(th), math.sin(th)
        ex = cx + ax * math.copysign(abs(c) ** (2.0 / p), c)
        ey = cy + ay * math.copysign(abs(s) ** (2.0 / p), s)
        bow = 1.0 + 0.025 * math.sin(3.0 * th + phase)
        outline.append([cx + (ex - cx) * bow + rng.uniform(-WIGGLE, WIGGLE),
                        cy + (ey - cy) * bow + rng.uniform(-WIGGLE, WIGGLE)])

    verts, faces = [], []
    ring_defs = [(1.0, 0.0), (1.0, ZSKIRT)]
    for rho in RING_R[1:]:
        ring_defs.append((rho, ZSKIRT + (h - ZSKIRT) * (1.0 - _sstep01(rho))))

    def ring_pts(rho, z):
        off = rng.uniform(-0.0010, 0.0010)
        out = []
        for pt in outline:
            x = cx + (pt[0] - cx) * (rho + off)
            y = cy + (pt[1] - cy) * (rho + off)
            zz = z if z == 0.0 else min(h, z + rng.uniform(-0.002, 0.002))
            out.append([x, y, zz])
        return out

    ringlist = [ring_pts(r, z) for r, z in ring_defs]
    ringlist.append(ring_pts(0.06, h))
    for rpts in ringlist:
        for v in rpts:
            verts.append(v)
    K, NR = OUT_K, len(ringlist)
    for ri in range(NR - 1):
        for i in range(K):
            a0 = ri * K + i
            a1 = ri * K + (i + 1) % K
            b0 = (ri + 1) * K + i
            b1 = (ri + 1) * K + (i + 1) % K
            faces.append([a0, a1, b1, b0])
    ci = len(verts)
    verts.append([cx, cy, min(h, h + rng.uniform(-0.002, 0.002))])
    ci_row = (NR - 1) * K
    for i in range(K):
        faces.append([ci_row + i, ci_row + (i + 1) % K, ci])
    return verts, faces


def emit_loaf(coll, cx, cy, ax, ay, h, seed, mats, name):
    rng = random.Random(int(seed))
    verts, faces = loaf_verts_faces(rng, cx, cy, ax, ay, h)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    a = me.attributes.new("cobble_seed", "FLOAT", "FACE")
    for fi in range(len(faces)):
        a.data[fi].value = rng.random()
    ox, oy = rng.uniform(0.0, 10.0), rng.uniform(0.0, 10.0)
    a = me.attributes.new("cobble_off", "FLOAT_COLOR", "FACE")
    for fi in range(len(faces)):
        a.data[fi].color = (ox, oy, 0.0, 1.0)
    ob = bpy.data.objects.new(name, me)
    me.materials.append(mats["M_COBBLE"])
    coll.objects.link(ob)
    return ob


def emit_bed(coll, blockname, mats):
    x0, x1, y0, y1 = BLOCKS[blockname]
    me = bpy.data.meshes.new(f"{blockname}_BED")
    me.from_pydata([(x0, y0, 0.0), (x1, y0, 0.0), (x1, y1, 0.0), (x0, y1, 0.0)],
                   [], [(0, 1, 2, 3)])
    me.update()
    ob = bpy.data.objects.new(me.name, me)
    me.materials.append(mats["M_COBBLEBED"])
    coll.objects.link(ob)


def pack_cell(coll, blockname, size, k, seed, mats, report):
    """Cobbles for design sprite k: COLS×ROWS sub-cells per game tile;
    interiors drift at joint scale; edge stones pinned (spill law);
    x-adjacent interior merges = large cobbles."""
    x0, x1, y0b, y1b = BLOCKS[blockname]
    row, col = divmod(k, 4)
    dx0 = x0 + col * size
    y_top = y1b - row * size             # the design's TOP edge y
    subx, suby = 1.0 / COLS, 1.0 / ROWS
    gx_tot, gy_tot = size * COLS, size * ROWS
    ax0, ay0 = (subx - JOINT) / 2.0, (suby - JOINT) / 2.0
    stones = {}
    for gi in range(gx_tot):
        for gj in range(gy_tot):
            rng = random.Random(seed * 331 + gi * 97 + gj * 13 + 5)
            ccx = dx0 + (gi + 0.5) * subx
            ccy = y_top - (gy_tot - 1 - gj + 0.5) * suby
            ex_l, ex_r = gi == 0, gi == gx_tot - 1
            ey_b, ey_t = gj == 0, gj == gy_tot - 1
            interior = not (ex_l or ex_r or ey_b or ey_t)
            jx = rng.uniform(-DRIFT, DRIFT)
            jy = rng.uniform(-DRIFT, DRIFT)
            if ex_l:
                jx = 0.0
                ccx -= rng.uniform(-SPILL, SPILL)      # the seedded spill slide
            if ex_r:
                jx = 0.0
                ccx += rng.uniform(-SPILL, SPILL)
            if ey_b:
                jy = 0.0
                ccy -= rng.uniform(-SPILL, SPILL)
            if ey_t:
                jy = 0.0
                ccy += rng.uniform(-SPILL, SPILL)
            # edge stones keep NOMINAL extent (their face = the lattice
            # anchor — variant-invariant); interior stones may shrink
            sj = 1.0 if not interior else rng.uniform(*SIZE_J)
            ax, ay = ax0 * sj, ay0 * sj
            jxx = 0.0 if (ex_l or ex_r) else jx
            jyy = 0.0 if (ey_b or ey_t) else jy
            stones[(gi, gj)] = [ccx + jxx, ccy + jyy, ax, ay,
                                rng.uniform(HMIN, HMAX), interior]
    # merges: absorb an x-adjacent neighbour. Edge-column members allowed
    # (their pinned face carries over — the union never spans both
    # boundaries for COLS=3, and never crosses one for the interior
    # case). The merged extent preserves pinned faces exactly.
    merges = 0
    for gi in range(gx_tot - 1):
        for gj in range(gy_tot):
            if (gi, gj) not in stones:
                continue
            left, right = stones.get((gi, gj)), stones.get((gi + 1, gj))
            if left is None or right is None:
                continue
            rngm = random.Random(seed * 331 + gi * 97 + gj * 13 + 77)
            if rngm.random() < MERGE_P:
                ccx = (left[0] + right[0]) / 2.0
                ax2 = (right[0] - left[0]) / 2.0 + (left[2] + right[2]) / 2.0
                left[0], left[2] = ccx, ax2
                del stones[(gi + 1, gj)]
                merges += 1
    stones_out = []
    for (gi, gj), st in sorted(stones.items()):
        name = f"C_{blockname}_{k}_{gi}_{gj}"
        emit_loaf(coll, st[0], st[1], st[2], st[3], st[4],
                  seed * 331 + gi * 97 + gj * 13 + 5, mats, name)
        stones_out.append((name, st[0], st[1], st[2], st[3], st[4], st[5], gi, gj))
    report[(blockname, k)] = (stones_out, merges, gx_tot, gy_tot)
    return stones_out


# ----------------------------------------------------------------- scenes/rig
def build_scene(samples):
    s = bpy.data.scenes.new("FLOOR")
    r = s.render
    r.engine = "CYCLES"
    r.resolution_x = 512
    r.resolution_y = 512
    s.cycles.samples = samples
    s.cycles.use_adaptive_sampling = True
    s.cycles.use_denoising = False
    s.cycles.max_bounces = 12
    s.view_settings.view_transform = "Standard"
    s.render.film_transparent = False
    s.world = bpy.data.worlds["BOARDS_WORLD"]
    for cname in ("CONTENT", "UNDERLAY", "LIGHTING", "CAMERAS"):
        s.collection.children.link(bpy.data.collections[cname])
    return s


def build_rig():
    """Boards rig VERBATIM (§3.5 mandatory template)."""
    w = bpy.data.worlds.new("BOARDS_WORLD")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.55, 0.55, 0.55, 1.0)
    bg.inputs[1].default_value = 0.06
    kd = bpy.data.lights.new("KEY", "POINT")
    kd.energy = 1800000.0
    kd.shadow_soft_size = 0.1
    k = bpy.data.objects.new("KEY", kd)
    k.location = (-126.0, 0.0, 126.0)
    bpy.data.collections["LIGHTING"].objects.link(k)


def census(report):
    # tol = the edge stone's total planned excursion: slide (SPILL) + the
    # outline budget (EXCURSION) + numeric margin
    tol = SPILL + EXCURSION + 1e-3
    def edge_assert(f, want, name):
        assert abs(f - want) <= tol, (name, f, want, tol)

    stones = merges_tot = 0
    for (blockname, k), (s_out, merges, gx, gy) in report.items():
        stones += len(s_out)
        merges_tot += merges
    bboxes = []
    for (blockname, k), (s_out, merges, gx, gy) in report.items():
        x0, x1, y0b, y1b = BLOCKS[blockname]
        row, col = divmod(k, 4)
        dx0 = x0 + col                      # the design's left lattice line
        y_top = y1b - row                   # the design's top lattice line
        for (name, ccx, ccy, ax, ay, h, interior, gi, gj) in s_out:
            bboxes.append((ccx - ax, ccx + ax, ccy - ay, ccy + ay, name))
            # EDGE LAW: an edge stone's outer face sits INSIDE the design's
            # lattice line by JOINT/2 ± slide (≤SPILL) ± outline wiggle
            # (variant-invariant; the spill slide = the ruled allowance).
            if gi == 0:
                f = ccx - ax
                want = dx0 + JOINT / 2
                edge_assert(f, want, name)
            if gi == gx - 1:
                f = ccx + ax
                want = dx0 + 1.0 - JOINT / 2
                edge_assert(f, want, name)
            if gj == 0:
                f = ccy - ay
                want = y_top - 1.0 + JOINT / 2
                edge_assert(f, want, name)
            if gj == gy - 1:
                f = ccy + ay
                want = y_top - JOINT / 2
                edge_assert(f, want, name)
            assert HMIN - 1e-9 <= h <= HMAX + 1e-9, (name, h)
    bad = 0
    obs_hmin = obs_hmax = None
    for i in range(len(bboxes)):
        for j in range(i + 1, len(bboxes)):
            A, B = bboxes[i], bboxes[j]
            if A[0] < B[1] - 1e-6 and B[0] < A[1] - 1e-6 and A[2] < B[3] - 1e-6 and B[2] < A[3] - 1e-6:
                bad += 1
    merge_map = " ".join(
        f"k{k}:{m}" for (bk, k), (s_out, m, _gx, _gy) in sorted(report.items()) if m)
    hvals = [st[5] for (_b, _k), (s_out, _m, _gx, _gy) in report.items() for st in s_out]
    hmin_px, hmax_px = (min(hvals) * U_PX, max(hvals) * U_PX) if hvals else (0.0, 0.0)
    print(f"== census: designs={len(report)} stones={stones} merges={merges_tot} "
          f"[per-design: {merge_map or 'none'}]")
    print(f"== overlap gate: {bad} overlaps (0 = the disjoint law)")
    print(f"== edge-law + height-band gates: {stones} stones checked, tol={tol:.4f}; "
          f"obs heights px = [{hmin_px:.1f} .. {hmax_px:.1f}] (knobs {HMIN*U_PX:.0f}..{HMAX*U_PX:.0f})")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    no_save = False
    row = None
    ptag = ""
    samples = 48
    outfile = os.path.join(HERE, "..", "..", "blender", "ford-cobble.blend")
    tune_over = {}
    for i, a in enumerate(argv):
        if a == "--no-save":
            no_save = True
        elif a == "--row":
            row = int(argv[i + 1])
        elif a == "--proof-tag":
            ptag = argv[i + 1]
        elif a == "--samples":
            samples = int(argv[i + 1])
        elif a == "--outfile":
            outfile = os.path.abspath(argv[i + 1])
        elif a == "--tune":
            for kv in argv[i + 1].split(","):
                kk, vv = kv.split("=")
                tune_over[kk.strip()] = vv.strip()
    tune = dict(TUNE_DEFAULTS)
    label = ""
    if row is not None:
        spec = ROW_VARIANTS[row]
        label = f"ROW{row}: {spec.get('label', '')}"
        for kk, vv in spec.items():
            if kk != "label":
                tune[kk] = tuple(float(x) for x in vv) if isinstance(vv, tuple) else vv
    for kk, vv in tune_over.items():
        tune[kk] = tuple(float(x) for x in vv.split(";")) if ";" in vv else float(vv)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    for cn in ("CONTENT", "UNDERLAY", "LIGHTING", "CAMERAS"):
        bpy.data.collections.new(cn)
    build_rig()
    mats = {"M_COBBLE": build_m_cobble(tune),
            "M_COBBLEBED": build_m_cobblebed(tune)}
    emit_bed(bpy.data.collections["UNDERLAY"], "AREA_1X1", mats)
    content = bpy.data.collections["CONTENT"]
    fill = (0,) if row is not None else tuple(range(16))
    report = {}
    for k in fill:
        pack_cell(content, "AREA_1X1", 1, k, seed=SEEDBASE + k, mats=mats, report=report)
    sc = build_scene(samples)
    cd = bpy.data.cameras.new("BLK1_CAM")
    cd.type = "ORTHO"
    cd.ortho_scale = CAM1[3]
    cd.clip_start, cd.clip_end = 0.1, 300.0
    c1 = bpy.data.objects.new("BLK1_CAM", cd)
    c1.location = (CAM1[1], CAM1[2], 60.0)
    bpy.data.collections["CAMERAS"].objects.link(c1)
    sc.camera = c1
    # proof renders (boards PROOF_ZOOM idiom: create once, reuse, remove)
    pcd = bpy.data.cameras.new("PROOF_ZOOM")
    pcd.type = "ORTHO"
    pcd.ortho_scale = 1.3
    pz = bpy.data.objects.new("PROOF_ZOOM", pcd)
    pz.location = (-1.5, 1.5, 60.0)      # cell (0,0) = AREA_1X1's top-left design
    bpy.data.collections["CAMERAS"].objects.link(pz)
    pcd2 = bpy.data.cameras.new("PROOF_CLOSE")
    pcd2.type = "ORTHO"
    pcd2.ortho_scale = 0.6
    pc = bpy.data.objects.new("PROOF_CLOSE", pcd2)
    pc.location = (-1.5, 1.5, 60.0)
    bpy.data.collections["CAMERAS"].objects.link(pc)
    renders = [("PROOF_ZOOM", 512, f"/tmp/cobble-proof{ptag}-zoom.png"),
               ("PROOF_CLOSE", 2048, f"/tmp/cobble-proof{ptag}-close.png")]
    if row is None:
        renders.append(("BLK1_CAM", 1024, f"/tmp/cobble-proof{ptag}-area.png"))
    saved = (sc.render.resolution_x, sc.render.resolution_y)
    for cam_name, res, out in renders:
        sc.camera = bpy.data.objects[cam_name]
        sc.render.resolution_x = sc.render.resolution_y = res
        sc.render.filepath = out
        bpy.ops.render.render(write_still=True, scene=sc.name)
    sc.render.resolution_x, sc.render.resolution_y = saved
    census(report)
    bpy.data.objects.remove(pz, do_unlink=True)
    bpy.data.objects.remove(pc, do_unlink=True)
    if no_save:
        print(f"COBBLE PROOF {label} done (renders only, nothing saved)")
        return
    # the Scene-fix idiom (boards, 2026-10-22) — the save path
    fs_ = bpy.data.scenes.get("Scene")
    if fs_ is not None and len(fs_.objects) == 0:
        bpy.data.scenes.remove(fs_)
    for w_ in bpy.context.window_manager.windows:
        w_.scene = sc
    bpy.context.window.scene = sc
    bpy.ops.wm.save_as_mainfile(filepath=outfile, compress=True)
    print(f"COBBLE BUILT mats={len(mats)} cells={len(fill)} out={outfile}")


if __name__ == "__main__":
    main()