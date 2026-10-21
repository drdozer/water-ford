# blender-gui-poke.py — startup poke for the boards GUI sessions.
#   blender blender/ford-boards.blend --python tools/paper-pipeline/blender-gui-poke.py
# Frames every 3D viewport on the rebuilt content (the three lattice areas
# live at the origin and down to y=-30 — the default framing shows nothing)
# and pokes viewport shading (the standing rule after any rebuild: the
# rendered-shading session holds dead data-block refs; MATERIAL re-inits).
import bpy

for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type != "VIEW_3D":
            continue
        for space in area.spaces:
            if space.type == "VIEW_3D":
                space.shading.type = "MATERIAL"
        region = [r for r in area.regions if r.type == "WINDOW"][0]
        with bpy.context.temp_override(window=window, area=area, region=region):
            bpy.ops.view3d.view_all(center=False)
print("BOARDS GUI POKE: viewports framed on the boards content (material shading)")