# mat-fresh.py — fresh cobble materials (2026-10-21, gut-and-remake: materials)
#
# STANDALONE, first brick of the NEW toolchain. NOT part of the condemned
# crank (auth-cobble/bake); runs only inside the open ford-cobble.blend
# session.
#
# REV 2 (same day, maintainer ruling "wet/dry is essential ... exactly as
# for the piling workflow"): the wet/dry split exists ONLY as the separate
# wetness-mask render — NEVER as wet art materials, and it does not touch
# the sprite renders at all.
#
# Components, transplanted verbatim from the piling workflow:
#   * ART = dry materials only (stones-shader convention, rev 1):
#     Noise(Scale S, Detail 8, Rough 0.5) -> ColorRamp(2 stops) ->
#     Principled(Roughness 0.85) = 4 nodes.
#   * MASK = M_COBBLE_MASK, the 6-node M_PILING_MASK graph
#     (.cache/water-ford/mat-posts.txt):
#         Attribute("in_wet")     -> SegmentGray.Fac   (0 -> dry gray 170)
#         Attribute("wet_depth")  -> WetDepthRamp      (MapRange 0..1, Steps 4)
#                                 -> WetGrayRamp.Fac   (85 -> 25 across wet zone)
#         -> Emission(Strength 1) -> Output
#     gray language (LINEAR emission -> sRGB bytes): 0.402=170 dry crown,
#     0.0908=85 wet edge, 0.0097=25 fully wet base, 0 outside silhouette.
#     The pass state (Standard transform, opaque film, world 0, dither 0)
#     is runtime-only, restored after — exactly bake-mask.py's toggles.
import bpy
import os

# --- gray language constants (piling conventions, byte-exact targets) -------
GRAY_DRY = 0.402      # -> 170
GRAY_WET_EDGE = 0.0908  # -> 85
GRAY_WET_FULL = 0.0097  # -> 25
MASK_ATTR_IN_WET = "in_wet"
MASK_ATTR_WET_DEPTH = "wet_depth"

SPECS = {
    # name: (stops [(pos, rgb)], noise scale, extra principled overrides)
    "M_COBBLE": ([(0.3, (0.42, 0.39, 0.36)), (0.72, (0.64, 0.52, 0.35))], 1.2, {}),
    # joint bed: the gravel/grout floor between cobbles (~L40..L72)
    "M_COBBLEBED": ([(0.3, (0.16, 0.15, 0.14)), (0.72, (0.30, 0.28, 0.26))], 3.0, {}),
}

ART_NAMES = list(SPECS) + []
MASK_MATERIAL = "M_COBBLE_MASK"


def luma(rgb):
    r, g, b = rgb
    return round(255 * (0.2126 * r + 0.7152 * g + 0.0722 * b))


def build(name, stops, scale, extra):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.location = (-200, 0)
    while len(ramp.color_ramp.elements) > len(stops):
        ramp.color_ramp.elements.remove(ramp.color_ramp.elements[-1])
    for (pos, rgb), el in zip(stops, ramp.color_ramp.elements):
        el.position = pos
        el.color = (*rgb, 1.0)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.location = (-500, 0)
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.5
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (50, 0)
    bsdf.inputs["Roughness"].default_value = 0.85
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (350, 0)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    for key, val in extra.items():
        bsdf.inputs[key].default_value = val
    return m


def build_mask(name=MASK_MATERIAL):
    """The 6-node M_PILING_MASK graph, verbatim."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)

    def node(t, loc, nname, props=None):
        n = nt.nodes.new(t)
        n.name = nname
        n.location = loc
        for k, v in (props or {}).items():
            setattr(n, k, v)
        return n

    out = node("ShaderNodeOutputMaterial", (300, 0), "Mask Output")
    attr_wet = node("ShaderNodeAttribute", (-500, 50), "In Wet Attr",
                    {"attribute_name": MASK_ATTR_IN_WET})
    attr_depth = node("ShaderNodeAttribute", (-500, -100), "Wet Depth Attr",
                      {"attribute_name": MASK_ATTR_WET_DEPTH})
    ramp_depth = node("ShaderNodeMapRange", (-260, -100), "Wet Depth Ramp")
    ramp_depth.inputs["From Min"].default_value = 0.0
    ramp_depth.inputs["From Max"].default_value = 1.0
    ramp_depth.interpolation_type = "STEPPED"   # exactly M_PILING_MASK's mode
    ramp_depth.inputs["Steps"].default_value = 4.0
    gray_wet = node("ShaderNodeMixRGB", (-60, -100), "Wet Gray Ramp")
    gray_wet.inputs["Color1"].default_value = (GRAY_WET_EDGE,) * 3 + (1.0,)
    gray_wet.inputs["Color2"].default_value = (GRAY_WET_FULL,) * 3 + (1.0,)
    seg = node("ShaderNodeMixRGB", (100, 0), "Segment Gray")
    seg.inputs["Color1"].default_value = (GRAY_DRY,) * 3 + (1.0,)
    em = node("ShaderNodeEmission", (170, 0), "Mask Emission")
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(attr_depth.outputs["Fac"], ramp_depth.inputs["Value"])
    nt.links.new(ramp_depth.outputs["Result"], gray_wet.inputs["Fac"])
    nt.links.new(attr_wet.outputs["Fac"], seg.inputs["Fac"])
    nt.links.new(gray_wet.outputs["Color"], seg.inputs["Color2"])
    nt.links.new(seg.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m


def luma_report(label, stops):
    return f"{label}: " + " -> ".join(
        f"L{luma(rgb)}@{pos}" for pos, rgb in stops
    )


def mask_pass_state(scene):
    """Dedicated Mask view layer fixture (material override), like bake-mask.

    Runtime toggles for the pass itself live in the (fresh) bake round; here
    we only ensure the view layer exists and carries the override, unused in
    default renders."""
    vl = scene.view_layers.get("Mask") or scene.view_layers.new("Mask")
    vl.material_override = bpy.data.materials[MASK_MATERIAL]
    return vl


def main():
    out = []
    assignments = {
        "COBBLE_FLOOR": "M_COBBLE",
        "JOINTBED": "M_COBBLEBED",
    }
    doomed = [m for m in bpy.data.materials if m.name.startswith("M_COBBLE")]
    new_mats = {}
    for name, (stops, scale, extra) in SPECS.items():
        new_mats[name] = build(name, stops, scale, extra)
        out.append(luma_report(name, stops))
    new_mats[MASK_MATERIAL] = build_mask()
    out.append("mask material built (M_PILING_MASK graph verbatim)")
    for obname, matname in assignments.items():
        ob = bpy.data.objects[obname]
        for slot in ob.material_slots:
            slot.material = new_mats[matname]
        out.append(f"{obname} <- {matname}")
    old_mats = [m for m in doomed if m not in new_mats.values()]
    if old_mats:
        out.append("gutting: " + ",".join(m.name for m in old_mats))
    for m in old_mats:
        if m.users:
            raise RuntimeError(f"{m.name} still referenced by {m.users} user(s)")
        bpy.data.materials.remove(m)
    out.append(f"remaining materials: {[m.name for m in bpy.data.materials]}")
    for sname in ("FLOOR", "FORD"):
        vl = mask_pass_state(bpy.data.scenes[sname])
        out.append(f"scene '{sname}': Mask VL override={vl.material_override.name}")
    bpy.ops.wm.save_mainfile()
    out.append("SAVED " + bpy.data.filepath)
    print("MATFRESH " + " || ".join(out))
    return out


if __name__ == "__main__":
    main()