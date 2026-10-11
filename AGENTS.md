# Tactical Soul Framework agent instructions

This is the independent host-only Aria framework. Start with README.md and
docs/START-HERE.md, then FILE-GUIDE, NATIVE-INTEGRATION, ROM-AND-RAM,
DATA-CONTRACTS, EXTENDING, TESTING and KNOWN-LIMITS. Full mod creation is the goal;
this is a working foundation, not a completed graphical/campaign editor.

Use TacticalSoul.cmd inspect/build/play. No Mario companion is required. Do not
introduce a dependency on the sibling Mario project or legacy parent folder.
Native code edits require --compile and tests. Preserve exact-host SHA-256 gate,
immutable original inputs, collision/resource constraints and separate outputs.
Typed record APIs do not establish every field's native semantic/call signature.
Document newly established ABIs, evidence, limitations and regression checks.

The local .gba is a private player copy. Never package it, generated games,
extracted commercial assets, saves, private paths or credentials. Use the
allowlist packager. Original code is MIT, third-party licenses remain separate.
No external upload or public publishing is authorized by this local copying task.
The earlier Mario archive upload was rejected; do not retry it without explicit
approval of that exact payload and destination.


## Existing-room milestone (2026-10-10)

See [Room design guide](docs/ROOM-DESIGN.md) for sparse entity moves, paired existing doors, map/save diagnostics, commands, test evidence and extension guidance. `aria/level.py` implements this layer; `examples/room-workshop/mod.json` is its runnable example. General geometry/collision authoring, map relocation and campaign-wide graph repair remain unimplemented; the narrow terrain milestone below is available.

## Weapons/equipment milestone (2026-10-10)

Read [docs/EQUIPMENT.md](docs/EQUIPMENT.md) before equipment work. `aria/equipment.py` adds named selection, signed STR/CON/INT/LCK, preserved unknown flag bits and narrow validated edits. `examples/equipment-workshop/mod.json` is runnable. Native graphics/attack-family changes, new inventory slots and custom item effects remain extension work. The low-level table API stays unsigned.

## Enemy toolkit milestone (2026-10-10)

See [Enemy and encounter guide](docs/ENEMIES.md) for all 113 named records, expected-value balance edits, named item drops, readable flags and conservative same-room moves/clones. `examples/enemy-workshop/mod.json` is playable; `scripts/verify_enemies.py` checks native stats, EXP, a real item drop, encounter traversal and return. Arbitrary AI, species/resource provisioning, soul reassignment and boss/event placement remain extension work.

## Native ability SDK (D)

Read [Ability SDK guide](docs/ABILITIES.md) for the registered dispatcher, JSON settings, input edges, conservative state guards, RAM claims, custom runtime copies and agent extension workflow. Run `TacticalSoul.cmd play examples/ability-workshop/mod.json` for passive regeneration and an R-button heal with MP cost/cooldown. Single-feature examples are `examples/still-regen` and `examples/focus-heal`. Custom save schemas, native grants and input consumption remain extension work.

## E: custom content foundation

Read [Custom content guide](docs/CUSTOM-CONTENT.md). `aria/content.py` imports indexed 4bpp tiles, RGB555 palettes and signed PCM, with checked replacement/allocation/pointer contracts. `examples/content-workshop/mod.json` replaces native item icons with original diamonds and composes healing abilities. Native icon rendering is verified. WAV samples are imported only; sound playback, music/voice linkage and arbitrary sprite animations remain unimplemented.

## Named resources and total-conversion direction

Read [RESOURCE-AUTHORING.md](docs/RESOURCE-AUTHORING.md) for named native icon pages/palettes, private exports, authored diffs, sparse edits, previews and important files. Use `TacticalSoul.cmd content-catalog`; runnable examples are `named-content-workshop` and `sparse-content-workshop`. Read [TOTAL-CONVERSIONS.md](docs/TOTAL-CONVERSIONS.md) for the staged engineering/acceptance plan. Full campaign geometry, general sprite animation and native audio playback remain unfinished. Native exports/diffs stay under local/ and must not enter source release examples.


## Room geometry foundation and project rename (2026-10-10)

The project is now **Tactical Soul Framework**, in its independent folder of the same name. Use `TacticalSoul.cmd`; `Dominance.cmd` and `Framework.cmd` remain aliases. See [rename compatibility](docs/RENAMING.md) for environment variables and retained native ABI identifiers.

