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
| Polished slate look; speckle/pitting breaks reflections; research-not-reinvent; variants = seeded geometry/packing jiggling (texture jiggle secondary) | 2026-10-22 | §3.2/§3.4 |
| Mandatory boards scene template (same lights/cams/staging areas); internal-grid jiggle free, outer edges law-bound | 2026-10-22 | §3.1/§3.5 |
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

## 3. The dry look — authoring decisions (RULINGS LANDED 2026-10-22)

STATUS (2026-10-22, session 3): every §3 decision has a recorded maintainer
ruling — walkthrough rounds 1–4, the hard-reset superellipsoid spec, and
the in-game rulings (masks, masters, borders "as-is", tiles in the live
solo run) — see journal 2026-10-22 entries. The subsections below stand as
the decision record; nothing is awaiting a ruling.

3.1 **Pattern law** — walkthrough rulings (2026-10-22, round 1):
     - Cobbles are **oblong, packed 3×4 per 1×1 tile** (12 stones/tile; the
       oblong transposition and exact stone/joint dimensions resolve at the
       first proof render).
     - **Neighbour merges into "large" cobbles** occur occasionally — a
       seeded authoring knob (frequency not yet fixed).
     - **Edge law (the R10 analog, cobble form)**: the cobble grid is
       aligned to the tile lattice so that NO joint between two arbitrarily
       chosen 1×1 variants reads as broken — edge-touching stones meet
       variant-invariant lattice positions ("pin the boundary, free the
       interior").
     - **Spill law — RULING (2026-10-22, round 2)**: small spill across the
       tile edge is allowed and expected — it stays small enough that
       shadows or neighbouring stones hide it (nearly always, per the
       ruling). The alignment of edge stones stays variant-invariant. The
       **cobble's top stays entirely within the tile**: what may cross the
       boundary is only the lower stone mass (base/skirt) — never the
       crown. Final px bound of "small" = a proof-round check.
     - **Coverage law**: cobbles fill most of the xy space; only very small
       amounts of the floor layer show through — thin joints, minimal bed
       exposure (the joint width = the measurable knob).
     - 2×2/4×4 designs: the same 1×1-periodic stone lattice across the
       design's internal tiles; merges may cross internal boundaries
       within a design area. The design's outer edge carries the edge law.

3.2 **Tone + surface — RULING (2026-10-22, round 3)**: hard, **polished**
rocks — base color slate / dark grey; tonal variety arrives as
**speckling and/or non-reflective pitting**: texture that keeps the
polished-stone read while breaking up harsh continuous reflections
(neither shiny-plastic nor matte-fake). Named failure modes: a deck
reading "dirty white", a joint bed reading black, polish reading plastic.
- **PROCESS directive: do not re-invent the shader — ask the internet**
(cobblestone/polished-stone material technique) and adopt a proven
approach as the working recipe; the researched technique seeds §3.5's
mechanism.
- Stones and joint bed toned independently; judged DRY (the WASHED/veil
preview column is retired); tuned + approved at proof rounds like §3.3's
numbers.
- **Bed ruling (2026-10-22, round 4)**: the floor joint layer is faux
  (shader-side, no extra geometry) textured as **sand/pebble rubble in
  the sandy palette** — the warm sand/ochre families recorded in
  `boards-visual-language.md` §3 as candidate references; pebble relief
  = Voronoi-family bump at low amplitude (matte rubble that catches
  shadows law-compliantly); pebble/fine scale = tuned at proofs. The
  bed stays recessed/dark-in-shadow via the joint geometry, not via a
  black tone.
- OPEN (tuned at proofs, approved by eyes): slate L-band, base roughness
+ breakup strength, speckle + pit tuning, exact sandy bed stops.

3.3 **Height/crown law** — walkthrough rulings (2026-10-22, rounds 1–3):
     - **Shadow law (binding): everything casts AND catches shadows,
       including the floor layer.** The 3D appearance comes from shadow
       interplay — the floor is a real recessed plane, stones stand proud
       of it, and receive/cast flags are never disabled anywhere in the
       deck family. No baked-flat look: relief is real geometry.
     - **Crown form — RULING (2026-10-22, round 2)**: a flattened dome —
       "a bit like a loaf of bread: a rectangle with irregularly rounded
       corners and edges and an inflated top" (maintainer's archetype). The
       inflated top lies entirely within the cobble's cell (spill law,
       §3.1).
     - **§3.3's numbers are TUNING KNOBS, not given constants (round 3)**:
       crown height range, breach fraction, waterline elevation, and the
       `wet_depth` mapping are tuned by the builder, measured numerically,
       then approved by the maintainer's eyes. "The crown height range
       will give you the breach fraction" — heights tune first; the
       breach share follows; §1.5's recorded z-numbers are starting hints
       only.

3.4 **Variant identity — RULING (2026-10-22, round 3)**: randomised cobble
GEOMETRY and packing; everything jiggled so nothing repeats — texture
jiggles too, geometry primarily. Per-variant seeds drive positions,
sizes, heights, rounding, and merges (tone casts as needed); the seed
law respects the lattice edge law (§3.1). Sanctioned pending "if it
works": approved at proof.

3.5 **Mechanism + light — RULINGS (2026-10-22, round 3)**:
- **Scene layout: MANDATORY boards template.** The cobble builder
  reproduces the boards builder's scene skeleton: the same staging areas
  (AREA_1X1/2X2/4X4), the same cameras (BLK1/2/4_CAM, ortho 4/8/16 at the
  contract depth), the same light rig — the cobble differs only in mesh
  and materials. The stones-verbatim sun default is **RETIRED** (the sun
  transplant lived in the purged blend; the boards template is the law).
- **Look materials**: the researched polished-stone technique (2026-10-22
  web round — blender.SE polished-granite accepted answer, a procedural
  cobblestone tutorial, PBR roughness-map deep dive) = the working
  recipe, per the "ask the internet" directive: see §3.2a.
- **§3.2a — the researched polished-stone recipe (candidate mechanism,
  to be proven at the proof rounds):**
  1. **Polish = low base roughness + a roughness-breakup layer** — never
     a uniform gloss: base roughness tuned (~0.25–0.4 candidate), then a
     low-contrast noise modulation layered on top so reflections break
     up but never read plastic-or-matte (the "plastic" failure mode =
     flat uniform roughness).
  2. **Speckle = scaled-up Voronoi through a ColorRamp mixed into Base
     Color at low factor** (the granite "crystal fleck" technique) —
     tonal variety WITHOUT raising metallic/shine.
  3. **Non-reflective pitting = smooth-Voronoi pit field through Bump at
     LOW strength (the 0.02-class default), optionally darkening Base
     Color / raising local roughness in the pits** — pits read as matte
     grunge catchers, never as shiny dimples ("non-reflective" is the
     spec, per §3.2).
  4. **Per-stone value/hue casts** via seeded per-stone attributes (the
     boards' per-plank cast law as a MECHANISM — geometry jiggle remains
     primary per §3.4).
  5. Stone-vs-bed separation (height, contact shadows) comes from the
     REAL geometry (loaf meshes + recessed floor) + the shadow law
     (§3.3) — the shader adds no displacement for stone silhouettes
     (top-down ortho camera; 1 px = 1/128 u ⇒ bump distances in the
     ~0.008–0.02 u range).
- `M_COBBLE_MASK` stays fixed (piling law, §2.1); wetness NEVER enters
  art materials (§2).
- OPEN (tuned at proofs, approved by eyes): slate L-band, base roughness
  value + breakup strength/contrast, speckle scale/density, pit scale,
  bed tone.

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