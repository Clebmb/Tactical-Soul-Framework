# Authored project composition — v0.22.0

A source project assembles ordered JSON modules into one ordinary checked mod manifest. Agents can keep terrain, routes, balance edits and room artwork in separate files without repeatedly patching the same room array. Build/play and existing `--mod` inspection commands accept a project file directly. Single-file manifests keep their existing behavior.

## Run the example

```powershell
.\TacticalSoul.cmd plan-project examples/bridge-project/project.json --out local/bridge-project-plan.json
.\TacticalSoul.cmd build examples/bridge-project/project.json
.\TacticalSoul.cmd play examples/bridge-project/project.json
.\TacticalSoul.cmd world-graph --mod examples/bridge-project/project.json --out local/project-graph.json
```

The five-module example produces exactly the same ROM, patch ledger, allocation addresses and cursors as `examples/bridge-route/mod.json`: SHA256 `bbe3d4b0cc80eee76bec1c77322050caf4547b9641c4e450457bbf22fe7fe840`. It is a new authoring structure, not new native behavior. The earlier native bridge/main-route evidence applies to these identical bytes; this release does not claim a new campaign/native run.

## Source project and module contracts

A project has exactly required `schema_version: 1`, `kind: "tsf-project"`, safe lowercase `id`, and `modules`, plus optional text `description`. Modules are 1–64 ordered relative JSON file paths. Each source/project JSON is bounded to 2 MiB. Example:

```json
{
  "schema_version": 1,
  "kind": "tsf-project",
  "id": "my-conversion",
  "modules": ["modules/terrain.json", "modules/routes.json", "modules/art.json"]
}
```

Modules are ordinary schema-1 manifest-shaped objects with their own unique safe lowercase IDs, optional descriptions and any of these fields: `geometry_edits`, `room_edits`, `room_assets`, `sprite_assets`, `enemy_encounters`, `enemy_edits`, `equipment_edits`, `table_edits`, `resource_edits`. The composed manifest gets the project's ID/description; module metadata is retained as source provenance, not emitted as game records. Unknown fields, duplicate module paths/IDs and invalid list shapes fail.

Currently excluded from projects: frame hooks, registered abilities, general content imports, raw patches, blobs and full entity/door-list replacements. Sprite asset modules are supported since v0.26 (see below); the remaining excluded features stay available through ordinary single-file manifests. Exclusion prevents silently ambiguous payload/compilation ownership while this first composition contract is narrow. Nested projects, optional/disabled modules, dependency solvers, overrides and parameter substitution are not implemented.

Module order is declarative merge order, **not sequential patch execution**. Domain application still uses the existing manifest writer's fixed order: tables/balance/rooms/assets/geometry as defined in `apply_manifest_data`. Module B cannot use a post-module-A layout preimage or overwrite A's cell by being later. Different list orders may alter allocation order, so preserve authored ordering when comparing golden builds.

## Room batching and conflicts

Geometry entries with the same sector/room/layer merge into one edit at the first occurrence of that group. They must share the same source layout hash. Cells append in module/entry order. Duplicate cell coordinates fail even if replacement values match; the error names both module owners. Each group can have at most one custom-metatile-definition provider; IDs are not automatically renumbered. Ordinary geometry validation still checks descriptor IDs, preimages, coordinates, definitions, registration and resource constraints.

All `room_edits.moves` and `room_edits.connections` append into one combined level batch, so each touched door/entity array is relocated once by the existing writer. Reused door endpoints and repeated moves for the same room/entity identity fail early with both module IDs. Spawn alignment, opposing sides and target bounds remain the domain writer's responsibility. Encounters also use the combined level writer; cross-domain entity/encounter conflicts are not universally diagnosed at composition time.

Other supported list fields append in module order. Their existing domain writers and patch ledger catch record/resource conflicts; early module ownership diagnostics are currently specific to geometry cells, metatile providers, door endpoints and entity moves. Do not promise every error will identify both modules. A plan/build failure is preferable to silently overriding another module.

