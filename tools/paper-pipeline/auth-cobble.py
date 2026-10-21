# cobblestone ford factory — full mechanical rebuild of blender/ford-cobble.blend.
#
# Provenance (2026-10-21): geometry functions recovered verbatim from the cobble
# session's factory script (`.cache/blender-cobble/auth-cobble-probe.py`, the
# accumulated artifact the session edited in place); the GRAPH literal below is
# a mechanical extraction of the blend's material node trees (inputs verbatim,
# ramps verbatim incl. WL knobs) captured by a headless oracle dump. The blend
# itself is a BUILD OUTPUT (gitignored — it exceeds GitHub's 100 MB file limit)
# and is reproducible from this script alone.
#
# Product ruling (maintainer, 2026-10-21): NO wetness-mask sheets — the wet look
# lives in the art pixels (M_COBBLE's WL ramp), exactly like the wooden ford.
# The M_COBBLEMASK material remains in-scene as the wet/dry semantics carrier.
#
# Run:  blender -b --python tools/paper-pipeline/auth-cobble.py -- <target.blend>
# Writes <target.blend> (default mods/water-ford/blender/ford-cobble.blend) and
# prints a mesh fingerprint for the oracle comparison.
import bpy, bmesh, math, random, os, sys, hashlib, json, time
import numpy as np

FLOOR_N = 24          # 24x24 tiles; 1 world unit = 1 game tile
# 2026-10-21 maintainer: cobbles dense/touching; NO flat bed between them.
EDGE = 0.0            # (retired: boundary crease folds into JOINT/2 insets;
#                      boundary furniture = stones ending exactly AT the line) pinned at every tile edge (law: pin
#                      boundary furniture -> 1.6px @64px/tile from each side
#                      so any variant pair joins as a full joint)
JOINT = 0.0           # NO GAPS (maintainer 2026-10-21): cobbles grown to
#                      contact; stones meet part way up their sides
SEED = 20261021
WET_DRY_ARTRUN_WL = -1.0   # the knob value that renders the deck fully dry

# ---- COLOR RIG (maintainer feedback 2026-10-21: cobble reads too white in
# game). The GUI knobs (COB_TONE / COB_BED_TONE on M_COBBLE / M_COBBLEBED)
# are the MAINTAINER'S SCRATCH SPACE — tune live, F12 preview. The COMMITTED
# state lives here: folding a found value back = edit these two + rerun
# bake-cobble.sh (the crank re-stamps + re-renders; the rig values ride the
# stamp). NOTE the maintainer has since ruled the ENTIRE cobble toolchain
# suspect — auth/bake survive only until the gut-and-remake replaces them;
# nothing further gets folded back into them.
TONE_COBBLE = 1.0
TONE_BED = 1.0
COBBLE_OBJ = 'COBBLE_FLOOR'

