# boards-builder.py — builds ford-boards.blend FROM PRIMITIVES (recipe Stage A)
#
# docs/export-recipe.md = the spec; boards-mplank-spec.json = the pinned
# grain/material look; this file = the generator. The .blend is BUILD OUTPUT:
# factory-empty rebuild every run — idempotent, seeded, committed logic.
#   blender -b --python boards-builder.py -- [--cells 0|all] [--outfile PATH]
#     --cells all  = fill every cell of every block
#     --cells 0    = the proof: only AREA_1X1's cell (0,0) (default)
#   A/B flag (maintainer look-test 2026-10-21):
#     --crown per-tile|per-plank   default per-tile = the old deck's
#       lattice-periodic crown in the pattern path (coplanar at every
#       1u cell edge — a wave in EVERY tile);
#       per-plank = one long arch per plank (h=0 at plank ends, arch
#       continues across internal tile lines). Same seeds otherwise.
#     --proof-tag TAG  renders /tmp/boards-proof<TAG>-*.png (A/B runs)
#     (the committed blend stays the default run's output; A/B outfiles
#     go elsewhere via --outfile)
# Design constants below = the measured construction facts (2026-10-21):
#   1 unit = 1 game tile = 128 px (maintainer-confirmed);
#   course pitch 0.25 u (4 courses per tile), plank width 0.234 u,
#   seam = fixed 2 px (0.0156 u) VOID with the GAP_TONE underlay beneath
#   (z=0.01); boards run along X: crown h = zbase + A*sin^2(pi(x-x0)/L),
#   strip granularity dx = 1/128 u, facet-shaded (sharp_face);
#   boards ~tile-long with staggered butts near unit boundaries;
#   bolts = 2 per plank end at 1/3 and 2/3 across the width (real mesh);
#   plank face attrs = plank_seed/origin/len/course/cx/cy/ringfreq/rgb.
# 2x2/4x4 rounds carry the old deck's measured facts (probe-old-deck.py
# over git 248d8f3, 2026-10-21):
#   - the "every-tile shade block" = round-13's DIVERSITY ENGINE (per-site
#     shuffled tone weights / patterns / casts, baked into face attrs — the
#     old file has NO shader branch: no modifiers, no drivers, no text
#     blocks; LAT_FIX is a 256-face missing-strip geometry patcher).
#     Here: per-1x1-TILE cast bias (weights tilted per tile, plank cast
#     picked by its midpoint tile's bias — planks stay cast-constant, the
#     old deck's law).
#   - multi-course planks measured in old 2x2s: w = 0.484 (2 courses,
#     ~20% of planks) and w = 0.734 (3 courses, ~2-8%); width law
#     w = h*PLANK_W + (h-1)*SEAM; the vertical phase law (old deck, ALL
#     planks): flush at the span's UPPER pitch line, the 2px seam slot
#     hangs just above the span's lower line — plank = [band bottom +
#     SEAM, band bottom + h*0.25]. (Maintainer 2026-10-21: multi-course
#     planks extend DOWNWARD from the flush upper line, not upward.)
#     1x1 cells carry the same phase (old zone: 100% w=0.234).
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
# Pool weights law (plank_pool_note, old deck 2026-10-17): honey 10/26 =
# 38.5%, grey spice ~11.5%; pool idx 0..7 = piling family, 8..11 = honey.
# (Applies to the 2x2/4x4 pattern path below; the approved 1x1 cells keep
# their committed pick law verbatim.)
POOL_W = (2, 3, 1, 3, 3, 1, 2, 1, 2, 2, 3, 3)
SEAM = COURSE_PITCH - PLANK_W  # 0.016 u; band's top strip = the seam
# Per-design pattern presets (old round-13 knob ranges re-based to PER-TILE
# semantics: the tile's TOP band decides the tile's multi-course plank);
# measured old-deck targets: doubles ~20-24% of planks / 35-40% area,
# triples ~2-11% / 5-24% area (probe-old-deck over LAT_BIG/2/3/4).
# "pin" = the band carries butts AT the internal 1x1 tile lines (old
# sites' edge courses: one full-tile plank per tile). Round-robin x16.
PATTERNS = (
    {"long": 0.45, "splice": 0.55, "pin": 0.00, "double": 0.30, "triple": 0.00},
    {"long": 0.60, "splice": 0.40, "pin": 0.00, "double": 0.65, "triple": 0.08},
    {"long": 0.75, "splice": 0.25, "pin": 0.00, "double": 0.75, "triple": 0.05},
    {"long": 0.60, "splice": 0.40, "pin": 0.00, "double": 0.90, "triple": 0.15},
    {"long": 0.75, "splice": 0.25, "pin": 0.15, "double": 0.45, "triple": 0.00},
    {"long": 0.45, "splice": 0.55, "pin": 0.10, "double": 0.70, "triple": 0.08},
    {"long": 0.75, "splice": 0.25, "pin": 0.25, "double": 0.55, "triple": 0.12},
    {"long": 0.60, "splice": 0.40, "pin": 0.20, "double": 0.75, "triple": 0.06},
)
# per-tile cast bias: TILE_BIAS_GAIN = max tilt (pool-luma halfspan units);
# per-tile tilt uniform(-1,1) — the tile mean leans bright or dark (target:
# per-tile-mean break like the old sheets' internal quartiles, ±5-10 L).
TILE_BIAS_GAIN = 2.4
BLOCKS = {
    "AREA_1X1": (-2.0, 2.0, -2.0, 2.0),      # x0,x1,y0,y1 (recipe Stage A)
    "AREA_2X2": (-4.0, 4.0, -12.0, -4.0),
    "AREA_4X4": (-8.0, 8.0, -30.0, -14.0),
}
CAMS = {"BLK1_CAM": (0.0, 0.0, 4.0, 512), "BLK2_CAM": (0.0, -8.0, 8.0, 1024),
        "BLK4_CAM": (0.0, -22.0, 16.0, 2048)}  # (cx, cy, ortho, res)