## Assets, fingerprints and confinement

Module paths resolve within the project folder. Room asset `graphics_source`/`palette_source` and sprite asset `source`/`palette_source` resolve within the owning module's folder; parent escapes, absolute paths and resolved symlinks outside the scope reject. Put reusable authored JSON assets below that folder. Composition remaps those payload paths to the project-root-relative namespace before normal installation. No assets are copied/generated by the composer itself. Duplicate sprite resource names across modules fail early naming both owners; the sprite installer still requires exactly one entry in the composed manifest, so multi-resource projects await a future multi-entry writer.

Reports include the source project SHA256, ordered module IDs/relative paths/SHA256 values, and sorted referenced room-asset and sprite-asset file paths/SHA256 values. This makes the source set reviewable; it is not a lockfile or concurrent-edit snapshot. Do not edit source inputs during a build. Include/exclude unused files is not a distribution license audit. No commercial payload bytes are emitted by the composition report.

## API and transactional application

`aria.projects.compose_project(path)` returns `{manifest, report}` without loading/mutating a ROM or writing a generated manifest. It validates the supported composition structure and resolves source payloads. It does not replace domain validation or certify gameplay.

`aria.cli.apply_manifest(rom, path)` detects `kind: tsf-project`, composes it, clones the complete ROM state, and calls `apply_manifest_data(staged, manifest, project_folder, compile_requested)`. After every domain/ledger check succeeds, it commits the staged object's state into the supplied ROM object and attaches `project_report`. Any failure before commit leaves source image bytes, ledger, allocations, cursors and profile unchanged. A late geometry-preimage failure after room edits is explicitly tested. The original host is never changed. References held separately to the old mutable data/ledger objects are not updated in place; use the ROM object's attributes after a successful commit.

Ordinary single-file manifest application retains its previous semantics; transactional application is a project feature. `apply_manifest_data` is the shared lower-level writer with an explicit confined payload folder. Do not call it directly as a way to bypass composition or conflict guards.

`plan-project` loads the exact host, stages the project on an isolated clone and emits schema-1 JSON: status `staged_not_gameplay_certified`, input/proposed image hashes, source provenance, patch count and allocations. It writes no ROM. Reports must be under `local/` with `.json` suffix and preserve host/project/module/asset inputs. A project stored inside `local/` still cannot overwrite its own modules/assets with the report. Build/play also reject output ROM/report paths that would overwrite those source inputs.

## Example files and extension points

`examples/bridge-project/project.json` lists:

1. `modules/showcase-terrain.json`: three existing original-art room edits.
2. `modules/bridge-left.json`: first eleven room5 bridge cells.
3. `modules/bridge-right.json`: remaining eleven cells; merged with the prior module into one room5 write.
4. `modules/routes.json`: all four paired connections (eight endpoints) in one batch.
5. `modules/art.json`: three original-art loads, with six authored JSON payloads under `modules/assets/`.

The result has four terrain batches, 25 changed terrain cells total and 58 ledger writes. Source artwork remains original framework-authored MIT content; commercial room tiles are reused from the private host without extraction into the release.

Important files: `aria/projects.py`, `aria/cli.py`, `tests/test_projects.py` (thirteen source-only cases and three private-host cases), `scripts/verify_projects.py`, this guide and the examples. `scripts/verify_projects.py` also checks that the composed `examples/sky-invaders/project.json` reproduces the flat sprite reskin bytes exactly. Native tests are not necessary for byte-identical composition; new authored content still needs the relevant native checks. Source-only tests create temporary directories under `local/project-tests/` for sandbox compatibility.

Next extensions should establish explicit payload/compilation ownership before adding hooks/abilities/content modules, and typed cross-domain conflict/dependency diagnostics before inventing override semantics. For total-conversion progress, also prioritize original sprite/frame/animation provisioning; project composition does not solve native graphics, audio, event or save contracts.