GRAPH = {
  'M_COBBLE': {"nodes":{"Material Output":{"bl":"ShaderNodeOutputMaterial","props":{},"inputs":{}},"Principled BSDF":{"bl":"ShaderNodeBsdfPrincipled","props":{},"inputs":{"Specular IOR Level":0.55}},"Geometry":{"bl":"ShaderNodeNewGeometry","props":{},"inputs":{}},"Voronoi Texture":{"bl":"ShaderNodeTexVoronoi","props":{},"inputs":{"Scale":230.0}},"Voronoi Texture.001":{"bl":"ShaderNodeTexVoronoi","props":{},"inputs":{"Scale":310.0}},"Voronoi Texture.002":{"bl":"ShaderNodeTexVoronoi","props":{},"inputs":{"Scale":55.0}},"Map Range":{"bl":"ShaderNodeMapRange","props":{},"inputs":{"From Min":0.9,"From Max":0.965,"To Min":1.0,"To Max":0.0}},"Map Range.001":{"bl":"ShaderNodeMapRange","props":{},"inputs":{"From Min":0.88,"From Max":0.94,"To Min":1.0,"To Max":0.0}},"Separate Color":{"bl":"ShaderNodeSeparateColor","props":{},"inputs":{}},"Map Range.002":{"bl":"ShaderNodeMapRange","props":{},"inputs":{"From Min":0.35,"From Max":0.65,"To Min":-0.13,"To Max":0.13}},"Attribute":{"bl":"ShaderNodeAttribute","props":{"attribute_name":"cobble_seed"},"inputs":{}},"Map Range.003":{"bl":"ShaderNodeMapRange","props":{},"inputs":{"To Min":-0.1,"To Max":0.14}},"Color Ramp":{"bl":"ShaderNodeValToRGB","props":{"__ramp__":{"i":"LINEAR","stops":[[0.0,[0.04667,0.05286,0.06663,1.0]],[0.35,[0.10702,0.12477,0.15593,1.0]],[0.7,[0.25415,0.28315,0.33245,1.0]],[1.0,[1.0,1.0,1.0,1.0]],[1.0,[0.41789,0.45079,0.50888,1.0]]]}},"inputs":{}},"Vector Math":{"bl":"ShaderNodeVectorMath","props":{},"inputs":{}},"Combine XYZ":{"bl":"ShaderNodeCombineXYZ","props":{},"inputs":{}},"Vector Math.001":{"bl":"ShaderNodeVectorMath","props":{"operation":"MULTIPLY"},"inputs":{}},"Combine XYZ.001":{"bl":"ShaderNodeCombineXYZ","props":{},"inputs":{}},"Mix":{"bl":"ShaderNodeMix","props":{"data_type":"RGBA","blend_type":"SCREEN"},"inputs":{"A_Color":[0.610496,0.64448,0.701102,1.0]}},"Mix.001":{"bl":"ShaderNodeMix","props":{"data_type":"RGBA","blend_type":"MULTIPLY"},"inputs":{"Factor_Float":1.0}},"Combine XYZ.002":{"bl":"ShaderNodeCombineXYZ","props":{},"inputs":{}},"WL":{"bl":"ShaderNodeValue","props":{"label":"waterline_z (toggled per render)","__out_value__":0.15},"inputs":{}},"Separate XYZ":{"bl":"ShaderNodeSeparateXYZ","props":{},"inputs":{}},"Math":{"bl":"ShaderNodeMath","props":{"operation":"SUBTRACT"},"inputs":{}},"Math.001":{"bl":"ShaderNodeMath","props":{"operation":"DIVIDE"},"inputs":{"Value_001":0.15}},"Math.002":{"bl":"ShaderNodeMath","props":{"operation":"MAXIMUM"},"inputs":{"Value_001":0.0}},"Math.003":{"bl":"ShaderNodeMath","props":{"operation":"MINIMUM"},"inputs":{"Value_001":1.0}},"Color Ramp.001":{"bl":"ShaderNodeValToRGB","props":{"__ramp__":{"i":"LINEAR","stops":[[0.0,[1.0,1.0,1.0,1.0]],[0.06,[0.5,0.5,0.5,1.0]],[1.0,[0.15,0.15,0.15,1.0]]]}},"inputs":{}},"Math.004":{"bl":"ShaderNodeMath","props":{"operation":"MULTIPLY"},"inputs":{}},"Mix (Legacy)":{"bl":"ShaderNodeMixRGB","props":{},"inputs":{"Fac":1.0,"Color1":[1.0,1.0,1.0,1.0]}},"Vector Math.002":{"bl":"ShaderNodeVectorMath","props":{"operation":"MULTIPLY"},"inputs":{}},"Mix (Legacy).001":{"bl":"ShaderNodeMixRGB","props":{},"inputs":{}},"Value":{"bl":"ShaderNodeValue","props":{"__out_value__":0.42},"inputs":{}},"Math.005":{"bl":"ShaderNodeMath","props":{"operation":"SUBTRACT"},"inputs":{}},"Map Range.004":{"bl":"ShaderNodeMapRange","props":{},"inputs":{"To Max":0.14}},"Math.006":{"bl":"ShaderNodeMath","props":{"operation":"SUBTRACT"},"inputs":{}}},"links":[["Geometry","Position","Voronoi Texture","Vector"],["Geometry","Position","Voronoi Texture.001","Vector"],["Geometry","Position","Voronoi Texture.002","Vector"],["Voronoi Texture","Distance","Map Range","Value"],["Voronoi Texture.001","Distance","Map Range.001","Value"],["Voronoi Texture.002","Color","Separate Color","Color"],["Separate Color","Red","Map Range.002","Value"],["Attribute","Fac","Map Range.003","Value"],["Color Ramp","Color","Vector Math","Vector"],["Map Range.002","Result","Combine XYZ","X"],["Map Range.002","Result","Combine XYZ","Y"],["Map Range.002","Result","Combine XYZ","Z"],["Combine XYZ","Vector","Vector Math","Vector_001"],["Vector Math","Vector","Vector Math.001","Vector"],["Map Range.003","Result","Combine XYZ.001","X"],["Map Range.003","Result","Combine XYZ.001","Y"],["Map Range.003","Result","Combine XYZ.001","Z"],["Combine XYZ.001","Vector","Vector Math.001","Vector_001"],["Vector Math.001","Vector","Mix","B_Color"],["Map Range","Result","Mix","Factor_Float"],["Mix","Result_Color","Mix.001","A_Color"],["Map Range.001","Result","Combine XYZ.002","X"],["Map Range.001","Result","Combine XYZ.002","Y"],["Map Range.001","Result","Combine XYZ.002","Z"],["Combine XYZ.002","Vector","Mix.001","B_Color"],["Geometry","Position","Separate XYZ","Vector"],["WL","Value","Math","Value"],["Separate XYZ","Z","Math","Value_001"],["Math","Value","Math.001","Value"],["Math.001","Value","Math.002","Value"],["Math.002","Value","Math.003","Value"],["Math.003","Value","Color Ramp.001","Fac"],["Color Ramp.001","Color","Mix (Legacy)","Color2"],["Mix.001","Result_Float","Vector Math.002","Vector"],["Mix (Legacy)","Color","Vector Math.002","Vector_001"],["Mix.001","Result_Float","Mix (Legacy).001","Color1"],["Vector Math.002","Vector","Mix (Legacy).001","Color2"],["Math.003","Value","Mix (Legacy).001","Fac"],["Mix (Legacy).001","Color","Principled BSDF","Base Color"],["Math.003","Value","Map Range.004","Value"],["Value","Value","Math.006","Value"],["Map Range.004","Result","Math.006","Value_001"],["Math.006","Value","Principled BSDF","Roughness"],["Principled BSDF","BSDF","Material Output","Surface"]]},
  'M_COBBLEBED': {"nodes":{"Material Output":{"bl":"ShaderNodeOutputMaterial","props":{},"inputs":{}},"Principled BSDF":{"bl":"ShaderNodeBsdfPrincipled","props":{},"inputs":{"Specular IOR Level":0.55}},"Geometry":{"bl":"ShaderNodeNewGeometry","props":{},"inputs":{}},"Voronoi Texture":{"bl":"ShaderNodeTexVoronoi","props":{},"inputs":{"Scale":230.0}},"Voronoi Texture.001":{"bl":"ShaderNodeTexVoronoi","props":{},"inputs":{"Scale":310.0}},"Voronoi Texture.002":{"bl":"ShaderNodeTexVoronoi","props":{},"inputs":{"Scale":55.0}},"Map Range":{"bl":"ShaderNodeMapRange","props":{},"inputs":{"From Min":0.9,"From Max":0.965,"To Min":1.0,"To Max":0.0}},"Map Range.001":{"bl":"ShaderNodeMapRange","props":{},"inputs":{"From Min":0.88,"From Max":0.94,"To Min":1.0,"To Max":0.0}},"Separate Color":{"bl":"ShaderNodeSeparateColor","props":{},"inputs":{}},"Map Range.002":{"bl":"ShaderNodeMapRange","props":{},"inputs":{"From Min":0.35,"From Max":0.65,"To Min":-0.13,"To Max":0.13}},"Attribute":{"bl":"ShaderNodeAttribute","props":{"attribute_name":"cobble_seed"},"inputs":{}},"Map Range.003":{"bl":"ShaderNodeMapRange","props":{},"inputs":{"To Min":-0.1,"To Max":0.14}},"Color Ramp":{"bl":"ShaderNodeValToRGB","props":{"__ramp__":{"i":"LINEAR","stops":[[0.0,[0.0331,0.03689,0.04519,1.0]],[0.55,[0.07036,0.08022,0.09759,1.0]],[1.0,[1.0,1.0,1.0,1.0]],[1.0,[0.11697,0.13287,0.15896,1.0]]]}},"inputs":{}},"Vector Math":{"bl":"ShaderNodeVectorMath","props":{},"inputs":{}},"Combine XYZ":{"bl":"ShaderNodeCombineXYZ","props":{},"inputs":{}},"Vector Math.001":{"bl":"ShaderNodeVectorMath","props":{"operation":"MULTIPLY"},"inputs":{}},"Combine XYZ.001":{"bl":"ShaderNodeCombineXYZ","props":{},"inputs":{}},"Mix":{"bl":"ShaderNodeMix","props":{"data_type":"RGBA","blend_type":"SCREEN"},"inputs":{"A_Color":[0.610496,0.64448,0.701102,1.0]}},"Mix.001":{"bl":"ShaderNodeMix","props":{"data_type":"RGBA","blend_type":"MULTIPLY"},"inputs":{"Factor_Float":1.0}},"Combine XYZ.002":{"bl":"ShaderNodeCombineXYZ","props":{},"inputs":{}},"WL":{"bl":"ShaderNodeValue","props":{"label":"waterline_z (toggled per render)","__out_value__":0.15},"inputs":{}},"Separate XYZ":{"bl":"ShaderNodeSeparateXYZ","props":{},"inputs":{}},"Math":{"bl":"ShaderNodeMath","props":{"operation":"SUBTRACT"},"inputs":{}},"Math.001":{"bl":"ShaderNodeMath","props":{"operation":"DIVIDE"},"inputs":{"Value_001":0.15}},"Math.002":{"bl":"ShaderNodeMath","props":{"operation":"MAXIMUM"},"inputs":{"Value_001":0.0}},"Math.003":{"bl":"ShaderNodeMath","props":{"operation":"MINIMUM"},"inputs":{"Value_001":1.0}},"Color Ramp.001":{"bl":"ShaderNodeValToRGB","props":{"__ramp__":{"i":"LINEAR","stops":[[0.0,[1.0,1.0,1.0,1.0]],[0.05,[0.4,0.4,0.4,1.0]],[1.0,[0.12,0.12,0.12,1.0]]]}},"inputs":{}},"Math.004":{"bl":"ShaderNodeMath","props":{"operation":"MULTIPLY"},"inputs":{}},"Mix (Legacy)":{"bl":"ShaderNodeMixRGB","props":{},"inputs":{"Fac":1.0,"Color1":[1.0,1.0,1.0,1.0]}},"Vector Math.002":{"bl":"ShaderNodeVectorMath","props":{"operation":"MULTIPLY"},"inputs":{}},"Mix (Legacy).001":{"bl":"ShaderNodeMixRGB","props":{},"inputs":{}},"Value":{"bl":"ShaderNodeValue","props":{"__out_value__":0.58},"inputs":{}},"Math.005":{"bl":"ShaderNodeMath","props":{"operation":"SUBTRACT"},"inputs":{}},"Map Range.004":{"bl":"ShaderNodeMapRange","props":{},"inputs":{"To Max":0.14}},"Math.006":{"bl":"ShaderNodeMath","props":{"operation":"SUBTRACT"},"inputs":{}}},"links":[["Geometry","Position","Voronoi Texture","Vector"],["Geometry","Position","Voronoi Texture.001","Vector"],["Geometry","Position","Voronoi Texture.002","Vector"],["Voronoi Texture","Distance","Map Range","Value"],["Voronoi Texture.001","Distance","Map Range.001","Value"],["Voronoi Texture.002","Color","Separate Color","Color"],["Separate Color","Red","Map Range.002","Value"],["Attribute","Fac","Map Range.003","Value"],["Color Ramp","Color","Vector Math","Vector"],["Map Range.002","Result","Combine XYZ","X"],["Map Range.002","Result","Combine XYZ","Y"],["Map Range.002","Result","Combine XYZ","Z"],["Combine XYZ","Vector","Vector Math","Vector_001"],["Vector Math","Vector","Vector Math.001","Vector"],["Map Range.003","Result","Combine XYZ.001","X"],["Map Range.003","Result","Combine XYZ.001","Y"],["Map Range.003","Result","Combine XYZ.001","Z"],["Combine XYZ.001","Vector","Vector Math.001","Vector_001"],["Vector Math.001","Vector","Mix","B_Color"],["Map Range","Result","Mix","Factor_Float"],["Mix","Result_Color","Mix.001","A_Color"],["Map Range.001","Result","Combine XYZ.002","X"],["Map Range.001","Result","Combine XYZ.002","Y"],["Map Range.001","Result","Combine XYZ.002","Z"],["Combine XYZ.002","Vector","Mix.001","B_Color"],["Geometry","Position","Separate XYZ","Vector"],["WL","Value","Math","Value"],["Separate XYZ","Z","Math","Value_001"],["Math","Value","Math.001","Value"],["Math.001","Value","Math.002","Value"],["Math.002","Value","Math.003","Value"],["Math.003","Value","Color Ramp.001","Fac"],["Color Ramp.001","Color","Mix (Legacy)","Color2"],["Mix.001","Result_Float","Vector Math.002","Vector"],["Mix (Legacy)","Color","Vector Math.002","Vector_001"],["Mix.001","Result_Float","Mix (Legacy).001","Color1"],["Vector Math.002","Vector","Mix (Legacy).001","Color2"],["Math.003","Value","Mix (Legacy).001","Fac"],["Mix (Legacy).001","Color","Principled BSDF","Base Color"],["Math.003","Value","Map Range.004","Value"],["Value","Value","Math.006","Value"],["Map Range.004","Result","Math.006","Value_001"],["Math.006","Value","Principled BSDF","Roughness"],["Principled BSDF","BSDF","Material Output","Surface"]]},
  'M_COBBLEMASK': {"nodes":{"Material Output":{"bl":"ShaderNodeOutputMaterial","props":{},"inputs":{}},"Emission":{"bl":"ShaderNodeEmission","props":{},"inputs":{}},"Geometry":{"bl":"ShaderNodeNewGeometry","props":{},"inputs":{}},"Separate XYZ":{"bl":"ShaderNodeSeparateXYZ","props":{},"inputs":{}},"Math":{"bl":"ShaderNodeMath","props":{"operation":"SUBTRACT"},"inputs":{}},"WL":{"bl":"ShaderNodeValue","props":{"__out_value__":0.15},"inputs":{}},"Math.001":{"bl":"ShaderNodeMath","props":{"operation":"DIVIDE"},"inputs":{"Value_001":0.15}},"Math.002":{"bl":"ShaderNodeMath","props":{"operation":"MAXIMUM"},"inputs":{"Value_001":0.0}},"Math.003":{"bl":"ShaderNodeMath","props":{"operation":"MINIMUM"},"inputs":{"Value_001":1.0}},"Color Ramp":{"bl":"ShaderNodeValToRGB","props":{"__ramp__":{"i":"LINEAR","stops":[[0.0,[0.3779,0.3779,0.3779,1.0]],[0.6,[0.0716,0.0716,0.0716,1.0]],[1.0,[0.0716,0.0716,0.0716,1.0]]]}},"inputs":{}}},"links":[["Geometry","Position","Separate XYZ","Vector"],["WL","Value","Math","Value"],["Separate XYZ","Z","Math","Value_001"],["Math","Value","Math.001","Value"],["Math.001","Value","Math.002","Value"],["Math.002","Value","Math.003","Value"],["Math.003","Value","Color Ramp","Fac"],["Color Ramp","Color","Emission","Color"],["Emission","Emission","Material Output","Surface"]]},
  '@WATERSHEET': {"nodes":{"Material Output":{"bl":"ShaderNodeOutputMaterial","props":{},"inputs":{}},"Principled BSDF":{"bl":"ShaderNodeBsdfPrincipled","props":{},"inputs":{"Base Color":[0.1,0.23,0.26,1.0],"Roughness":0.06,"IOR":1.33,"Alpha":0.55,"Transmission Weight":1.0}}},"links":[["Principled BSDF","BSDF","Material Output","Surface"]]},
  'WORLD': {"name":"COBBLE_WORLD","g":{"nodes":{"Background":{"bl":"ShaderNodeBackground","props":{},"inputs":{"Color":[0.55,0.55,0.55,1.0],"Strength":0.06}},"World Output":{"bl":"ShaderNodeOutputWorld","props":{},"inputs":{}}},"links":[["Background","Background","World Output","Surface"]]}},
}


