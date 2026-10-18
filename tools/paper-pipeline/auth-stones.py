# Author ford-stones.blend v2 (pebble+stone ballast decorative factory) in the
# visible GUI session. Round-25 changes (maintainer steered):
#   - camera = the posts-factory rig (ICON cam: loc (0,-0.707,1.107), rot X 45deg,
#     ortho) instead of the steeper fresh rig - the v1 stones read "top down";
#   - every stone mesh is SLICED at a uniform waterline plane into an above part
#     and a below part (true vertex ring at the cut, same semantics as the
#     piling GN water-plane cut); per-frame heap = above objects + below objects;
#   - the bake renders aligned ABOVE/BELLOW sheets; the wiring composites them
#     via Sprite.layers with blend_mode "multiplicative-with-alpha" on the
#     below part (dry part stays normal/opaque).
# Scenes: PEBBLES (24 frames @ 40px cells) and STONES (12 frames @ 64px cells).
# West key sun (light travels +X, shadows east), transparent film, AgX, Cycles
# posts-state, single-thread fixed, no adaptive sampling (pixel --twice proven).
import bpy, math, os, random, bmesh

HERE = "/home/nmrp3/devel/factorio-mods/mods/water-ford/blender"
DEST = os.path.join(HERE, "ford-stones.blend")

WATERLINE_Z = 0.0   # uniform world-plane slice: above = dry stone, below = water part

bpy.ops.wm.read_factory_settings(use_empty=True)

def make_stone_object(name, r, subdiv, seed, disp):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    random.seed(seed)
    for v in me.vertices:
        n = random.uniform(-1.0, 1.0)
        v.co = v.co + v.co.normalized() * (n * disp * r * 0.25)
    me.update()
    return ob

def split_mesh_at_z(src, z0):
    """Split a star-convex mesh at plane z=z0 into (above, below) coordinate
    lists. Spanning faces are clipped on their edges (linear interpolation),
    producing a true vertex ring at the cut (piling GN-cut semantics)."""
    verts = [v.co.copy() for v in src.vertices]
    polys = [list(p.vertices) for p in src.polygons]
    above, below = [], []
    def crossp(a, b):
        t = (z0 - a.z) / (b.z - a.z)
        return a.lerp(b, t)
    for idx in polys:
        pts = [(verts[i], verts[i].z >= z0) for i in idx]
        zs = [p[0].z for p in pts]
        if all(z >= z0 for z in zs):
            above.append([p[0].copy() for p in pts])
        elif all(z <= z0 for z in zs):
            below.append([p[0].copy() for p in pts])
        else:
            # one vertex on one side, two on the other: clip the triangle
            hi = [p for (p, a) in pts if a]
            lo = [p for (p, a) in pts if not a]
            if len(hi) == 1:
                A, B, C = hi[0], lo[0], lo[1]
                if (B - A).length > (C - A).length:
                    B, C = C, B
                cAB, cAC = crossp(A, B), crossp(A, C)
                above.append([A.copy(), cAB, cAC])
                below.append([B.copy(), C.copy(), cAC, cAB])
            else:
                A, B = hi[0], hi[1]
                C = lo[0]
                if (A - C).length > (B - C).length:
                    A, B = B, A
                cAC, cBC = crossp(A, C), crossp(B, C)
                below.append([C.copy(), cAC, cBC])
                above.append([A.copy(), B.copy(), cBC, cAC])
    return above, below

def object_from_faces(name, faces, mat):
    """faces = list of vert-coordinate lists; produces a mesh object."""
    verts, face_idx = [], []
    seen = {}
    def vid(p):
        key = (round(p.x, 7), round(p.y, 7), round(p.z, 7))
        if key not in seen:
            seen[key] = len(verts); verts.append((p.x, p.y, p.z))
        return seen[key]
    for f in faces:
        face_idx.append(tuple(vid(p) for p in f))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], face_idx)
    me.update()
    ob = bpy.data.objects.new(name, me)
    if mat: ob.data.materials.append(mat)
    return ob

def stone_material(name, dark, light):
    dark  = (*dark,  1.0) if len(dark)  == 3 else dark
    light = (*light, 1.0) if len(light) == 3 else light
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.85
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 14.0
    noise.inputs["Detail"].default_value = 8.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = dark
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = light
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m

# light stops raised to the vanilla-anchor range's bright end so lit faces
# read brighter than the deck planks (maintainer: south faces read "in
# shadow" against the boards even after the sun fix); dark stops keep umber
M_DARK_PEBBLE  = (0.060, 0.033, 0.014)
M_LIGHT_PEBBLE = (0.300, 0.185, 0.078)
M_DARK_STONE   = (0.048, 0.028, 0.012)
M_LIGHT_STONE  = (0.250, 0.155, 0.058)

