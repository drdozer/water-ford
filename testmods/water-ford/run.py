#!/usr/bin/env python3
"""Headless runner for the water-ford ford-vehicle-crossing scenario.

Assembles a hermetic Factorio instance under <superproject>/.cache/water-ford-vehicle-test/
(binary + data from the dlc install named in devctl.conf), launches the scenario
as a dedicated server, waits for the results JSON, quits via RCON, and maps the
verdict onto the exit code:

    0  pass        - wooden ford car stopped; cobblestone ford car crossed;
                     biters have a crossing path onto the cobble ford
                     (balance ruling 2026-10-22: cobble paving must not be
                     a biter barrier) and across wooden/shallow/landfill
                     controls; deepwater stays pathless
    1  fail        - a contract gate violated (wooden car crossed, cobble car
                     stopped, or a unit path crosses the cobble ford)
    2  harness-error - control lane failed / results missing / server died

Run from anywhere:  devctl python run mods/water-ford/testmods/water-ford/run.py
(also works with plain python3 - stdlib only).
"""
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import time

RCON_PORT = 27015
RCON_PASSWORD = "water-ford-probe"
RESULTS_NAME = "ford-vehicle-crossing-results.json"
LAUNCH_BUDGET_S = 180      # max wait for the results file
RCON_BUDGET_S = 60


def find_root():
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, "devctl.conf")):
            return d
        d = os.path.dirname(d)
    sys.exit("run.py: could not locate the superproject root (no devctl.conf above the testmod)")


def conf_value(root, key):
    with open(os.path.join(root, "devctl.conf")) as f:
        for line in f:
            line = line.strip()
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip('"')
    sys.exit(f"run.py: {key} not found in devctl.conf")


def rcon_quit(port, password):
    def pkt(pid, ptype, body):
        d = struct.pack("<ii", pid, ptype) + body.encode() + b"\x00\x00"
        return struct.pack("<i", len(d)) + d

    def read_pkt(s):
        ln = struct.unpack("<i", s.recv(4))[0]
        buf = b""
        while len(buf) < ln:
            chunk = s.recv(ln - len(buf))
            if not chunk:
                break
            buf += chunk
        return buf[8:-2].decode(errors="replace")

    deadline = time.time() + RCON_BUDGET_S
    while time.time() < deadline:
        try:
            s = socket.create_connection(("127.0.0.1", port), timeout=5)
            s.sendall(pkt(1, 3, password))          # auth
            read_pkt(s)
            s.sendall(pkt(2, 2, "/quit"))           # clean shutdown -> exit 0
            read_pkt(s)
            s.close()
            return True
        except OSError:
            time.sleep(1)                           # RCON binds late (~10 s)
    return False


def main():
    root = find_root()
    dlc = conf_value(root, "FACTORIO_DLC_PATH")
    factorio = os.path.join(dlc, "bin", "x64", "factorio")
    if not os.path.exists(factorio):
        sys.exit(f"run.py: factorio binary not found at {factorio}")

    scratch = os.path.join(root, ".cache", "water-ford-vehicle-test")
    mods_dir = os.path.join(scratch, "mods")
    if os.path.isdir(scratch):
        shutil.rmtree(scratch)
    os.makedirs(os.path.join(scratch, "config"))
    os.makedirs(mods_dir)

    # hermetic mod set: the mod under test + this testmod (symlinks, devctl style)
    os.symlink(os.path.join(root, "mods", "water-ford", "mod"),
               os.path.join(mods_dir, "water-ford"))
    os.symlink(os.path.join(root, "mods", "water-ford", "testmods", "water-ford"),
               os.path.join(mods_dir, "water-ford-testmod"))

    with open(os.path.join(scratch, "config", "config.ini"), "w") as f:
        f.write("[path]\nread-data=__PATH__executable__/../../data\n"
                f"write-data={scratch}\n")
    with open(os.path.join(scratch, "server-settings.json"), "w") as f:
        json.dump({"name": "water-ford-vehicle-test", "description": "", "tags": [],
                   "max_players": 0, "visibility": {"public": False, "lan": False},
                   "auto_pause": False, "only_admins_can_pause_the_game": False}, f)

    log_path = os.path.join(scratch, "server.log")
    cmd = [factorio, "-c", os.path.join(scratch, "config", "config.ini"),
           "--mod-directory", mods_dir,
           "--start-server-load-scenario", "water-ford-testmod/ford-vehicle-crossing",
           "--server-settings", os.path.join(scratch, "server-settings.json"),
           "--rcon-port", str(RCON_PORT), "--rcon-password", RCON_PASSWORD,
           "--disable-audio"]
    with open(log_path, "w") as logf:
        proc = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT)

        results_path = os.path.join(scratch, "script-output", RESULTS_NAME)
        results, died_early = None, False
        deadline = time.time() + LAUNCH_BUDGET_S
        while time.time() < deadline:
            if os.path.exists(results_path):
                try:
                    with open(results_path) as f:
                        results = json.load(f)
                    break
                except json.JSONDecodeError:
                    pass                    # partial write; keep polling
            if proc.poll() is not None:
                died_early = True
                break
            time.sleep(1)

        rcon_ok = rcon_quit(RCON_PORT, RCON_PASSWORD)
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            print("run.py: server did not quit via RCON; killed", file=sys.stderr)

    def tail(path, n=25):
        try:
            with open(path) as f:
                return "".join(f.readlines()[-n:])
        except OSError:
            return "(no log)"

    if results is None:
        print(f"run.py: HARNESS-ERROR — no results file"
              f" (server {'died early' if died_early else 'timed out'}, rcon_quit={rcon_ok})")
        print(f"--- log tail: {log_path} ---")
        print(tail(log_path))
        sys.exit(2)

    overall = results.get("overall", "harness-error")
    print(f"verdict: {overall}   (eval tick {results.get('eval_tick')})")
    for key in ("wooden-ford", "cobblestone-ford", "water-shallow", "landfill",
                "unit-cobblestone-ford", "unit-wooden-ford", "unit-water-shallow",
                "unit-landfill", "unit-deepwater", "deepwater"):
        lane = results.get("lanes", {}).get(key, {})
        print(f"  {key:14} min_x={lane.get('min_x')} final_x={lane.get('final_x')}"
              f" crossed={lane.get('crossed')} -> {lane.get('verdict')}")
    if overall == "pass":
        sys.exit(0)
    if overall == "fail":
        sys.exit(1)
    print(f"--- log tail: {log_path} ---")
    print(tail(log_path))
    sys.exit(2)


if __name__ == "__main__":
    main()
