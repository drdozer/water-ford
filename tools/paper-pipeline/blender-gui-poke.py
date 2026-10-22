# blender-gui-poke.py — startup poke for the boards GUI sessions.
#   blender blender/ford-boards.blend --python tools/paper-pipeline/blender-gui-poke.py
# Frames every 3D viewport on the rebuilt content (the three lattice areas
# live at the origin and down to y=-30 — the default framing shows nothing)
# and pokes viewport shading (the standing rule after any rebuild: the
# rendered-shading session holds dead data-block refs; MATERIAL re-inits).
import bpy


def _poke(_scene=None):
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
    # once is enough
    if _poke in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_poke)
    print("BOARDS GUI POKE: viewports framed on the boards content (material shading)")


# Blender 4.x runs CLI --python scripts BEFORE the file argument is read
# (incident 2026-10-22: the poke framed the empty factory scene); the poke
# therefore hooks load_post, which fires after the file lands
bpy.app.handlers.load_post.append(_poke)
# already-loaded sessions (no file pending) get the immediate poke
if bpy.data.filepath:
    _poke()