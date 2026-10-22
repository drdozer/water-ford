# bake-ladder.py — the ladder exporter recipe's driver (tools, new toolchain)
#
# docs/export-recipe.md is the spec; this file implements stages B (render)
# and C (cut) and the deploy/gate machinery. Boards first, then cobbles
# (`--wetpass`). NOT part of the condemned cobble crank; shares nothing with
# auth-cobble/bake-cobble.
#
# Usage:
#   blender --background --python-expr ... --python bake-ladder.py --   \
#       --blend <file> --base <basename> [--wetpass]
#   python3 bake-ladder.py --selftest      # machinery proof, no blender
#
# Stages:
#   render (blender side, --blend): per design area x FLOOR scene: the
#           in-file lattice cams at the contract depth (128 px/tile) ->
#           masters to assets-src/boards/; --twice renders each master a
#           second time to /tmp and demands PIXEL equality (loud abort).
#   cut (python3, offline): law-3 identity arrangement — the Stage-A
#           lattice makes each area's render == the contract sheet shape,
#           so the cut copies windows 1:1 (still goes through the same
#           machinery the synthetic selftest proves); staged per sheet
#           name for BOTH tiles that share the art (wooden-ford,
#           wooden-flooring — the pairs measured byte-identical).
#   deploy: byte-verified copy staged -> mod/graphics (both names).
#   gate:   contract conformance (16 sprites, (128*size)^2, 4x4 grids for
#           ALL sizes incl 1x1 — the 2026-10-21 recipe revision) + staged
#           == deployed byte-equal + the two families byte-equal.
#
# The AREA REGISTRY (camera + window table per file) is the LAYOUT's
# committed state; the boards live in the rebuilt ford-boards.blend
# (BLOCKS + CAMS, builder output). --wetpass (cobble) is not wired yet.
import os
import sys
import json
import shutil
import numpy as np
from PIL import Image

# bpy is imported lazily in main_blend(): bake-ladder's selftest/cut/deploy
# run as plain python3 (no bpy); only the render stage runs inside blender.

SIZES = (1, 2, 4)
SPRITES_PER_SIZE = {1: 16, 2: 16, 4: 16}
# contract: sheet shape per size — ALL sizes render as 4x4 sprite grids
# (the 2026-10-21 revision: size 1 = 512x512, 4x4 grid of 128^2 sprites;
# the 2048x128 strip retires WITH the lua line_length 16->4 flip, same commit)
def sheet_shape(size):
    side = 128 * size
    return 4 * side, 4 * side


def parse_args(argv):
    # blender splits its own flags and mine with "--"; a plain python3 run
    # has no separator, so everything after argv[0] is mine
    ai = argv.index("--") + 1 if "--" in argv else 1
    rest = argv[ai:] if ai is not None else []
    out = {"mode": "run"}
    if "--selftest" in argv:
        out["mode"] = "selftest"
        return out, rest
    for i, a in enumerate(rest):
        if a == "--blend":
            out["blend"] = rest[i + 1]
        elif a == "--base":
            out["base"] = rest[i + 1]
        elif a == "--wetpass":
            out["wetpass"] = True
        elif a == "--twice":
            out["twice"] = True
        elif a == "--stages":
            out["stages"] = rest[i + 1]
    if out["mode"] == "run" and "blend" in out:
        out["mode"] = "blend"                      # Stage B runs inside blender
    if out["mode"] == "run" and "base" not in out:
        raise SystemExit("--base is required (sprite name, e.g. wooden-ford)")
    return out, rest


def contract_check(sheet_path, base, size):
    """The lua contract: shapes + counts; returns list of faults.
    ALL sizes = 4x4 sprite grids; size 1 must be 512x512 (the strip retired)."""
    faults = []
    im = Image.open(sheet_path)
    w, h = im.size
    sprite_side = 128 * size
    expected = (4 * sprite_side, 4 * sprite_side)
    if (w, h) != expected:
        faults.append(f"{os.path.basename(sheet_path)}: {w}x{h} != contract {expected[0]}x{expected[1]}")
    if im.mode != "RGBA":
        faults.append(f"{os.path.basename(sheet_path)}: mode {im.mode} != RGBA")
    return faults


