# Tactical Soul Framework handoff

Current original room-art pipeline: [ROOM-ASSETS.md](ROOM-ASSETS.md).

Current conversion scope and completion: [COMPLETION-ROADMAP.md](COMPLETION-ROADMAP.md). New terrain composition: [CUSTOM-TERRAIN.md](CUSTOM-TERRAIN.md).

Current room browser backend: [ROOM-CATALOG.md](ROOM-CATALOG.md).

Current renderer/editor entry points: [ROOM-PREVIEWS.md](ROOM-PREVIEWS.md) and [GUI-EDITOR-ROADMAP.md](GUI-EDITOR-ROADMAP.md).

Current custom-content entry points: [RESOURCE-AUTHORING.md](RESOURCE-AUTHORING.md) and [TOTAL-CONVERSIONS.md](TOTAL-CONVERSIONS.md). The first is implemented authoring; the second is the staged plan for remaining conversion systems.

This folder is independently usable: its own host original, Python, mGBA, Zig,
libretro core, original hook templates, examples, tools and documentation. New
framework work belongs here. No code/build path depends on the old root or the
separate Aria of Mario World project. Run TacticalSoul.cmd --help.

Begin with README.md; follow FILE-GUIDE -> NATIVE-INTEGRATION -> ROM-AND-RAM ->
DATA-CONTRACTS -> EXTENDING -> TESTING -> KNOWN-LIMITS -> FRAMEWORK-ROADMAP.
TOOLS.md records toolchain/source provenance. Shared historical documents explain
the Mario investigation: Mario-specific src/data/Launch paths live in that
separate project. Here, wrapper source provenance is src/hook-template.asm.

Working examples: native-balance edits actual native enemy, weapon and red-soul
records. frame-counter runs original Thumb code once per frame, independently
of Mario. See local/framework-verification.json for real-emulator evidence.
Default builds reuse fingerprint-verified counter code; --compile rebuilds it.
Output is build/mods/<id>/<id>.gba plus a mutation manifest and isolated saves.

Implemented versus planned APIs are listed in framework/capabilities.json.
Room entity/door APIs do not automatically rebuild graphics, geometry, maps or
save tables. A full-mod agent must implement those contracts before promising
arbitrary campaign redesign. The original Mario save failure demonstrated why.

Private original is USA revision 0, exact hash in COMPATIBILITY.md. Do not alter
hash gates. Local development folder contains commercial game data, so never
share the whole directory. The allowlist package excludes inputs/generated data.


## Existing-room milestone (2026-10-10)

See [ROOM-DESIGN.md](ROOM-DESIGN.md) for sparse entity moves, paired existing doors, map/save diagnostics, commands, test evidence and extension guidance. `aria/level.py` implements this layer; `examples/room-workshop/mod.json` is its runnable example. General geometry/collision authoring, map relocation and campaign-wide graph repair remain unimplemented; the narrow terrain milestone below is available.

## Weapons/equipment milestone (2026-10-10)

Read [EQUIPMENT.md](EQUIPMENT.md) before equipment work. `aria/equipment.py` adds named selection, signed STR/CON/INT/LCK, preserved unknown flag bits and narrow validated edits. `examples/equipment-workshop/mod.json` is runnable. Native graphics/attack-family changes, new inventory slots and custom item effects remain extension work. The low-level table API stays unsigned.

## Enemy toolkit milestone (2026-10-10)

See [Enemy and encounter guide](ENEMIES.md) for all 113 named records, expected-value balance edits, named item drops, readable flags and conservative same-room moves/clones. `examples/enemy-workshop/mod.json` is playable; `scripts/verify_enemies.py` checks native stats, EXP, a real item drop, encounter traversal and return. Arbitrary AI, species/resource provisioning, soul reassignment and boss/event placement remain extension work.

## Ability milestone D

See [ABILITIES.md](ABILITIES.md) for the implemented native SDK and precise extension contracts. `aria/abilities.py` validates config/RAM/runtime selection; `native/abilities/` owns C modules, guards, ABI, linker and dependency fingerprints; `tests/test_abilities.py` covers contracts; `scripts/verify_abilities.py` verifies native behavior. The SDK uses the existing single hook. Custom mechanics remain trusted native code, with transient RAM and no custom SRAM schema.

## E: custom content

See [CUSTOM-CONTENT.md](CUSTOM-CONTENT.md) for supported source formats, exact native item-icon bindings, per-asset provenance/hashes, PNG authoring, PCM import limits, test fixtures and agent workflows. `aria/content.py` and `examples/content-workshop` provide the working layer; `tests/test_content.py` and `scripts/verify_content.py` cover codecs, bindings and actual native rendering. Sound playback and arbitrary sprite/animation allocation remain future contracts.

