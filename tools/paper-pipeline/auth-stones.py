# Author ford-stones.blend (pebble+stone ballast decorative factory) in the
# visible GUI session. Maintainer round-23 feedback baked in:
#   - west key sun (light travels +X) so cast shadows fall on the EAST side
#     (posts-family law 6; the first try had the tilt sign flipped);
#   - each variation = a HEAP of multiple stones, not one displaced lump;
#   - palette anchored to vanilla rock decoratives (measured mean [79,56,33]
#     sRGB, highlights ~[120,96,48] -> umber/brown, no white-grey).
# Scenes: PEBBLES (24 frames @ 40px cells) and STONES (12 frames @ 64px cells).
# Transparent film, no cast shadows onto art, Cycles posts-state (AgX, seed 0),
# single-thread fixed + no adaptive sampling (byte-stable in pixels, proven
# --twice). One frame per sprite: one heap visible per frame (staged by the
# bake script via hide_render - no fcurves, boolean fcurve eval is unreliable).
import bpy, math, os, random, bmesh

HERE = "/home/nmrp3/devel/factorio-mods/mods/water-ford/blender"
DEST = os.path.join(HERE, "ford-stones.blend")

bpy.ops.wm.read_factory_settings(use_empty=True)

def stone_mesh(name, r, subdiv, seed, disp):
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

# vanilla rock palette anchored (measured: mean [79,56,33], hi [120,96,48]);
# linear-space stops under AgX
M_DARK_PEBBLE  = (0.060, 0.033, 0.014)
M_LIGHT_PEBBLE = (0.220, 0.135, 0.050)
M_DARK_STONE   = (0.045, 0.026, 0.011)
M_LIGHT_STONE  = (0.180, 0.110, 0.040)

def build_scene(name, tag, n, cellpx, heap_lo, heap_hi, radii, subdiv, mat, seed_base):
    sc = bpy.data.scenes.new(name)
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 24
    sc.cycles.use_denoising = False
    sc.cycles.use_adaptive_sampling = False   # scheduling-dependent, byte-drifts
    sc.render.threads_mode = 'FIXED'
    sc.render.threads = 1                     # sequential accumulation = pixel-stable
    sc.cycles.seed = 0                     # posts-factory state (proven --twice)
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
        k = random.randint(heap_lo, heap_hi)          # stones in this heap
        r_main = radii[1] - ((i - 1) % 3) * 0.02      # main stone varies a bit
        cluster = [(0.0, 0.0, 0.0, r_main)]
        for j in range(1, k):
            ang = random.uniform(0, 6.283)
            dist = (r_main * 0.75) + random.uniform(0, r_main * 0.45)
            r = radii[0] + random.uniform(0, (radii[1] - radii[0]) * 0.75)
            cluster.append((math.cos(ang) * dist, math.sin(ang) * dist, j, r))
        for (x, y, j, r) in cluster:
            ob = stone_mesh(f"{tag}{i:03d}_{j}", r, subdiv, seed_base + i * 911 + j * 941, 0.6 + 0.15 * (j % 3))
            ob.data.materials.append(mat)
            random.seed(seed_base * 7 + i * 31 + j)
            ob.rotation_euler = (random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), random.uniform(0, 6.283))
            ob.location = (x, y, -r * 0.35 + (j * 0.0))
            coll.objects.link(ob)
            # inert by default: the bake script stages hide_render per frame
            ob.hide_render = True

    # west key sun: travelling +X and down (light from the west, shadows east)
    sun = bpy.data.lights.new("KEY_SUN", 'SUN')
    sun.energy = 3.5
    sun.angle = math.radians(10)
    sun_ob = bpy.data.objects.new("KEY_SUN", sun)
    sun_ob.rotation_euler = (0, math.radians(-55), 0)
    sc.collection.objects.link(sun_ob)

    fill = bpy.data.lights.new("FILL", 'AREA')
    fill.energy = 25
    fill.size = 2.0
    fill_ob = bpy.data.objects.new("FILL", fill)
    fill_ob.location = (0.35, -0.9, 1.2)
    fill_ob.rotation_euler = (math.radians(48), 0, math.radians(-12))
    sc.collection.objects.link(fill_ob)

    # camera: classic factorio 3/4 view from the south, ortho
    cam = bpy.data.cameras.new("SC_CAM")
    cam.type = 'ORTHO'
    cam.ortho_scale = cellpx / 40.0 * 0.55   # 0.55 units across a 40px cell; scales up for cells
    cam_ob = bpy.data.objects.new("SC_CAM", cam)
    sc.collection.objects.link(cam_ob)
    target = bpy.data.objects.new("SC_TARGET", None)
    target.empty_display_size = 0.05
    sc.collection.objects.link(target)
    target.location = (0, 0, -0.05)
    cam_ob.location = (0, -0.78, 0.95)
    tc = cam_ob.constraints.new('TRACK_TO')
    tc.target = target
    tc.track_axis = 'TRACK_NEGATIVE_Z'
    tc.up_axis = 'UP_Y'
    sc.camera = cam_ob

    sc.view_settings.view_transform = 'AgX'   # posts-family look pipeline
    return sc

m_pebble = stone_material("M_PEBBLE",  M_DARK_PEBBLE,  M_LIGHT_PEBBLE)
m_stone  = stone_material("M_STONE",   M_DARK_STONE,   M_LIGHT_STONE)

build_scene("PEBBLES", "pf", 24, 40, 2, 3, (0.055, 0.115), 2, m_pebble, 77000)
build_scene("STONES",  "sf", 12, 64, 2, 3, (0.10, 0.24),  3, m_stone,  99100)

bpy.ops.wm.save_as_mainfile(filepath=DEST)
print("AUTH-STONES-DONE saved", DEST)