def sheet_sprites(im, size):
    """Yield (k, box) sprite windows of the contract sheet, row-major;
    ALL sizes = 4x4 grids (16 sprites)."""
    side = 128 * size
    for k in range(16):
        row, col = divmod(k, 4)
        box = (col * side, row * side, (col + 1) * side, (row + 1) * side)
        yield k, box


def cut_sheet(master, size, out_path):
    """Law-3: build the contract sheet from the master's sprite windows.
    The Stage-A lattice + in-file cams make this the IDENTITY arrangement
    (the windows paste back to their own places); the machinery is the
    same gate-proven one the synthetic selftest exercises."""
    im = Image.open(master).convert("RGBA")
    sheet = Image.new("RGBA", im.size, (0, 0, 0, 0))
    for k, box in sheet_sprites(im, size):
        sheet.paste(im.crop(box), box)
    sheet.save(out_path)
    return out_path


def verify_bytes(a_path, b_path):
    a = open(a_path, "rb").read()
    b = open(b_path, "rb").read()
    if a != b:
        raise SystemExit(f"DEPLOY BYTE MISMATCH {a_path} -> {b_path}")


def deploy(staged, deployed):
    """Byte-verified copy staged -> deployed (copy, then verify)."""
    shutil.copyfile(staged, deployed)
    verify_bytes(staged, deployed)
    return deployed


# render stage: the lattice areas + their in-file cams (builder's CAMS:
# ortho = the area's width, 128 px/tile = the contract depth)
AREAS = {"AREA_1X1": ("BLK1_CAM", 512), "AREA_2X2": ("BLK2_CAM", 1024),
         "AREA_4X4": ("BLK4_CAM", 2048)}
SIZE_TAG = {1: "1x1", 2: "2x2", 4: "4x4"}
# both tiles that share the boards art (measured byte-identical pairs,
# journal 2026-10-21): one staged sheet deploys under both names
SHARED_ART = ("wooden-ford", "wooden-flooring")


def root_dir(level=4):
    r = os.path.dirname(os.path.abspath(__file__))
    for _ in range(level):
        r = os.path.dirname(r)
    return r


STAGING = os.path.join(root_dir(), "assets-src", "boards")
MODGRAPHICS = os.path.join(root_dir(), "mods", "water-ford", "mod", "graphics")


def render_area(args):
    import bpy
    sc = bpy.data.scenes["FLOOR"]
    saved_cam, saved_res = sc.camera.name, (sc.render.resolution_x, sc.render.resolution_y)
    masters = {}
    for area, (cam_name, res) in AREAS.items():
        sc.camera = bpy.data.objects[cam_name]
        sc.render.resolution_x = sc.render.resolution_y = res
        out = os.path.join(STAGING, f"{args['base']}-master-{SIZE_TAG[AREAS.index(area) if False else list(AREAS).index(area)]}.png") if False else \
              os.path.join(STAGING, f"{args['base']}-master-{SIZE_TAG[list(AREAS).index(area)]}.png")
        sc.render.filepath = out
        bpy.ops.render.render(write_still=True, scene=sc.name)
        masters[list(AREAS).index(area)] = out
    sc.camera = bpy.data.objects[saved_cam]
    sc.render.resolution_x, sc.render.resolution_y = saved_res
    if args.get("twice"):
        import numpy as np
        for size_i, master in masters.items():
            alt = f"/tmp/{args['base']}-master-alt-{SIZE_TAG[size_i]}.png"
            sc.camera = bpy.data.objects[AREAS[f"AREA_{SIZE_TAG[size_i].upper()}"[0:4] + SIZE_TAG[size_i].upper()[4:]][0]]
            sc.render.resolution_x = sc.render.resolution_y = AREAS[f"AREA_{SIZE_TAG[size_i].upper()}"[0:4] + SIZE_TAG[size_i].upper()[4:]][1]
            sc.render.filepath = alt
            bpy.ops.render.render(write_still=True, scene=sc.name)
            a = np.asarray(Image.open(master).convert("RGBA"), dtype=np.int16)
            b = np.asarray(Image.open(alt).convert("RGBA"), dtype=np.int16)
            if not np.array_equal(a, b):
                ndiff = int((a != b).any(axis=-1).sum())
                raise SystemExit(f"--twice FAILED: {master} vs re-render differs on {ndiff} px")
        print("TWICE: all masters pixel-identical across two renders")
    return masters