## Named native resource milestone

[RESOURCE-AUTHORING.md](RESOURCE-AUTHORING.md) documents `aria/resources.py`, profile catalog, CLI export/diff, sparse tile/palette contracts, optional previews and new native examples/tests. [TOTAL-CONVERSIONS.md](TOTAL-CONVERSIONS.md) defines prerequisites and acceptance for room geometry, actors/animation, native audio, progression, campaign/save integration and release. This milestone adds native icon authoring, not a generic geometry/animation/audio engine.


## Room geometry foundation and project rename (2026-10-10)

The project is now **Tactical Soul Framework**, in its independent folder of the same name. Use `TacticalSoul.cmd`; `Dominance.cmd` and `Framework.cmd` remain aliases. See [rename compatibility](RENAMING.md) for environment variables and retained native ABI identifiers.

Read [ROOM-GEOMETRY.md](ROOM-GEOMETRY.md) before terrain work. `aria/compression.py` implements bounded LZ10/Aria resource reconstruction; `aria/geometry.py` inspects type-2 layers and applies checked, isolated existing-metatile edits. `inspect-geometry` and private `export-geometry` expose the source-backed format. `examples/geometry-workshop/mod.json` adds one stone step in the first hallway and composes the paired save-room route. Writes currently support only this registered main layer, unchanged dimensions and existing metatiles. New graphics, collision definitions, room resizing and full campaign compilation remain unimplemented.

Validation: 101 unit tests pass. `scripts/verify_geometry.py` passes eight structural/native checks: original walking reaches world X329, the edited step stops Soma at X311, native A jumping reaches X458, and fresh save/continue plus natural return stops at X360 on the other face. Initial comparisons declare a camera-relative X/zero-velocity fixture and retain settled Y; terrain is never injected into RAM. Private evidence stays in `local/geometry-verification.json`. See the geometry guide for format provenance, contracts, file responsibilities and next extensions.


## Static room previews and GUI editor goal

Read [ROOM-PREVIEWS.md](ROOM-PREVIEWS.md) for the implemented renderer, private PNG/atlas/report command, resource formats, API contracts and native evidence. `TacticalSoul.cmd preview-room 0 3 --out local/previews/hallway.png` works with bundled Python. Add `--mod examples/geometry-workshop/mod.json` to preview checked terrain edits. `aria/rendering.py` returns GUI-independent RGBA buffers; it does not modify ROM data. The atlas currently includes referenced metatiles only. Native checks match all eight graphics chunks, eight palette banks and 7,217 opaque wall pixels for baseline and edited rooms. The suite now has 111 tests.

[GUI-EDITOR-ROADMAP.md](GUI-EDITOR-ROADMAP.md) makes a graphical level editor an explicit goal and describes frontend/model boundaries, document/undo semantics, milestones and acceptance. No GUI, room catalog, layer compositor, complete brush catalog, inherited resources or 8bpp preview is implemented yet. Current source package: `release/Tactical-Soul-Framework-0.3.0.zip`. Update the inventory with `python scripts/update_inventory.py` before packaging. Native verification requires local development tools; normal previews do not.


## Room browser backend (v0.4)

[ROOM-CATALOG.md](ROOM-CATALOG.md) documents `aria/room_catalog.py` and `TacticalSoul.cmd room-catalog`: stable base-state slot IDs, bounded pagination, independent diagnostics and optional rendering checks. The shared room lookup now handles the final sector using the source-backed area-table end boundary. Full private audit covers 343 slots; twelve selected layers render. 122 unit tests pass. Catalog availability describes decoder support, not gameplay safety; terrain permissions are unchanged. Current source package: `release/Tactical-Soul-Framework-0.4.0.zip`. Next editor foundation: immutable editor documents and undo/redo, followed by a viewer frontend.


## Custom terrain and tracked completion (v0.5)

Read [CUSTOM-TERRAIN.md](CUSTOM-TERRAIN.md) for newly authored type-2 metatiles, explicit empty/solid collision, loaded-resource validation and isolated visual/collision streams. `examples/custom-terrain-workshop/mod.json` is runnable; `python scripts/verify_geometry.py --custom-terrain` verifies native pixels, walking, jumping, save/continue and return. All 127 unit tests pass. Original character/palette imports, VRAM allocation, other collision families and broader room writes remain unfinished.