# ---------------------------------------------------------------- materials
def build_material(name, spec_name=None, pfx_scale=1.0):
    """Replay a spec material verbatim; name = the data-block's name,
    spec_name = the SPEC entry (for renamed variants). pfx_scale != 1:
    insert a multiply between Position.X and the pin chain's FRACT
    (ND_PFX.Value) so the pin window's period = the design sprite
    (per-sprite pins: the B look — internal tile-line windows gone,
    grain continuous inside the design; sprite-edge windows remain)."""
    spec = SPEC[spec_name or name]
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
    if pfx_scale != 1.0:
        pfx = nt.nodes["ND_PFX"]
        mn = nt.nodes.new("ShaderNodeMath")
        mn.operation = "MULTIPLY"
        mn.name = "ND_PFXSCALE"
        mn.location = (pfx.location[0] - 120, pfx.location[1])
        mn.inputs[1].default_value = pfx_scale
        # rewire: SEP.X -> PFXSCALE -> PFX (drop the direct link)
        for lk in list(nt.links):
            if lk.to_node == pfx and lk.to_socket.name == "Value":
                src = lk.from_node
                nt.links.remove(lk)
                nt.links.new(src.outputs["X"], mn.inputs["Value"])
        nt.links.new(mn.outputs["Value"], pfx.inputs["Value"])
    return m


# ---------------------------------------------------------------- geometry
def pick_cast(seed, weights=None):
    """Cast draw: weights=None = the 1x1 path's committed uniform pick
    (bit-stable); list = weighted + per-tile-bias path (weights already
    tilted by the tile's bias)."""
    pool = SPEC["plank_pool"]
    r = random.Random(seed * 7919)
    if weights is None:
        return r.choice(pool)[:3]
    tot = sum(weights)
    x = r.uniform(0, tot)
    acc = 0.0
    for i, w in enumerate(weights):
        acc += w
        if x <= acc:
            return pool[i][:3]
    return pool[-1][:3]


