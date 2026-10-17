#!/usr/bin/env python3
# bake-save: regenerate the stable in-game viewer save from the transition asset.
#   provision scratch (config + symlinked mods) -> headless scenario server
#   (seed-pinned) -> graceful SIGTERM -> rename -> headless load-check.
# Deterministic: same seed + same sheet = same save. Scenario state is all on_init;
# loading the save runs zero scenario Lua (by design, after the global/on_tick crash).
import argparse, os, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
for _ in range(4):                     # paper-pipeline -> tools -> water-ford -> mods -> superproject
    ROOT = os.path.dirname(ROOT)
SCRATCH = os.path.join(ROOT, "mods", "water-ford", "testing", "scratch")
VIEWER = os.path.join(ROOT, "mods", "water-ford", "testing", "wf-piling-viewer")
FACTORIO = os.environ.get("FACTORIO_BIN", os.path.expanduser("~/.local/share/factorio_2_dlc/bin/x64/factorio"))
GEN_WAIT = 28          # headless server: sculpt completes in on_init; server pauses when empty
TERM_FLUSH = 10        # max seconds for the shutdown save to appear after SIGTERM
CHECK_WAIT = 14        # headless load-check window

ap = argparse.ArgumentParser()
ap.add_argument("--seed", type=int, default=4242)
ap.add_argument("--no-loadcheck", action="store_true")
args = ap.parse_args()

def provision():
    os.makedirs(os.path.join(SCRATCH, "config"), exist_ok=True)
    os.makedirs(os.path.join(SCRATCH, "mods"), exist_ok=True)
    os.makedirs(os.path.join(SCRATCH, "saves"), exist_ok=True)
    with open(os.path.join(SCRATCH, "config", "config.ini"), "w") as fh:
        fh.write(f"[path]\nread-data={os.path.expanduser('~/.local/share/factorio_2_dlc/data')}\n"
                 f"write-data={SCRATCH}\n")
    links = [
        (os.path.join(ROOT, "mods", "water-ford", "mod"), "water-ford"),
        (VIEWER, "wf-piling-viewer"),
    ]
    for target, name in links:
        dst = os.path.join(SCRATCH, "mods", name)
        tmp = dst + ".tmp"
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        os.symlink(target, tmp)
        os.replace(tmp, dst)

def run(flags, log, wait, term=True):
    cfg = os.path.join(SCRATCH, "config", "config.ini")
    moddir = os.path.join(SCRATCH, "mods")
    p = subprocess.Popen([FACTORIO, "-c", cfg, "--mod-directory", moddir, *flags],
                         stdout=open(log, "w"), stderr=subprocess.STDOUT)
    time.sleep(wait)
    alive = p.poll() is None
    if term:
        if alive:
            p.send_signal(signal.SIGTERM); time.sleep(3)
        try: p.wait(timeout=10)
        except subprocess.TimeoutExpired: p.kill()
    return alive, log

prov_ok = provision()
# the ford transition asset lives in the mod now (viewer decorative sheets retired)
sheet = os.path.join(ROOT, "mods", "water-ford", "mod", "graphics", "pilings-transition.png")
maskf = os.path.join(ROOT, "mods", "water-ford", "mod", "graphics", "pilings-transition-mask.png")
if not (os.path.exists(sheet) and os.path.getsize(sheet) > 50000 and os.path.exists(maskf)):
    sys.exit("transition asset missing in mod graphics - run the deploy stage first")

for name in ["ford-view.zip", "ford-view-test.zip"]:
    p = os.path.join(SCRATCH, "saves", name)
    if os.path.exists(p): os.remove(p)

log = os.path.join(SCRATCH, "server.log")
alive, _ = run(["--start-server-load-scenario", "wf-piling-viewer/ford-view",
                "--map-gen-seed", str(args.seed)], log, GEN_WAIT)
src = os.path.join(SCRATCH, "saves", "ford-view.zip")
for _ in range(TERM_FLUSH * 2):
    if os.path.exists(src): break
    time.sleep(0.5)
if not os.path.exists(src):
    sys.exit(f"scenario save did not appear; see {log}")
dst = os.path.join(SCRATCH, "saves", "ford-view-test.zip")
os.replace(src, dst)
print(f"save regenerated: {dst}")

if not args.no_loadcheck:
    clog = os.path.join(SCRATCH, "loadcheck.log")
    alive, _ = run(["--start-server", dst], clog, CHECK_WAIT)
    if not alive:
        sys.exit(f"load-check FAILED - server died; see {clog}")
    print(" HEADLESS LOAD OK")

logtxt = open(log).read() + (open(os.path.join(SCRATCH, "loadcheck.log")).read()
                            if not args.no_loadcheck and os.path.exists(os.path.join(SCRATCH, "loadcheck.log")) else "")
if "Exception" in logtxt or "ScriptError" in logtxt:
    sys.exit("script exceptions found in logs - inspect before trusting this save")
print("BAKE-SAVE DONE")