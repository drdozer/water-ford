# Water Ford — dependency audit

Written 2026-10-15, against the devctl-managed installs (`vanilla` = Factorio/base
**2.0.77**, `dlc` = **2.1.21**) and the dependency zips present in the dlc install
(`cargo-ships_2.1.8`, `pyalienlife_3.1.8` + its py closure).

The mod was written declaring "latest everything" (`factorio_version: "2.1"`,
`base >= 2.1.0`). This audit asks what it *actually* requires, feature by feature.

---

## 1. TL;DR

| Declaration today | Verdict |
|---|---|
| `factorio_version = "2.1"` | **Correct and already minimal** for the 2.1 series. The engine matches `factorio_version` against the game's major.minor **exactly** (verified both directions below), so no single zip can serve 2.0 and 2.1. |
| `base >= 2.1.0` | Correct/minimal **within** the 2.1 series (base versions track the game series). |
| Code itself | **Contains no 2.1-only API.** Empirically loads on 2.0.77 with only the two info.json lines changed (test below). |
| `? cargo-ships >= 2.1.8` | Advisory only — no code references cargo-ships. Keep as a known-good pin. |
| `? pyalienlife >= 3.1.8` | The real integration. Its recipe items come via pyalienlife's **hard** deps (see §4). Keep the known-good pin. |

**If 2.0 reachability is ever wanted:** the code needs zero changes — only
`factorio_version: "2.0"` + `base >= 2.0.0` in info.json, as a separate release
(a branch, since one zip = one minor series).

---

## 2. The `factorio_version` gate is exact (empirically verified)

- **2.1.21 rejects a mod declaring `"2.0"`**: documented in the superproject's
  `docs/testing.md` §3 — `Incompatible Factorio version (current: 2.1, required: 2.0)`.
- **2.0.77 rejects a mod declaring `"2.1"`**: reproduced with the hermetic probe
  (`.cache/water-ford-2.0-probe/`, see `docs/testing.md` for the recipe) — the mod
  fails to load at the version check.

Portal consequence: a `2.1`-declared mod is invisible to 2.0 clients, and vice
versa. One zip serves exactly one minor series.

---

## 3. Every API touchpoint, and the version that introduced it

### data.lua (item + recipe + technology)

| Touchpoint | Min version | Note |
|---|---|---|
| `place_as_tile.condition = {layers = {water_tile = true}}` | 2.0 | CollisionMask-object form; vanilla 2.0.77 `base/prototypes/item.lua` uses the identical shape. (1.1 used string tile-group conditions.) |
| `place_as_tile.invert = true` | 2.0 | Survives the 2.0.77 dump intact (verified). |
| typed ingredients `{type = "item", name = …}` | 1.1 | Not a gate. |
| `localised_name` / `localised_description` | 1.1 | Not a gate. |
| technology `unit` block | 1.1 | Not a gate. |

### data-final-fixes.lua (tile)

| Touchpoint | Min version | Note |
|---|---|---|
| `data.raw.tile["water-shallow"]` clone | **2.0** | water-shallow/water-mud ship with base 2.0 (Nauvis rework; not a later 2.0.x patch — official 2.0.34 changelog touches them as existing base tiles). On 1.1 this deepcopy would nil-crash: this is the hard floor. |
| `collision_mask = {layers = {…}}` | 2.0 | 1.1 used string arrays (`{"water-tile", …}`). |
| `tile.fluid`, `is_foundation`, `ambient_sounds`, `default_cover_tile` | 2.0 (all present in 2.0.77 base) | Verified in `vanilla`'s `data/base/prototypes/tile/tiles.lua`. |
| `water_transition_group_id` global | 2.0.77-verified; guarded `or 1` anyway | Defined by base `tiles.lua` in both installs. |
| `to_tiles` incl. `"water-wube"` | 2.0 | **Not dead config**: water-wube is the Factorio-logo easter-egg tile, defined in `base/prototypes/entity/factorio-logo.lua` in *both* 2.0.77 and 2.1.21. |

