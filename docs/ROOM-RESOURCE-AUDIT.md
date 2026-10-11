# Static room resource dependencies and lifecycle evidence

This backend milestone audits a room's loaded BG character chunks, palette banks, tilemap ranges and every type-2 metatile's dependencies. It helps agents diagnose resource availability before authoring larger mods. It does not assign global VRAM ownership, authorize new import slots, add writable rooms or implement a GUI.

## Commands and API

```powershell
.\TacticalSoul.cmd audit-resources 0 3 --out local/audits/hallway.json
.\TacticalSoul.cmd audit-resources 0 3 --include-consumers --out local/audits/hallway-consumers.json
.\TacticalSoul.cmd audit-resources 0 3 --mod examples/original-room-art/mod.json --out local/audits/original-art.json
```

Host selection and optional in-memory manifest application match existing commands. `--out` is optional; omitted prints JSON, provided requires a `.json` under framework `local/` and preserves host/manifest files. Generated reports describe private game resources and should remain local. This command audits all three layer slots.

Python callers use `aria.room_resources.audit_room_resources(rom, sector, index, include_consumers=False)` with a verified image. It returns JSON-compatible data, does not allocate, write ROM bytes or modify the ledger, and has no GUI/image-library dependency. Invalid room/API options raise; unsupported load or layer data produces independent diagnostics.

## Result contract

Schema version 1 includes current in-memory image SHA-256, room identity/address, source load records, tilemap ranges, diagnostics, per-layer dependencies and a budget report. Stable browser IDs remain the room catalog's responsibility.

| Field | Meaning |
|---|---|
| `graphics`, `palettes` | Resolved source/load mappings from existing bounded readers |
| `tilemaps` | All active layers' half-open BG memory intervals |
| `budget.loaded_character_bytes` | Distinct final loaded 2KB character chunks × 2048 |
| `budget.loaded_palette_bytes` | Distinct loaded sixteen-color banks × 32 |
| `budget.character_tilemap_overlaps` | Static character loads intersecting an active tilemap range |
| `budget.static_unloaded_non_tilemap_chunks` | BG chunks absent from final static loads and known tilemaps; null if load/range observations failed |
| `budget.static_unloaded_palette_banks` | Banks absent from static loads; null if load/range observations failed |
| `budget.load_observations_complete` | Graphics, palette and tilemap readers completed |
| `budget.runtime_ownership_verified` | Always false in this static audit |
| `dependency_observations_complete` | Load observations and all nonempty layer geometry were inspected |

**An unloaded chunk/bank is not a safe allocation.** Events, animation, UI transitions and inherited resources may use it dynamically. The importer's explicit profile registration remains mandatory. Missing observations yield null candidate lists rather than making all memory appear free.

Each layer has status `empty`, `inspected` or `unavailable` plus diagnostics. Every inspected type-2 layer lists all metatile IDs, including definitions not used by its layout. Each entry reports whether it is referenced, required absolute 2KB character chunks, required palette banks, missing sets and `available`. Blank metatile zero is implicit transparent and has no dependencies. Local descriptor flips do not change the source chunk/bank; the character base is included in address resolution.

Availability here means static character/palette dependencies exist. It does not mean a complete native brush, safe collision, actor compatibility or runtime rendering certification. The existing PNG atlas still renders referenced definitions only. A future complete brush preview can use this dependency report to decide which unreferenced definitions can be rendered, without inventing missing resources.

Optional `shared_list_consumers` scans the bounded twelve normal sector tables and reports base-state rooms with the same graphics/palette **list pointers**. It includes the selected room. Distinct lists can share underlying wrappers/art resources, and alternate event states are not scanned; this is not a full asset-sharing graph. Separate scan errors are preserved rather than silently ignored.

## Implementation and shared safety rules

`bg_tilemap_ranges` reads the three list entries and uses GBA text BG size bits to reserve one/two/four consecutive 2KB screen blocks. Wrapped ranges beyond 64KB are rejected. `plan_room_assets` now calls this same helper, avoiding separate audit/import calculations. Existing original-art builds remain byte-identical.

`metatile_dependencies` resolves u16 descriptors using the layer's BG character base, low ten character bits and high four palette bits. It does not generate images or mutate resources. Existing source-backed geometry and resource readers retain their bounds and exact-host gate. Type-1/other unsupported geometry is reported unavailable, not interpreted speculatively.

## Static survey results

`python scripts/verify_room_resources.py` audits all **343 normal-sector base-state room slots**. It terminates without mutating bytes, allocation state or ledger, and verifies the imported metatile's new chunk/bank dependency. The current survey yields:

- 901 inspected layer slots, 104 empty and 24 unavailable to the current geometry reader.
- 32 rooms with load-reader diagnostics, including resources beyond current supported formats/inheritance rules.
- 60 rooms with at least one referenced metatile whose required character/palette is unavailable to the static readers.
- Zero character/tilemap overlaps among the loads/ranges the readers successfully resolve.

These numbers identify **tool coverage gaps**, not corrupt native rooms. Do not “repair” original data or register slots based on this survey. Zero observed overlap does not certify rooms with unavailable loads. Runtime ownership and full rendering remain unproven for the general catalog.

Private full survey: `local/room-resource-verification.json`. The source inventory embeds only its aggregate summary, not full per-room generated survey rows. Tests cover character-base/flip dependencies, missing resources, tilemap sizes/wrap, import dependency changes, independent unsupported layers and non-mutation. Total suite: **141 passing tests**.

## Expanded original-art lifecycle test

Run `python scripts/verify_geometry.py --room-art --lifecycle`. It retains the prior art-pixel, collision, jump, save, fresh-continue and natural-return checks, then exercises:

1. Open native pause menu and confirm native substate 6. Let the menu settle, then cancel with native B and explicitly confirm gameplay state 4/substate 1. Imported character/palette bytes match again after resume. Sending Start to this menu did not establish resume in this fixture; checking state avoids accepting a menu screenshot as gameplay evidence.
2. Set native HP to zero as a declared controlled death fixture. The native engine reaches player state 16, then game state 5 with the actual Game Over screen. No graphics/palette/terrain/collision memory is injected.
3. Copy SRAM **after Game Over**, create a fresh emulator, and continue. The native save restores positive HP in the expected save room. Walk back naturally to the hallway and its step. Collision still blocks at the expected face, and the full imported 2KB chunk and 32-byte palette bank match the source assets.

This verifies post-death saved state and resource reload using fresh-session continue. It does **not** verify same-session Game Over-menu navigation, arbitrary event scenes, every pause submenu, hardware or a full campaign. The original-art ROM bytes remain unchanged from v0.6; this milestone adds audit APIs and stronger evidence rather than silently altering the mod.

Private evidence remains `local/original-room-art-verification.json` with declared fixtures. New captures are `original-room-art-paused.png`, `-resumed.png`, `-death.png`, `-gameover.png` and `-post-death-return.png` under `local/`. Earlier guides describe earlier coverage; this lifecycle guide is the current evidence boundary.

## Files and next work

| File | Responsibility |
|---|---|
| `aria/room_resources.py` | Shared tilemap ranges, all-metatile dependencies, static budgets and narrow consumer scan |
| `aria/room_assets.py` | Import planning reuses the shared tilemap exclusion helper |
| `aria/cli.py` | Read-only audit command and private output rules |
| `tests/test_room_resources.py` | Synthetic dependency/range and private-host contracts |
| `scripts/verify_room_resources.py` | Bounded full base-state static survey |
| `scripts/verify_geometry.py --room-art --lifecycle` | Pause/death/post-death continue evidence |

Next resolve the survey's unsupported/inherited resource cases and establish ownership for an additional ordinary room through native tests. Then register a narrowly tested additional room or import shape. Keep diagnostic observations, registered import permissions and native lifecycle certification separate. Preserve source-only packaging and keep the GUI application deferred.


## Mixed resource inspection (v0.8.0)

See [MIXED-ROOM-RESOURCES.md](MIXED-ROOM-RESOURCES.md) for raw/LZ 4bpp and 8bpp load inspection, format guards, agent API contracts and remaining limitations. Full suite: 145 tests. Static survey: 343 slots, 6 rooms with load diagnostics. No additional write targets or 8bpp terrain rendering.


## Integrated background discovery (v0.11.0)

See [BACKGROUND-DISCOVERY.md](BACKGROUND-DISCOVERY.md) for catalog/audit schema version 2, format-aware dispatch and texel-derived palette dependencies. 156 tests; 925 nonempty layers inspect and all 24 byte-index source rasters render. No new write permissions or viewport verification. See [MODS-YOU-CAN-MAKE-NOW.md](MODS-YOU-CAN-MAKE-NOW.md) for current playable-mod examples and scoped agent prompts.


## Tilemap accounting and multiplayer feasibility (v0.12.0)

See [TILEMAP-MEMORY.md](TILEMAP-MEMORY.md) for corrected text/affine byte ranges and partial-chunk reservations, with 157 tests and native fixture evidence. No new write slots. See [MULTIPLAYER-FEASIBILITY.md](MULTIPLAYER-FEASIBILITY.md) for optional multiplayer research directions; no multiplayer feature is implemented.
