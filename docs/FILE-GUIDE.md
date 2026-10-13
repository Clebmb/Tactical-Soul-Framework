# File guide and dependency map

Paths are relative to each project root. Code derives roots from __file__ or
PSScriptRoot; generated absolute paths are evidence, not configuration.

## Tactical Soul Framework core

| File | Responsibility | Change rule |
|---|---|---|
| Framework.cmd | Find bundled Python, invoke scripts/aria_tool.py | Forwards all arguments |
| scripts/aria_tool.py | Add root to sys.path for isolated embedded Python | Needed because embedded Python excludes cwd |
| aria/__main__.py | python -m aria alternative | Standard Python entrypoint |
| aria/core.py | Hash gate, bounded writes, overlap ledger, aligned allocation | Central binary safety layer |
| aria/tables.py | Native enemy/item/soul field edits | Layouts in framework/tables.json |
| aria/rooms.py | Native room lookup and entity/door array replacement | Sorting/identity preserved; graphics/map separate |
| aria/hooks.py | One after-update Thumb callback | Exact-version ABI; original wrapper template |
| aria/compiler.py | Zig compilation and source/linker/bin fingerprint | --compile after code edits |
| aria/cli.py | Inspect/build/play orchestration | Separate output plus mutation report |
| framework/aos-usa-r0.json | Hash, symbols, allocation/hook regions | A new version requires a fresh audit |
| framework/tables.json | Table addresses/counts/strides/field widths | Storage facts, not complete semantic validation |
| examples/native-balance/mod.json | Host-only enemy, weapon and soul changes | No Mario or compiled code needed |
| examples/frame-counter/ | Original callback C/linker/bin/manifest/fingerprint | Demonstrates native code independent of Mario |
| runtime/hook.bin, entry.bin | Original trampoline templates | Provenance from src/hook.asm, no commercial art |
| tests/test_framework.py | Synthetic safety tests | Runs without commercial ROMs |
| scripts/verify_framework.py | Native record checks and real emulator smoke tests | Host, Pillow, local libretro DLL |

## Mario example

| File | Responsibility | Important dependency |
|---|---|---|
| data/design.json | Agreed design/scope | Descriptive, not a runtime parser |
| data/rooms.json | Four ordered rooms and custom objects | Fixed topology/ABI; not arbitrary castle authoring |
| data/enemies.json | Goomba/Koopa balance and declared behavior | C implements behavior; selected numeric fields loaded |
| data/powerups.json | Flower balance and declared semantics | Selected numeric fields loaded; C controls lifecycle |
| data/assets.json | SMA2 source offsets/provenance | Contains no extracted graphics |
| src/runtime.c | Actors, renderer, pickups, approximate collision/combat | Reads native state; calls host damage routine |
| src/hook.asm | Thumb entry trampoline/after-update wrapper | Opens build/AriaOfMarioWorld.gba |
| src/link.ld | Runtime origin/sections | Must match wrapper/ROM reservation |
| scripts/build.py | Verify originals; rebuild rooms/map/imports/tables; compile/apply runtime | Default uses runtime binaries; --compile uses Zig/armips |
| runtime/runtime.bin | Original compiled Mario logic | Must match C/generated ABI |
| Launch.cmd / Launch.ps1 | Select/remember originals, build and start mGBA | local/copies.json is private |
| scripts/inspect_roms.py | Header and original room inventory | Outputs local/rom-inspection.json |
| scripts/emulator.py | libretro ctypes callbacks, controls, memory, captures | Pillow + DLL; serial use |
| scripts/playtest.py | Exploratory controller sequence and helpers | Diagnostic prints; not all assertions |
| scripts/verify.py | Fourteen actual-emulator checks | Explicit fixtures and limitations |
| scripts/package.py | ROM-free allowlist ZIP with app/ prefix | Include notices; exclude build/local |
| melty.json | Managed ROM/install/launch recipe | Static checks pass; actual client launch untested |

## Private and generated files