Read [ROOM-GEOMETRY.md](docs/ROOM-GEOMETRY.md) before terrain work. `aria/compression.py` implements bounded LZ10/Aria resource reconstruction; `aria/geometry.py` inspects type-2 layers and applies checked, isolated existing-metatile edits. `inspect-geometry` and private `export-geometry` expose the source-backed format. `examples/geometry-workshop/mod.json` adds one stone step in the first hallway and composes the paired save-room route. Writes currently support only this registered main layer, unchanged dimensions and existing metatiles. New graphics, collision definitions, room resizing and full campaign compilation remain unimplemented.

Validation: 101 unit tests pass. `scripts/verify_geometry.py` passes eight structural/native checks: original walking reaches world X329, the edited step stops Soma at X311, native A jumping reaches X458, and fresh save/continue plus natural return stops at X360 on the other face. Initial comparisons declare a camera-relative X/zero-velocity fixture and retain settled Y; terrain is never injected into RAM. Private evidence stays in `local/geometry-verification.json`. See the geometry guide for format provenance, contracts, file responsibilities and next extensions.


## Static room previews and GUI editor goal

Read [ROOM-PREVIEWS.md](docs/ROOM-PREVIEWS.md) for the implemented renderer, private PNG/atlas/report command, resource formats, API contracts and native evidence. `TacticalSoul.cmd preview-room 0 3 --out local/previews/hallway.png` works with bundled Python. Add `--mod examples/geometry-workshop/mod.json` to preview checked terrain edits. `aria/rendering.py` returns GUI-independent RGBA buffers; it does not modify ROM data. The atlas currently includes referenced metatiles only. Native checks match all eight graphics chunks, eight palette banks and 7,217 opaque wall pixels for baseline and edited rooms. The suite now has 111 tests.

[GUI-EDITOR-ROADMAP.md](docs/GUI-EDITOR-ROADMAP.md) makes a graphical level editor an explicit goal and describes frontend/model boundaries, document/undo semantics, milestones and acceptance. No GUI, room catalog, layer compositor, complete brush catalog, inherited resources or 8bpp preview is implemented yet. Current source package: `release/Tactical-Soul-Framework-0.3.0.zip`. Update the inventory with `python scripts/update_inventory.py` before packaging. Native verification requires local development tools; normal previews do not.


## Room browser backend (v0.4)

[ROOM-CATALOG.md](docs/ROOM-CATALOG.md) documents `aria/room_catalog.py` and `TacticalSoul.cmd room-catalog`: stable base-state slot IDs, bounded pagination, independent diagnostics and optional rendering checks. The shared room lookup now handles the final sector using the source-backed area-table end boundary. Full private audit covers 343 slots; twelve selected layers render. 122 unit tests pass. Catalog availability describes decoder support, not gameplay safety; terrain permissions are unchanged. Current source package: `release/Tactical-Soul-Framework-0.4.0.zip`. Next editor foundation: immutable editor documents and undo/redo, followed by a viewer frontend.


## Custom terrain and tracked completion (v0.5)

Read [CUSTOM-TERRAIN.md](docs/CUSTOM-TERRAIN.md) for newly authored type-2 metatiles, explicit empty/solid collision, loaded-resource validation and isolated visual/collision streams. `examples/custom-terrain-workshop/mod.json` is runnable; `python scripts/verify_geometry.py --custom-terrain` verifies native pixels, walking, jumping, save/continue and return. All 127 unit tests pass. Original character/palette imports, VRAM allocation, other collision families and broader room writes remain unfinished.

[COMPLETION-ROADMAP.md](docs/COMPLETION-ROADMAP.md) and `framework/roadmap.json` track the total-conversion scope and weighted maturity estimate (currently about 21%). A GUI application is deferred; work belongs in reusable framework APIs. At the end of every development turn, report progress/validation, next milestone and estimated framework completion. Next: original room graphics/palette imports with isolated load lists and explicit resource budgets. Current package: `release/Tactical-Soul-Framework-0.5.0.zip`.


## Original room artwork (v0.6)