[COMPLETION-ROADMAP.md](COMPLETION-ROADMAP.md) and `framework/roadmap.json` track the total-conversion scope and weighted maturity estimate (currently about 21%). A GUI application is deferred; work belongs in reusable framework APIs. At the end of every development turn, report progress/validation, next milestone and estimated framework completion. Next: original room graphics/palette imports with isolated load lists and explicit resource budgets. Current package: `release/Tactical-Soul-Framework-0.5.0.zip`.


## Original room artwork (v0.6)

[ROOM-ASSETS.md](ROOM-ASSETS.md) documents the registered original 4bpp/palette importer, isolated load lists, source/preimage guards, static VRAM/tilemap budgets and native evidence. `examples/original-room-art/mod.json` imports original neon-brick artwork and composes custom solid terrain with the save route. All 134 tests pass; native checks cover pixel identity, collision, jumping, fresh continue and exact resource reload on return. General VRAM ownership, other rooms, animation and death/pause/event coverage remain unfinished. Current package: `release/Tactical-Soul-Framework-0.6.0.zip`; tracked completion estimate is about 23%. Next: resource dependency/budget audits and broader native lifecycle support.


## Static dependencies and original-art lifecycle (v0.7)

[ROOM-RESOURCE-AUDIT.md](ROOM-RESOURCE-AUDIT.md) documents `audit-resources`, static all-metatile dependencies, budgets, narrow shared-list consumer scanning and the 343-slot survey. Unloaded memory observations are not import authorization. `python scripts/verify_geometry.py --room-art --lifecycle` adds verified native B pause cancellation, forced-HP death/Game Over and fresh continue from post-death SRAM with exact art reload on natural return. All 141 tests pass. No new writable/import room registrations were added. Current package: `release/Tactical-Soul-Framework-0.7.0.zip`; estimated weighted completion is about 24%. Next: resolve unsupported/inherited resources and validate another ordinary room before expanding permissions.


## Mixed resource inspection (v0.8.0)

See [MIXED-ROOM-RESOURCES.md](MIXED-ROOM-RESOURCES.md) for raw/LZ 4bpp and 8bpp load inspection, format guards, agent API contracts and remaining limitations. Full suite: 145 tests. Static survey: 343 slots, 6 rooms with load diagnostics. No additional write targets or 8bpp terrain rendering.


## Byte-index background inspection (v0.9.0)

See [BYTE-INDEX-BACKGROUNDS.md](BYTE-INDEX-BACKGROUNDS.md) for the separate read-only type-1/type-3 API and private lossless exports. All 24 native byte-index layers roundtrip; 149 tests pass. Rendering, collision semantics and write permissions remain pending. Existing type-2 consumers retain their contracts.


## Static background source rendering (v0.10.0)

See [BACKGROUND-RENDERING.md](BACKGROUND-RENDERING.md) for preview-background, 8bpp source APIs and native memory evidence. 153 tests; native character loads, declared palettes and a 1024-byte type-3 tilemap verified. Native viewport pixel matching remains unresolved; no new write permissions.


## Integrated background discovery (v0.11.0)

See [BACKGROUND-DISCOVERY.md](BACKGROUND-DISCOVERY.md) for catalog/audit schema version 2, format-aware dispatch and texel-derived palette dependencies. 156 tests; 925 nonempty layers inspect and all 24 byte-index source rasters render. No new write permissions or viewport verification. See [MODS-YOU-CAN-MAKE-NOW.md](MODS-YOU-CAN-MAKE-NOW.md) for current playable-mod examples and scoped agent prompts.


## Tilemap accounting and multiplayer feasibility (v0.12.0)

See [TILEMAP-MEMORY.md](TILEMAP-MEMORY.md) for corrected text/affine byte ranges and partial-chunk reservations, with 157 tests and native fixture evidence. No new write slots. See [MULTIPLAYER-FEASIBILITY.md](MULTIPLAYER-FEASIBILITY.md) for optional multiplayer research directions; no multiplayer feature is implemented.


## Bounded room-state discovery (v0.13.0)

See [ROOM-STATES.md](ROOM-STATES.md) for room-states, chain bounds/diagnostics and explicit empty-load observations. 161 tests. All 343 original base slots have zero alternate links; alternate chain behavior is synthetically tested, not natively certified. No new editing or multiplayer capability.


## Two-room original art (v0.14.0)

See [TWO-ROOM-ART.md](TWO-ROOM-ART.md) for hallway plus save-room registered main layers, contrasting original graphics/palettes, native entry/return/save/death/fresh-continue evidence and limits. Run examples/two-room-art/mod.json. Full suite: 163 tests. Current estimate: 25%. No arbitrary-room or multiplayer permission.


## Three-room original-art route (v0.15.0)

