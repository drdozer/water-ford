# BACKLOG — deferred work charter (durable note)

Purpose: carry deferred work across sessions. Items here were explicitly
deferred by the maintainer — do NOT do them opportunistically mid-stage;
stage work is gated one item at a time. When an item is done, move it to the
bottom as DONE with the date.

## FULL TIDYING PASS (queued — maintainer request 2026-10-16: "make a durable
## note to do a full tidying of everything")

A dedicated session that cleans up ALL accumulated cruft in the factory.
Known candidates (add more as discovered; verify each before touching):

1. **Param-fcurve timeline hygiene** (the known defect class from the jitter
   fix): the modifier sockets' key lists are a historic patchwork — dense
   1..64, a stray key at 71, then 110..152 — while the variant timeline is
   1..108. Rebuild every per-frame parameter (sink Socket_5, cuts 6-14, rings
   15/16) on clean keys 1..108, dropping dead keys beyond the timeline.
   The jitter pair (Socket_4/17) is already clean (re-keyed 2026-10-16).
   After re-keying: full chain re-run + --twice bit-repro gate.
2. **Legacy/viewport-only leftovers** in ford-posts.blend: WATER_LEVEL and
   WATER_BED (hide_render=True globally, viewport-only legacy context),
   "TEST Blue Top" unlinked test node on M_PILING, TILE_GRID helper.
   Decide keep/drop per object; the renderer must stay bit-identical.
3. **Action name and modifier name**: object action "POLEAction.004" and the
   modifier still named "pole_builder" while the object is PILING and the
   node group is piling_builder — finish the naming law (rename modifier +
   re-path fcurves atomically, verify keys still apply frame-by-frame).
4. **.cache hygiene**: quarantined blue-era artifacts (trash-icons64-blue-
   donotuse etc.) and any other stale dirs in .cache/ford-factory and
   .cache/blender-post — archive to a dated /tmp tarball then delete.
5. **Pipeline README + journal**: after the tidying, reconcile the README's
   stage list with reality (any stages that changed since it was written).
6. **Sheet-stage status** (post Stage-B): the .cache sheet builder + sheets
   (piling-sheet/mask-sheet/shadow-sheet 768x576) now serve nothing game-side
   (the transition asset = the strips directly; the viewer decoratives are
   retired) — decide keep-as-pane-previews vs drop the stage.
7b. **bake.sh view hardening**: the view stage should abort if the window id
   is unchanged from a previous run (stale-window trap: a failed save stage
   leaves the old game window showing old state while "VIEW WINDOW ALIVE"
   can still be true from a survivor process).
7. **gen-textures.py legacy status**: the old procedural generator still
   exists and would regenerate the deleted pilings-exp/mask — mark it legacy
   or remove it in the tidying pass.

Rule for the whole pass: measure before changing, bit-hash before/after, one
candidate per commit-sized step, journal entry per candidate.
## STATUS 2026-10-22 (boards arc wrap)

- Items 1-3 above (the param-fcurve hygiene / legacy leftovers / action+modifier
  naming) TARGETED THE OLD HAND-BUILT ford-boards.blend. That file is GONE:
  ford-boards.blend is now regenerative BUILD OUTPUT (boards-builder.py,
  factory-empty, lattice layout, approved B pins) — no fcurves, no legacy
  objects, builder-clean names. ITEMS 1-3 = SUPERSEDED for ford-boards.
  (They stand for ford-posts.blend if that file's tidying is ever queued.)
- Item 4 (.cache hygiene) + the README reconcile = still standing.
- CLOSED (2026-10-22, session 3): the cobble family run (deck art shipped,
  22ed875 — wetpass masks look-approved with engine consumption shelved
  per the border ruling), the cobble recipes (Q2, 2c0ce4c), and the README
  reconcile (1.1.0 player-facing sections) — see journal.
- RELEASE-PACKAGING (moved out of this file; owned by the 1.1.0 release
  wrap): gallery images (04/05 grabbed), description/summary drafted, build
  green (strict-clean), publish go = the maintainer's,
  changelog date-stamp at publish.