def tile_lumas():
    lumas = [0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] for c in SPEC["plank_pool"]]
    return lumas, (min(lumas) + max(lumas)) / 2, (max(lumas) - min(lumas)) / 2


def tile_weights(tilt, lumas, mid, half):
    return [max(0.05, w * (1.0 + TILE_BIAS_GAIN * tilt * (l - mid) / half))
            for w, l in zip(POOL_W, lumas)]


def emit_plank(coll, x0, y0, L, course, seed, mats, name, h=1, pick=None,
               periodic=False, plank_mat=None):
    """One plank: strip fan along X. y0 = the plank's BOTTOM (the call site
    passes span_bottom + SEAM; the plank is flush with its span's UPPER
    pitch line — the old deck's downward phase, maintainer 2026-10-21).
    h = band count 1..3: w = h*PLANK_W + (h-1)*SEAM (= h*0.25 - SEAM).
    Crown: per-plank sin² arch (the approved 1x1 law); periodic=True = the
    old deck's lattice-periodic crown A*sin²(π·fract(x)) — coplanar at
    every 1u cell edge (required where planks cross tile lines)."""
    dx = 1.0 / U_PX
    w = PLANK_W if h == 1 else h * PLANK_W + (h - 1) * SEAM
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
        if periodic:
            z = zbase + A * math.sin(math.pi * (x % 1.0)) ** 2
        else:
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
    cast = pick_cast(seed, pick)
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
    for slot, mat in enumerate((plank_mat or mats["M_PLANK"], mats["BOLT_METAL"])):
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


