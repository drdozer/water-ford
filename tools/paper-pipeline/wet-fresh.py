# wet-fresh.py — mesh wetness keying (2026-10-21, fresh toolchain: DATA round)
#
# STANDALONE (no condemned-toolchain involvement). Owns the wetness DATA
# keying of the mesh, separate from mat-fresh.py (materials). Ruling
# maintainer 2026-10-21: the grounding bed (JOINTBED) is logically UNDER
# WATER; the cobbles rise up through the water, some breaching the surface
# (dry tops). The bed exposed between cobbles must be keyed JUST AS WET AS
# THE BOTTOMS OF COBBLES — the old mesh shipped the bed with NO wetness
# attributes, so the mask pass defaulted it to dry (gray 170).
#
# Convention (unchanged from the geometry build): in_wet 0/1; wet_depth
# 0.0 at the waterline (z≈0.15) → 1.0 at the bottom (z=0); the bed plane
# sits at z=0 ⇒ in_wet=1, wet_depth=1.0 (fully-wet gray 25, the same
# bucket as cobble bottoms).
import bpy

BED = "JOINTBED"
BED_WET = {"in_wet": 1.0, "wet_depth": 1.0}


def main():
    out = []
    ob = bpy.data.objects[BED]
    me = ob.data
    for name, val in BED_WET.items():
        a = me.attributes.get(name)
        if not a:
            a = me.attributes.new(name, "FLOAT", "POINT")
            out.append(f"added attribute {name} ({len(a.data)} verts)")
        v = float(val)
        for i in range(len(a.data)):
            a.data[i].value = v
        out.append(f"{name} := {v} on {len(a.data)} verts")
    # verify
    for name, val in BED_WET.items():
        got = set(round(a.data[i].value, 4) for i in range(len(me.attributes[name].data)))
        if got != {float(val)}:
            raise RuntimeError(f"JOINTBED {name}: expected only {val}, got {got}")
    out.append("verified")
    bpy.ops.wm.save_mainfile()
    out.append("SAVED " + bpy.data.filepath)
    print("WETFRESH " + " || ".join(out))
    return out


if __name__ == "__main__":
    main()