[ROOM-ASSETS.md](docs/ROOM-ASSETS.md) documents the registered original 4bpp/palette importer, isolated load lists, source/preimage guards, static VRAM/tilemap budgets and native evidence. `examples/original-room-art/mod.json` imports original neon-brick artwork and composes custom solid terrain with the save route. All 134 tests pass; native checks cover pixel identity, collision, jumping, fresh continue and exact resource reload on return. General VRAM ownership, other rooms, animation and death/pause/event coverage remain unfinished. Current package: `release/Tactical-Soul-Framework-0.6.0.zip`; tracked completion estimate is about 23%. Next: resource dependency/budget audits and broader native lifecycle support.


## Static dependencies and original-art lifecycle (v0.7)

[ROOM-RESOURCE-AUDIT.md](docs/ROOM-RESOURCE-AUDIT.md) documents `audit-resources`, static all-metatile dependencies, budgets, narrow shared-list consumer scanning and the 343-slot survey. Unloaded memory observations are not import authorization. `python scripts/verify_geometry.py --room-art --lifecycle` adds verified native B pause cancellation, forced-HP death/Game Over and fresh continue from post-death SRAM with exact art reload on natural return. All 141 tests pass. No new writable/import room registrations were added. Current package: `release/Tactical-Soul-Framework-0.7.0.zip`; estimated weighted completion is about 24%. Next: resolve unsupported/inherited resources and validate another ordinary room before expanding permissions.


## Mixed resource inspection (v0.8.0)

See [docs/MIXED-ROOM-RESOURCES.md](docs/MIXED-ROOM-RESOURCES.md) for raw/LZ 4bpp and 8bpp load inspection, format guards, agent API contracts and remaining limitations. Full suite: 145 tests. Static survey: 343 slots, 6 rooms with load diagnostics. No additional write targets or 8bpp terrain rendering.


## Byte-index background inspection (v0.9.0)

See [docs/BYTE-INDEX-BACKGROUNDS.md](docs/BYTE-INDEX-BACKGROUNDS.md) for the separate read-only type-1/type-3 API and private lossless exports. All 24 native byte-index layers roundtrip; 149 tests pass. Rendering, collision semantics and write permissions remain pending. Existing type-2 consumers retain their contracts.


## Static background source rendering (v0.10.0)

See [docs/BACKGROUND-RENDERING.md](docs/BACKGROUND-RENDERING.md) for preview-background, 8bpp source APIs and native memory evidence. 153 tests; native character loads, declared palettes and a 1024-byte type-3 tilemap verified. Native viewport pixel matching remains unresolved; no new write permissions.


## Integrated background discovery (v0.11.0)

See [BACKGROUND-DISCOVERY.md](docs/BACKGROUND-DISCOVERY.md) for catalog/audit schema version 2, format-aware dispatch and texel-derived palette dependencies. 156 tests; 925 nonempty layers inspect and all 24 byte-index source rasters render. No new write permissions or viewport verification. See [MODS-YOU-CAN-MAKE-NOW.md](docs/MODS-YOU-CAN-MAKE-NOW.md) for current playable-mod examples and scoped agent prompts.


## Tilemap accounting and multiplayer feasibility (v0.12.0)

See [TILEMAP-MEMORY.md](docs/TILEMAP-MEMORY.md) for corrected text/affine byte ranges and partial-chunk reservations, with 157 tests and native fixture evidence. No new write slots. See [MULTIPLAYER-FEASIBILITY.md](docs/MULTIPLAYER-FEASIBILITY.md) for optional multiplayer research directions; no multiplayer feature is implemented.


## Bounded room-state discovery (v0.13.0)

See [ROOM-STATES.md](docs/ROOM-STATES.md) for room-states, chain bounds/diagnostics and explicit empty-load observations. 161 tests. All 343 original base slots have zero alternate links; alternate chain behavior is synthetically tested, not natively certified. No new editing or multiplayer capability.


## Two-room original art (v0.14.0)

See [TWO-ROOM-ART.md](docs/TWO-ROOM-ART.md) for hallway plus save-room registered main layers, contrasting original graphics/palettes, native entry/return/save/death/fresh-continue evidence and limits. Run examples/two-room-art/mod.json. Full suite: 163 tests. Current estimate: 25%. No arbitrary-room or multiplayer permission.


## Three-room original-art route (v0.15.0)

