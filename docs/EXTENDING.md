# Extending Aria and creating future mashups

## Native records

Copy native-balance to a new example, change id and fields from tables.json, run
inspect/build/play. Native enemies include code pointers, drops, stats and soul
references; items/souls expose common balance/behavior fields. Start with assets
and behavior already loaded by the host. Table index is not inventory ID or an
guaranteed displayed name. Inspect values before editing.

## Abilities and enemy AI

Copy frame-counter, change id/C, keep linker origin 0x08680000 and use --compile.
Gate on state/room; initialize owned RAM; use configured input; implement a small
feature and preserve original behavior. Multiple features share one dispatcher.
Enemy/soul code replacement requires its own caller/signature audit; the frame
callback signature is not automatically valid there. Trace native grants/damage/
EXP routines rather than silently approximating them with counter writes.

## Level and campaign design

Current APIs replace entity/door arrays, preserving IDs/order. A new enemy can
require graphics/palette loading. Whole rooms need a geometry pipeline covering
layer records, compression/tiles/collision, resources, sizes, door destination
spawns, map/visited metadata, new-game placement and native save lookup. Validate
save/reload and traversal both ways after each topology step. The Mario example
proved that doors can work while saved room IDs are corrupt.

Do not append a fifth JSON room and loosen a guard. Generalize C loops, ABI/table
sizes, topology, geometry assumptions and map compiler together with new tests.
Preserve original map data for a full-castle extension; the example intentionally
clears it to create an isolated slice.

## Graphics and other games

Each importer needs a companion version/hash, source ranges, compression, tile
layout, palette interpretation, animation/sprite sizes and provenance. Verify bank
identity through live VRAM/OAM rather than assuming a static sheet. Decode assets
locally for investigation; do not ship them. Build a resource manager before
mixing arbitrary native/custom actors. Every game has different source offsets.

Keep companion extraction separate from original integration code. Both games
should contribute actual playable mechanics, not just labels or artwork. Start
with one small interaction and a native test scene. New-game, traversal, death,
menu, reentry and save behavior matter as much as a visible screenshot.

## Recommended engineering sequence

1. Generate native headers from the version profile and explicit resource claims.
2. Establish real item/soul grants, level-ups and lifecycle APIs through evidence.
3. Add native graphics/animation provisioning and exact collision semantics.
4. Build a full room/map/save compiler preserving the original campaign.
5. Add entity/ability dispatch contracts, then custom persistence/migration.
6. Add versioned companion modules/templates and packaging/client tests.

Split the legacy Mario tick into renderer/actors/pickups/host adapters only with
regression preservation. Its source/binary drift protection is less mature than
the generic callback compiler. Promote an API only when the native contract and
its tests are known, and keep working examples as regressions.

## Weapons/equipment milestone (2026-10-10)

Read [EQUIPMENT.md](EQUIPMENT.md) before equipment work. `aria/equipment.py` adds named selection, signed STR/CON/INT/LCK, preserved unknown flag bits and narrow validated edits. `examples/equipment-workshop/mod.json` is runnable. Native graphics/attack-family changes, new inventory slots and custom item effects remain extension work. The low-level table API stays unsigned.

## Enemy toolkit milestone (2026-10-10)

See [Enemy and encounter guide](ENEMIES.md) for all 113 named records, expected-value balance edits, named item drops, readable flags and conservative same-room moves/clones. `examples/enemy-workshop/mod.json` is playable; `scripts/verify_enemies.py` checks native stats, EXP, a real item drop, encounter traversal and return. Arbitrary AI, species/resource provisioning, soul reassignment and boss/event placement remain extension work.

## Ability milestone D

See [ABILITIES.md](ABILITIES.md) for the implemented native SDK and precise extension contracts. `aria/abilities.py` validates config/RAM/runtime selection; `native/abilities/` owns C modules, guards, ABI, linker and dependency fingerprints; `tests/test_abilities.py` covers contracts; `scripts/verify_abilities.py` verifies native behavior. The SDK uses the existing single hook. Custom mechanics remain trusted native code, with transient RAM and no custom SRAM schema.

## E: custom content

See [CUSTOM-CONTENT.md](CUSTOM-CONTENT.md) for supported source formats, exact native item-icon bindings, per-asset provenance/hashes, PNG authoring, PCM import limits, test fixtures and agent workflows. `aria/content.py` and `examples/content-workshop` provide the working layer; `tests/test_content.py` and `scripts/verify_content.py` cover codecs, bindings and actual native rendering. Sound playback and arbitrary sprite/animation allocation remain future contracts.
