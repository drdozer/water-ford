# Boards research — running notes (ford-boards arc)

Ticket: `../../inbox/produce-ford-boards-tilesets.md` (order 1, OPEN).
Scope of THIS doc: the research phase of the arc. Blender authoring happens in
a later, joint phase with the maintainer; nothing here builds or renders the
factory. Scratch/provenance: `.cache/boards-research/` (superproject scratch,
recreated from this doc).

Method + limitations (2026-10-17 session): this session is headless and the
agent cannot view images — every visual claim below is **numeric** (PIL/numpy
measurements with scripts/method noted) and the maintainer does the eyeball
review (gwenview gates exist in the ticket's verification section anyway).
References: `docs/blender-factory-laws.md` (binding), `docs/ford-knobs.md`,
`docs/shore-rim.md`, `shadows.md`.

## Question register

| ID | Question | Status |
|---|---|---|
| R1 | What IS the inherited deck art, numerically? (planks.png palette anchors, plank geometry per 64px variant, grain/shade rhythm, alpha) — deliverable (a) | OPEN |
| R2 | Stone/gravel palette sources: py gravel/stone item assets + vanilla stone assets; swatch set restricted to the mid-to-light half. Is planks.png == planks-base.png today? | OPEN |
| R3 | "Rich tiles" precedents: vanilla concrete + Space-Age platform tile variant layouts (sizes/counts/layers), py tile definitions; what would rich mean for the land tile (stretch goal) and could it fit the ford too? | OPEN |
| R4 | Doodad fallback mechanics (maintainer's "decal" = in-game decorative components): can engine decoratives be composed over a tile face? mapgen vs script placement; control-stage legality vs the round-9 ban; does any local mod (AsphaltPaving?) do this | OPEN |
| R5 | Vanilla concrete consult (land tile registration): is_foundation, buildable-on vs the ford's not-buildable, collision_mask, decoratives fields | OPEN |
| R6 | Light rig extraction from ford-posts.blend (read-only): sun + ambient transforms/energies relative to origin for origin-staged boards | OPEN |
| R7 | W3 response check: simulate the committed water mix on candidate stone swatches (in-sprite ballast lead option) — do mid-light pebbles survive the mix with enough contrast? | OPEN |
| R8 | What board content, if any, lives in the pilings transition frames today (P1 composite re-derivation scope, ticket c3)? | OPEN |
| R9 | Pipeline shape for boards: where boards stages slot into bake.sh stages (strips/sheet/deploy/save/view), what --twice covers, deploy mechanics | OPEN |

## Findings

(appended below as questions resolve; each finding carries its method and, where
useful, the scratch path that can regenerate it)

## Session log

- 2026-10-17 — opened doc during the research phase kickoff (agent session
  after maintainer's go-ahead; see ticket chat: ballast-in-sprite is the lead
  option, doodad composition is the fallback if in-sprite can't be made nice;
  land tile = plain single-cell flooring first, rich tiles are a stretch goal
  and may apply to the ford too).