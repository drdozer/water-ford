# boards-builder.py — builds ford-boards.blend FROM PRIMITIVES (recipe Stage A)
#
# docs/export-recipe.md = the spec; boards-mplank-spec.json = the pinned
# grain/material look; this file = the generator. The .blend is BUILD OUTPUT:
# factory-empty rebuild every run — idempotent, seeded, committed logic.
#   blender -b --python boards-builder.py -- [--cells 0|all] [--outfile PATH]
#     --cells all  = fill every cell of every block
#     --cells 0    = the proof: only AREA_1X1's cell (0,0) (default)
# Design constants below = the measured construction facts (2026-10-21):
#   1 unit = 1 game tile = 128 px (maintainer-confirmed);
#   course pitch 0.25 u (4 courses per tile), plank width 0.234 u,
#   seam = fixed 2 px (0.0156 u) VOID with the GAP_TONE underlay beneath
#   (z=0.01); boards run along X: crown h = zbase + A*sin^2(pi(x-x0)/L),
#   strip granularity dx = 1/128 u, facet-shaded (sharp_face);
#   boards ~tile-long with staggered butts near unit boundaries;
#   bolts = 2 per plank end at 1/3 and 2/3 across the width (real mesh);
#   plank face attrs = plank_seed/origin/len/course/cx/cy/ringfreq/rgb.
import bpy
import math
import os
import sys
import json
import random

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = json.load(open(os.path.join(HERE, "boards-mplank-spec.json")))

U_PX = 128
COURSE_PITCH = 0.25
PLANK_W = 0.234  # the course's plank width; the rest = the 2px seam
PLANK_BOTTOM_Z = 0.056
BLOCKS = {
    "AREA_1X1": (-2.0, 2.0, -2.0, 2.0),      # x0,x1,y0,y1 (recipe Stage A)
    "AREA_2X2": (-4.0, 4.0, -12.0, -4.0),
    "AREA_4X4": (-8.0, 8.0, -30.0, -14.0),
}
CAMS = {"BLK1_CAM": (0.0, 0.0, 4.0, 512), "BLK2_CAM": (0.0, -8.0, 8.0, 1024),
        "BLK4_CAM": (0.0, -22.0, 16.0, 2048)}  # (cx, cy, ortho, res)