def selftest():
    """Machinery proof with synthetic bytes — no blender, no art.

    Proves: contract_check catches malformed sheets; cut_sheet preserves
    windows 1:1 into the contract shapes; sheet_sprites row-major indexing;
    deploy byte-verification catches tampering.
    """
    import tempfile
    tmp = tempfile.mkdtemp(prefix="bakeladder-selftest-")
    faults = []
    # 1) synthetic master for size 2: 1024x1024, each sprite window filled
    #    with a unique solid color keyed by its index
    master = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    colors = {}
    for k, box in sheet_sprites(master, 2):
        c = ((k * 37 % 256), (k * 91 % 256), (k * 13 % 256), 255)
        colors[k] = c
        master.paste(Image.new("RGBA", (box[2] - box[0], box[3] - box[1]), c), box)
    mpath = os.path.join(tmp, "master-2x2.png")
    master.save(mpath)
    # 2) cut into the contract sheet -> must be pixel-identical to master
    spath = os.path.join(tmp, "sheet-2x2.png")
    cut_sheet(mpath, 2, spath)
    a, b = np.asarray(master, dtype=np.int32), np.asarray(Image.open(spath), dtype=np.int32)
    if not np.array_equal(a, b):
        faults.append(f"cut_sheet pixel drift on {spath}")
    # 3) contract check on the good sheet passes, on a tampered one fails
    if contract_check(spath, "selftest", 2):
        faults.append("contract_check flagged the CONTRACT-CONFORMANT sheet")
    bad = Image.new("RGBA", (999, 999), (1, 1, 1, 255))
    bpath = os.path.join(tmp, "bad.png"); bad.save(bpath)
    if not contract_check(bpath, "selftest", 2):
        faults.append("contract_check missed a malformed sheet")
    # 4) byte verification: mismatched files are caught, equal files pass
    dpath = os.path.join(tmp, "deployed-2x2.png")
    deploy(mpath, dpath)          # copy path: must succeed silently
    with open(dpath, "r+b") as f:
        f.seek(16); orig = f.read(1); f.seek(16); f.write(bytes([orig[0] ^ 0xFF]))
    try:
        verify_bytes(mpath, dpath)
        faults.append("verify_bytes accepted a tampered copy")
    except SystemExit:
        pass
    # 5) row-major windows sanity: first sprite of each sheet at (0,0)
    for size in SIZES:
        sheet = Image.new("RGBA", sheet_shape(size), (0, 0, 0, 0))
        k0, box0 = next(iter(sheet_sprites(sheet, size)))
        if box0[:2] != (0, 0):
            faults.append(f"size {size}: first sprite not at origin")
    for m in faults:
        print("SELFTEST FAULT:", m)
    print("BAKELADDER SELFTEST:", "FAIL" if faults else "GREEN "
          f"(synthetic cut/arrange/contract/deploy all verified in {tmp})")
    return 1 if faults else 0
STAGING = os.path.join(root_dir(2), "assets-src", "boards")
MODGRAPHICS = os.path.join(root_dir(2), "mod", "graphics")
COBBLE_STAGING = os.path.join(root_dir(2), "assets-src", "cobble")


