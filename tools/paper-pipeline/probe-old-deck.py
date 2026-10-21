# probe-old-deck.py — headless enumerator + geometry prober for the OLD
# boards deck (the pre-lattice ford-boards.blend), for the per-tile-shade
# mechanism hunt + the double-height-plank measurement (journal 2026-10-21
# PARKED items 1a/1b). One probe, reusable: nothing here mutates the file.
#
# Recipe (the old deck is recoverable from git history — never stored in
# the worktree):
#   git -C <repo> show 248d8f3:blender/ford-boards.blend > /tmp/ford-boards-old.blend
#   blender -b /tmp/ford-boards-old.blend --python probe-old-deck.py \
#     -- enumerate | measure-planks [--block AREA_2X2]
#
# enumerate: objects (name/type/collection), mesh stats, modifiers,
#   custom props, drivers, scenes' custom props, text blocks — everything
#   needed to identify a mechanism WITHOUT interpreting any image.
# measure-planks: groups plank faces by (seed, origin) identity and
#   histograms the number of COURSES each plank spans (rows of faces),
#   reporting the double-height ratio; region-restrictable.
#
# GROUND RULES (export-recipe.md): numeric/geometric facts only — no
# visual interpretation of renders lives in this file.
import bpy, os, sys, json, math
from collections import defaultdict
from math import floor

bpy.ops.wm.open_mainfile(filepath=os.environ.get("BLEND", "/tmp/ford-boards-old.blend"))

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
mode = argv[0] if argv else "enumerate"
args = argv[1:]

# ------------------------------------------------------------- enumerate
def dump_drivers(obj):
    lines = []
    if obj.animation_data:
        for dr in obj.animation_data.drivers:
            lines.append(f"    driver {dr.driver.expression} on {dr.data_path}")
    return lines

def dump():
    # collections
    print("== collections ==")
    for c in bpy.data.collections:
        print(f"  {c.name}: {len(c.objects)} objects, children={[ch.name for ch in c.children]}")
    # scenes + their custom props
    for sc in bpy.data.scenes:
        props = {k: sc[k] for k in sc.keys() if not k.startswith("_")}
        print(f"== scene {sc.name} props ==")
        for k, v in props.items():
            print(f"  {k} = {str(v)[-400:] if k == 'atlas_note' else str(v)[:1500]}")
        r = sc.render
        print(f"  render: {r.resolution_x}x{r.resolution_y} engine={r.engine} "
              f"camera={sc.camera.name if sc.camera else None}")
        print(f"  view_transform={sc.view_settings.view_transform} "
              f"world={sc.world.name if sc.world else None}")
    # objects
    print("== objects ==")
    for ob in bpy.data.objects:
        coll = [c.name for c in bpy.data.collections if ob.name in c.objects]
        extra = ""
        if ob.type == "MESH":
            me = ob.data
            attrs = {a.name: (a.data_type, tuple(d.domain for d in ())) for a in me.attributes}
            attrs = ", ".join(f"{a.name}:{a.data_type}" for a in me.attributes)
            extra = (f" verts={len(me.vertices)} faces={len(me.polygons)} "
                     f"mats={[m.name if m else None for m in ob.data.materials]} "
                     f"mods={[m.name + ':' + m.type for m in ob.modifiers]} "
                     f"attrs=[{attrs}]")
        if ob.type == "CAMERA":
            extra = (f" ortho={ob.data.ortho_scale} type={ob.data.type} "
                     f"loc={[round(v,2) for v in ob.location]}")
        if ob.type == "LIGHT":
            extra = (f" energy={ob.data.energy} type={ob.data.type} "
                     f"loc={[round(v,2) for v in ob.location]} "
                     f"shadow_soft_size={ob.data.shadow_soft_size}")
        print(f"  {ob.name} type={ob.type} loc={[round(v,3) for v in ob.location]} "
              f"scale={[round(v,3) for v in ob.scale]} colls={coll}{extra}")
        oprops = {k: ob[k] for k in ob.keys() if not k.startswith("_")}
        for k, v in oprops.items():
            print(f"    prop {k} = {str(v)[:600]}")
        for ln in dump_drivers(ob):
            print(ln)
    # text blocks (scripts kept in the file)
    print("== text blocks ==")
    for t in bpy.data.texts:
        print(f"  text {t.name} ({len(t.as_string())} chars)")
        print(t.as_string()[:8000])
        print("  ---")

