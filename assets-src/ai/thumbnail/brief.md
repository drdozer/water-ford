# Thumbnail — mod-portal image (engineer wading the submerged ford)

**Delivery**: `mod/thumbnail.png`, 288×288 (@2× pixel density of the portal's
144×144 spec), built from a 512² generation master via LANCZOS. **Adopted**:
run 20261018T142048Z candidate 1 (maintainer, 2026-10-18; commit `ff73498`).

## Intent

Bold, clean cartoon storytelling that reads at 144²: the engineer — the
cartoony reference design (yellow hard hat + headlamp, round goggles, orange
shirt, grey vest; see `reference/cartoonish-character.png`) — wades across the
ford; the **boards are submerged**, seen through clear teal water (wet boots,
splash energy); pilings rise at the ford edges; green trees frame one side;
open water recedes to a hazy far shore; an orange fish adds life. No text,
letters, logos or UI. Diagonal/asymmetric composition (a square-on framing was
explicitly rejected in round 2). Calm/confident expressions only ("capable,
calm", "warm smile" — a surprised face was rejected).

## References (copies; sources in superproject `shared-assets/from-maintainer/`)

- `screengrab.png` — in-game ford: submerged planks, pilings, trees SW, sandy
  shore SE (the ground truth for what the mod looks like)
- `character.png` — in-game engineer sprite
- `cartoonish-character.png` — the cartoony engineer the thumbnails stylize

## Hard-won prompt findings (rounds 1–3)

- **Submersion is fragile under text-only prompting**: 3 of 4 round-2 runs
  flipped "planks under water" into a dry pier/wharf. What worked (round 3):
  "wades across", "planks visible through the clear water underfoot",
  "the waterline cuts across the planks", low camera near the surface,
  splashes.
- Expressions must be stated positively; negations and "looking at" phrasings
  drift to surprise faces.
- 512² master → 288/144 LANCZOS downscale; never generate at delivery size.
- Same seed across prompts (seed_mode shared, seed 7) isolates the prompt
  effect — the round-2/3 methodology.

## Regeneration

`devctl mods art water-ford thumbnail generate` (offline dry-run: `--dry-run`).
Engine/VRAM facts: superproject `docs/ai-art-tooling.md`; process spec:
`docs/ai-art-briefs.md`.