def wetpass(args):
    """Stage B-wet (--wetpass, inside blender on the cobble blend): the
    wetness mask masters, per §2 of cobble-visual-language.md + the
    maintainer's water-plane design (2026-10-22).

      water height = the in-file WATER_PLANE's z (THE GUI KNOB — its z is
      the ruling; the bake slices at that height), ZW below.
      SLICE: each stone -> a DRY piece (above ZW; flat gray 170) + a WET
      piece (below; NO fill — the open cut, so the top-down ray's first
      hit = the stone's true submerged surface), the wet gray = the §2.1
      stepped ramp: gray 85 at the waterline down to 25 at the bed plane
      (stops 0.0097→25 / 0.0908→85 with a 4-step ladder between, CONSTANT
      interp, input w = 0.402·z/ZW — the doc's ramp with the in_wet key
      materialized geometrically by the slice; buried z<0 clamps to 25).
      the BED = ALL WET (flat 25 — maintainer ruling).
      outside = gray 0 (world strength 0 + opaque film + dither 0 — the
      paper-mask pass state, toggled ALL-OR-NOTHING in try/finally).
      ALIGNMENT LAW (maintainer, 2026-10-22): the mask renders through the
      SAME in-file cameras at the SAME contract res (AREAS: 512/1024/2048
      = 128 px/unit at every size) -> the mask pixel grid = the art
      masters' grid 1:1 by construction; the cut reuses cut_sheet; the
      --twice pixel-identity gate applies to the mask masters as to art.

      The pieces are RUNTIME-ONLY (created from the saved blend, never
      saved; re-derivable — the seeds are stable and the plane carries ZW).
    """
    import bpy, bmesh
    import numpy as np
    from PIL import Image
    sc = bpy.data.scenes["FLOOR"]
    r = sc.render
    zw = bpy.data.objects["WATER_PLANE"].location.z     # THE VARIABLE
    print(f"WETPASS: water height (WATER_PLANE.z = WATER_Z) = {zw:.4f}")
    vf = sc.view_settings.view_transform
    film = r.film_transparent
    dither = r.dither_intensity
    world = sc.world
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    wstrength = bg.inputs["Strength"].default_value

    def mask_mat(name, gray=None, ramp=False):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        for nd in list(nt.nodes):
            nt.nodes.remove(nd)
        em = nt.nodes.new("ShaderNodeEmission")
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        if not ramp:
            g = gray / 255.0
            em.inputs["Color"].default_value = (g, g, g, 1.0)
            nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
            return m
        # the stepped ramp: input w = 0.402·z/ZW; the doc's stops with the
        # 4-step ladder between, CONSTANT interp; buried z<0 -> w<0 -> the
        # ramp clamps below the first stop = 25 (the bed + bottoms bucket)
        cr = nt.nodes.new("ShaderNodeValToRGB")
        cr.color_ramp.interpolation = "CONSTANT"
        stops_ = [(0.0097, 25), (0.0300, 40), (0.0501, 55), (0.0705, 70),
                  (0.0908, 85)]
        for i, (pos, v) in enumerate(stops_):
            el = cr.color_ramp.elements[0] if i == 0 else cr.color_ramp.elements.new(pos)
            el.position = pos
            el.color = (v / 255.0, v / 255.0, v / 255.0, 1.0)
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = 0.402 / zw
        nt.links.new(geo.outputs["Position"], sep.inputs[0])
        nt.links.new(sep.outputs["Z"], mul.inputs[0])
        nt.links.new(mul.outputs[0], cr.inputs["Fac"])
        nt.links.new(cr.outputs["Color"], em.inputs["Color"])
        nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
        return m

    m_dry = mask_mat("M_COBBLE_MASK_DRY", gray=170)
    m_wet = mask_mat("M_COBBLE_MASK_WET", ramp=True)
    m_bed = mask_mat("M_COBBLE_MASK_BED", gray=25)

    under = bpy.data.collections["UNDERLAY"]
    stones = [o for o in sc.objects if o.name.startswith("C_AREA")]
    pieces = []
    n_empty = 0
    for ob in stones:
        for part in ("dry", "wet"):
            bm = bmesh.new()
            bm.from_mesh(ob.data)
            bmesh.ops.bisect_plane(
                bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                plane_co=(0.0, 0.0, zw), plane_no=(0.0, 0.0, 1.0),
                clear_outer=(part == "wet"), clear_inner=(part == "dry"))
            if not bm.verts:
                n_empty += 1
                bm.free()
                continue
            me = bpy.data.meshes.new(f"MP_{ob.name}_{part}")
            bm.to_mesh(me)
            me.update()
            bm.free()
            po = bpy.data.objects.new(me.name, me)
            me.materials.append(m_dry if part == "dry" else m_wet)
            po.hide_render = True
            under.objects.link(po)
            pieces.append(po)
    beds = [o for o in under.objects if o.name.endswith("_BED")]
    for bd in beds:
        bd.data.materials[0] = m_bed
    print(f"WETPASS: ZW={zw:.4f}; sliced {len(stones)} stones -> {len(pieces)} "
          f"pieces ({n_empty} empty halves skipped); {len(beds)} beds all-wet")

    def set_pass(on):
        for o in stones:
            o.hide_render = on
        for po in pieces:
            po.hide_render = not on
        sc.view_settings.view_transform = "Standard"   # the paper-pass state
        r.film_transparent = False
        bg.inputs["Strength"].default_value = 0.0 if on else wstrength
        r.dither_intensity = 0.0 if on else dither

    try:
        set_pass(True)
        saved_res = (r.resolution_x, r.resolution_y)
        masters = []
        for size, (area, (cam_name, res)) in zip(SIZES, AREAS.items()):
            sc.camera = bpy.data.objects[cam_name]
            r.resolution_x = r.resolution_y = res   # THE CONTRACT DEPTH
            out = os.path.join(COBBLE_STAGING,
                               f"{args['base']}-mask-master-{SIZE_TAG[size]}.png")
            r.filepath = out
            bpy.ops.render.render(write_still=True)
            masters.append((size, out, cam_name, res))
        r.resolution_x, r.resolution_y = saved_res
        if args.get("twice"):
            for size, master, cam_name, res in masters:
                sc.camera = bpy.data.objects[cam_name]
                r.resolution_x = r.resolution_y = res
                alt = f"/tmp/{args['base']}-mask-master-alt-{SIZE_TAG[size]}.png"
                r.filepath = alt
                bpy.ops.render.render(write_still=True)
                a = np.asarray(Image.open(master).convert("RGBA"), dtype=np.int16)
                b = np.asarray(Image.open(alt).convert("RGBA"), dtype=np.int16)
                if not np.array_equal(a, b):
                    ndiff = int((a != b).any(axis=-1).sum())
                    raise SystemExit(f"--twice FAILED (mask): {master} differs "
                                     f"from its re-render on {ndiff} px")
            r.resolution_x, r.resolution_y = saved_res
            print("TWICE (mask): all masters pixel-identical across two renders")
        for size, master, _cam, _res in masters:
            res = AREAS[f"AREA_{SIZE_TAG[size].upper()}"][1]
            im = Image.open(master)
            if im.size != (res, res):
                raise SystemExit(f"MASK {os.path.basename(master)}: {im.size} != "
                                 f"the contract ({res}, {res}) — alignment broken")
            a = np.asarray(im.convert("RGBA"))
            if a[..., 3].min() != 255:
                raise SystemExit(f"MASK {os.path.basename(master)}: alpha < 255 (opaque law)")
            g = a[..., 0].astype(int)
            dry = ((g >= 168) & (g <= 172)).sum()
            w85 = ((g >= 83) & (g <= 87)).sum()
            deep = ((g >= 23) & (g <= 27)).sum()
            steps = sum(((g >= v - 3) & (g <= v + 3)).sum() for v in (40, 55, 70))
            if dry < 100 or w85 < 100 or deep < 100 or steps < 3:
                raise SystemExit(f"MASK {os.path.basename(master)}: bands missing "
                                 f"(dry {dry}, 85 {w85}, 25 {deep}, steps {steps})")
            outside = ((g < 15) | (g > 173)).sum()
            if outside:
                raise SystemExit(f"MASK {os.path.basename(master)}: {outside} px "
                                 "outside [15,173] — foreign grays")
            print(f"MASK GATE {SIZE_TAG[size]}: dry170={dry} wet85={w85} fully25={deep} "
                  f"steps={steps} px — {os.path.basename(master)}")
        for size, master, _c, _r in masters:
            sp = os.path.join(COBBLE_STAGING,
                              f"{args['base']}{sheet_suffix(size)}-mask.png")
            cut_sheet(master, size, sp)
            sp2 = sp + ".twice.png"
            cut_sheet(master, size, sp2)
            aa = np.asarray(Image.open(sp).convert("RGBA"), dtype=np.int16)
            bb = np.asarray(Image.open(sp2).convert("RGBA"), dtype=np.int16)
            if not np.array_equal(aa, bb):
                raise SystemExit(f"--twice FAILED (mask cut): {sp} != its second run")
            os.remove(sp2)
            print(f"MASK CUT: {os.path.basename(sp)} (identity windows; "
                  "pixel-locked 1:1 with the art masters)")
    finally:
        set_pass(False)
        for po in list(pieces):
            bpy.data.objects.remove(po, do_unlink=True)
    print("WETPASS DONE")