def build_cell(coll, block, size, k, seed, mats, crown="per-tile", pins="per-tile"):
    """Build design sprite k (row-major) of `size` inside its block.

    Coordination law (maintainer 2026-10-21, after the uncoordinated proof):
    planks TILE THE CELL's full x-span exactly — the first plank starts at
    the cell's left edge, the last ends at the right edge; butts seeded;
    every plank section carries its own arch with h=0 at both its ends,
    so joins land flush; bolts flank interior butts only; the pinned tone
    caps at the cell edges come from the shader, not geometry.

    size == 1 keeps the committed approved-look path VERBATIM (uniform
    pool pick, <=1 butt per course, single-course planks). size > 1 runs
    the pattern engine (the old deck's measured facts): per-design pattern
    preset round-robin (long / splice / pinned courses), h=2 (w=0.484) and
    h=3 (w=0.734) planks ANCHORED AT THEIR TILE'S TOP LINE extending
    downward (the old deck's measured doubles = tile-top pairs {2,3},
    triples = top triples {1,2,3}; maintainer 2026-10-21: multi-course
    planks extend DOWNward, not upward), lattice-periodic crowns so planks
    cross tile lines flush, and the PER-TILE CAST BIAS — the old diversity
    engine's per-tile shade block, applied per 1x1 tile so it breaks even
    under continuing planks (planks are cast-constant: the pick uses the
    bias of the tile containing the plank's midpoint).

    VERTICAL PHASE LAW (all paths): every plank = [span bottom + SEAM,
    span top FLUSH] — the seam hangs 2px just above the span's lower line
    (old deck measured); plank course attr = the plank's BOTTOM band's
    INTERNAL-to-tile index from the tile's BOTTOM (old deck measured:
    attr 0 = each tile's bottom course) = 3 - ((bc + bh - 1) % 4)."""
    lumas, lmid, lhalf = tile_lumas()
    x0, x1, y0, y1 = BLOCKS[block]
    side = size  # units per design sprite
    row, col = divmod(k, 4)
    sx0 = x0 + col * side
    sy1 = y1 - row * side
    if size == 1:
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
                emit_plank(coll, sx0 + lo, cy0 + SEAM, L, 3 - (c % 4), sseed, mats,
                           f"P_{block}_{k}_{c}_{pi}")
            # bolt each INTERIOR join ONCE (the butts only — never cell edges)
            for cut in butts:
                jrng = random.Random(seed * 101 + c * 31 + int(cut * 997))
                zjoin = PLANK_BOTTOM_Z + jrng.uniform(-0.003, 0.003)
                emit_bolts(coll, sx0 + cut, cy0, PLANK_W, zjoin, mats)
        return
    pat = PATTERNS[k % len(PATTERNS)]
    BUTT_GAP = 0.008
    for ty in range(size):                 # tiles walk downward from the design's top
        c0 = 4 * ty                        # the tile's TOP band (my top-down index)
        # the tile-top band decides the tile's multi-course plank (the old
        # deck's multis anchor at the tile's TOP line and extend downward:
        # doubles = top pairs (old internal bands {2,3}), triples = top
        # triples ({1,2,3})
        rng = random.Random(seed * 101 + c0)
        h0 = 1
        hd = rng.random()
        if hd < pat["triple"]:
            h0 = 3
        elif hd < pat["triple"] + pat["double"]:
            h0 = 2
        bands = [(c0, h0)] + [(c0 + j, 1) for j in range(h0, 4)]
        for (bc, bh) in bands:
            rng = random.Random(seed * 101 + bc)
            mode = rng.random()
            if mode < pat["long"]:
                butts = []
            elif mode < pat["long"] + pat["splice"]:
                butts = [side * 0.25 + rng.uniform(0.25, 0.75) * side * 0.5]
            elif mode < pat["long"] + pat["splice"] + pat["pin"]:
                butts = [float(i) for i in range(1, int(side))]  # internal tile lines
            else:
                butts = [side * 0.25 + rng.uniform(0.25, 0.75) * side * 0.5]
            # plank span: covers my bands bc..bc+bh-1 (extends DOWNWARD from
            # band bc; maintainer 2026-10-21); BOTTOM = lowest band's bottom
            # line + SEAM, TOP flush at band bc's top line
            y0_span = sy1 - (bc + bh) * 0.25 + SEAM
            cuts = [0.0] + sorted(butts) + [side]
            w_b = bh * PLANK_W + (bh - 1) * SEAM
            # course attr = the plank's BOTTOM band's internal-from-bottom
            # index (old deck law; feeds the per-course CRSRAMP ladder)
            course_attr = 3 - ((bc + bh - 1) % 4)
            for pi, (a, b) in enumerate(zip(cuts[:-1], cuts[1:])):
                lo = a + (BUTT_GAP / 2 if 0 < a < side else 0.0)
                hi = b - (BUTT_GAP / 2 if 0 < b < side else 0.0)
                L = hi - lo
                if L < 0.08:
                    continue
                midx = sx0 + lo + L / 2
                tx = int(((midx - sx0) // 1) % side)
                tilt = random.Random(seed * 131 + tx * 7919 + ty * 104729).uniform(-1, 1)
                weights = tile_weights(tilt, lumas, lmid, lhalf)
                sseed = seed * 101 + bc * 31 + pi
                emit_plank(coll, sx0 + lo, y0_span, L, course_attr, sseed, mats,
                           f"P_{block}_{k}_{bc}_{pi}", h=bh, pick=weights,
                           periodic=(crown == "per-tile"),
                           plank_mat=(mats[f"M_PLANK_{side}"] if pins == "per-sprite"
                                      else None))
            for cut in butts:
                jrng = random.Random(seed * 101 + bc * 31 + int(cut * 997))
                zjoin = PLANK_BOTTOM_Z + jrng.uniform(-0.003, 0.003)
                emit_bolts(coll, sx0 + cut, y0_span, w_b, zjoin, mats)


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


def census():
    """Numeric self-checks straight from the emitted face attrs (no renders):
    per-design internal-tile plank-cast means (the per-tile shade break) and
    the plank width classes (doubles/triples vs old-deck ratios)."""
    from collections import defaultdict
    import statistics
    tile_cast = defaultdict(lambda: defaultdict(list))
    wcls = defaultdict(lambda: defaultdict(int))
    for ob in bpy.data.objects:
        if not ob.name.startswith("P_"):
            continue
        # P_AREA_1X1_k_c_pi: block = the two name pieces after P_
        parts = ob.name.split("_")
        block, k = "_".join(parts[1:3]), int(parts[3])
        side = {"AREA_1X1": 1, "AREA_2X2": 2, "AREA_4X4": 4}[block]
        x0, x1_, y0_, y1_ = BLOCKS[block]
        row, col = divmod(k, 4)
        row_top = y1_ - row * side
        me = ob.data
        xs = [v.co.x for v in me.vertices]
        ys = [v.co.y for v in me.vertices]
        cxm, cym = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        tx = int((cxm - (x0 + col * side)))
        ty = int((row_top - cym))
        rgb = me.attributes["plank_rgb"].data[0].color
        luma = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
        area = (max(xs) - min(xs)) * (max(ys) - min(ys))
        tile_cast[block][k].append((tx, ty, luma, area))
        wcls[block][round(max(ys) - min(ys), 3)] += 1
    print("== census: per-tile plank-cast means (linear, area-weighted) ==")
    for block, designs in tile_cast.items():
        for k in sorted(designs):
            tm = defaultdict(list)
            for tx, ty, luma, area in designs[k]:
                tm[(tx, ty)].append((luma, area))
            means = {t: sum(l*a for l, a in vs) / sum(a for _l, a in vs)
                     for t, vs in tm.items()}
            ms = sorted(means.values())
            sv = statistics.pstdev(ms) if len(ms) > 1 else 0.0
            print(f"  {block} design {k}: tiles={[f'{t[0]},{t[1]}:{m:.3f}' for t, m in sorted(means.items())]}"
                  f" sigma={sv:.4f} range={ms[-1]-ms[0]:.4f}")
    print("== census: plank width classes (count, count-share) ==")
    for block, cw in wcls.items():
        n = sum(cw.values())
        print(f"  {block}: " + ", ".join(
            f"w={w}: {cnt} ({100.0*cnt/n:.1f}%)" for w, cnt in sorted(cw.items())))
    # FLUSH + PHASE + COURSE-ATTR GATES (the old deck's vertical law):
    # every plank = [span bottom + SEAM, span top flush at its starting
    # band's upper line]; course attr = 3 - ((bc+bh-1) % 4). Hard gate on
    # every P_ object, parsed from its name.
    bad = 0
    for ob in bpy.data.objects:
        if not ob.name.startswith("P_"):
            continue
        parts = ob.name.split("_")
        block, k, bc = "_".join(parts[1:3]), int(parts[3]), int(parts[4])
        me = ob.data
        ys = [v.co.y for v in me.vertices]
        y_top, y_bot = max(ys), min(ys)
        w = round(y_top - y_bot, 6)
        bh = int(round((w + SEAM) / COURSE_PITCH))
        side = {"AREA_1X1": 1, "AREA_2X2": 2, "AREA_4X4": 4}[block]
        _, _, y0b, y1b = BLOCKS[block]
        row, col = divmod(k, 4)
        row_top = y1b - row * side
        line_top = row_top - bc * COURSE_PITCH
        line_bot = row_top - (bc + bh) * COURSE_PITCH + SEAM
        if abs(y_top - line_top) > 1e-6 or abs(y_bot - line_bot) > 1e-6:
            bad += 1
        ca = me.attributes["plank_course"].data[0].value
        want = 3 - ((bc + bh - 1) % 4)
        if abs(ca - want) > 1e-6:
            bad += 1
    print(f"== flush/phase/attr gates: {bad} failures on "
          f"{len([o for o in bpy.data.objects if o.name.startswith('P_')])} planks "
          f"(0 = the vertical law exact)")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    cells = "0"
    crown = "per-tile"
    pins = "per-tile"
    ptag = ""
    outfile = os.path.join(HERE, "..", "..", "blender", "ford-boards.blend")
    for i, a in enumerate(argv):
        if a == "--cells":
            cells = argv[i + 1]
        if a == "--outfile":
            outfile = os.path.abspath(argv[i + 1])
        if a == "--crown":
            crown = argv[i + 1]
        if a == "--pins":
            pins = argv[i + 1]
        if a == "--proof-tag":
            ptag = argv[i + 1]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = {n: build_material(n) for n in ("M_PLANK", "BOLT_METAL", "GAP_TONE")}
    if pins == "per-sprite":
        # B: the pin window rides the design sprite's period instead of the
        # 1u tile: per-size M_PLANK variants with a x/side multiply before
        # the pin FRACT (geometry + everything else verbatim)
        for side_ in (2, 4):
            mats[f"M_PLANK_{side_}"] = build_material(f"M_PLANK_{side_}",
                                                      spec_name="M_PLANK",
                                                      pfx_scale=1.0 / side_)
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
    for block in ("AREA_1X1", "AREA_2X2", "AREA_4X4"):
        emit_underlay(bpy.data.collections["UNDERLAY"], block, mats)
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
    # one seed base per size (1x1 keeps its committed 1000; the 2x2 keeps
    # 2000; the 4x4's own base mirrors the cam roster 1/2/4)
    for size, seedbase in ((1, 1000), (2, 2000), (4, 4000)):
        for k in fill:
            build_cell(content, f"AREA_{size}X{size}", size, k, seed=seedbase + k,
                       mats=mats, crown=crown, pins=pins)
    sc = build_scene("FLOOR", 1536, 96)
    sc.camera = bpy.data.objects["BLK1_CAM"]
    # proof renders (transient: the zoom camera is created ONCE and reused —
    # a second .new() got auto-renamed PROOF_ZOOM.001 and leaked into the
    # save; found by the reopen census 2026-10-21)
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 48
    pcd = bpy.data.cameras.new("PROOF_ZOOM")
    pcd.type = "ORTHO"
    pcd.ortho_scale = 1.3
    pz = bpy.data.objects.new("PROOF_ZOOM", pcd)
    pz.location = (0.0, 0.0, 60.0)
    bpy.data.collections["CAMERAS"].objects.link(pz)
    renders = [
        ("BLK1_CAM", 512, f"/tmp/boards-proof{ptag}-1x1.png", (-1.5, 1.5)),
        ("BLK2_CAM", 1024, f"/tmp/boards-proof{ptag}-2x2.png", None),
        ("BLK4_CAM", 2048, f"/tmp/boards-proof{ptag}-4x4.png", None),
        (None, 512, f"/tmp/boards-proof{ptag}-zoom.png", (-1.5, 1.5)),
        (None, 512, f"/tmp/boards-proof{ptag}-zoom2.png", (-3.0, -11.0)),
        (None, 512, f"/tmp/boards-proof{ptag}-zoom4.png", (-7.0, -15.0)),
    ]
    saved_res = (sc.render.resolution_x, sc.render.resolution_y)
    for cam_name, res, out, zpos in renders:
        sc.camera = bpy.data.objects[cam_name] if cam_name else pz
        if cam_name is None:  # close-up over a block's cell (0,0), 1.3u wide
            pz.location = (zpos[0], zpos[1], 60.0)
        sc.render.resolution_x = sc.render.resolution_y = res
        sc.render.filepath = out
        bpy.ops.render.render(write_still=True, scene=sc.name)
    sc.render.resolution_x, sc.render.resolution_y = saved_res
    sc.camera = bpy.data.objects["BLK1_CAM"]
    bpy.data.objects.remove(pz, do_unlink=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(outfile), compress=True)
    np_ = len([o for o in bpy.data.objects if o.name.startswith("P_")])
    nb = len([o for o in bpy.data.objects if o.name.startswith("BOLT")])
    nu = len([o for o in bpy.data.objects if o.name.endswith("_UNDERLAY")])
    census()
    print(f"BOARDS BUILT crown={crown} pins={pins} mats={len(mats)} "
          f"cells={len(fill)}/block blocks=3 planks={np_} bolts={nb} underlays={nu} "
          f"scene={sc.camera.name} out={outfile}")


main()