# ---------------------------------------------------------- measure-planks
def measure_planks():
    """Group faces into planks and count COURSES each spans.

    A plank = maximal connected run of faces sharing (plank_seed,
    plank_origin) identity attrs. Course span = #distinct plank_course
    values in the group (1 = normal, 2 = double-height, measured against
    the world-space y extent too — the attrs' definition is decoded from
    the file, not assumed)."""
    objname = "LAT_BOARDS"
    region = None
    it = iter(args)
    for a_ in it:
        if a_ == "--obj":
            objname = next(it)
        if a_ == "--region":
            region = [float(v) for v in next(it).split(",")]
    me = bpy.data.objects[objname].data
    print(f"== {objname} attributes ==")
    for a in me.attributes:
        print(f"  {a.name} {a.data_type} domain={a.domain}")
    attrs = {a.name: a for a in me.attributes}
    need = ("plank_seed", "plank_origin", "plank_course", "plank_len", "plank_cx", "plank_cy", "plank_ringfreq")
    have = {n: attrs[n] for n in need if n in attrs}
    missing = [n for n in need if n not in attrs]
    if missing:
        print("MISSING attrs:", missing)
        return
    fidx = list(range(len(me.polygons)))
    if region is not None:
        x0, x1, y0, y1 = region
        keep = []
        for i in fidx:
            polys_c = [me.vertices[v].co for v in me.polygons[i].vertices]
            if all(x0 <= c.x <= x1 and y0 <= c.y <= y1 for c in polys_c):
                keep.append(i)
        fidx = keep
    def fvals(a, idxs):
        return [a.data[i].value for i in idxs]
    # world positions of face centers
    mw = [me.vertices[me.polygons[i].vertices[0]].co
          for i in fidx]
    # group by (seed, origin) — connected grouping (flood over shared verts)
    adj = defaultdict(list)
    for pi, p in enumerate(me.polygons):
        for v in p.vertices:
            adj[v].append(pi)
    seed_a, origin_a = have["plank_seed"], have["plank_origin"]
    course_a, len_a = have["plank_course"], have["plank_len"]
    cx_a, cy_a, rf_a = have["plank_cx"], have["plank_cy"], have["plank_ringfreq"]
    # group planks by CONSTANT-PER-PLANK attr identity (the old deck emits
    # per-face attrs that are constant within a plank: seed/cx/cy/rf —
    # connectivity fails: strip verts are duplicated)
    idkey = {}
    groups = []
    keymap = defaultdict(list)
    for pi in range(len(me.polygons)):
        if me.polygons[pi].material_index != 0:  # planks only
            continue
        k = (round(seed_a.data[pi].value, 4), round(cx_a.data[pi].value, 3),
             round(cy_a.data[pi].value, 3), round(rf_a.data[pi].value, 3))
        keymap[k].append(pi)
    groups = keymap.values()
    print(f"== {objname} plank groups (by seed+cx+cy+rf): {len(groups)} ==")
    rgb_a = attrs["plank_rgb"]
    # per-island facts: bbox, y-width, distinct courses, cast constancy
    islands = []
    for g in groups:
        xs = [me.vertices[v].co.x for i in g for v in me.polygons[i].vertices]
        ys = [me.vertices[v].co.y for i in g for v in me.polygons[i].vertices]
        cs = sorted({round(course_a.data[i].value, 5) for i in g})
        rgb0 = rgb_a.data[g[0]].color
        rgb_var = max(max(abs(rgb_a.data[i].color[q] - rgb0[q]) for q in range(3)) for i in g)
        islands.append({
            "n": len(g), "x": (round(min(xs),3), round(max(xs),3)),
            "y": (round(min(ys),3), round(max(ys),3)),
            "w": round(max(ys)-min(ys), 3), "l": round(max(xs)-min(xs), 3),
            "courses": cs, "seed": round(seed_a.data[g[0]].value, 4),
            "cy": round(cy_a.data[g[0]].value, 2), "rf": round(rf_a.data[g[0]].value, 2),
            "rgb": [round(c, 4) for c in rgb0], "rgb_var": round(rgb_var, 6),
            "l": round(0.299*rgb0[0] + 0.587*rgb0[1] + 0.114*rgb0[2], 3),
        })
    n_var = sum(1 for isl in islands if isl["rgb_var"] > 0.01)
    print(f"planks with varying cast within plank: {n_var} of {len(islands)}")
    luma = sorted(isl["l"] for isl in islands)
    import statistics
    print(f"cast luma: min={luma[0]} p25={luma[len(luma)//4]} med={luma[len(luma)//2]} "
          f"p75={luma[3*len(luma)//4]} max={luma[-1]} (linear, deck-wide)")
    # PER-1x1-TILE cast mean (the decisive per-tile-shade fact) + per-band means
    tile_mean = defaultdict(list)
    for isl in islands:
        t = (floor((isl["x"][0]+isl["x"][1])/2), floor((isl["y"][0]+isl["y"][1])/2))
        tile_mean[t].append(isl["l"])
    tile_means = {t: statistics.fmean(v) for t, v in tile_mean.items() if len(v) >= 3}
    if tile_means:
        vals = sorted(tile_means.values())
        import statistics
        sv = statistics.pstdev(vals) if len(vals) > 1 else 0.0
        print(f"per-tile cast-mean spread: min={vals[0]:.4f} p5={vals[len(vals)//20]:.4f} "
              f"med={vals[len(vals)//2]:.4f} p95={vals[19*len(vals)//20]:.4f} max={vals[-1]:.4f} "
              f"sigma={sv:.4f} ({len(vals)} tiles with >=3 planks)")
    # per-BAND mean too (a band = one course row of one site)
    band_mean = defaultdict(list)
    for isl in islands:
        b = round(isl["courses"][0], 1) if isl["courses"] else None
        band_mean[b].append(isl["l"])
    bvals = sorted(statistics.fmean(v) for v in band_mean.values() if len(v) >= 3)
    if bvals:
        svb = statistics.pstdev(bvals) if len(bvals) > 1 else 0.0
        print(f"per-band cast-mean spread: min={bvals[0]:.4f} med={bvals[len(bvals)//2]:.4f} "
              f"max={bvals[-1]:.4f} sigma={svb:.4f}")
    # width-class histogram + area share + course-span cross-check
    wcls = defaultdict(int)
    warea = defaultdict(int)
    span_hist = defaultdict(int)
    den = max(1, len(islands))
    for isl in islands:
        wcls[isl["w"]] += 1
        warea[isl["w"]] += isl["n"]  # faces ∝ strips; × width for area
        span_hist[len(isl["courses"])] += 1
    area_norm = {w: n*w for w, n in warea.items()}
    area_tot = sum(area_norm.values())
    print("== y-width histogram (plank count, count-share, area-share) ==")
    for w in sorted(wcls):
        print(f"  w {w}: {wcls[w]} planks ({100.0*wcls[w]/den:.1f}%), "
              f"area {100.0*area_norm[w]/area_tot:.1f}%")
    print("== distinct-course-span histogram ==")
    for s_ in sorted(span_hist):
        print(f"  span {s_}: {span_hist[s_]} ({100.0*span_hist[s_]/den:.1f}%)")
    # cluster islands into y-bands (sites live in wide bands)
    centers = [(round((isl["x"][0]+isl["x"][1])/2, 2), round((isl["y"][0]+isl["y"][1])/2, 2)) for isl in islands]
    ys_sorted = sorted(set(c[1] for c in centers))
    bands = []
    for yv in ys_sorted:
        if bands and abs(yv - bands[-1][-1]) < 0.5:
            bands[-1].append(yv)
        else:
            bands.append([yv])
    print("== island y-center bands ==")
    for b in bands:
        bw = [isl for isl in islands if abs((isl["y"][0]+isl["y"][1])/2 - sum(b)/len(b)) < 0.6]
        wcls_b = defaultdict(int)
        for isl in bw:
            wcls_b[isl["w"]] += 1
        print(f"  band y~{sum(b)/len(b):.2f}: islands={len(bw)} by_width={dict(sorted(wcls_b.items()))}")
    print("first islands (n, x, y, w, courses, seed, cy, rf):")
    for isl in islands[:10]:
        print("  ", (isl["n"], isl["x"], isl["y"], isl["w"], isl["courses"][:4],
                    isl["seed"], isl["cy"], isl["rf"]))