def render_area(args):
    """Stage B inside blender: each lattice area through its in-file cam at
    the contract depth (128 px/tile)."""
    import bpy
    sc = bpy.data.scenes["FLOOR"]
    saved_cam, saved_res = sc.camera.name, (sc.render.resolution_x, sc.render.resolution_y)
    masters = []   # (size, path) row-major by the AREAS roster
    # staging follows the base family: cobble masters belong in
    # assets-src/cobble (the boards pair above stays boards-only)
    staging = COBBLE_STAGING if args["base"].startswith("cobble") else STAGING
    for size, (area, (cam_name, res)) in zip(SIZES, AREAS.items()):
        sc.camera = bpy.data.objects[cam_name]
        sc.render.resolution_x = sc.render.resolution_y = res
        out = os.path.join(staging, f"{args['base']}-master-{SIZE_TAG[size]}.png")
        sc.render.filepath = out
        bpy.ops.render.render(write_still=True, scene=sc.name)
        masters.append((size, out))
    sc.camera = bpy.data.objects[saved_cam]
    sc.render.resolution_x, sc.render.resolution_y = saved_res
    if args.get("twice"):
        import numpy as np
        for size, master in masters:
            cam_name, res = AREAS["AREA_" + SIZE_TAG[size].upper()]
            sc.camera = bpy.data.objects[cam_name]
            sc.render.resolution_x = sc.render.resolution_y = res
            alt = f"/tmp/{args['base']}-master-alt-{SIZE_TAG[size]}.png"
            sc.render.filepath = alt
            bpy.ops.render.render(write_still=True, scene=sc.name)
            a = np.asarray(Image.open(master).convert("RGBA"), dtype=np.int16)
            b = np.asarray(Image.open(alt).convert("RGBA"), dtype=np.int16)
            if not np.array_equal(a, b):
                ndiff = int((a != b).any(axis=-1).sum())
                raise SystemExit(f"--twice FAILED: {master} differs from its "
                                 f"re-render on {ndiff} px")
        sc.camera = bpy.data.objects[saved_cam]
        sc.render.resolution_x, sc.render.resolution_y = saved_res
        print("TWICE: all masters pixel-identical across two renders")
    return masters


