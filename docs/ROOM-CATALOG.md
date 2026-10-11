# Room catalog: read-only discovery for agents and a future GUI

The framework now provides paginated normal-sector room discovery with stable base-state identifiers and independent layer diagnostics. A room browser can enumerate rooms, inspect supported layers and report unsupported resources without aborting the whole page. This milestone does not implement a GUI, editing document, undo/redo or new terrain-writing permissions.

## Commands

Run from the Tactical Soul Framework folder:

```powershell
.\TacticalSoul.cmd room-catalog --limit 32
.\TacticalSoul.cmd room-catalog --offset 32 --limit 32 --out local/catalog/page-32.json
.\TacticalSoul.cmd room-catalog --sector 11 --limit 64 --out local/catalog/final-sector.json
.\TacticalSoul.cmd room-catalog --sector 0 --offset 3 --limit 1 --check-rendering
.\TacticalSoul.cmd room-catalog --sector 0 --offset 3 --limit 1 --mod examples/geometry-workshop/mod.json
```

`--host` and the documented host environment variables work as for other commands. `--mod` applies a manifest in memory before cataloging; the original remains unchanged and no patched ROM is written. `--out` is optional: omitted means JSON on stdout, provided means a `.json` file under this framework's `local/`, preserving the host and manifest. Catalogs contain original-game structure and hashes, so keep generated reports local and outside source releases.

The default page has at most 32 rooms; `--limit` allows 1..128. `--offset` is a zero-based slot offset across the selected sectors, not a room ID. With `--sector`, offsets are local to that sector's slot list. Without it, slots are ordered by sector then index. Follow `next_offset` until it is null. An offset past the known list yields an empty page, not an error. Offset is bounded to 0..3072, the implementation's maximum of twelve sectors × 256 slots.

Default cataloging decodes geometry but does not render full images. `--check-rendering` explicitly resolves native resources and renders each supported selected layer on that page, returning dimensions and an RGBA hash rather than raster buffers. It is more expensive; use small pages for interactive browsing. Generate actual PNGs with `preview-room` after selecting a room.

## Stable identity and snapshot consistency

Example: `aos-usa-r0:s00:r003:base` identifies profile aos-usa-r0, normal sector 0, room-table slot 3, base state. Room addresses and resource pointers are properties, not identities. Moving a pointer or applying the geometry-workshop manifest does not change this ID.

IDs are stable for the same profile/table-slot organization, not across a campaign that deliberately reorders room tables, a different ROM profile or future custom project identity migrations. Alternate/event room states are reported by their pointer when present but are not enumerated or assigned IDs in this version. No English room or area names are guessed.

Every page carries `image_sha256`, calculated from the current in-memory ROM bytes, and its profile ID. A frontend should discard/restart pagination if that hash changes. Pagination offsets can shift when a previously invalid sector table becomes readable; compare snapshot hashes and `enumeration_complete`, rather than treating offset as a permanent room bookmark.

## Table boundary fix

AoS's normal room tables do not have zero terminators. The twelve sector table pointers come from the area table referenced at ROM 0x08001990. For sectors 0..10, the next sector pointer bounds the current room-pointer array. The final sector ends at the area table itself. Reading `area+12*4` as another sector pointer reads unrelated layer data and previously made public lookup reject the final sector.

`aria.rooms.sector_span` now centralizes this rule; `room_address` uses it too. This is based on local DSVEdit `dsvlib/sector.rb` (`read_room_pointers_from_rom` stops at the area-table address for AoS), confirmed by inspecting all 343 original room slots and public lookup results. Local source is preserved under `tools/references/DSVEdit/dsvlib/sector.rb` and excluded from releases with the other development references.

The implementation requires aligned, ascending table bounds within the original pre-area organization, at most 256 slots per sector, and in-ROM ranges. It deliberately does not accept arbitrary relocated/noncontiguous campaign room tables. Supporting those requires a new explicit format/profile contract and tests. Room record pointers must separately fit a full 36-byte native record. These bounds supplement, rather than replace, the original SHA-256 gate.

## Python API and result contract

```python
from aria.room_catalog import catalog_rooms

page = catalog_rooms(verified_rom, sector=0, offset=3, limit=1,
                     check_rendering=True)
room = page['rooms'][0]
```

The API accepts an already verified `RomImage` and returns JSON-compatible data. No GUI, emulator or optional image dependency is needed. It creates no caches and mutates no ROM bytes, allocation cursors or patch ledger. Applying a manifest is a separate caller operation.

| Page field | Meaning |
|---|---|
| `schema_version` | Catalog schema version 1, separate from mod-manifest schema |
| `profile`, `image_sha256` | Identity and current in-memory snapshot hash |
| `enumeration_complete` | All requested sector-table bounds parsed; does not imply all layers render |
| `sectors` | Parsed sector bounds and slot counts |
| `diagnostics` | Sector-level failures, each with sector/code/message |
| `total_known_slots` | Count from readable requested tables, including invalid room-pointer slots |
| `offset`, `limit`, `next_offset` | Requested page and continuation cursor |
| `rendering_checked` | Whether full rendering checks were requested |
| `rooms` | Ordered per-slot records for this page |

