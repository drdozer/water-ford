# Decisions log — thumbnail brief

Human verdicts per round. Variants are numbered per run; pre-tooling library
labels are mapped below.

## Run 20261017T172004Z — round 1 (capability proof; 6 prompts, seed 11)

- Result: pipeline capability proven (maintainer: "truly amazing work").
- **Rejected (all six)**: style — the planks float on top of the water; the
  ford is submerged. Corrected the brief before round 2.

## Run 20261018T133828Z — round 2 (4 prompts, seed 7)

- **Liked: variant 4** (dynamic low angle, wading engineer, leaping fish) —
  became the direction anchor.
- Rejected: variant 1 (square-on composition "not ideal"); variant 2
  (surprised engineer — "not the vibe", though its underwater fish + a splash
  + a sensible engineer was named as a potential winner → became round-3
  candidate 2); variant 3 (boards above water — a wharf; the mod's boards are
  submerged).

## Run 20261018T142048Z — round 3 (4 prompts, seed 7) — ADOPTED

- **ADOPTED: candidate 1** (old library label "variant 5"): engineer striding
  forward arm pointing ahead, ford diagonal, submerged planks underfoot,
  leaping fish at the corner → `mod/thumbnail.png` @288 (commit `ff73498`).
- Not chosen: candidate 2 (the requested round-2×round-4 hybrid — calm
  engineer + bursting fish), candidate 3 (side-angle crossing with red
  toolbox), candidate 4 (welcoming gesture, fish under the foreground water).
- Label mapping: library `variant-5..8` ≡ this run's `variant-1..4`.

## Run 20261018T190142Z — tooling shakedown (1 candidate, seed 7, --count 1)

- First pipeline-era run: verified end-to-end (brief → drift gate → engine →
  run record). **Determinism re-proven live**: the fresh candidate 1 is
  byte-identical to the adopted round-3 candidate 1 — the idempotent re-adopt
  confirmed the target unchanged (`3643e678…`). No new art decision.
