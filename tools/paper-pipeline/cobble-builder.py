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
WATER_Z = 0.18             # the water height — the wetpass's tuneable (§2):
                           # the mask's slice/z-ramp datum. WATER_PLANE's z is
                           # wired to this (maintainer's ball-park ruling,
                           # 2026-10-22); move it in the GUI to preview the
                           # mix, then this gets set to match and rebuilt.
COLS, ROWS = 3, 4          # the packing per 1×1 tile (§3.1)
JOINT = 0.0                # joint width ZERO (ruling 2026-10-22): nominal extents
                           # fill the cells; walls kiss at the lattice midpoints
                           # (sub-pixel position jitter is indistinguishable from none)
WIGGLE = 0.0006            # §3.1 law: WIGGLE + DRIFT ≤ JOINT/2
SPILL = 0.0015             # max edge-stone outward slide past lattice
EXCURSION = 0.002          # outline bow+jitter+ring-off budget doc (bow amp 0.006)
HMIN, HMAX = 0.06, 0.13    # crown height tuning band (§3.3 knobs)
SUP_R = (0.40, 0.50)       # horizontal roundness r band (per-stone jitter):
                           # low r squares the footprint into a rounded-rect
                           # squircle so stones nest tightly (spec below)
SUP_T_TOP = 0.2            # vertical exponent, top half: flat paving face
SUP_T_BOT = 0.8            # vertical exponent, bottom half: rounded base
SUP_NTOP, SUP_NBUT = 24, 14 # u-grid rings per half (top face / buried dome) —
                            # doubled 2026-10-22: the wall read too few hoops
MERGE_P = 0.22             # neighbour-merge probability per candidate pair
SEEDBASE = 1000
OUT_K = 24                 # plan outline verts per stone (v resolution)
DRIFT = 0.0013             # max interior position drift (no-overlap-safe)
SIZE_J = (0.98, 1.0)       # per-stone size jitter: shrink-only (keeps joints);
                           # floor raised 0.98 (touching ruling): worst pair
                           # gap ≈ JOINT + 2·2% ≈ 1 px, pairs tend to touch

TUNE_DEFAULTS = {
    "base": (0.035, 0.038, 0.043),      # darker + bluish restored (ruling
                                        # 2026-10-22): another tone down, the
                                        # original R:G:B slate ratio (1:1.07:1.23)
    "bed":  (0.035, 0.038, 0.043),      # sand := the stone base (ruling
                                        # 2026-10-22: darker+bluish slate tone;
                                        # the warm tan joints read wrong + tile badly)
    "mottle_s": 0.9, "mottle_light": 1.5,
    "rough": 0.55, "rough_break": 0.16, "rough_s": 20.0,   # matte-stone ruling
    # (2026-10-22: the 0.35/0.10 read as polished metal — silver sheet)
    "speck_s": 14.0, "speck_fac": 0.15, "speck_light": 1.8,
    "pit_s": 28.0, "pit_bump": 0.7, "pit_dist": 0.010, "pit_rough": 0.08,
    "bed_rough": 0.8,
    "peb_mid": 55.0, "peb_fine": 110.0, "peb_tint": 0.18, "peb_bump": 0.55,
    "peb_dist": 0.008,
}
# the FIRST look ladder: same geometry (seed chain ignores the tune),
# material variants only — rows the maintainer looks at and numbers
ROW_VARIANTS = {
    1: {"label": "slate dark A (linear .09) — the too-dark control"},
    2: {"label": "slate mid B (linear .16)", "base": (0.158, 0.168, 0.188)},
    3: {"label": "slate bright C (linear .22)", "base": (0.215, 0.225, 0.245)},
    4: {"label": "coarse sparse flecks @ B", "base": (0.158, 0.168, 0.188),
        "speck_s": 7.0, "speck_fac": 0.22},
    5: {"label": "strong pitting @ B", "base": (0.158, 0.168, 0.188),
        "pit_bump": 1.3, "pit_dist": 0.016, "rough_break": 0.14},
}