- Root *.gba: private originals, read only and SHA-256 verified.
- build/*.gba and build/mods/: generated games, never distribute.
- build/generated.h: derived C ABI/fixed-ROM macros, not editable source.
- build/runtime.elf: compiler output useful for symbols/disassembly.
- build/manifest.json: hash/status, not proof of gameplay.
- local/*.png: actual emulated frames and research captures.
- local/*verification.json: run-specific evidence and fixture descriptions.
- local/copies.json: private absolute original paths, never package.
- release/: allowlist archives/staging; a ZIP is not filtered by .gitignore.
- tools/: compilers/runtimes/research checkouts; licenses remain separate.

A working development folder with copied commercial ROMs is not distributable.
Never zip a whole working project. Original integration code is MIT; Nintendo
and Konami assets and third-party runtime licenses remain distinct.


## Existing-room milestone (2026-10-10)

See [ROOM-DESIGN.md](ROOM-DESIGN.md) for sparse entity moves, paired existing doors, map/save diagnostics, commands, test evidence and extension guidance. `aria/level.py` implements this layer; `examples/room-workshop/mod.json` is its runnable example. General geometry/collision authoring, map relocation and campaign-wide graph repair remain unimplemented; the narrow terrain milestone below is available.

## Equipment files

| File | Responsibility |
|---|---|
| aria/equipment.py | Local English label lookup, keys, catalog, signed fields, validated edits and reports |
| framework/equipment.json | Editable semantic fields, global ID bases, effect labels and attack-family labels |
| examples/equipment-workshop/mod.json | Starting Knife/clothes tradeoffs plus edited Cape |
| tests/test_equipment.py | Flag and private-host contracts, range/precondition/identity/resource protection |
| scripts/verify_equipment.py | Native stat/menu/combat/save checks with declared inventory and route fixtures |
| docs/EQUIPMENT.md | Complete authoring contract, native IDs/formats, evidence, limitations and extension path |

Full equipment catalogs exported under local/ are private derived data, excluded from packages. No embedded commercial name/description bank is required for the source distribution.

## Enemy files

| File | Responsibility |
|---|---|
| aria/text.py | Shared bounded English labels from immutable original; no dialogue writer |
| aria/enemies.py | Named enemy catalog, native item-drop IDs, balance/flag/drop preconditions and edit reports |
| aria/encounters.py | Immutable original-room evidence, native-code checks, move/clone plans and audits |
| framework/enemies.json | Editable fields, reference flag meanings, protected placements and clone templates |
| aria/level.py | Shared staging and one entity relocation per touched room, including encounter operations |
| examples/enemy-workshop/ | Native Zombies/Skeletons and composed hallway shortcut example |
| tests/test_enemies.py | Native ID/drop/range/unknown-field and placement contracts, plus standalone flag test |
| scripts/verify_enemies.py | Controller-only native stats/EXP/drop/encounter/return checks |
| docs/ENEMIES.md | Complete contract, format facts, evidence, limitations and custom-AI/resource roadmap |

Equipment delegates label reading to aria/text.py. Catalog exports and native captures stay under local/ and are excluded from distribution.

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


## v0.18 native endpoint evidence

[Native connection testing](NATIVE-CONNECTION-TESTING.md) documents four controlled bidirectional crossings, settled landings and movement checks. Independent endpoint position fixtures are explicit; continuous room5 traversal and repaired-campaign lifecycle remain pending. The planner remains static-only; existing playable examples are unchanged.


## v0.19 input replay foundation

[Input replay and checkpoints](INPUT-REPLAYS.md) documents bounded JSON input traces, boundary assertions, same-instance native forks and a 28-candidate room5 jump sweep. No candidate reached the continuous-route goal; this is not an impossibility proof. 180 unit tests pass. The original route examples and endpoint proof remain unchanged.


## v0.20 terrain authoring milestone

[Rectangle terrain authoring](TERRAIN-PAINTING.md) adds `plan-terrain`, checked room5 support and the separate bridge-route example. Input-only full bridge crossings pass in both directions; the final build separately passes main-route save/death/fresh-continue and art regression. 184 tests pass. Estimated framework completion is now 27%; prior milestone percentages are historical.


## v0.21 terrain discovery and living handoff

[Terrain support discovery](TERRAIN-SUPPORT.md) adds paginated main-layer diagnostics and loaded brush IDs. The original 343-slot survey finds 4 registered, 311 static candidates and 28 blocked rooms; candidates are not write grants. [Muse Spark 1.3 handoff](../handoff.md) is mandatory reading and must be updated at the end of every turn. Use `scripts/update_handoff.py` to refresh its latest-status section, then refresh inventory/package.


## v0.22 project composition

[Source project composition](PROJECT-COMPOSITION.md) adds ordered terrain/route/art/data modules, early ownership errors, asset fingerprints, transactional project staging and `plan-project`. Build/play accept project JSON directly. The modular bridge example reproduces the flat build exactly; existing single-file manifests remain supported. 202 tests pass with the private host. Current maturity estimate: 29% (28.6/100). Update `handoff.md` every turn before final delivery.


## Campaign reachability

`aria/campaign_audit.py` consumes the static world graph to report start-relative
reachability, shortest required routes and observed returns. CLI: `audit-campaign`.
`tests/test_campaign_audit.py` covers synthetic graphs and private nonmutation.
See [Campaign audit contracts](CAMPAIGN-AUDIT.md).
`aria/campaign_progression.py`, `tests/test_campaign_progression.py` and
`examples/progression-policy/` add bounded authored flag-state exploration.
See [Progression policies](PROGRESSION-POLICIES.md); no native events are written.

## Audio source reconstruction helpers

`aria/audio_synthesis.py` contains the bounded sampled ADSR reference model;
`tests/test_audio_synthesis.py` covers it and event timing regressions.
It also provides checked signed PCM resampling, loop seams and independent
envelope clocks; diagnostic WAVs and the song renderer stay under `local/`.
`aria/audio.py:resolve_note_voice` adds checked direct/rhythm instrument lookup;
`tests/test_audio_voices.py` covers synthetic child-bank/pitch/pan and rejection cases.
`tests/test_audio_ties.py` covers TIE/EOT events and `gate_tied_events` diagnostic
gate conversion in `aria/audio_synthesis.py`.
See [audio provenance and limits](AUDIO-RECON.md). No native audio writer.

## v0.23 sprite structure backend

See [Sprite inspection](SPRITES.md) for `aria/sprites.py`, registered common/Julius/background-bats resources, bounded frames/parts/hitboxes/animations, and lossless fixed-record checks. Run `TacticalSoul.cmd inspect-sprite common`. 209 tests pass with the private host. This is read-only: actor rendering/replacement and real Soma animation binding remain unfinished. Next: registered page/palette resolution and static sprite previews, then native original-art replacement. Completion remains 29%; this prerequisite does not complete sprite authoring.


## v0.24 static sprite previews

[Sprite guide](SPRITES.md) documents `aria/sprite_rendering.py`, explicit page/palette registrations, packed 8x8 source addressing, transparent RGBA composition, source bank selection, bounds and origin contracts. `TacticalSoul.cmd preview-sprite julius --frame 0 --out local/sprite-previews/julius-0.png` works with bundled Python. `scripts/verify_sprites.py` covers all 216 registered frames and creates private contact sheets; source releases exclude those images. 222 tests pass. Static previews do not prove native OAM/resource ownership or permit sprite writes. Next: verified native consumer binding and one checked original-art replacement. Completion: 29% (29.1/100).


## v0.25 original native sprite artwork

[Sprite authoring](SPRITE-AUTHORING.md) documents `aria/sprite_assets.py`, the fixed shared bats/clouds page/palette, guarded compressed relocation, transaction/source protection, original `examples/sky-invaders` content and native evidence. Run `TacticalSoul.cmd play examples/sky-invaders/mod.json`; `preview-sprite` and `inspect-sprite` now accept `--mod`. `scripts/verify_sprite_assets.py --lifecycle` verifies final-example native entry/pause/reentry and a separate composed save/death/fresh-continue harness. 234 tests pass. Completion: 30% (30.0/100). Next: one ordinary enemy visual binding and combat lifecycle, plus checked project-module sprite composition. Read [REA workflow](REA-WORKFLOW.md): user requires the skill and connected MCP for binary investigation; skill installed locally, MCP not registered/exposed here.

- `aria/native_events.py`, `scripts/verify_native_events.py`: read-only transient modal bit and controller-driven lifecycle proof; see [native events](NATIVE-EVENTS.md).

- `scripts/verify_soul_progression.py`: native first red-soul acquisition/save/continue evidence, using a private existing-door redirect; no soul-grant ABI.

- `aria/progression_traces.py`: bounded image-bound authored-policy versus observed-checkpoint comparison; see [progression traces](PROGRESSION-TRACES.md).

- `examples/soul-gate/`, `scripts/verify_soul_gate.py`: standalone narrow native ownership barrier and unowned/owned lifecycle evidence; no general lock API.

- `examples/soul-gate-abilities/`: custom SDK runtime combining the fixed barrier and healing with unchanged ABI/RAM claims; native checks use `scripts/verify_soul_gate.py --composed`.

- `scripts/verify_soul_menu.py`: deterministic private soul-name label twins and native first red-soul MP-cost proof; no production soul-label/grant writer.

- `aria/souls.py`, `examples/soul-cost/`, `scripts/verify_soul_cost.py`: checked named first red-soul mana-cost edits with native acceptance; see [soul authoring](SOULS.md).

- `aria/music.py`, `docs/BOOT-MELODY.md`, `examples/boot-melody/`: checked original one-shot boot melody and native acceptance.

- `docs/MUSIC-SAMPLES.md`, `examples/imported-melody/`, `scripts/verify_imported_melody.py`: original WAV linkage and native controls.

- `docs/MUSIC-LIFECYCLE.md`, `scripts/verify_music_lifecycle.py`: original boot instrument scene takeover, native twins and passive control.