See [THREE-ROOM-ART.md](docs/THREE-ROOM-ART.md) for registered room 0,6 plus hallway/save targets, native contrasting-resource route and lifecycle checks, effect-aware fixed-rectangle capture and campaign limits. Run examples/three-room-art/mod.json. 164 tests; current estimate 26%. No arbitrary-room registration or repaired full campaign graph.


## Static world graph (v0.16.0)

See [WORLD-GRAPH.md](docs/WORLD-GRAPH.md) for world-graph, incoming/outgoing edges, observed direct returns and mod routing deltas. Three-room example: four displaced incoming links explicitly identified. 170 tests; no automatic repairs, progression certification or new room permissions. Current estimate: 26%.


## v0.17 connection proposals

See [Connection planning](docs/CONNECTION-PLANNING.md) for the isolated existing-door planner, input/output contracts, four restored static return links, and required native landing verification. `plan-connections` emits review evidence only. Current completion remains 26%; 174 tests pass with the private supported host.


## v0.18 native endpoint evidence

[Native connection testing](docs/NATIVE-CONNECTION-TESTING.md) documents four controlled bidirectional crossings, settled landings and movement checks. Independent endpoint position fixtures are explicit; continuous room5 traversal and repaired-campaign lifecycle remain pending. The planner remains static-only; existing playable examples are unchanged.


## v0.19 input replay foundation

[Input replay and checkpoints](docs/INPUT-REPLAYS.md) documents bounded JSON input traces, boundary assertions, same-instance native forks and a 28-candidate room5 jump sweep. No candidate reached the continuous-route goal; this is not an impossibility proof. 180 unit tests pass. The original route examples and endpoint proof remain unchanged.


## v0.20 terrain authoring milestone

[Rectangle terrain authoring](docs/TERRAIN-PAINTING.md) adds `plan-terrain`, checked room5 support and the separate bridge-route example. Input-only full bridge crossings pass in both directions; the final build separately passes main-route save/death/fresh-continue and art regression. 184 tests pass. Estimated framework completion is now 27%; prior milestone percentages are historical.


## REA skill and MCP (explicit user request)

For ROM/native-binary reverse engineering, use the installed reverse-engineer-anything skill and prefer connected REA MCP tools. Read [REA workflow](docs/REA-WORKFLOW.md) and the required REA section in handoffprompt.md. The skill exists on this host; REA MCP is not registered/exposed at the v0.25 handoff. Do not claim otherwise or invent REA evidence. Follow the skill's diagnostics and setup approval rules if connection repair is needed; continue independent source/local-native work. Ordinary Python repository edits do not require binary analysis tooling.

## Living handoff requirements

Read [handoffprompt.md](handoffprompt.md), addressed to Muse Spark 1.3. At the end of every generation/turn, update that exact file before final response; never skip it, including documentation/planning turns. Preserve standing instructions and replace latest status with actual changes, checks, blockers and next work. Refresh inventory/package after the final handoff edit. Every final response reports progress, next steps, roadmap percentage, current mod examples and that the handoff was updated. On `continue`, make concrete autonomous progress toward the full framework; do not merely repeat a narrow investigation.


## v0.22 project composition

[Source project composition](docs/PROJECT-COMPOSITION.md) adds ordered terrain/route/art/data modules, early ownership errors, asset fingerprints, transactional project staging and `plan-project`. Build/play accept project JSON directly. The modular bridge example reproduces the flat build exactly; existing single-file manifests remain supported. 202 tests pass with the private host. Current maturity estimate: 29% (28.6/100). Update `handoffprompt.md` every turn before final delivery.


## v0.23 sprite structure backend

See [Sprite inspection](docs/SPRITES.md) for `aria/sprites.py`, registered common/Julius/background-bats resources, bounded frames/parts/hitboxes/animations, and lossless fixed-record checks. Run `TacticalSoul.cmd inspect-sprite common`. For files under docs/, the guide is `SPRITES.md`. 209 tests pass with the private host. This is read-only: actor rendering/replacement and real Soma animation binding remain unfinished. Next: registered page/palette resolution and static sprite previews, then native original-art replacement. Completion remains 29%; this prerequisite does not complete sprite authoring.


## v0.24 static sprite previews