BLOCKS = {"AREA_1X1": (-2.0, 2.0, -2.0, 2.0),      # x0,x1,y0,y1 — recipe Stage A
          "AREA_2X2": (-4.0, 4.0, -12.0, -4.0),    # world positions mirrored from
          "AREA_4X4": (-8.0, 8.0, -30.0, -14.0)}   # the boards (law for both files)
CAMS = {"BLK1_CAM": (0.0, 0.0, 4.0, 1024),        # (cx, cy, ortho, res) — boards
        "BLK2_CAM": (0.0, -8.0, 8.0, 1024),       # roster: one cam per design
        "BLK4_CAM": (0.0, -22.0, 16.0, 2048)}     # area (recipe Stage A.5)


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
    # THE OUTPUT LINK (v1 fault: this was missing — black-render diagnosis
    # 2026-10-22, maintainer ruling): surface socket must consume the BSDF
    nt.links.new(n["BSDF"].outputs["BSDF"], n["OUT"].inputs["Surface"])
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
    # same v1 fault as M_COBBLE: output link was missing → bed rendered black
    nt.links.new(n["BSDF"].outputs["BSDF"], n["OUT"].inputs["Surface"])
    return m


# ----------------------------------------------------------------- geometry
def stone_verts_faces(rng, cx, cy, ax, ay, h):
    """Superellipsoid cobble (maintainer spec, 2026-10-22 — verbatim model):

        x(u,v) = (W/2)·sgn(cos u cos v)·|cos u cos v|^r
        y(u,v) = (L/2)·sgn(cos u sin v)·|cos u sin v|^r
        z(u,v) = (H/2)·sgn(sin u)·|sin u|^t      u ∈ [-π/2, π/2], v ∈ [-π, π]

    W,L = 2·(ax, ay): the lattice-anchor extents the edge law is enforced
    on (the packing's half-extents pass straight through; gates read the
    packing, not this mesh). H = 2h so the crown tops out at +h — the
    heights knob band unchanged. The stone's centre sits ON the bed plane
    z=0: z<0 is the t≈0.8 rounded base, buried and clipped by the plane
    ("anchors well into a mortar bed"). r is per-stone jittered inside
    SUP_R; the spec's shape itself is untouched — the jitters riding on
    top (3-lobe bow + WIGGLE outline budget, per-band off jitter, z
    jitter) are the irregular-edge budgets the §3.1 law grants every
    build, identical to the first working scene's.

    LIFT ruling 2026-10-22: the stone's centre no longer sits on the bed
    plane — it is raised by a per-stone jittered quarter-to-a-third of
    the stone's full height (lift ∈ [0.25, 1/3]·2h), so roughly 3/4 of
    the stone stands above the bed and the rounded base still anchors
    below it (the plane clips the crossing). Crowns reach h + lift (the
    shear cap follows the stone up).

    Mesh: horizontal bands sampled UNIFORM IN Z per half (ruling
    2026-10-22: with t=0.2 the spec's z saturates fast, so s-uniform
    bands crowded ~22 of 23 rings onto the top face and left the wall one
    tall band — the maintainer's read was: only ~3 segments spanned the
    whole height). From the spec, z/h = (1−s^(2/r))^(t/2) inverted:
        s = (1 − (z/h)^(2/t))^(r/2)
    each ring still sits exactly ON the spec surface; only the spacing
    changes. Ring counts are unchanged (23 upper + 13 lower + equator)."""
    r_e = rng.uniform(SUP_R[0], SUP_R[1])
    phase = rng.uniform(0.0, 2.0 * math.pi)
    lift = rng.uniform(0.25, 1.0 / 3.0) * (2.0 * h)   # the lift ruling

    # plan outline, built ONCE per stone in stone-local coords and scaled
    # by every horizontal band (coherent vertical bands, as before):
    # squircle corner falloff |cos θ|^r, 3-lobe bow, WIGGLE budget.
    outline = []
    for i in range(OUT_K):
        th = 2.0 * math.pi * i / OUT_K
        c, sn = math.cos(th), math.sin(th)
        ex = ax * math.copysign(abs(c) ** r_e, c)
        ey = ay * math.copysign(abs(sn) ** r_e, sn)
        bow = 1.0 + 0.006 * math.sin(3.0 * th + phase)   # hairline-joint budget
        outline.append([ex * bow + rng.uniform(-WIGGLE, WIGGLE),
                        ey * bow + rng.uniform(-WIGGLE, WIGGLE)])

    # rings sampled uniform in z per half (see docstring): the spec
    # inverted per ring, so bands are evenly spaced up the height.
    def sring(zfrac, t):
        return (1.0 - zfrac ** (2.0 / t)) ** (r_e / 2.0)

    ring_defs = []                                   # listed bottom→top
    for j in range(SUP_NBUT - 1, 0, -1):             # buried dome: z ascending
        ring_defs.append((sring(j / SUP_NBUT, SUP_T_BOT), -h * j / SUP_NBUT))
    ring_defs.append((1.0, 0.0))                     # equator = lattice anchor
    for j in range(1, SUP_NTOP):                     # wall → shoulder → top
        ring_defs.append((sring(j / SUP_NTOP, SUP_T_TOP), h * j / SUP_NTOP))

    def ring_pts(s, z):
        off = rng.uniform(-0.0004, 0.0004)
        out = []
        for pt in outline:
            x = cx + pt[0] * (s + off)
            y = cy + pt[1] * (s + off)
            zz = min(h + lift, z + lift + rng.uniform(-0.002, 0.002))
            out.append([x, y, zz])
        return out

    verts, faces = [], []
    ringlist = [ring_pts(s, z) for s, z in ring_defs]
    for rpts in ringlist:
        for v in rpts:
            verts.append(v)
    K, NR = OUT_K, len(ringlist)
    # buried bottom pole fan (reversed winding: outward = down)
    verts.append([cx, cy, lift - h + rng.uniform(-0.002, 0.002)])
    bp = len(verts) - 1
    for i in range(K):
        faces.append([bp, (i + 1) % K, i])
    for ri in range(NR - 1):
        for i in range(K):
            a0 = ri * K + i
            a1 = ri * K + (i + 1) % K
            b0 = (ri + 1) * K + i
            b1 = (ri + 1) * K + (i + 1) % K
            faces.append([a0, a1, b1, b0])
    # crown pole fan — the shear cap (sheared-off flat top ruling); the
    # shear plane rises with the stone (h + lift)
    tp = len(verts)
    verts.append([cx, cy, min(h + lift, h + lift + rng.uniform(-0.002, 0.002))])
    ci_row = (NR - 1) * K
    for i in range(K):
        faces.append([ci_row + i, ci_row + (i + 1) % K, tp])
    return verts, faces


