# Rectangle terrain authoring — v0.20.0

Agents can now describe rectangular paints instead of manually enumerating native layout cells. `aria.terrain_plans.plan_terrain(rom, spec)` compiles them into the existing checked geometry-edit contract and stages a hypothetical result on an isolated clone. No GUI, arbitrary room registration, output ROM, new metatile generation or room resizing is performed by this planner.

## CLI and input

From the framework folder:

```powershell
.\TacticalSoul.cmd plan-terrain --spec examples/bridge-route/terrain-plan.json --out local/bridge-terrain-review.json
.\TacticalSoul.cmd build examples/bridge-route/mod.json
.\TacticalSoul.cmd play examples/bridge-route/mod.json
```

`plan-terrain` also accepts `--mod` to load a base mod before planning. Its image preimage must then match that patched image. Reports must be JSON under `local/`, preserve host/spec/manifest inputs, or go to stdout. The supplied example specification targets the exact unpatched original; omit `--mod` for it.

Schema 1 requires exactly `schema_version`, `expected_image_sha256`, `room: {sector, room}`, `layer`, `expected_layout_sha256`, `rectangles`. Both preimages must match the current in-memory image/layout. `rectangles` has 1–64 objects with exactly `x`, `y`, `width`, `height`, `value`. Positions and sizes are in 32-pixel metatile cells, not 8-pixel characters, screen pixels or castle-map cells. Values are existing native 16-bit layout descriptors; existing metatile ID is `value & 0x3FFF`. Preserve/understand layout flip flags when reusing descriptors.

Rectangles must be in bounds and non-overlapping, even if overlapping cells would be unchanged or painted identically. All integer fields reject booleans. Missing metatile IDs, stale preimages, invalid schema, unsupported rooms/layers and total no-ops fail. Unchanged cells inside a rectangle are omitted from the emitted edit; `painted_cells` includes them, while `changed_cells` counts actual differences. Partial no-ops are valid when another cell changes.

The compiled `geometry_edit` contains the room, layer, layout preimage and per-cell `expect`/`value` fields, suitable for a manifest's `geometry_edits` list. The report also contains input/proposed image SHA256, checked room reports, status `static_terrain_proposal` and scope. Native floor clearance, hazards, reachability and actor behavior are not established by a static report. Source image, ledger, allocations, cursors, profile and caller specification remain unchanged on success/failure.

## Supported write scope

The checked profile now registers main layer 0 in rooms `(0,3)`, `(0,6)`, `(0,31)` and `(0,5)`. All must remain type 2 and retain dimensions. The planner uses existing metatiles only; the lower-level geometry writer separately supports bounded appended definitions in registered rooms. Room5 registration establishes existing-asset terrain editing, not a new graphics import slot, all collision families, slopes authoring, moving platforms, alternate states or full campaign safety. Unsupported rooms continue to fail closed.

Registration evidence for room5: type-2 main layer, 2x2 screens / 16x16 cells, 247 metatiles including blank, exact lossless metadata/resource/layout roundtrip. Original layout SHA256 `6e2c412efa9cf9e196884c9cf757bfe91e743beeedb69e47735a9311a1324831`; visual SHA256 `bc3b91a069b956efa58c3287cae0f4fbb7ce8d8b86979bc45d652d20dfc72708`; collision SHA256 `3b68a5d6260b987d5f4129a102b373fd492994830e78bae9401be9abab5d4535`. The bridge reuses blank 0 and existing surface metatile 6, whose 16 collision bytes are all 03. No slope byte semantics are inferred.

## Bridge example and evidence

`examples/bridge-route/terrain-plan.json` clears x=2..13 across rows 3..4 and paints metatile 6 across row 5. This paints 36 cells and changes 22. It clears the central obstruction and creates a floor at y=160 between the existing upper endpoints; Soma settles to y=159. The compiled entry exactly matches the last geometry edit in the separately copied bridge-route manifest.

`verify_bridge_route.py` verifies the original source layout, visual/collision resources and castle-map bytes remain unchanged; only a copied layout/metadata/list chain is referenced by room5. The patched graph retains 343 nodes/725 doors, zero unresolved destinations and the original three edges without observed direct returns. It also checks every proposed neighbor endpoint matches between the final build and a separate native entry harness.

The harness redirects the hallway shortcut to room5 using its existing lower-left door record with an upper spawn. This is an explicit entry fixture, not proof of natural access to that branch from the playable campaign. After boot, there are no gameplay RAM writes. Right+B traverses the full bridge to room9; Left+B traverses room5 into room25; Right+B traverses it back into room9. Both complete crossing traces include world X below 64 and above 448 while active in room5. No position, velocity, HP, ability or collision manipulation is used for this native test.

The actual final build separately passes the three-room main-route new-game/save/fresh-continue/pause/forced-death/game-over/post-death-fresh-continue tests, including 400-pixel art checks in the save room/gallery. The forced HP death and initial hallway collision fixture remain declared in that existing lifecycle harness. This is not a single continuous neighbor-branch-to-save campaign proof; event/campaign access, map redesign, same-session game-over continue and physical hardware remain unverified.

## Agent extension workflow

1. Inspect the target room/resources and current capability registration. Do not silently add unsupported rooms to bypass checks.
2. Author rectangle plans against the intended image/layout hashes; preview/review the resulting checked cell edits before putting them in a manifest.
3. Combine terrain edits for each room into one entry and connections for each touched door array into one level batch. Separate repeated writes may conflict with the ledger/allocator.
4. Build a separate output, inspect graph deltas/shared resources and run native traversal. Keep bootstrap fixtures explicit and separate from the final manifest.
5. Test entry, both traversal directions, return, actors, collision clearance and relevant save/death/continue events. Document exactly what remains unsupported.

Important files: `aria/terrain_plans.py` (compilation/staging), `aria/geometry.py` (checked relocation), `framework/aos-usa-r0.json` (narrow registration), `aria/cli.py` (private output boundary), `tests/test_terrain_plans.py` (four private-host regression tests), `scripts/verify_bridge_route.py` (input-only bridge proof), `scripts/verify_geometry.py --bridge-route --lifecycle` (separate final-build lifecycle).


## v0.21 terrain discovery and living handoff

[Terrain support discovery](TERRAIN-SUPPORT.md) adds paginated main-layer diagnostics and loaded brush IDs. The original 343-slot survey finds 4 registered, 311 static candidates and 28 blocked rooms; candidates are not write grants. [Muse Spark 1.3 handoff](../handoffprompt.md) is mandatory reading and must be updated at the end of every turn. Use `scripts/update_handoff.py` to refresh its latest-status section, then refresh inventory/package.