See [THREE-ROOM-ART.md](THREE-ROOM-ART.md) for registered room 0,6 plus hallway/save targets, native contrasting-resource route and lifecycle checks, effect-aware fixed-rectangle capture and campaign limits. Run examples/three-room-art/mod.json. 164 tests; current estimate 26%. No arbitrary-room registration or repaired full campaign graph.


## Static world graph (v0.16.0)

See [WORLD-GRAPH.md](WORLD-GRAPH.md) for world-graph, incoming/outgoing edges, observed direct returns and mod routing deltas. Three-room example: four displaced incoming links explicitly identified. 170 tests; no automatic repairs, progression certification or new room permissions. Current estimate: 26%.


## v0.17 connection proposals

See [Connection planning](CONNECTION-PLANNING.md) for the isolated existing-door planner, input/output contracts, four restored static return links, and required native landing verification. `plan-connections` emits review evidence only. Current completion remains 26%; 174 tests pass with the private supported host.


## v0.19 input replay foundation

[Input replay and checkpoints](INPUT-REPLAYS.md) documents bounded JSON input traces, boundary assertions, same-instance native forks and a 28-candidate room5 jump sweep. No candidate reached the continuous-route goal; this is not an impossibility proof. 180 unit tests pass. The original route examples and endpoint proof remain unchanged.


## v0.20 terrain authoring milestone

[Rectangle terrain authoring](TERRAIN-PAINTING.md) adds `plan-terrain`, checked room5 support and the separate bridge-route example. Input-only full bridge crossings pass in both directions; the final build separately passes main-route save/death/fresh-continue and art regression. 184 tests pass. Estimated framework completion is now 27%; prior milestone percentages are historical.


## v0.21 terrain discovery and living handoff

[Terrain support discovery](TERRAIN-SUPPORT.md) adds paginated main-layer diagnostics and loaded brush IDs. The original 343-slot survey finds 4 registered, 311 static candidates and 28 blocked rooms; candidates are not write grants. [Muse Spark 1.3 handoff](../handoffprompt.md) is mandatory reading and must be updated at the end of every turn. Use `scripts/update_handoff.py` to refresh its latest-status section, then refresh inventory/package.


## v0.22 project composition

[Source project composition](PROJECT-COMPOSITION.md) adds ordered terrain/route/art/data modules, early ownership errors, asset fingerprints, transactional project staging and `plan-project`. Build/play accept project JSON directly. The modular bridge example reproduces the flat build exactly; existing single-file manifests remain supported. 202 tests pass with the private host. Current maturity estimate: 29% (28.6/100). Update `handoffprompt.md` every turn before final delivery.


## v0.23 sprite structure backend

See [Sprite inspection](SPRITES.md) for `aria/sprites.py`, registered common/Julius/background-bats resources, bounded frames/parts/hitboxes/animations, and lossless fixed-record checks. Run `TacticalSoul.cmd inspect-sprite common`. 209 tests pass with the private host. This is read-only: actor rendering/replacement and real Soma animation binding remain unfinished. Next: registered page/palette resolution and static sprite previews, then native original-art replacement. Completion remains 29%; this prerequisite does not complete sprite authoring.


## v0.24 static sprite previews

[Sprite guide](SPRITES.md) documents `aria/sprite_rendering.py`, explicit page/palette registrations, packed 8x8 source addressing, transparent RGBA composition, source bank selection, bounds and origin contracts. `TacticalSoul.cmd preview-sprite julius --frame 0 --out local/sprite-previews/julius-0.png` works with bundled Python. `scripts/verify_sprites.py` covers all 216 registered frames and creates private contact sheets; source releases exclude those images. 222 tests pass. Static previews do not prove native OAM/resource ownership or permit sprite writes. Next: verified native consumer binding and one checked original-art replacement. Completion: 29% (29.1/100).


## v0.25 original native sprite artwork

[Sprite authoring](SPRITE-AUTHORING.md) documents `aria/sprite_assets.py`, the fixed shared bats/clouds page/palette, guarded compressed relocation, transaction/source protection, original `examples/sky-invaders` content and native evidence. Run `TacticalSoul.cmd play examples/sky-invaders/mod.json`; `preview-sprite` and `inspect-sprite` now accept `--mod`. `scripts/verify_sprite_assets.py --lifecycle` verifies final-example native entry/pause/reentry and a separate composed save/death/fresh-continue harness. 234 tests pass. Completion: 30% (30.0/100). Next: one ordinary enemy visual binding and combat lifecycle, plus checked project-module sprite composition. Read [REA workflow](REA-WORKFLOW.md): user requires the skill and connected MCP for binary investigation; skill installed locally, MCP not registered/exposed here.