[Sprite guide](docs/SPRITES.md) documents `aria/sprite_rendering.py`, explicit page/palette registrations, packed 8x8 source addressing, transparent RGBA composition, source bank selection, bounds and origin contracts. `TacticalSoul.cmd preview-sprite julius --frame 0 --out local/sprite-previews/julius-0.png` works with bundled Python. `scripts/verify_sprites.py` covers all 216 registered frames and creates private contact sheets; source releases exclude those images. 222 tests pass. Static previews do not prove native OAM/resource ownership or permit sprite writes. Next: verified native consumer binding and one checked original-art replacement. Completion: 29% (29.1/100).


## v0.25 original native sprite artwork

## v0.37 viewer contracts with room-viewer wiring

`aria/viewer.py` is the headless data backend for a future viewer:
viewport math, room view models with markers and cropped pixels, plus
document views proven over two clean builds (real-manifest hallway
proof). See [viewer contracts](docs/VIEWER.md). Authoring 2.9→3.1.
265 tests pass. Completion: 32% (31.7/100). Next: deeper native
authoring (campaign/event slices, audio binding, grant APIs).

## v0.36 document-driven room previews

`preview_document` renders a room layer from a document's manifest state
(two clean builds, two renders, identical pixels required) — the headless
equivalent of `preview-room --mod` for documents. See [editor
documents](docs/EDITOR-DOCUMENTS.md). Authoring 2.7→2.9. 260 tests pass.
Completion: 32% (31.5/100). Next: viewer contracts with a first
room-viewer wiring.

## v0.35 clean-rebuild application of documents

`build_from_document` proves identical rebuilds from two clean images
(covered `sprite_assets` path, 2 ledger entries) and rejects
nondeterministic appliers. See [editor
documents](docs/EDITOR-DOCUMENTS.md). Authoring 2.5→2.7. 258 tests pass.
Completion: 31% (31.3/100). Next: viewer contracts, real-manifest
preview wiring.

## v0.34 authored-change diffs and manifest IO

Editor documents gain `changes_since_saved()` review records plus
`save_manifest`/`load_manifest_state` canonical JSON round-trips.
See [editor documents](docs/EDITOR-DOCUMENTS.md). Authoring 2.4→2.5.
256 tests pass. Completion: 31% (31.1/100). Next: preview/build
application of documents and viewer contracts.

## v0.33 immutable editor documents with undo/redo

`aria/editor_docs.py` is the headless editor foundation (no GUI):
immutable states, bounded history, stable fingerprints, dirty/save
round-trips, 6 synthetic tests. See [editor
documents](docs/EDITOR-DOCUMENTS.md). Authoring 2.2→2.4. 254 tests pass.
Completion: 31% (31.0/100). Next: document-to-manifest authoring and
viewer contracts.

## v0.32 spawn-anchored twin negative

`scripts/attribute_spawn_events.py` (private) kill-then-respawns the
hallway walker and twin-diffs the EWRAM-observed spawn window on the
original vs the magenta diagnostic: spawn frame 8 thrice, world-x 35,
control deterministic, zero diffs pre and post. The page is not rendered
at the hallway spawn moment either. 248 tests pass. See [enemy
binding](docs/ENEMY-BINDING.md). Next: other rooms/actors. Completion:
31% (30.8/100).

## v0.31 reusable attribution; hallway Soma-art negative

`aria/sprite_attribution.py` is a reusable snapshot-anchored diff library
(synthetic tests; no OAM-map dependence) now used by
`scripts/trace_sprite_consumers.py`. The post-kill Soma-only hallway scene
still shows zero diffs, so page `0x08635990` is neither walker nor Soma art
here. 248 tests pass. See [enemy binding](docs/ENEMY-BINDING.md). Next:
spawn-event diffs, other rooms/actors. Completion: 31% (30.7/100).

## v0.30 walker twin-run negative; player/enemy attribution corrected

`scripts/trace_sprite_consumers.py` repoints all three copies of page
`0x08635990` at one solid index-1 stream and twin-runs hallway
idle/walk/fight-contact/kill with verified determinism: zero differing
pixels, zero magenta rendered, although diagnostic art reaches VRAM. No
walker writer ships. Kinematics (world-minus-OAM pinned at 32;
cross-room persistence) show tracked bank-0 entries follow Soma, and a
full manual render matches 0/2320 snapshot pixels, so OAM-map reads are
untrusted for render attribution. v0.29 stands as art-content identity
only; render proof withdrawn. 244 tests pass. See [enemy
binding](docs/ENEMY-BINDING.md). Next: snapshot-anchored attribution,
other rooms, Soma-art hypothesis. Completion: 31% (30.6/100).

