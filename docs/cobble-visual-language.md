# Cobble visual language — spec (v1, wet-first)

Binding spec for the cobblestone ford deck (`cobblestone-ford`) and its land
partner (`cobblestone-path`). v1 is the frame for the rebuild AFTER the purge
(maintainer 2026-10-22: "all the old cobble code and blend gone — it is all
cursed"): it starts from the water, not from any art.

**No art stand-ins (maintainer ruling, 2026-10-22).** Planks are not cobbles;
stone heaps are not cobbles; the retired cobble generations are not a look
reference. The boards arc's *process* mirrors here but its *look* does not —
nothing inherited from another family's rendering drives this spec. Laws that
transfer are only those this file restates as binding.

**The water veil does not exist** (maintainer ruling, 2026-10-22): there is no
uniform wash a tile receives (the px' = 0.75·px + 0.25·(51,51,51) sim), and no
preview of this family may premise on one. Wetness = the wet/dry mask pass —
our data block, exactly as for the piling workflow.

## 0. Standing rulings this spec stands on

| Ruling | Date | Where |
|---|---|---|
| WET/DRY = the mask pass; art renders dry only, forever | 2026-10-21 rev 2 | journal; restated §2 |
| Bed keys just as wet as cobble bottoms (physical model) | 2026-10-21 rev 3 | journal; §1 |
| Gut-and-rebuild of texture/coloring (the toning stacks died) | 2026-10-21 | journal; §4 heritage |
| Light rig + mask graph = conventions from existing families (transplants, not looks) | 2026-10-21 | journal; §3.5, §2 |
| GAME_VEIL abolished (no resurrection path) | 2026-10-21 | journal |
| Sun transplant: stones-verbatim rig applied in the (now-purged) blend | 2026-10-21 | journal; §3.5 re-homes it |
| The purge: old cobble code + blend removed | 2026-10-22 | journal; §4 |
| No art stand-ins; veil nonexistent | 2026-10-22 | header |
| Game contract (16 sprites/size, all 4×4 grids, 128 px/tile @ 0.25) | 2026-10-21 | docs/export-recipe.md (binding, unchanged) |

## 1. The physical model (binding — water first)

The deck is a **waterline**, not a texture painted over water:

1. The joint bed plane sits **under water** — logically, and in the mask pass
   (it keys just as wet as cobble bottoms; rev-3 law).
2. Cobbles **rise through the water**; the wet/dry boundary on each cobble is
   where its surface meets the waterline.
3. **Some crowns breach the waterline** (dry tops exist — the 170 gray band
   must be nonempty by design, not by accident).
4. Wetness is **geometry-derived, never painted**: two mesh attributes per
   vertex/face, the piling convention —
   `in_wet` (0/1; the ≥0.5 wet key) and
   `wet_depth` (0..1, normalized depth under the waterline: 1 = deep/submerged,
   0 = at the waterline). No material may reference wetness except
   `M_COBBLE_MASK` (the mask graph; §2.1).
5. The waterline elevation and the height/breach distribution are the cobble
   **builder's authoring decisions** (§3.3). The purged mesh's numbers (bed
   z=0, waterline ≈0.15 @ 1 u = 128 px) are recorded as non-binding start
   points, measured off a cursed artifact — re-author, don't inherit.
6. The Stage-A lattice law (export-recipe §A) holds unmodified: 1 blender
   unit = 1 game tile = 128 px; contiguous 4×4 design areas per size; variant
   k = cell (r = k div 4, c = k mod 4).

## 2. The wet/dry mask pass (binding — the wetness data block)

1. **Gray language** (piling bake-mask law, unchanged):
   - **170** = dry / emergent (breaching crown tops);
   - **85** = wetted (submerged faces, at/under the waterline);
   - **25** = fully wet (the bed plane + cobble bottoms — the bed is part of
     this bucket by the rev-3 law);
   - **0/black** = outside the deck (opaque background).
   - The ramp is `wet_depth` → stepped (Steps=4) →
     0.0908=85 … 0.0097=25, dry keyed via `in_wet` → 0.402=170 — the
     `M_PILING_MASK` graph **verbatim** (the mask graph is FIXED; it is a
     convention transplant, not part of the condemned look).
2. **Render mechanics**: per design area, an extra render through the `Mask`
   view layer + `M_COBBLE_MASK` material_override. The runtime pass state
   (Standard transform, opaque film, world 0, dither 0, view-layer switch) is
   toggled **all-or-nothing (try/finally)** — the aborted-toggle lesson is
   binding procedure.
3. **Masters are committed** like art masters (assets-src staging before any
   cut); the `--twice` pixel-identity gate applies to masks as to art.
4. **Engine consumption = a separate, named change** (pending): it follows the
   wooden tile's dryness-effect precedent. Masks stay unshipped in `mod/` until
   that change lands. The prototype's `effect_color` values carry a question
   mark from the veil ruling (journal 2026-10-22) — resolved there, not here.

## 3. The dry look — authoring decisions (OPEN, maintainer rules each)

3.1 **Pattern law** — how cobbles pack a 1×1 tile: stone size/count range,
joint (gravel bed) widths, regular vs irregular courses. And the **boundary
furniture rule** for the lattice: what meets across internal 1×1 tile
boundaries on 2×2/4×4 designs — the boards analogs were per-tile lattice-
periodic crowns vs the approved per-sprite pins (materials); the cobble
equivalent must be chosen, not assumed. (Preliminary shape: a tile-local
pattern law that is tile-boundary-compliant, so variant identity lives in the
pattern, not in seams.)

3.2 **Tone bands** — stones and joint bed are toned **independently**;
verdicts are judged **DRY** (the WASHED/veil preview column is retired with
the veil ruling). Candidate palette reference material (context, not binding):
the stone-family palettes recorded in `boards-visual-language.md` §3
(vanilla stone ochre, py gravel/crush families — gathered as ingredient keys
for another deck but measured facts); vanilla `stone-path` as brightness
context. A dry deck that never reads "dirty white" and no joint bed that
reads black are the failure modes named to date.

3.3 **Height/crown law** — relief per cobble (rounded crowns, flat cuts,
irregularity), how much of the deck breaches the waterline ("some"), how the
height field interacts with the wet_depth normalization (§1.4). Height is
what makes wetness legible — the decision is structural, not cosmetic.

3.4 **Variant identity** — what distinguishes the 16 variants per size:
seeded arrangement, tone casts, stone mixes, or all three; how identity
survives tiling (boundary-compliant randomness, per §3.1).

3.5 **Material mechanism + light** — candidate mechanism for look materials:
the 4-node Noise → 2-stop ramp → Principled convention (the stones-family
transplant, previously applied to M_COBBLE/M_COBBLEBED); it is a MECHANISM
transplant, not a look stand-in — parameters are §3.2's to decide. Light rig:
the stones-verbatim sun (SUN 4.2 W, angle 0.1745, rot (0.829, 0, −1.1345),
azimuth ENE shadows) as the working default unless ruled otherwise at the
proof round; world/fill re-decided fresh with the builder (nothing inherited
carries authority).

## 4. Condemned heritage (provenance record)

Removed 2026-10-22 at the purge ruling — recoverable at that commit:
`auth-cobble.py`, `bake-cobble.py/.sh` (the condemned crank: provenance stamps,
mesh-hash oracle), `mat-fresh.py`/`wet-fresh.py` (session bricks whose object
died with the blend), `palette-ladder-cobble.py` (condemned inputs + veil),
`blender/ford-cobble.blend(+1)` (the irregular ~58×52 blob), `__pycache__`/
gitignore entries. The committed sheet generations (`assets-src/cobble`,
`mod/graphics` deploys) are art, not code: they **retire to archive per
export-recipe.md once the new look is approved** — the documented drift fault
(230,954 / 1,038,847 / 4,141,417 px staging-vs-deployed) closes then.

## 5. The process (the boards mirror, corrected)

1. This spec (§3 open points ruled by the maintainer).
2. A committed cobble spec JSON — **authored** from §3 rulings (nothing is
   extracted: no inherited look exists to extract from) — the pinned material/
   pattern constants.
3. `cobble-builder.py`: regenerates `blender/ford-cobble.blend` from
   primitives ON the Stage-A lattice (factory-empty, FLOOR-only, cams at
   contract depth, census/geometry gates like boards), materials per spec,
   wetness keying per §1 — the blend is build output, nothing hand-authored.
4. `bake-ladder.py --base cobblestone-ford --wetpass` (the shared-art pair
   becomes cobblestone-ford + cobblestone-path): art masters + mask masters
   committed, `--twice` both, identity cut, byte-verified deploy, contract
   gates.
5. Icon re-run (make-icons reads deployed sheets), then the named mask-wiring
   change, then in-game: the maintainer's eyes on the real wet/dry look.
   Every visual verdict is theirs.