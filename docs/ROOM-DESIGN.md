# Existing-room level foundation

Read this before designing rooms with Tactical Soul Framework. This milestone edits actual Aria of Sorrow room records and runs the resulting separate ROM in bundled mGBA. It is a working foundation for future level tools, not a geometry or collision editor.

## Quick start

From this project folder in PowerShell:

```powershell
.\TacticalSoul.cmd inspect --room 0 3
.\TacticalSoul.cmd export-room 0 3 --out local/hallway.json
.\TacticalSoul.cmd audit-room 0 31
.\TacticalSoul.cmd build examples/room-workshop/mod.json
.\TacticalSoul.cmd inspect --room 0 3 --mod examples/room-workshop/mod.json
.\TacticalSoul.cmd audit-room 0 31 --mod examples/room-workshop/mod.json
.\TacticalSoul.cmd play examples/room-workshop/mod.json
```

`--host` selects the verified original. Inspection with `--mod` applies the manifest in memory; do not pass a patched ROM as the host because the exact-original fingerprint deliberately rejects it. Export is a discovery snapshot, not an automatically importable level file. Build outputs are in `build/mods/room-workshop/`. The adjacent manifest records every mutation and static room audit. Keep saves per mod.

## Example and authoring contract

`examples/room-workshop/mod.json` moves the first hallway enemy (entity ID 3) from (128,176) to (192,176), and candle ID 4 from (256,128) to (320,128). It connects the hallway right door (sector 0, room 3, door 2) to the existing sanctuary left door (sector 0, room 31, door 0). Both directions are written together.

A manifest may include `room_edits` with `moves` and `connections`. See the example for exact JSON. Each move requires `room: {sector, room}`, `entity_id`, `from: [x,y]`, and `to: [x,y]`. IDs identify existing records, independent of loading order. `from` is a mandatory coordinate precondition. Positions are pixels within the main layer screen dimensions, each screen 256 pixels. Entity identity, subtype, resources and parameters are preserved. Types 1,3,4,5,6 can be moved. Type 2 scripted/save/warp/special objects cannot be moved through this interface. Moving a record does not guarantee its graphics or floor collision will behave at the new location.

Each connection has `a` and `b`. Each endpoint requires `room`, zero-based existing `door`, and `spawn: [x,y]`. An endpoint's spawn is where the player arrives **in that endpoint's room**, not where its outgoing door lands. Opposite boundary sides are required: left/right or up/down. A door cannot be used twice. Self-room loops and new door creation are unsupported. Native auxiliary destination coordinates are reset to zero; validate scroll behavior in the emulator, especially vertical connections.

Unknown properties fail. Out-of-bounds positions, missing or duplicate entity IDs, changed preconditions, invalid boundary doors and reused endpoints fail. `room_edits` cannot combine with raw `patches`, `entity_lists` or `door_lists`; that prevents lower-level writes from invalidating the audit. Native table edits and a frame hook may accompany it. On any exception discard the in-memory ROM; the CLI writes output only after a successful build.

## Map and save semantics

The main map is 64 by 47 u16 records at 0x08116650. Room ownership occupies sector bits 6..9 and room bits 0..5. Bit 15 marks save rooms; 0xFFFF is blank. The map line nibble bank begins at 0x08117DD0. Room map origin is packed in metadata at offset 32. This API leaves geometry, map origins, both map banks, graphics and original room scripts intact. It explicitly compares both map banks before and after editing.

The audit reports layer dimensions, map ownership across the rectangular footprint, save marker ownership, duplicate entity IDs, destination spawn bounds and whether each destination has a direct return door. Native irregular rooms/overlapping map footprints can produce warnings; those are not automatically corruption. A native save statue is special entity type 2/subtype 28. It must have an owned map save marker. Builds reject newly introduced audit errors relative to the original touched rooms; preexisting errors are retained in `baseline_errors` for review. A clean audit cannot prove collision, landing, event progression or save compatibility.

