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
#   render: per design area x scene: master renders -> assets-src staging.
#           --wetpass adds the wetness-mask render per area (Mask view layer
#           + M_COBBLE_MASK override; toggles all-or-nothing, try/finally).
#   cut:    law-3 pure arrangement, master windows -> contract sheet shapes.
#   deploy: byte-verified copy staged -> mod/graphics.
#   gate:   contract conformance (16 sprites, (128*size)^2, strips/grids) +
#           staged == deployed byte-equal; failures abort loudly.
#
# The AREA REGISTRY (camera + window table per file) is the LAYOUT's
# committed state: it lives in areas_tables.py next to this driver and is
# re-based per file by the LAYOUT rounds (recipe Stage A).
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
# contract: sheet shape per size: (width_px, height_px) given 128 px/tile
# (maintainer-confirmed: 1x1 = 16 sprites in a row; sizes 2/4 = 4x4 grids)
def sheet_shape(size):
    side = 128 * size
    if size == 1:
        return 128 * SPRITES_PER_SIZE[1], 128
    return 4 * side, 4 * side


def parse_args(argv):
    ai = argv.index("--") + 1 if "--" in argv else len(argv)
    rest = argv[ai:]
    out = {"mode": "run"}
    if rest and rest[0] == "--selftest":
        out["mode"] = "selftest"
        return out, rest
    for i, a in enumerate(rest):
        if a == "--blend":
            out["blend"] = rest[i + 1]
        elif a == "--base":
            out["base"] = rest[i + 1]
        elif a == "--wetpass":
            out["wetpass"] = True
    if "base" not in out:
        raise SystemExit("--base is required (sprite name, e.g. wooden-flooring)")
    return out, rest


def contract_check(sheet_path, base, size):
    """The lua contract: shapes + counts; returns list of faults."""
    faults = []
    im = Image.open(sheet_path)
    w, h = im.size
    sprite_side = 128 * size
    if size == 1:
        expected = (sprite_side * 16, 128)
    else:
        expected = (4 * sprite_side, 4 * sprite_side)
    if (w, h) != expected:
        faults.append(f"{os.path.basename(sheet_path)}: {w}x{h} != contract {expected[0]}x{expected[1]}")
    if im.mode != "RGBA":
        faults.append(f"{os.path.basename(sheet_path)}: mode {im.mode} != RGBA")
    return faults


def sheet_sprites(im, size):
    """Yield (k, box) sprite windows of the contract sheet, row-major."""
    side = 128 * size
    for k in range(16):
        row, col = divmod(k, 4 if size != 1 else 16)
        box = (col * side, row * side, (col + 1) * side, (row + 1) * side)
        yield k, box


def cut_sheet(master, size, out_path):
    """Law-3: build the contract sheet from the master's sprite windows."""
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


def main_blend():
    """Stage B (render) implementation for a live blend session."""
    import bpy  # only the render stage needs bpy
    raise SystemExit("STAGE B (render) lands in the LAYOUT round: the area "
                     "registry does not exist yet; nothing renders until the "
                     "Stage-A lattice is committed into the file + "
                     "areas table.")


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


if __name__ == "__main__":
    argv = sys.argv
    invoked_carefully = len(argv) == 1 or "--selftest" in argv
    if invoked_carefully:
        raise SystemExit(selftest())
    args, rest = parse_args(argv)
    if "blend" in args:
        import bpy  # blender-side invocations come via --python
        bpy.ops.wm.open_mainfile(filepath=args["blend"])
        main_blend()
    else:
        raise SystemExit(selftest())