def clamp01(x):
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)

def dome_bmesh(w, h, rng):
    """Loaf cobble: superellipse plan (rounded rect, exponent p), flat-ish
    crown with rounded shoulders (the bread-loaf profile), per-cobble skew.
    Returns list of (x, y, z) verts + faces as index tuples, base at z=0."""
    p = rng.uniform(4.8, 6.0)      # corner roundness (boxier: seals corner lenses)
    ns = 20
    ax, bx = w * 0.5, h * 0.5
    th = rng.uniform(-0.09, 0.09)  # skew rotation
    sh = rng.uniform(-0.07, 0.07)  # shear
    ct, st = math.cos(th), math.sin(th)
    plan = []
    for i in range(ns):
        t = 2 * math.pi * i / ns
        cx, sx = math.cos(t), math.sin(t)
        px = math.copysign(abs(cx) ** (2.0 / p), cx)
        py = math.copysign(abs(sx) ** (2.0 / p), sx)
        x, y = ax * px, bx * py
        xr = x * ct - y * st
        yr = x * st + y * ct
        xr += sh * yr
        plan.append((xr, yr))
    D = min(w, h) * rng.uniform(0.38, 0.55)   # dome height above base
    NR = 6
    rings = []
    for j in range(NR + 1):
        f = j / NR
        # FLANK PROFILE = the POINTWISE MIDPOINT of the two blessed states:
        #   prior (immediate recession from the base)  mid(f) = (1 - 0.92f)+
        #   current (hold full width, round at shoulder)
        s_prior = max(0.08, 1.0 - 0.92 * f)
        s_now = max(0.08, 1.0 - 0.92 * max(0.0, (f - 0.55) / 0.45) ** 1.5)
        s = 0.5 * (s_prior + s_now)   # height curve (f/0.55)^0.75 is common
                                      # to both parents and stays untouched
        z = D * clamp01(f / 0.55) ** 0.75      # loaf: steady rise, flat top
        ring = []
        for (xr, yr) in plan:
            jx = rng.uniform(-0.02, 0.02) * f
            jy = rng.uniform(-0.02, 0.02) * f
            # clamp ring into the stone's plan envelope: flanks crease with
            # neighbours but never cross the span (boundary furniture law)
            ring.append((min(max(xr * s + jx, -ax), ax),
                         min(max(yr * s + jy, -bx), bx), z))
        rings.append(ring)
    # stitch rings + center cap
    verts, faces = [], []
    for ring in rings:
        for (x, y, z) in ring:
            verts.append((x, y, z))
    # side bands between consecutive rings
    for j in range(NR):
        a0 = j * ns
        b0 = (j + 1) * ns
        for k in range(ns):
            k2 = (k + 1) % ns
            faces.append((a0 + k, a0 + k2, b0 + k2, b0 + k))
    # crown cap fan at the last ring
    c = len(verts)
    last = [(x, y, z) for (x, y, z) in rings[NR]]
    cx = sum(v[0] for v in last) / ns
    cy = sum(v[1] for v in last) / ns
    verts.append((cx, cy, rings[NR][0][2] + 0.002 * min(w, h) / 0.05))
    n_last = len(verts) - 1
    a0 = NR * ns
    for k in range(ns):
        k2 = (k + 1) % ns
        faces.append((a0 + k, a0 + k2, n_last))
    return verts, faces