# ------------------------------------------------------------ dump-planks
def dump_planks():
    """JSON of every P_* plank object (name, verts, per-plank attrs, cast)
    from the BLEND env file — for bit-stability diffs between builds
    (e.g. the 1x1 block must survive pattern-path changes unchanged), and
    for the bolt-vanish isolate recipe (compare same-name objects across
    builds). No visual content."""
    import sys, os
    out_path = os.environ.get("DUMP_OUT", "/tmp/plank-dump.json")
    out = []
    for ob in sorted(bpy.data.objects, key=lambda o: o.name):
        if not ob.name.startswith(("P_", "BOLT", "AREA")):
            continue
        me = ob.data
        d = {"name": ob.name,
             "verts": [[round(c, 5) for c in v.co] for v in me.vertices],
             "faces": [list(p.vertices) for p in me.polygons],
             "mats": [m.name if m else None for m in ob.data.materials][:2]}
        for a in me.attributes:
            if a.name in ("plank_seed", "plank_origin", "plank_len", "plank_course",
                          "plank_cx", "plank_cy", "plank_ringfreq"):
                d["attrs"] = d.get("attrs", [])
                d["attrs"].append("%s=%.5f" % (a.name, a.data[0].value))
            elif a.name == "plank_rgb":
                d["cast"] = [round(x, 5) for x in a.data[0].color]
        out.append(d)
    with open(out_path, "w") as f:
        json.dump(out, f)
    print("PLANK DUMP:", out_path, len(out), "objects")


dump() if mode == "enumerate" else (dump_planks() if mode == "dump-planks" else measure_planks())