# paper-pipeline — ford piling sprites, deterministic bake chain

The Blender paper pipeline: `ford-posts.blend` renders 108 keyed piling
variants; this chain turns them into a spritesheet and a stable in-game
viewer save. Every stage is idempotent, hard-failing, and bit-reproducible.

## Usage

```bash
tools/paper-pipeline/bake.sh                    # strips → sheet → deploy → save → view
tools/paper-pipeline/bake.sh --stages strips,sheet --twice
tools/paper-pipeline/bake.sh --stages save --seed 4242
```

| Stage | Script | Proof printed |
|---|---|---|
| strips | `bake-strips.py` (via `blender -b`) | 108/108 per-frame checks + centroid σ / border scan + piling luma distribution |
| sheet | `bake-sheet.py` | every cell **bit-equal** to its source frame; alpha channel present |
| deploy | (in `bake.sh`) | sheet copied into the viewer test-mod |
| save | `bake-save.py` | seed-pinned scenario run → shutdown save renamed `ford-view-test.zip` → headless load-check; zero script exceptions |
| view | (in `bake.sh`) | windowed `--load-game` on `:0`, alive after 26 s |

## Invariants

1. **Paper pixels = Blender output only.** `bake-strips.py` renders; nothing
   processes pixels. `bake-sheet.py` merely repacks — enforced by the
   bit-equality proof. The sheet's alpha channel *is* the mask.
2. **Empties fail hard.** The old "missing frame → copy stale `.png`"
   fallback is deleted; an unwritten render aborts the crank.
3. **`--twice` is the reproducibility gate**: two crank runs must be
   bit-identical across all 108 frames.
4. **Blend-side scripts are separate.** `blender/` holds only the project
   file's own helpers (`ford_gui_setup.py`, `ford_pane_resync.py` — text
   blocks inside the .blend, run once through the MCP bridge). The .blend
   must NOT carry copies of these bake scripts: a stale `ford_crank.py`
   text block once drifted from the disk crank and masked the empty-frame
   bug (journal 2026-10-16).
5. **Never render from the MCP GUI session** (returns 0×0 empties) — the
   strip stage runs headless only.

## Calibration (on demand, not per cycle)

`calibrate-icon64.py` re-aims the ICON camera (frame 27 fill/center loop).
`bake-strips.py` prints the piling luma distribution used to reconcile lamp
and ramp changes against the retired `tools/gen-textures.py` art (mean 116).