def layout_field(bm, seed_layer, ox, oy, W, H, rng, courses=None):
    """One variant cell as a continuous lattice field: W x H units, ~4
    courses per unit (the 3x4 rhythm: 2x2 cells = 6x8 cobbles, 4x4 = 12x16
    per maintainer's corrected density), stones crease-only (JOINT/EDGE=0),
    outer edge = stones ending ON the boundary (the pinned furniture)."""
    ED = 0.0
    JD = 0.0
    n_courses = courses if courses else max(1, round(H * 4))
    course_h = H / n_courses
    x0, x_end = ox + ED, ox + W - ED
    for c in range(n_courses):
        y0 = oy + ED + c * course_h + JD * 0.5
        y1 = y0 + course_h - JD
        if y1 <= y0: continue
        cursor = x0
        row_stones = []
        while cursor < x_end - 1e-4:
            r = rng.random()
            if row_stones and rng.random() < 0.10 and len(row_stones) >= 1:
                w = rng.uniform(1.9, 2.6) * course_h
            elif r < 0.02:
                w = rng.uniform(2.8, 3.9) * course_h
            else:
                w = rng.uniform(0.85, 1.30) * course_h
            w = min(w, x_end - cursor)
            if w < course_h * 0.6:
                if row_stones:
                    row_stones[-1] = (row_stones[-1][0], x_end)
                break
            row_stones.append((cursor, cursor + w))
            cursor += w + JD
        if row_stones and row_stones[-1][1] < x_end - 1e-4:
            row_stones[-1] = (row_stones[-1][0], x_end)
        for (sx0, sx1) in row_stones:
            w = sx1 - sx0
            hgt = y1 - y0
            if w < 0.04 or hgt < 0.04: continue
            seed = rng.random()
            verts, faces = dome_bmesh(w, hgt, rng)
            vmap = []
            for (px, py, pz) in verts:
                vmap.append(bm.verts.new((sx0 + w * 0.5 + px, y0 + hgt * 0.5 + py, pz)))
            for f in faces:
                try:
                    face = bm.faces.new([vmap[i] for i in f])
                    face.smooth = True
                    face[seed_layer] = seed
                except ValueError:
                    pass