# ---------------------------------------------------------------- materials
def build_material(name):
    spec = SPEC[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    made = {}
    for d in spec["nodes"]:
        bl = {"ATTRIBUTE": "ShaderNodeAttribute", "NEW_GEOMETRY": "ShaderNodeNewGeometry",
              "SEPXYZ": "ShaderNodeSeparateXYZ", "COMBXYZ": "ShaderNodeCombineXYZ",
              "VECT_MATH": "ShaderNodeVectorMath", "MATH": "ShaderNodeMath",
              "MAP_RANGE": "ShaderNodeMapRange", "MIX_RGB": "ShaderNodeMixRGB",
              "VALTORGB": "ShaderNodeValToRGB", "TEX_NOISE": "ShaderNodeTexNoise",
              "BSDF_PRINCIPLED": "ShaderNodeBsdfPrincipled",
              "OUTPUT_MATERIAL": "ShaderNodeOutputMaterial"}.get(d["type"], d["type"])
        n = nt.nodes.new(bl)
        n.name = d["name"]
        n.location = d["location"]
        for k, v in d.get("props", {}).items():
            if k == "ramp":
                while len(n.color_ramp.elements) > 1:
                    n.color_ramp.elements.remove(n.color_ramp.elements[-1])
                n.color_ramp.interpolation = v["interpolation"]
                r = n.color_ramp.elements[0]
                r.position, r.color = v["stops"][0]
                for pos, col in v["stops"][1:]:
                    e = n.color_ramp.elements.new(pos)
                    e.color = col
            elif k == "interpolation_type":
                n.interpolation_type = v
            elif k == "attribute_name":
                n.attribute_name = v
            else:
                try:
                    setattr(n, k, v)
                except Exception:
                    pass
        for ik, iv in d.get("inputs", {}).items():
            if isinstance(iv, str):  # identifier-keyed string value = skip
                continue
            sock = n.inputs.get(ik)
            if sock is None or not hasattr(sock, "default_value"):
                continue
            try:
                sock.default_value = iv
            except Exception:
                pass
        made[d["name"]] = n
    for fn, fs, tn, ts in spec["links"]:
        if fn in made and tn in made:
            nt.links.new(made[fn].outputs.get(fs, made[fn].outputs[0]),
                         made[tn].inputs.get(ts, made[tn].inputs[0]))
    return m


# ---------------------------------------------------------------- geometry
def emit_plank(coll, x0, y0, L, course, seed, mats, name):
    """One plank: strip fan along X with the sin^2 crown; face attrs; bolts."""
    dx = 1.0 / U_PX
    w = PLANK_W
    rng = random.Random(seed * 31)
    A = rng.uniform(0.008, 0.014)
    zbase = PLANK_BOTTOM_Z + rng.uniform(-0.003, 0.003)
    x1 = x0 + L
    n_strip = max(2, int(round(L / dx)))
    verts = []   # (x, y, z) per strip edge, two y-rows
    faces = []
    attrs = []
    for i in range(n_strip + 1):
        x = x0 + min(i * dx, L)
        z = zbase + A * math.sin(math.pi * (x - x0) / L) ** 2
        verts.append((x, y0, z))
        verts.append((x, y0 + w, z))
    for i in range(n_strip):
        a = 2 * i
        faces.append([a, a + 1, a + 3, a + 2])
        attrs.append(i)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    # face attrs — the measured virtual-log model (old deck, decoded
    # 2026-10-21): plank_cx = the plank's WORLD-CENTER x; plank_cy = the
    # plank's center y + an OFF-CANVAS pith shift (old range ±11.5 over a
    # ±6 deck); ringfreq = uniform(8, 16) (rings every ~8-16px); the
    # grain's ring radius = len(world_pos - pith), so arcs are per-plank.
    n_faces = n_strip
    rngB = random.Random(seed)
    pith_shift_y = rngB.uniform(-5.5, 5.5)
    cx = x0 + L / 2
    cy = y0 + w / 2 + pith_shift_y
    rf = rngB.uniform(8.0, 16.0)
    cast = random.Random(seed * 7919).choice(SPEC["plank_pool"])[:3]
    for fname, size in (("plank_seed", 1), ("plank_len", 1), ("plank_course", 1),
                        ("plank_cx", 1), ("plank_cy", 1), ("plank_ringfreq", 1)):
        a = me.attributes.new(fname, "FLOAT", "FACE")
        val = {"plank_seed": rngB.uniform(0, 1), "plank_len": L,
               "plank_course": course, "plank_cx": cx, "plank_cy": cy,
               "plank_ringfreq": rf}[fname]
        for f in range(n_faces):
            a.data[f].value = val
    a = me.attributes.new("plank_rgb", "FLOAT_COLOR", "FACE")
    for f in range(n_faces):
        a.data[f].color = (*cast, 1.0)
    a = me.attributes.new("sharp_face", "BOOLEAN", "FACE")
    for f in range(n_faces):
        a.data[f].value = True
    ob = bpy.data.objects.new(name, me)
    for slot, mat in enumerate((mats["M_PLANK"], mats["BOLT_METAL"])):
        ob.data.materials.append(mat)
    coll.objects.link(ob)
    return ob


def emit_bolts(coll, x_cut, y0, w, zbase, mats):
    """The join's bolt pair: 2 bolts AT the join (1/3 and 2/3 across the
    plank width) — one pair per join, shared by both planks, emitted once
    per join line. CALLED ONLY FOR INTERIOR BUTTS (maintainer 2026-10-21:
    bolts place where two boards MEET within a course within a tile — not
    at cell edges).

    Geometry = the extracted VERBATIM template (boards-mplank-spec.json
    bolt_template): a flat 12-gon washer, ~10.2px diameter, 1.3px tall —
    round, matching the old deck's 462 identical 13-poly/24-vert domes; it
    sits 0.5px above the flush join surface."""
    import math as mt
    tmpl = SPEC["bolt_template"]
    tv = tmpl["verts"]
    tf = tmpl["faces"]
    R = 0.04                     # the template washer's radius
    # spread by the 1x:2x space law (maintainer 2026-10-21: ~1x space to the
    # board edge, ~2x between the bolts): g = (w - 2*2R)/4, between = 2g
    g = max(0.0, (w - 4 * R) / 4)
    dz = zbase + 0.004  # the old disc's bottom sits +0.004 over the plank
    for fy in (g + R, w - g - R):
        by = y0 + fy
        me = bpy.data.meshes.new(f"BOLT_{x_cut:.2f}_{fy:.2f}")
        verts = [(round(x_cut + vx, 5), round(by + vy, 5), round(dz + vz, 5))
                 for vx, vy, vz in tv]
        me.from_pydata(verts, [], tf)
        me.update()
        ob = bpy.data.objects.new(me.name, me)
        ob.data.materials.append(mats["BOLT_METAL"])
        coll.objects.link(ob)


def emit_underlay(coll, block, mats):
    x0, x1, y0, y1 = BLOCKS[block]
    me = bpy.data.meshes.new(f"{block}_UNDERLAY")
    me.from_pydata([(x0, y0, 0.01), (x1, y0, 0.01), (x1, y1, 0.01), (x0, y1, 0.01)],
                   [], [(0, 1, 2, 3)])
    me.update()
    ob = bpy.data.objects.new(me.name, me)
    ob.data.materials.append(mats["GAP_TONE"])
    coll.objects.link(ob)


def build_cell(coll, block, size, k, seed, mats):
    """Build design sprite k (row-major) of `size` inside its block.

    Coordination law (maintainer 2026-10-21, after the uncoordinated proof):
    planks TILE THE CELL's full x-span exactly — the first plank starts at
    the cell's left edge, the last ends at the right edge; 0-1 interior
    butts per course (seeded); every plank section carries its own arch
    with h=0 at both its ends, so joins land flush; end bolts flank every
    plank end; the pinned tone caps at the cell edges come from the shader,
    not geometry."""
    x0, x1, y0, y1 = BLOCKS[block]
    side = size  # units per design sprite
    row, col = divmod(k, 4)
    sx0 = x0 + col * side
    sy1 = y1 - row * side
    for c in range(4 * size):          # courses through the design (0.25 pitch)
        cy0 = sy1 - (c + 1) * 0.25
        rng = random.Random(seed * 101 + c)
        # butt schedule: planks partition [0, side] exactly; 0-1 interior butts
        BUTT_GAP = 0.008                # ~1px = half the course seam
        butts = []
        if rng.random() < 0.5:
            butts = [side * 0.25 + rng.uniform(0.25, 0.75) * side * 0.5]
        cuts = [0.0] + sorted(butts) + [side]
        for pi, (a, b) in enumerate(zip(cuts[:-1], cuts[1:])):
            lo = a + (BUTT_GAP / 2 if 0 < a < side else 0.0)
            hi = b - (BUTT_GAP / 2 if 0 < b < side else 0.0)
            L = hi - lo
            if L < 0.08:
                continue
            sseed = seed * 101 + c * 31 + pi
            emit_plank(coll, sx0 + lo, cy0, L, c % 4, sseed, mats,
                       f"P_{block}_{k}_{c}_{pi}")
        # bolt each INTERIOR join ONCE (the butts only — never cell edges)
        for cut in butts:
            jrng = random.Random(seed * 101 + c * 31 + int(cut * 997))
            zjoin = PLANK_BOTTOM_Z + jrng.uniform(-0.003, 0.003)
            emit_bolts(coll, sx0 + cut, cy0, PLANK_W, zjoin, mats)
    return k


# ---------------------------------------------------------------- scenes/rig
def build_scene(name, res, samples):
    s = bpy.data.scenes.new(name)
    r = s.render
    r.engine = "CYCLES"
    r.resolution_x = res
    r.resolution_y = res
    s.cycles.samples = samples
    s.cycles.use_adaptive_sampling = True
    s.cycles.use_denoising = False
    s.cycles.max_bounces = 12
    s.view_settings.view_transform = "Standard"
    s.render.film_transparent = False
    w = bpy.data.worlds.get("BOARDS_WORLD")
    s.world = w
    for cname in ("CONTENT", "UNDERLAY", "LIGHTING", "CAMERAS"):
        s.collection.children.link(bpy.data.collections[cname])
    return s


def build_rig():
    kd = bpy.data.lights.new("KEY", "POINT")
    kd.energy = 1800000.0
    kd.shadow_soft_size = 0.1
    k = bpy.data.objects.new("KEY", kd)
    k.location = (-126.0, 0.0, 126.0)
    bpy.data.collections["LIGHTING"].objects.link(k)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    cells = "0"
    outfile = os.path.join(HERE, "..", "..", "blender", "ford-boards.blend")
    for i, a in enumerate(argv):
        if a == "--cells":
            cells = argv[i + 1]
        if a == "--outfile":
            outfile = os.path.abspath(argv[i + 1])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = {n: build_material(n) for n in ("M_PLANK", "BOLT_METAL", "GAP_TONE")}
    # world
    w = bpy.data.worlds.new("BOARDS_WORLD")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.55, 0.55, 0.55, 1.0)
    bg.inputs[1].default_value = 0.06
    for cn in ("CONTENT", "UNDERLAY", "LIGHTING", "CAMERAS"):
        bpy.data.collections.new(cn)
    build_rig()
    content = bpy.data.collections["CONTENT"]
    emit_underlay(bpy.data.collections["UNDERLAY"], "AREA_1X1", mats)
    # CAMERAS
    sc_list = []
    for cam_name, (cx, cy, ortho, res) in CAMS.items():
        cd = bpy.data.cameras.new(cam_name)
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
        cd.clip_start, cd.clip_end = 0.1, 300.0
        ob = bpy.data.objects.new(cam_name, cd)
        ob.location = (cx, cy, 60.0)
        bpy.data.collections["CAMERAS"].objects.link(ob)
    fill = (0,) if cells == "0" else tuple(range(16))
    for k in fill:
        build_cell(content, "AREA_1X1", 1, k, seed=1000 + k, mats=mats)
    sc = build_scene("FLOOR", 1536, 96)
    sc.camera = bpy.data.objects["BLK1_CAM"]
    # proof renders (transient: restored below, files to /tmp)
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 48
    renders = [
        ("BLK1_CAM", 512, "/tmp/boards-proof-1x1.png"),
        (None, 512, "/tmp/boards-proof-zoom.png"),
    ]
    saved_res = (sc.render.resolution_x, sc.render.resolution_y)
    for cam_name, res, out in renders:
        if cam_name is None:  # a close-up cam over cell (0,0): tile = x -2..-1, y 1..2
            cd = bpy.data.cameras.new("PROOF_ZOOM")
            cd.type = "ORTHO"
            cd.ortho_scale = 1.3
            ob = bpy.data.objects.new("PROOF_ZOOM", cd)
            ob.location = (-1.5, 1.5, 60.0)
            bpy.data.collections["CAMERAS"].objects.link(ob)
            sc.camera = ob
        else:
            sc.camera = bpy.data.objects[cam_name]
        sc.render.resolution_x = sc.render.resolution_y = res
        sc.render.filepath = out
        bpy.ops.render.render(write_still=True, scene=sc.name)
    sc.render.resolution_x, sc.render.resolution_y = saved_res
    sc.camera = bpy.data.objects["BLK1_CAM"]
    bpy.data.objects.remove(bpy.data.objects["PROOF_ZOOM"], do_unlink=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(outfile), compress=True)
    print(f"BOARDS BUILT mats=3 cells={len(fill)} scene={sc.camera.name} out={outfile}")


main()