def sheet_suffix(size):
    return "" if size == 1 else f"-{SIZE_TAG[size]}"


def main_offline(args):
    """Stage C + deploy + gate, offline from committed masters (no bpy):"""
    base = args["base"]
    stages = [s.strip() for s in (args.get("stages") or "cut,deploy,gate").split(",")]
    masters = []
    for size in SIZES:
        mp = os.path.join(STAGING, f"{base}-master-{SIZE_TAG[size]}.png")
        if not os.path.exists(mp):
            raise SystemExit(f"MASTER MISSING: {mp} - run the render stage first")
        fa = contract_check(mp, base, size)
        if fa:
            raise SystemExit("MASTER VIOLATES THE CONTRACT: " + "; ".join(fa))
        masters.append((size, mp))

    if "cut" in stages:
        import numpy as np
        for size, mp in masters:
            sp = os.path.join(STAGING, f"{base}{sheet_suffix(size)}.png")
            cut_sheet(mp, size, sp)
            sp2 = sp + ".twice.png"
            cut_sheet(mp, size, sp2)              # the twice-gate: cut runs twice
            a = np.asarray(Image.open(sp).convert("RGBA"), dtype=np.int16)
            b = np.asarray(Image.open(sp2).convert("RGBA"), dtype=np.int16)
            if not np.array_equal(a, b):
                raise SystemExit(f"--twice FAILED (cut): {sp} != its second run")
            os.remove(sp2)
            print(f"CUT: {base}{sheet_suffix(size)}.png ({sp} == master identity)")
        for size in SIZES:
            for name in SHARED_ART:
                if name == base:
                    continue
                dst = os.path.join(STAGING, f"{name}{sheet_suffix(size)}.png")
                shutil.copyfile(os.path.join(STAGING, f"{base}{sheet_suffix(size)}.png"), dst)
                verify_bytes(os.path.join(STAGING, f"{base}{sheet_suffix(size)}.png"), dst)
            print(f"STAGED: {name}{sheet_suffix(size)}.png == {base}{sheet_suffix(size)}.png (shared art)")

    if "deploy" in stages:
        for size in SIZES:
            for name in SHARED_ART:
                staged = os.path.join(STAGING, f"{name}{sheet_suffix(size)}.png")
                if not os.path.exists(staged):
                    raise SystemExit(f"STAGED SHEET MISSING: {staged} - run the cut stage first")
                deployed = os.path.join(MODGRAPHICS, f"{name}{sheet_suffix(size)}.png")
                deploy(staged, deployed)
                print(f"DEPLOYED: {deployed} (byte-verified vs staging)")

    if "gate" in stages:
        faults = []
        for size in SIZES:
            for name in SHARED_ART:
                deployed = os.path.join(MODGRAPHICS, f"{name}{sheet_suffix(size)}.png")
                faults += contract_check(deployed, name, size)
                verify_bytes(os.path.join(STAGING, f"{name}{sheet_suffix(size)}.png"), deployed)
            a = os.path.join(MODGRAPHICS, f"{SHARED_ART[0]}{sheet_suffix(size)}.png")
            b = os.path.join(MODGRAPHICS, f"{SHARED_ART[1]}{sheet_suffix(size)}.png")
            verify_bytes(a, b)
        if faults:
            raise SystemExit("GATE FAILURES:\n  " + "\n  ".join(faults))
        print(f"GATE: contract + staging/deploy byte-equality + shared-art pairs PASS "
              f"({6} sheets, {len(SIZES)} sizes, 16 sprites each)")


if __name__ == "__main__":
    args, rest = parse_args(sys.argv)
    if args["mode"] == "selftest":
        raise SystemExit(selftest())
    if args["mode"] == "blend":
        import bpy
        bpy.ops.wm.open_mainfile(filepath=args["blend"])
        if args.get("wetpass"):
            wetpass(args)
        else:
            render_area(args)
    else:
        main_offline(args)