def build_floor_mesh():
    bm = bmesh.new()
    seed_layer = bm.faces.layers.float.new('cobble_seed')
    ti_list = []
    for tj in range(FLOOR_N):
        for ti in range(FLOOR_N):
            # tile layout in PURE LOCAL units (0..1); world offset added once
            # at the vertex stage (bug caught on first render: px0/x0 were
            # absolute-tile-space and ox was added on top -> 2.ti smear)
            rng = random.Random(SEED + ti * 31 + tj * 613)
            ox, oy = ti - 12.0, tj - 12.0
            inner = 1.0 - 2 * EDGE
            n_courses = rng.choice([3, 3, 4, 4])
            course_h = inner / n_courses
            rows = []
            for c in range(n_courses):
                x = EDGE                      # local left edge of the interior
                x_end = 1.0 - EDGE            # local right edge
                cursor = x
                row_stones = []
                while cursor < x_end - 1e-4:
                    r = rng.random()
                    if row_stones and rng.random() < 0.10 and len(row_stones) >= 1:
                        w = rng.uniform(1.9, 2.6) * course_h
                    elif r < 0.02:
                        w = rng.uniform(2.8, 3.9) * course_h   # flag
                    else:
                        w = rng.uniform(0.85, 1.30) * course_h  # regular
                    w = min(w, x_end - cursor)
                    if w < course_h * 0.6:
                        # rows must fill to the boundary: fold the sliver
                        # into the last stone (wider stone = the style)
                        if row_stones:
                            row_stones[-1] = (row_stones[-1][0], x_end)
                        break
                    row_stones.append((cursor, cursor + w))
                    cursor += w + JOINT
                rows.append((c, row_stones, course_h))
            # build stones (joint bands handled by shrinking stone spans)
            for c, row_stones, ch in rows:
                y0 = EDGE + c * course_h + JOINT * 0.5  # local
                y1 = y0 + course_h - JOINT
                if y1 <= y0:
                    continue
                for (lx0, lx1) in row_stones:
                    px0 = lx0 + JOINT * 0.5
                    px1 = lx1 - JOINT * 0.5
                    if px1 - px0 < 0.04 or y1 - y0 < 0.04:
                        continue
                    w = px1 - px0
                    hgt = y1 - y0
                    seed = rng.random()
                    verts, faces = dome_bmesh(w, hgt, rng)
                    vmap = []
                    for (x, y, z) in verts:
                        # centre the dome on its intended SPAN (was: origin at the
                        # span's left edge -> half-stone shift to -x/-y, the
                        # grid-underflow bug the maintainer caught in viewport)
                        vmap.append(bm.verts.new((ox + px0 + w * 0.5 + x,
                                                  oy + y0 + hgt * 0.5 + y, z)))
                    for f in faces:
                        try:
                            face = bm.faces.new([vmap[i] for i in f])
                            face.smooth = True
                            face[seed_layer] = seed
                        except ValueError:
                            pass
    # TRIM AT THE WATERBED (maintainer 2026-10-21): nothing survives below
    # the bed plane; true vertex ring at z=0, loaves terminate at the cut.
    # (posts GN-cut semantics: same plane, here the below-part DIES instead
    # of shipping — a trim, not an a/w split.)
    import bmesh.ops as ops
    ops.bisect_plane(bm,
                     geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                     plane_co=(0.0, 0.0, 0.0), plane_no=(0.0, 0.0, 1.0),
                     use_snap_center=False, clear_outer=False, clear_inner=True)
    low = [v for v in bm.verts if v.co.z < -1e-6]
    if low:
        raise RuntimeError('trim left %d verts below the bed' % len(low))
    #
    # WET/DRY CUT AT THE WATERLINE (maintainer 2026-10-21, piling recipe):
    # bisect at z=WL (the M_COBBLE WL knob — single source of truth), KEEP
    # BOTH SIDES, then split the ring edges so every wet/dry polygon owns its
    # own ring copy — the 'dry ring' that cleanly separates wet from dry
    # polygons. Attributes per side: in_wet (0/1) + wet_depth (0 at the
    # waterline -> 1 at the bed). Materials still drive the wet LOOK from the
    # analytic WL ramp; consuming these attrs is a separate, named change.
    wl_cut = bpy.data.materials['M_COBBLE'].node_tree.nodes['WL'].outputs[0].default_value
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    ops.bisect_plane(bm, geom=geom,
                     plane_co=(0.0, 0.0, float(wl_cut)), plane_no=(0.0, 0.0, 1.0),
                     use_snap_center=False, clear_outer=False, clear_inner=False)
    # edge-split the waterline ring so the two sides own their own verts
    ring_edges = []
    for e in bm.edges:
        z0, z1 = e.verts[0].co.z, e.verts[1].co.z
        if abs(z0 - wl_cut) < 1e-5 and abs(z1 - wl_cut) < 1e-5:
            ring_edges.append(e)
    if ring_edges:
        ops.split_edges(bm, edges=ring_edges, use_verts=False)
    layers = {}
    layers['in_wet'] = bm.verts.layers.float.new('in_wet')
    layers['wet_depth'] = bm.verts.layers.float.new('wet_depth')
    DEPTH_EXT = float(wl_cut)
    for face in bm.faces:
        wet = (sum(v.co.z for v in face.verts) / len(face.verts)) < wl_cut - 1e-6
        for v in face.verts:
            v[layers['in_wet']] = 1.0 if wet else 0.0
            d = (wl_cut - v.co.z) / DEPTH_EXT
            v[layers['wet_depth']] = 0.0 if d < 0.0 else (1.0 if d > 1.0 else d)
    n_wet = sum(1 for v in bm.verts if v[layers['in_wet']] > 0.5)
    print('WL-CUT %.3f: ring edges split=%d, wet verts=%d' % (wl_cut, len(ring_edges), n_wet))
    # VARIANT FIELD GRIDS (boards pattern: fields at known frames)
    # 2x2: 4x4 grid of 2-unit continuous fields, 8 courses each
    for r in range(4):
        for c in range(4):
            layout_field(bm, seed_layer, -22.0 + c * 2.0, -22.0 + r * 2.0, 2.0, 2.0,
                         random.Random(SEED + 90001 + r * 17 + c * 731), courses=8)
    # 4x4: 4x4 grid of 4-unit fields, 16 courses each
    for r in range(4):
        for c in range(4):
            layout_field(bm, seed_layer, -46.0 + c * 4.0, -40.0 + r * 4.0, 4.0, 4.0,
                         random.Random(SEED + 90003 + r * 17 + c * 731), courses=16)
    mesh = bpy.data.meshes.new(COBBLE_OBJ)
    bm.to_mesh(mesh)
    bm.free()
    ob = bpy.data.objects.new(COBBLE_OBJ, mesh)
    ob.rotation_mode = 'XYZ'
    bpy.data.collections['COBBLE'].objects.link(ob)
    return ob, len(mesh.polygons) if mesh else 0

