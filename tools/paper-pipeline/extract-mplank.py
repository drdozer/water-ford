# extract-mplank.py — pin M_PLANK (the grain shader) + M_BOLT/GAP_TONE +
# the scene's plank_pool as a committed spec, for the boards builder.
# One-off extraction of the APPROVED look; the builder rebuilds from this
# spec verbatim (nodes-as-data). Run: blender -b ford-boards.blend --python extract-mplank.py
import bpy, os, json, sys
bpy.ops.wm.open_mainfile(filepath=os.environ.get("BLEND", "ford-boards.blend"))

spec = {}

def ramp_spec(r):
    stops = []
    for e in r.color_ramp.elements:
        stops.append([round(e.position, 5), [round(c, 5) for c in e.color]])
    return {"interpolation": r.color_ramp.interpolation, "stops": stops}

for matname in ("M_PLANK", "BOLT_METAL", "GAP_TONE"):
    m = bpy.data.materials[matname]
    nodes = []
    links = []
    for n in m.node_tree.nodes:
        d = {"name": n.name, "type": n.type, "location": [round(v, 1) for v in n.location], "inputs": {}, "props": {}}
        for k, v in (("operation", getattr(n, "operation", None)), ("blend_type", getattr(n, "blend_type", None)),
                     ("attribute_name", getattr(n, "attribute_name", None) if n.type == "ATTRIBUTE" else None),
                     ("interpolation_type", getattr(n, "interpolation_type", None) if n.type == "MAP_RANGE" else None)):
            if v is not None:
                d["props"][k] = str(v)
        if n.type == "VALTORGB":
            d["props"]["ramp"] = ramp_spec(n)
        if n.type == "TEX_NOISE":
            for inp in ("Scale", "Detail", "Roughness", "Distortion"):
                d["inputs"][inp] = round(n.inputs[inp].default_value, 4)
        for inp in n.inputs:
            if inp.is_linked: continue
            try:
                v = inp.default_value
            except Exception:
                continue
            key = inp.identifier
            d["inputs"][key] = (round(v, 5) if isinstance(v, float) else
                                [round(c, 5) for c in v] if hasattr(v, "__len__") else v)
        nodes.append(d)
    for lk in m.node_tree.links:
        links.append([lk.from_node.name, lk.from_socket.identifier, lk.to_node.name, lk.to_socket.identifier])
    spec[matname] = {"nodes": nodes, "links": links}

sc = bpy.data.scenes["FLOOR"]
if "plank_pool" in sc:
    pool = list(sc["plank_pool"])
    spec["plank_pool"] = [[float(c) for c in p] for p in pool] if pool and hasattr(pool[0], "__len__") else [float(p) for p in pool]
# --- bolt TEMPLATE: the true 2D round head, extracted verbatim from the
# old deck's geometry (13 polys / 60 verts / ~10.2px diameter / 1.3px tall).
# (2026-10-21: the old deck's bolt geometry was destroyed by the first
# factory-empty rebuild; this re-extracts it from git HEAD's file.)
def bolt_template():
    me = bpy.data.objects["LAT_BOARDS"].data
    from collections import defaultdict
    adj = defaultdict(set)
    for pi, p in enumerate(me.polygons):
        if p.material_index == 1:
            for v in p.vertices:
                adj[v].add(pi)
    seen_poly, seen_vert = set(), set()
    groups = []
    for seed in list(adj):
        if seed in seen_vert: continue
        stack = [seed]; grp_vs = set(); grp_ps = set()
        while stack:
            v = stack.pop()
            if v in seen_vert: continue
            seen_vert.add(v); grp_vs.add(v)
            for pj in adj[v]:
                grp_ps.add(pj)
                if pj not in seen_poly:
                    seen_poly.add(pj)
                    for vv in me.polygons[pj].vertices:
                        if vv not in seen_vert:
                            stack.append(vv)
        groups.append((grp_vs, grp_ps))
    # take one dome: verts relative to its bbox center, faces re-indexed
    grp_vs, grp_ps = groups[0]
    co = {v: tuple(me.vertices[v].co) for v in grp_vs}
    cx = sum(c[0] for c in co.values()) / len(co)
    cy = sum(c[1] for c in co.values()) / len(co)
    cz = min(c[2] for c in co.values())
    vmap = {}
    verts = []
    for v in sorted(grp_vs):
        vmap[v] = len(verts)
        x, y, z = co[v]
        verts.append([round(x - cx, 5), round(y - cy, 5), round(z - cz, 5)])
    faces = []
    for pj in sorted(grp_ps):
        faces.append([vmap[v] for v in me.polygons[pj].vertices])
    return {"verts": verts, "faces": faces}

spec["bolt_template"] = bolt_template()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "boards-mplank-spec.json")
with open(out, "w") as f:
    json.dump(spec, f, indent=1)
print("MPLANK SPEC:", out, "| nodes:", {k: len(spec[k]["nodes"]) for k in spec if isinstance(spec[k], dict) and "nodes" in spec[k]}, "| pool:", "plank_pool" in spec)