## v0.29 walker art source identified; premature zombie registration corrected

A read-only live capture (`scripts/dump_walker_source.py`: hallway OAM
tiles + OBJ bank-0 palette, zero RAM writes) plus static analysis identified
walker art content: actor table `0x080E13C0` (32×12B rows), row 8
(palette `0x0820B164`, graphics struct `0x0823199C`, 12-frame part lists),
LZ art page `0x08635990` (tiles at decoded offsets `0x1600`–`0x1BA0`)
and raw top-half tiles at `0x08166D18`-family. v0.30 corrects the render
half: tracked bank-0 entries follow Soma, and the page twin-run names no
consumer — art-content identity only, no rendered proof. The v0.28 "not any LZ page"
claim was a residency-vs-content comparison error (live OAM bases are zero
padding). A premature `zombie` registration is withdrawn for cause (live
palette/art mismatch; its pools belong to Arachne create plus helpers) and
renamed `unknown-actor-2`; its writer entry is removed, bats stays the only
production resource. 248 tests pass; 272 frames render. See [enemy
binding](docs/ENEMY-BINDING.md). Done in v0.30: the page twin-run names no
consumer and the render proof is withdrawn (30.6/100).

## v0.28 tracer verdict and raw writer infrastructure

A deterministic magenta twin-run tracer disproves hallway zombie use of the
v0.27 candidate page (zero differing pixels across idle/fight/kill/sweep
scenes); the registration is renamed `unknown-actor` and no enemy writer
exists. `aria/sprite_assets.py` is registry-driven with synthetically tested
raw in-place replacement; bats stays the only production resource. 240 tests
pass. Completion: 30% (30.5/100). See [enemy binding](docs/ENEMY-BINDING.md).

## v0.27 enemy binding discovery (read-only)

See [enemy binding](docs/ENEMY-BINDING.md) for the actor resource table, the single-referenced zombie spawn-candidate entry (raw page, 1-bank palette, 21-frame struct), native OAM tracking (moving bank-0 zombie vs static bank-10 Soma), the HP-zero kill fixture and the open walker-source question. `inspect-sprite unknown-actor` works with the true palette; 238 tests pass and all 237 registered frames render. No enemy writer exists: hallway combat proves the walker uses none of the candidate sources. Next: loader trace plus zombie-pinned capture, then a checked reskin writer. Completion: 30% (30.4/100).

## v0.26 composed sprite projects

[Project composition](docs/PROJECT-COMPOSITION.md) now accepts `sprite_assets` modules with confined source rebasing, asset fingerprints and duplicate-resource ownership errors. `examples/sky-invaders/project.json` reproduces the flat reskin bytes exactly (SHA256 `3b17a2fd90da7c332d0181c66da55583432d56b1a3013af3378ae9ed4b02f1bd`); shared art lives under `modules/assets/`. 238 tests pass. Static pointer-occurrence counts (common 77/90, Julius 7, bats 2/2) scope the next enemy-binding investigation without proving consumers. Completion: 30% (30.2/100). REA MCP is connected but rejects GBA ROMs as unsupported; see [REA workflow](docs/REA-WORKFLOW.md).

[Sprite authoring](docs/SPRITE-AUTHORING.md) documents `aria/sprite_assets.py`, the fixed shared bats/clouds page/palette, guarded compressed relocation, transaction/source protection, original `examples/sky-invaders` content and native evidence. Run `TacticalSoul.cmd play examples/sky-invaders/mod.json`; `preview-sprite` and `inspect-sprite` now accept `--mod`. `scripts/verify_sprite_assets.py --lifecycle` verifies final-example native entry/pause/reentry and a separate composed save/death/fresh-continue harness. 234 tests pass. Completion: 30% (30.0/100). Next: one ordinary enemy visual binding and combat lifecycle, plus checked project-module sprite composition. Read [REA workflow](docs/REA-WORKFLOW.md): user requires the skill and connected MCP for binary investigation; skill installed locally, MCP not registered/exposed here.