### control.lua (placement guard)

| Touchpoint | Min version | Note |
|---|---|---|
| `on_player_built_tile` fields `tile`, `item`, `quality` | 2.0 | All three listed in the 2.0 (stable) runtime docs; `quality` shipped with the 2.0 quality system. |
| `on_robot_built_tile`, `set_tiles`, `create_local_flying_text`, `insert` | 1.1 | Not a gate. |

**Conclusion: the entire mod runs against the 2.0.0 feature set.** Nothing in the
code needs 2.1.

---

## 4. Empirical floor test (2.0.77, vanilla install)

Hermetic probe per `docs/testing.md` (`--mod-directory` + `-c`, base+water-ford only):

1. Probe copy declaring `"2.1"` / `base >= 2.1.0` on 2.0.77 → **rejected** (version gate).
2. Probe copy with only info.json changed to `"2.0"` / `base >= 2.0.0` →
   `--dump-data` **exit 0**; dump inspection confirms the ford tile fully intact:
   `layer 9` / `layer_group water`, collision mask `{water_tile, resource, floor}`,
   `effect = water`, both transition rules (out-of-map + the piling rule, group 1),
   `place_as_tile` with `invert`, technology present.

So: **the only thing standing between this mod and 2.0 support is two info.json lines.**

---

## 5. The py branch: where the ingredients actually come from

The py integration gates on `mods["pyalienlife"]`, but the recipe's items and the
tech prerequisite live in **sibling py mods** — reached only through pyalienlife's
hard dependencies (verified in the dlc install's zips):

| Recipe/tech token | Defined by | Reachable because pyalienlife hard-depends on |
|---|---|---|
| `treated-wood` | **pycoalprocessing** (`prototypes/items/items.lua`) | `pycoalprocessing >= 3.1.0` |
| `log` | **pycoalprocessing** | `pycoalprocessing >= 3.1.0` |
| `gravel` | **pycoalprocessing** | `pycoalprocessing >= 3.1.0` |
| `bolts` | **pypetroleumhandling** (`ITEM` def; every other py mention is an ingredient use) | `pypetroleumhandling >= 3.1.0` |
| technology `creosote` | **pycoalprocessing** (`prototypes/technologies/creosote.lua`) | `pycoalprocessing >= 3.1.0` |

pyalienlife 3.1.8's own info.json: `factorio_version: 2.1`, `base >= 2.1.20`,
hard deps `pyrawores >= 3.1.0`, `pypetroleumhandling >= 3.1.0`,
`pycoalprocessing >= 3.1.0` (plus `~ pypostprocessing` and the graphics packs).

Consequences worth knowing:

- The py branch is only reachable on **Factorio 2.1.20+** (pyalienlife's own
  bounds) — 2.0 players would always get the vanilla branch. Consistent with the
  optional-dep design.
- Installing "just pyalienlife" drags in the coal/petroleum/raw-ores suite, so the
  closure is sound today. If a future py reorganization moved any of these items,
  the ford recipe would crash the data stage — the audit doc is the map for
  re-checking.
- `? pyalienlife >= 3.1.8` is a **known-good pin**, not a derived minimum (the
  items are ancient, stable py content). Py releases move in lockstep; keep the pin.

---

## 6. Recommendations

1. **Keep `factorio_version = "2.1"` and `base >= 2.1.0`** for the release line.
   They are already minimal for the series the mod is developed and played in
   (caravans + cargo-ships + py all live on 2.1).
2. **Optional:** cut a `2.0` release for stable-branch players — a `factorio-2.0`
   branch carrying only the two-line info.json delta, cherry-picked from master
   per release. Zero code divergence expected (the tile config is
   version-agnostic by construction).
3. Keep both optional deps as known-good pins; document the item-provenance map
   (§5) in the mod's AGENTS.md so a py refactor gets caught at review, not at
   runtime.