def build_scene(name, tag, n, cellpx, heap_lo, heap_hi, radii, subdiv, mat, mat_wet, seed_base):
    sc = bpy.data.scenes.new(name)
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 24
    sc.cycles.use_denoising = False
    sc.cycles.use_adaptive_sampling = False
    sc.render.threads_mode = 'FIXED'
    sc.render.threads = 1
    sc.cycles.seed = 0
    sc.render.resolution_x = cellpx
    sc.render.resolution_y = cellpx
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.frame_start = 1
    sc.frame_end = n

    coll = bpy.data.collections.new("FRAMES")
    sc.collection.children.link(coll)

    for i in range(1, n + 1):
        random.seed(seed_base + i * 911)
        k = random.randint(heap_lo, heap_hi)
        r_main = radii[1] - ((i - 1) % 3) * 0.02
        cluster = [(0.0, 0.0, 0.0, r_main)]
        for j in range(1, k):
            ang = random.uniform(0, 6.283)
            dist = (r_main * 0.75) + random.uniform(0, r_main * 0.45)
            r = radii[0] + random.uniform(0, (radii[1] - radii[0]) * 0.75)
            cluster.append((math.cos(ang) * dist, math.sin(ang) * dist, j, r))
        for (x, y, j, r) in cluster:
            src = make_stone_object(f"tmp{i:03d}_{j}", r, subdiv,
                                    seed_base + i * 911 + j * 941, 0.6 + 0.15 * (j % 3))
            above, below = split_mesh_at_z(src.data, WATERLINE_Z)
            rx = 0.0   # no tilt: the waterline cut must stay a horizontal plane
            ry = 0.0
            rz = random.uniform(0, 6.283)
            # rotation_mode note: blender objects default to QUATERNION, which
            # SILENTLY IGNORES rotation_euler (v1/v2 bug: sun, fill and camera
            # never rotated - top-down renders). All rotated objects set XYZ.
            for part, faces in (("a", above), ("w", below)):
                if not faces: continue
                ob = object_from_faces(f"{tag}{i:03d}_{j}{part}", faces, mat if part == "a" else mat_wet)
                ob.rotation_mode = 'XYZ'
                ob.rotation_euler = (rx, ry, rz)
                ob.location = (x, y, -r * 0.12)
                coll.objects.link(ob)
            bpy.data.objects.remove(src)

    # west key sun: light travels east+north+down (from the west-southwest, up)
    # so the camera-visible south faces stay lit and shadows fall on the
    # east-ward side, away from the camera (maintainer round-25). The posts
    # factory's pure-west key works for tall poles; low mounds need the
    # southward component or their visible faces sit at the terminator.
    sun = bpy.data.lights.new("KEY_SUN", 'SUN')
    sun.energy = 4.2
    sun.angle = math.radians(10)
    sun_ob = bpy.data.objects.new("KEY_SUN", sun)
    sun_ob.rotation_mode = 'XYZ'
    sun_ob.rotation_euler = (math.radians(47.5), 0, math.radians(-65))
    sc.collection.objects.link(sun_ob)

    # south fill: carries the camera-visible south faces (sun owns the shadow
    # direction); pure-south so it never washes the east shadow side
    fill = bpy.data.lights.new("FILL", 'AREA')
    fill.energy = 25
    fill.size = 2.0
    fill_ob = bpy.data.objects.new("FILL", fill)
    fill_ob.rotation_mode = 'XYZ'
    fill_ob.location = (0.15, -1.15, 0.9)
    fill_ob.rotation_euler = (math.radians(54), 0, math.radians(7))
    sc.collection.objects.link(fill_ob)

    # camera: the posts-factory rig angle (45 deg elevation, ortho) re-aimed
    # at the stones' center: same direction as ICON_CAM, shifted along its
    # axis so the small heaps fill the cell (the posts rig aims mid-post)
    cam = bpy.data.cameras.new("SC_CAM")
    cam.type = 'ORTHO'
    cam.ortho_scale = cellpx / 40.0 * 0.55
    cam_ob = bpy.data.objects.new("SC_CAM", cam)
    sc.collection.objects.link(cam_ob)
    cam_ob.rotation_mode = 'XYZ'
    cam_ob.location = (0.0, -0.785, 0.785)
    cam_ob.rotation_euler = (math.radians(45.0), 0.0, 0.0)
    sc.camera = cam_ob

    sc.view_settings.view_transform = 'AgX'
    return sc

m_pebble = stone_material("M_PEBBLE",  M_DARK_PEBBLE,  M_LIGHT_PEBBLE)
m_stone  = stone_material("M_STONE",   M_DARK_STONE,   M_LIGHT_STONE)
# bright washed masks for the below-waterline slices (multiplicative layer)
m_pebble_wet = stone_material("M_PEBBLE_WET", (0.42, 0.38, 0.30), (0.74, 0.68, 0.58))
m_stone_wet  = stone_material("M_STONE_WET",  (0.38, 0.35, 0.28), (0.68, 0.63, 0.54))

build_scene("PEBBLES", "pf", 24, 40, 2, 3, (0.055, 0.115), 2, m_pebble, m_pebble_wet, 77000)
build_scene("STONES",  "sf", 12, 64, 2, 3, (0.10, 0.24),  3, m_stone, m_stone_wet, 99100)

bpy.ops.wm.save_as_mainfile(filepath=DEST)
print("AUTH-STONES-DONE saved", DEST)