def build_bed():
    # bed must underlie EVERY sheet region: the central 24x24 floor AND the
    # variant field blocks (sq2 @ -22..-14, sq4 @ -46..-30 x -40..-24) —
    # unmapped voids baked as black art + 0-byte mask cells in the old sheets
    bm = bmesh.new()
    for (cx, cy, half) in ((0.0, 0.0, FLOOR_N / 2),
                           (-18.0, -18.0, 4.0),
                           (-38.0, -32.0, 8.0)):
        before = len(bm.verts)
        bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=half)
        bmesh.ops.translate(bm, verts=bm.verts[before:], vec=(cx, cy, 0.0))
    mesh = bpy.data.meshes.new('JOINTBED')
    bm.to_mesh(mesh); bm.free()
    ob = bpy.data.objects.new('JOINTBED', mesh)
    ob.rotation_mode = 'XYZ'
    ob.data.materials.append(bpy.data.materials['M_COBBLEBED'])
    bpy.data.collections['WATERBED'].objects.link(ob)
    # raise bed top to z=0
    ob.location = (0.0, 0.0, 0.0)
    return ob

def build_water_plane():
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=FLOOR_N / 2)
    mesh = bpy.data.meshes.new('WATERSHEET')
    bm.to_mesh(mesh); bm.free()
    ob = bpy.data.objects.new('WATERSHEET', mesh)
    ob.rotation_mode = 'XYZ'
    m = bpy.data.materials['M_WATER']   # built by build_all_materials (GRAPH)
    ob.data.materials.append(m)
    bpy.data.collections['WATER'].objects.link(ob)
    # waterline = whatever the materials' WL knob says (single source of
    # truth; the sheet must never disagree with the ramp after a rebuild)
    wl = bpy.data.materials['M_COBBLE'].node_tree.nodes['WL'].outputs[0].default_value
    ob.location = (0.0, 0.0, wl)
    ob.hide_render = True  # sheet renders force-hide; viewport/beauty toggle externally
    return ob


# ---------------------------------------------------------------------------
# material/rig/scenes builder (generic, from the oracle codegen)
# ---------------------------------------------------------------------------
def _socket(socks, key):
    for s in socks:
        if s.identifier == key:
            return s
    for s in socks:
        if s.name == key:
            return s
    return None


def build_material(name, g):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    made = {}
    for nm, nd in g["nodes"].items():
        node = nt.nodes.new(nd["bl"])
        node.name = nm
        made[nm] = node
        for pid, v in nd["props"].items():
            if pid == "__ramp__":
                r = node.color_ramp
                r.interpolation = v["i"]
                while len(r.elements) > len(v["stops"]):
                    r.elements.remove(r.elements[-1])
                while len(r.elements) < len(v["stops"]):
                    r.elements.new(min(1.0, v["stops"][len(r.elements) - 1][0]))
                for i, (pos, col) in enumerate(v["stops"]):
                    r.elements[i].position = pos
                    r.elements[i].color = col
            elif pid == "__out_value__":
                node.outputs[0].default_value = v
            else:
                setattr(node, pid, v)
        for sid, val in nd["inputs"].items():
            s = _socket(node.inputs, sid)
            if s is not None and hasattr(s, "default_value"):
                try:
                    s.default_value = val
                except Exception as e:
                    print("WARN material %s node %s input %s: %s" % (name, nm, sid, e))
    for (fn, fs, tn, ts) in g["links"]:
        a, b = made.get(fn), made.get(tn)
        so, si = (_socket(a.outputs, fs), _socket(b.inputs, ts)) if a and b else (None, None)
        if a is None or b is None or so is None or si is None:
            print("WARN material %s: unresolved link %r.%s -> %r.%s" % (name, fn, fs, tn, ts))
            continue
        nt.links.new(so, si)
    return m


def build_node_tree(nt, g, label):
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    made = {}
    for nm, nd in g["nodes"].items():
        node = nt.nodes.new(nd["bl"])
        node.name = nm
        made[nm] = node
        for pid, v in nd["props"].items():
            if pid == "__out_value__":
                node.outputs[0].default_value = v
        for sid, val in nd["inputs"].items():
            s = _socket(node.inputs, sid)
            if s is not None and hasattr(s, "default_value"):
                try:
                    s.default_value = val
                except Exception as e:
                    print("WARN %s input %s: %s" % (nm, sid, e))
    for (fn, fs, tn, ts) in g["links"]:
        so, si = _socket(made[fn].outputs, fs), _socket(made[tn].inputs, ts)
        if so is None or si is None:
            print("WARN %s: unresolved link %r.%s -> %r.%s" % (label, fn, fs, tn, ts))
        else:
            nt.links.new(so, si)
    return made