def emit_stone(coll, cx, cy, ax, ay, h, seed, mats, name):
    rng = random.Random(int(seed))
    verts, faces = stone_verts_faces(rng, cx, cy, ax, ay, h)
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
        emit_stone(coll, st[0], st[1], st[2], st[3], st[4],
                  seed * 331 + gi * 97 + gj * 13 + 5, mats, name)
        stones_out.append((name, st[0], st[1], st[2], st[3], st[4], st[5], gi, gj))
    report[(blockname, k)] = (stones_out, merges, gx_tot, gy_tot)
    return stones_out


# ----------------------------------------------------------------- scenes/rig
def render_audit(sc, out):
    """Post-render numeric audit: read the written file back and print its
    luminance stats. A render stage that emits black must fail LOUDLY here,
    not at someone's gwenview."""
    import numpy
    im = bpy.data.images.load(out)
    px = numpy.asarray(im.pixels[:], dtype=numpy.float32).reshape(-1, im.size[0], im.size[1], 4)[..., :3]
    lum = (0.2126 * px[..., 0] + 0.7152 * px[..., 1] + 0.0722 * px[..., 2]) * (px.max() and 1)
    # NB: bpy image pixels are linear if colorspace=Linear; png Standard view
    # writes sRGB-encoded — stats are comparable run-to-run either way.
    print(f"RENDER AUDIT {out}: {im.size[0]}x{im.size[1]} lum[min={lum.min():.3f} "
          f"max={lum.max():.3f} mean={lum.mean():.5f}]")
    if float(lum.max()) < 0.02:
        print("RENDER AUDIT: near-black output — LIGHTING/SCENE fault (see scene audit above)")
    bpy.data.images.remove(im)
    return float(lum.mean())