Room entries contain stable ID, sector/index, `state: base`, table-entry address, room address when readable, alternate-state pointer, graphics/palette list pointers, declared door count, map position, layer records and diagnostics. Declared metadata is not a validated door graph, map compiler or save/progression audit. `terrain_write_registered` reports membership in the existing terrain allowlist; it does not certify that arbitrary edits or all layers can be written.

Room `status` is `invalid` if its metadata cannot be read, `partial` if any layer's geometry is unsupported/invalid or a requested render fails, and `available` if all layers are available/empty and no requested render fails. An available room can have empty layers; it is not a guarantee of paintability, full rendering, reachability or gameplay safety.

Layer records preserve layer index, z, scroll, BG controls, declared pixel dimensions, metadata pointer and, when readable, type and screen dimensions. Supported geometry adds the existing `inspect_geometry` summary. Statuses are deliberately separate:

| Field | Values |
|---|---|
| `geometry_status` | `available`, `empty`, `unsupported`, `invalid` |
| `render_status` | `not_checked`, `available`, `unavailable` |

An empty layer has no metadata pointer and is not rendered. Unsupported type means the current decoder does not support its format; it does not mean the native game data is corrupt. A supported layer can still have an unavailable preview because it inherits resources or requests unsupported graphics. Do not automatically attempt to fix original data based on decoder limitations.

Machine-readable diagnostic codes are `invalid_sector_table`, `invalid_room_metadata`, `unsupported_tileset_type`, `invalid_geometry`, and `render_unavailable`. Each includes explanatory text. A bad sector is skipped while other sectors are enumerated; a bad room preserves its slot/ID; a bad layer does not suppress its siblings. Rendering failures leave successfully decoded geometry inspectable. Invalid API options raise `PatchError`; unexpected programming errors are not swallowed as data diagnostics.

The CLI returns success for a report that contains isolated data diagnostics, allowing a GUI to display that report. Invalid command options, host verification failures and output failures return a failing exit code. Clients that require an entirely renderable selection must inspect the statuses.

## Verified evidence and bounds

`python -m unittest discover -s tests` now passes 122 tests. New synthetic cases cover final-sector bounds, malformed tables, IDs surviving pointer movement, pagination, empty layers, invalid arguments, independent sector/room/layer failures, render failure reporting and non-mutation. The private-host case confirms all 41 final-sector slots and stable identity across the terrain example.

Run `python scripts/verify_room_catalog.py` with your local exact original. It audits all **343 normal-sector base-state slots** across 11 pages, with unique IDs and agreement with public room lookup. Results: 319 room records available, 24 partial; among 1,029 layer slots, 901 geometry layers available, 104 empty and 24 unsupported. No geometry record is classified invalid in this original-host audit. These are decoder classifications, not campaign certification or full rendering coverage.

It separately renders all twelve layers across sector 0 rooms 0, 3, 6 and 31 through catalog checks, confirms the mod changes the hallway's layout hash while retaining its ID, and verifies ROM/ledger/allocation preservation. Private summary is `local/room-catalog-verification.json`; full private pages are under `local/catalog-audit/`. The geometry native collision/jump/save/return verifier also passes after the room lookup boundary change.

## Files and next steps

| File | Responsibility |
|---|---|
| `aria/rooms.py` | Shared bounded sector-span and public room lookup |
| `aria/room_catalog.py` | Stable IDs, bounded pagination and independent structured diagnostics |
| `aria/cli.py` | `room-catalog`, private output and manifest preview integration |
| `tests/test_room_catalog.py` | Synthetic bounds/diagnostics and bounded private-host contracts |
| `scripts/verify_room_catalog.py` | Full slot audit and bounded render checks |
| `docs/GUI-EDITOR-ROADMAP.md` | Remaining editor-document and frontend milestones |

Next build the editor document and undo/redo contracts over an immutable original, then the first room-viewer frontend. Keep selection IDs and snapshot hashes distinct. Do not cache by pointer or slot alone, treat a missing atlas tile as a valid brush, broaden terrain permissions to enable GUI controls, or infer native campaign safety from an available decoder status.


## Integrated background discovery (v0.11.0)

See [BACKGROUND-DISCOVERY.md](BACKGROUND-DISCOVERY.md) for catalog/audit schema version 2, format-aware dispatch and texel-derived palette dependencies. 156 tests; 925 nonempty layers inspect and all 24 byte-index source rasters render. No new write permissions or viewport verification. See [MODS-YOU-CAN-MAKE-NOW.md](MODS-YOU-CAN-MAKE-NOW.md) for current playable-mod examples and scoped agent prompts.


## Bounded room-state discovery (v0.13.0)

See [ROOM-STATES.md](ROOM-STATES.md) for room-states, chain bounds/diagnostics and explicit empty-load observations. 161 tests. All 343 original base slots have zero alternate links; alternate chain behavior is synthetically tested, not natively certified. No new editing or multiplayer capability.