def add_tone_knob(m, name, value=None):
    """COLOR RIG (maintainer request 2026-10-21): one drag-able gray-level
    knob between the palette mix and the Principled BSDF. 1.0 = as-rendered
    palette. The node name is the GUI search term (Shading workspace,
    M_COBBLE's node tree: 'COB_TONE' / 'COB_BED_TONE' — the cobble read too
    white in-game; tune live and drive the knob, F12 to preview). Default
    value = the committed TONE_* constant (the knob's scratch edits stay
    live-only; folding a value back = TONE_COBBLE/TONE_BED + re-crank).
    """
    nt = m.node_tree
    if nt.nodes.get(name):
        return
    src = nt.nodes["Mix (Legacy).001"]  # the final palette mix
    tgt = nt.nodes["Principled BSDF"]
    tone = nt.nodes.new("ShaderNodeValue"); tone.name = name
    defaults = {"COB_TONE": TONE_COBBLE, "COB_BED_TONE": TONE_BED}
    tone.outputs[0].default_value = value if value is not None else defaults.get(name, 1.0)
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.name = name + "_MUL"
    nt.links.new(src.outputs["Color"], mul.inputs[0])
    nt.links.new(tone.outputs[0], mul.inputs[1])
    nt.links.new(mul.outputs[0], tgt.inputs["Base Color"])
    # framed + parked left of the palette mix so it is findable in the GUI
    frame = nt.nodes.new("NodeFrame")
    frame.name = "TONE " + name
    frame.label = "TONE KNOB — " + ("COBBLE" if name == "COB_TONE" else "BED (grout)") + "  (edit the Value, drag)"
    frame.use_custom_color = True
    frame.color = (1.0, 0.65, 0.1)
    knob_y = src.location.y - 40.0
    tone.location = (src.location.x - 340.0, knob_y)
    mul.location = (src.location.x - 180.0, knob_y)
    tone.parent = frame
    mul.parent = frame


def layout_node_tree(nt, x_step=280.0, y_step=240.0):
    """Arrange a node tree for humans (4.3 ships no tree-arrange operator; the
    extraction drops every node at (0,0)). Deterministic longest-path layering
    from link-free sources toward the sink(s), then rows sorted by name.
    Cosmetic only — never touches links, only unparented node locations
    (framed knob pairs keep their parked spots)."""
    live = [n for n in nt.nodes if n.parent is None]
    links = {n.name: [l.from_node.name for l in nt.links if l.to_node == n] for n in live}
    byname = {n.name: n for n in live}
    depth = {}
    def d(name, seen):
        if name in depth:
            return depth[name]
        if name not in byname or not links.get(name) or name in seen:
            depth[name] = 0
            return 0
        seen.add(name)
        depth[name] = max((d(p, seen) for p in links[name]), default=-1) + 1
        return depth[name]
    for n in live:
        d(n.name, set())
    for name in links:
        if name not in depth:
            depth[name] = 0
    maxd = max(depth.values())
    layers = {}
    for n in live:
        layers.setdefault(depth[n.name], []).append(n)
    for k in layers:
        rows = sorted(layers[k], key=lambda n: n.name)
        for i, n in enumerate(rows):
            n.location = ((maxd - k) * -x_step, (len(rows) / 2 - i) * y_step)


def srgb_lin(gray_byte):
    """Standard/view-transform inverse: byte -> linear emission that ENCODES back to gray_byte."""
    v = gray_byte / 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def fix_mask_material(m):
    """MAINTAINER RULINGS on the wetness mask, 2026-10-21 (revised same day):
    wetness masks SHIP as functional sheets (the engine mixes them with the
    water effects shader to submerge the sprite below the waterline — the
    pilings pattern: pilings-transition-mask.png / bake-mask.py law).
    Engine recipe (bake-mask.py): gray 170 = dry (crown); ramp 170 -> 85 over
    the first 60% of the submerged band; hold 85 to the base; 0 outside.
    The recovered material rendered 165/76 (its ramp stored single-decode
    values, i.e. double-encoded) and divided depth by a stale 0.014 from the
    08:3x-era WL=0.010 build (the knob moved to 0.15, the divisor never did).
    Fixed here, single-sourced:
    - ramp stops re-encoded so the Standard transform lands on bytes 170/85;
    - the depth divisor IS the WL knob (linked, not hard-coded): the ramp's
      X domain spans the full WL-to-bed depth, giving the ~12px band @128px.
    """
    nt = m.node_tree
    wl_node = nt.nodes["WL"]
    div = nt.nodes["Math.001"]
    inp = [s for s in div.inputs if s.identifier == "Value_001"][0]
    nt.links.new(wl_node.outputs[0], inp)
    ramp = nt.nodes["Color Ramp"].color_ramp
    dry, hold = srgb_lin(170), srgb_lin(85)
    for i, (pos, v) in enumerate(((0.0, dry), (0.6, hold), (1.0, hold))):
        ramp.elements[i].position = pos
        ramp.elements[i].color = (v, v, v, 1.0)
    print("MASK RULINGS: ramp 170/85 re-encoded, depth divisor := WL knob")


def build_all_materials():
    for key, g in GRAPH.items():
        if key == "WORLD":
            continue
        if key == "@WATERSHEET":
            b = build_material("M_WATER", g)
            b.blend_method = 'BLEND'
        else:
            b = build_material(key, g)
        if key == "M_COBBLEMASK":
            # zero-user by design (the bake grabs it at runtime for the Mask
            # view-layer); fake_user so the save/load cycle keeps it alive
            b.use_fake_user = True
            fix_mask_material(b)
        if key == "M_COBBLE":
            add_tone_knob(b, "COB_TONE", TONE_COBBLE)
        if key == "M_COBBLEBED":
            add_tone_knob(b, "COB_BED_TONE", TONE_BED)
        layout_node_tree(b.node_tree)
    w = bpy.data.worlds.new(GRAPH["WORLD"]["name"])
    w.use_nodes = True
    build_node_tree(w.node_tree, GRAPH["WORLD"]["g"], "WORLD")
    return w


def build_veil_sim(s):
    # 2026-10-21, maintainer ruling: there is NO game veil. Repeated removals
    # kept dying here — this function resurrected the compositor sim on every
    # auth run. Amputated (not folded back): the scenes build with the
    # compositor OFF, matching the reference files (no GAME_VEIL anywhere).
    # The in-game wash is a delivery fact, previewed at the game window, not
    # simulated in art tooling.
    s.use_nodes = False
    return