def scene_audit(sc):
    """Pre-render numeric audit: the discriminating facts (objects the
    scene's collection tree actually contains; light; camera; world)."""
    objs = sorted(o.name for o in sc.objects)
    lights = [o for o in sc.objects if o.type == 'LIGHT']
    cams = [o for o in sc.objects if o.type == 'CAMERA']
    meshes = [o for o in sc.objects if o.type == 'MESH']
    print(f"SCENE AUDIT {sc.name}: objects={len(objs)} "
          f"[mesh={len(meshes)} light={len(lights)} cam={len(cams)}]")
    for o in lights:
        print(f"  LIGHT {o.name} energy={o.data.energy} loc={tuple(round(v,2) for v in o.location)} "
              f"type={o.data.type} soft={getattr(o.data, 'shadow_soft_size', 'n/a')}")
    for o in cams:
        print(f"  CAM {o.name} loc={tuple(round(v,2) for v in o.matrix_world.translation)} "
              f"ortho={o.data.ortho_scale} rotation={tuple(round(math.degrees(a),1) for a in o.rotation_euler)}")
    w = sc.world
    if w and w.use_nodes:
        for nd in w.node_tree.nodes:
            if nd.type == 'BACKGROUND':
                print(f"  WORLD {w.name} color={tuple(round(c,3) for c in nd.inputs['Color'].default_value)} "
                      f"strength={nd.inputs['Strength'].default_value}")
    mesh_mats = set(m.materials[0].name if m.materials else 'NONE' for m in "") if False else None
    print(f"  first objects: {objs[:4]} ... total mesh objects = {len(meshes)}")