The example is intentionally a **nonadjacent shortcut**. Minimap positions remain in their original locations. Original neighboring rooms retain their old exits; rewiring two endpoints does not repair every incoming edge elsewhere in the castle. Do not use this example to claim the full campaign graph is coherent. Before a campaign release, inventory every incoming/outgoing door, decide how to repair displaced neighbors, and test progression and saves. Map relocation, room creation, geometry compilation and campaign-wide graph repair remain extension points.

## Engineering path for the next agent

`aria/rooms.py` parses native structures and allocates replacement arrays. `aria/level.py` adds sparse edits, pairing and audits. `aria/cli.py` validates manifests, applies edits, and exposes inspection/build/play. `aria/core.py` enforces ROM version, bounds, preimages, allocation and overlap tracking. Keep gameplay logic out of the manifest parser. Add new capabilities in small independently testable modules with explicit address provenance and format documentation.

First inspect an original room and compare its records with the copied DSVEdit reference material under `tools/references`. Never infer a new native field from one successful screenshot. For geometry work, document layer dimensions, compressed layout formats, tileset/palette ownership, collision types and camera boundaries before writing them. For new actors, establish graphics/resource dependencies and native behavior parameters before adding a type/subtype. For a campaign editor, build a complete door graph and map ownership model before changing room identities. For every milestone, include a minimal playable example and a reproducible emulator check.

## Verification

`tests/test_level.py` tests rejection cases and structural invariants against a locally supplied original (skips if absent). `scripts/verify_rooms.py` exercises the workshop through native mGBA gameplay, captures arrival/return/save evidence and checks original/map preservation. It requires system Python with Pillow and the local libretro DLL. These private test artifacts are excluded from distribution. General hardware behavior, all vertical doors, all room types and the full campaign are not certified.

## Enemy-toolkit integration

`apply_level_edits(rom, spec, enemy_encounters=())` now stages named enemy moves/clones alongside ordinary room moves and door pairs. Each touched entity array is written once. See ENEMIES.md for the exact encounter schema and original-resource/clone restrictions. Existing room-only manifests keep the same behavior/output.


## Room geometry foundation and project rename (2026-10-10)

The project is now **Tactical Soul Framework**, in its independent folder of the same name. Use `TacticalSoul.cmd`; `Dominance.cmd` and `Framework.cmd` remain aliases. See [rename compatibility](RENAMING.md) for environment variables and retained native ABI identifiers.

Read [ROOM-GEOMETRY.md](ROOM-GEOMETRY.md) before terrain work. `aria/compression.py` implements bounded LZ10/Aria resource reconstruction; `aria/geometry.py` inspects type-2 layers and applies checked, isolated existing-metatile edits. `inspect-geometry` and private `export-geometry` expose the source-backed format. `examples/geometry-workshop/mod.json` adds one stone step in the first hallway and composes the paired save-room route. Writes currently support only this registered main layer, unchanged dimensions and existing metatiles. New graphics, collision definitions, room resizing and full campaign compilation remain unimplemented.

Validation: 101 unit tests pass. `scripts/verify_geometry.py` passes eight structural/native checks: original walking reaches world X329, the edited step stops Soma at X311, native A jumping reaches X458, and fresh save/continue plus natural return stops at X360 on the other face. Initial comparisons declare a camera-relative X/zero-velocity fixture and retain settled Y; terrain is never injected into RAM. Private evidence stays in `local/geometry-verification.json`. See the geometry guide for format provenance, contracts, file responsibilities and next extensions.


## Static world graph (v0.16.0)

See [WORLD-GRAPH.md](WORLD-GRAPH.md) for world-graph, incoming/outgoing edges, observed direct returns and mod routing deltas. Three-room example: four displaced incoming links explicitly identified. 170 tests; no automatic repairs, progression certification or new room permissions. Current estimate: 26%.