def build_scenes_and_rig(w):
    for cname in ("COBBLE", "WATERBED", "WATER", "LIGHTING", "CAMERAS"):
        bpy.data.collections.new(cname)
    # KEY light, this session's tuned descendant of the boards rig
    kd = bpy.data.lights.new("KEY", 'POINT')
    kd.energy = 1800000.0
    kd.shadow_soft_size = 0.1
    k = bpy.data.objects.new("KEY", kd)
    k.location = (-126.0, 0.0, 126.0)
    bpy.data.collections["LIGHTING"].objects.link(k)
    # cameras: FLOOR + ZOOM + BEAUTY as saved; COB2/COB4 rebuilt ORTHO top-down
    # (the saved session left them PERSP eyeballing cams while the bake's
    # REGIONS table and the 128px/unit slice math assume ortho framing).
    def cam(name, ortho_scale, loc, rot=(0.0, 0.0, 0.0), ctype='ORTHO', clip=(0.1, 1000.0)):
        cd = bpy.data.cameras.new(name)
        cd.type = ctype
        if ctype == 'ORTHO':
            cd.ortho_scale = ortho_scale
        cd.clip_start, cd.clip_end = clip
        ob = bpy.data.objects.new(name, cd)
        ob.rotation_mode = 'XYZ'
        ob.location = loc
        ob.rotation_euler = (math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2]))
        bpy.data.collections["CAMERAS"].objects.link(ob)
        return ob
    cam("FLOOR_CAM", 24.0, (0.0, 0.0, 60.0), clip=(1.0, 1000.0))
    cam("ZOOM_CAM", 4.0, (-9.5, -9.5, 60.0), clip=(1.0, 1000.0))
    cam("BEAUTY_CAM", 10.0, (-13.1, 0.0, 9.2), rot=(55.0, 0.0, -90.0), clip=(1.0, 1000.0))
    cam("COB2_CAM", 8.0, (-18.0, -18.0, 60.0))
    cam("COB4_CAM", 16.0, (-38.0, -32.0, 60.0))
    for sname, include_water, cam_name, res in (("FLOOR", False, "ZOOM_CAM", 512),
                                               ("FORD", True, "BEAUTY_CAM", 512)):
        # the SAVED state is the COLOR RIG: preview-fast (512/48 samples ≈s
        # per F12), swatch cameras; the bake overrides every knob it needs
        s = bpy.data.scenes.new(sname)
        for cname in ("COBBLE", "WATERBED", "LIGHTING", "CAMERAS") + (("WATER",) if include_water else ()):
            s.collection.children.link(bpy.data.collections[cname])
        s.world = w
        s.render.engine = 'CYCLES'
        s.render.resolution_x = res
        s.render.resolution_y = res
        s.render.film_transparent = False
        s.render.threads_mode = 'AUTO'
        s.render.use_compositing = True
        s.view_settings.view_transform = 'Standard'
        s.cycles.samples = 48
        s.cycles.use_adaptive_sampling = True
        s.cycles.adaptive_threshold = 0.01
        s.cycles.use_denoising = False
        s.cycles.seed = 0
        s.cycles.transparent_max_bounces = 8
        s.cycles.max_bounces = 12
        s.camera = bpy.data.objects[cam_name]
        build_veil_sim(s)


def mesh_fingerprint(me):
    h = hashlib.sha1()
    if len(me.vertices):
        arr = np.empty(len(me.vertices) * 3, dtype=np.float64)
        me.vertices.foreach_get("co", arr)
        np.round(arr, 4, out=arr)
        h.update(arr.tobytes())
    attrs = []
    for a in me.attributes:
        attrs.append([a.name, a.data_type, a.domain])
        if a.data_type == "FLOAT" and len(a.data):
            fa = np.empty(len(a.data), dtype=np.float64)
            a.data.foreach_get("value", fa)
            np.round(fa, 4, out=fa)
            h.update(a.name.encode()); h.update(fa.tobytes())
    return {"verts": len(me.vertices), "polys": len(me.polygons), "hash": h.hexdigest()[:16], "attrs": attrs}


# ---------------------------------------------------------------------------
# assembly (fresh scene; idempotent by construction)
# ---------------------------------------------------------------------------
def main(target):
    import json
    bpy.ops.wm.read_factory_settings(use_empty=True)
    build_all_materials()
    w = bpy.data.worlds[GRAPH["WORLD"]["name"]]
    build_scenes_and_rig(w)
    try:
        if "Scene" in bpy.data.scenes:
            bpy.data.scenes.remove(bpy.data.scenes["Scene"])
    except Exception as e:
        print("WARN default Scene removal failed: %s" % e)
    build_bed()
    build_water_plane()
    ob, nfaces = build_floor_mesh()
    ob.data.materials.append(bpy.data.materials['M_COBBLE'])
    # SAVED WL = the DRY product state (the shipped art is dry; the wet look
    # ships in the mask sheets). Set AFTER the geometry: build_floor_mesh
    # reads the WL knob for the waterline cut, so it must ride at 0.15 during
    # the build and may only change afterwards. The WATERSHEET keeps its
    # built-in z=0.15 (the ford scene still shows the correct waterline).
    for mn in ('M_COBBLE', 'M_COBBLEBED'):
        bpy.data.materials[mn].node_tree.nodes['WL'].outputs[0].default_value = WET_DRY_ARTRUN_WL
    fp = mesh_fingerprint(ob.data)
    # ---- provenance stamp (reproducibility 2026-10-21): the bake refuses any
    # blend whose stamp is missing or stale, so a crashed auth can never
    # silently hand the bake an old file again.
    stamp = {'auth_sha256': hashlib.sha256(open(os.path.abspath(__file__), 'rb').read()).hexdigest(),
             'generated': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
             'mesh_hash': fp['hash'],
             'tone': {'COB_TONE': TONE_COBBLE, 'COB_BED_TONE': TONE_BED},
             'saved_wl': WET_DRY_ARTRUN_WL}
    for sn in ('FLOOR', 'FORD'):
        bpy.data.scenes[sn]['cobble_auth'] = json.dumps(stamp)
    print('STAMP', json.dumps({'auth_sha256': stamp['auth_sha256'][:12], 'mesh_hash': stamp['mesh_hash']}))
    os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(target), compress=True)
    print("FLOOR OK cobbles faces=%d" % nfaces)
    print("MESH= {'COBBLE_FLOOR': %s}" % json.dumps(fp))


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    default = os.path.normpath(os.path.join(HERE, "..", "..", "blender", "ford-cobble.blend"))
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(args[0] if args else default)