def emit_water_plane(target):
    """The water-height plane (§2 wetpass round): the maintainer's GUI
    tuning knob, linked into the FLOOR scene tree by the caller. NOT in
    any render (hide_render = True) — the plane's z IS the WATER_Z
    constant; the mask stage slices the stones at this height (dry above
    / wet below) and drives the 85→25 stepped ramp from it. Principled
    alpha 0.4 = a see-through sheet in the shaded viewport, so the mix of
    cobbles above and below the water reads while tuning."""
    me = bpy.data.meshes.new("WATER_PLANE")
    me.from_pydata([(-9.0, -31.5, 0.0), (9.0, -31.5, 0.0),
                    (9.0, 3.5, 0.0), (-9.0, 3.5, 0.0)], [], [(0, 1, 2, 3)])
    me.update()
    mat = bpy.data.materials.new("M_WATER_PLANE")
    mat.use_nodes = True
    p = mat.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (0.15, 0.35, 0.55, 1.0)
    p.inputs["Alpha"].default_value = 0.4
    p.inputs["Emission Color"].default_value = (0.25, 0.55, 0.75, 1.0)
    p.inputs["Emission Strength"].default_value = 1.2
    ob = bpy.data.objects.new("WATER_PLANE", me)
    me.materials.append(mat)
    ob.location = (0.0, 0.0, WATER_Z)      # THE WIRE: plane z = the constant
    ob.hide_render = True                  # never in the art or the mask render
    target.collection.objects.link(ob)
    return ob


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
    for (blockname, k), (s_out, merges, gx, gy) in report.items():
        x0, x1, y0b, y1b = BLOCKS[blockname]
        row, col = divmod(k, 4)
        dx0 = x0 + col                      # the design's left lattice line
        y_top = y1b - row                   # the design's top lattice line
        size = gx // COLS                   # design side (1/2/4)
        row, col = divmod(k, 4)
        dx0 = x0 + col * size               # the design's left lattice line
        y_top = y1b - row * size            # the design's top lattice line
        for (name, ccx, ccy, ax, ay, h, interior, gi, gj) in s_out:
            # EDGE LAW: an edge stone's outer face sits INSIDE the design's
            # lattice line by JOINT/2 ± slide (≤SPILL) ± outline wiggle
            # (variant-invariant; the spill slide = the ruled allowance).
            # design side = size (the 2X2/4X4 windows cross internal
            # boundaries; their outer faces still obey the same law).
            if gi == 0:
                f = ccx - ax
                want = dx0 + JOINT / 2
                edge_assert(f, want, name)
            if gi == gx - 1:
                f = ccx + ax
                want = dx0 + size - JOINT / 2
                edge_assert(f, want, name)
            if gj == 0:
                f = ccy - ay
                want = y_top - size + JOINT / 2
                edge_assert(f, want, name)
            if gj == gy - 1:
                f = ccy + ay
                want = y_top - JOINT / 2
                edge_assert(f, want, name)
            assert HMIN - 1e-9 <= h <= HMAX + 1e-9, (name, h)
    merge_map = " ".join(
        f"k{k}:{m}" for (bk, k), (s_out, m, _gx, _gy) in sorted(report.items()) if m)
    hvals = [st[5] for (_b, _k), (s_out, _m, _gx, _gy) in report.items() for st in s_out]
    hmin_px, hmax_px = (min(hvals) * U_PX, max(hvals) * U_PX) if hvals else (0.0, 0.0)
    print(f"== census: designs={len(report)} stones={stones} merges={merges_tot} "
          f"[per-design: {merge_map or 'none'}]")
    # NOTE 2026-10-22 maintainer ruling: mesh intersections between cobbles
    # are FINE — the old bbox 'disjoint law' overlap gate is gone; the
    # packing remains lattice-anchored by the edge law below.
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
    for blockname in ("AREA_1X1", "AREA_2X2", "AREA_4X4"):
        emit_bed(bpy.data.collections["UNDERLAY"], blockname, mats)
    content = bpy.data.collections["CONTENT"]
    fill = (0,) if row is not None else tuple(range(16))
    report = {}
    # one seed base per size (boards roster: 1x1 keeps 1000; 2x2 = 2000;
    # 4x4 = 4000) — the same lattice, larger design windows (recipe A.3)
    for size, seedbase in ((1, SEEDBASE), (2, 2000), (4, 4000)):
        for k in fill:
            pack_cell(content, f"AREA_{size}X{size}", size, k,
                      seed=seedbase + k, mats=mats, report=report)
    sc = build_scene(samples)
    emit_water_plane(sc)                   # the GUI water knob (§2; §3 tune)
    for cam_name, (cx, cy, ortho, res) in CAMS.items():
        cd = bpy.data.cameras.new(cam_name)
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
        cd.clip_start, cd.clip_end = 0.1, 300.0
        ob = bpy.data.objects.new(cam_name, cd)
        ob.location = (cx, cy, 60.0)
        bpy.data.collections["CAMERAS"].objects.link(ob)
    sc.camera = bpy.data.objects["BLK1_CAM"]
    # proof renders (ruling 2026-10-22: ONLY the area renders, one per
    # area — zoom/close cameras retired from the builder)
    renders = [(nm, res, f"/tmp/cobble-proof{ptag}-area-{nm[3:6].lower()}.png")
               for nm, res in ((nm, CAMS[nm][3]) for nm in CAMS)]
    saved = (sc.render.resolution_x, sc.render.resolution_y)
    # context binding: the factory-empty smuggled 'Scene' still owns the
    # context — drop it (FLOOR exists now) and render under temp_override
    # so every op evaluates FLOOR's own view layer.
    fs_ = bpy.data.scenes.get("Scene")
    if fs_ is not None and len(fs_.objects) == 0:
        bpy.data.scenes.remove(fs_)
    scene_audit(sc)
    for cam_name, res, out in renders:
        sc.camera = bpy.data.objects[cam_name]
        sc.render.resolution_x = sc.render.resolution_y = res
        sc.render.filepath = out
        with bpy.context.temp_override(scene=sc, view_layer=sc.view_layers[0]):
            bpy.ops.render.render(write_still=True)
        render_audit(sc, out)
    sc.render.resolution_x, sc.render.resolution_y = saved
    census(report)
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