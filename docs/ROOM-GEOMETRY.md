# Existing-room geometry: implementation and agent guide

Tactical Soul Framework now inspects Aria type-2 layers and edits selected existing main-layer cells using existing visual/collision metatiles. This is the first terrain-writing step toward total conversions. It does not import arbitrary new tilesets, resize rooms, build a new castle map, or define a general collision scripting language.

## Working commands

Run from the Tactical Soul Framework folder (PowerShell uses .\TacticalSoul.cmd):

```bat
TacticalSoul.cmd inspect-geometry 0 3
TacticalSoul.cmd inspect-geometry 0 3 --layer 1
TacticalSoul.cmd export-geometry 0 3 --out local/geometry/hallway.json
TacticalSoul.cmd inspect-geometry 0 3 --mod examples/geometry-workshop/mod.json
TacticalSoul.cmd play examples/geometry-workshop/mod.json
```

Inspection is read-only and returns dimensions, pointers, counts, native control fields, layout/resource hashes and supported scope. Export adds private layout cells, native records and decoded/compressed resource bytes. It verifies reconstruction before writing. Exports must stay under local/ and cannot overwrite the host or manifest. They contain original game geometry/art data and are excluded from source packages.

The workshop adds a 32px stone step in the first hallway at sector 0, room 3. It replaces cell x=10,y=5 (world rectangle x320..351,y160..191) from metatile 53 to metatile 49. Both metatiles already exist in the room's tileset; 49's collision data consists of sixteen 0x03 bytes. The engine loads the existing graphics and collision together. The example also includes the previously tested paired connection from this hallway to the original save room 31, making save/continue regression accessible. It preserves original room identities/map placement.

## Source and format evidence

Implementation is based on available local DSVEdit source, not guessed ROM field names. Relevant reference files are copied under tools/references/DSVEdit for independent development; third-party source stays excluded from the framework source archive. This module is an independent Python implementation of the documented data layouts.

| Source | Established layout |
|---|---|
| dsvlib/layer.rb BGLayer | 16-byte layer metadata, width/height in screens, tileset type/pointers and raw u16 layout |
| dsvlib/layer.rb RoomLayer | three 12-byte AoS layer list entries with native z/scroll/BG controls and pixel dimensions |
| dsvlib/layer.rb LayerTile | metatile index low 14 bits; horizontal/vertical flip bits 14/15 |
| dsvlib/tileset.rb | type-2 compressed visual records, implicit blank metatile, collision record grouping |
| dsvlib/gba_dummy_filesystem.rb | four-byte inner resource header removed after GBA decompression |
| dsvlib/gba_lz77.rb | GBA LZ10 literal/backreference stream format |
| constants/gba_constants.rb | 32px metatiles, eight cells per 256px screen in both axes |
| dsvlib/room.rb | three GBA layer entries per room |

Room metadata's layer-list pointer is at room+8. Each list entry is `<BBHHHI`: z, scroll, BG control, pixel width, pixel height, metadata pointer. Selected metadata is `<BBHIII`: width screens, height screens, tileset type, visual tileset pointer, collision tileset pointer, raw layout pointer. Layout size is width*height*128 bytes, with cells row-major across the full width, not independent screen-major blocks.

A visual type-2 metatile is sixteen little-endian u16 minitile descriptors (32 bytes). Collision supplies sixteen raw bytes per metatile. Both omit metatile zero, which is implicitly blank. The reader requires matching visual/collision counts and at most 512 metatiles including blank. It does not assign a semantic name to every collision byte or certify slope/hazard behavior.

## Compression and reconstruction

aria/compression.py decodes standard GBA LZ10: 0x10 plus 24-bit decoded size; each flag byte selects literals or 3..18-byte backreferences with distance 1..4096. It supports overlapping copies and rejects truncation, invalid distances, declared-size overruns and decoded sizes above the configured 0x20000-byte bound. ROM input reads are bounded to 0x25000 bytes.

Aria resources contain an additional four-byte header in the decoded stream. Its upper 24 bits must match the full expanded length. The reader preserves the low byte verbatim; observed original resources use zero, while DSVEdit's recompressor can emit 0x10. Do not normalize this byte merely because it resembles an LZ header.

Exports preserve data_hex, inner_header_hex and the exact consumed compressed_hex. verify_roundtrip rebuilds selected metadata fields and the selected layer entry from exposed fields, repacks layout cells, and verifies the saved compressed streams decode to the exported resource data. This is a byte-exact reconstruction of the used original stream; unused alignment padding outside the consumed stream is untouched in ROM, not invented by export.

rebuild_aria(preserve=False) uses the framework's literal LZ encoder around the preserved inner header. The recompressed stream can be larger and byte-different while decoding identically. Current geometry editing does not install recompressed resources: it reuses their original pointers. Full exported bundles are inspection/reconstruction artifacts, not an editable full-room import schema.

## Geometry manifest contract

```json
{
  "schema_version":1,
  "id":"my-stone-step",
  "geometry_edits":[{
    "room":{"sector":0,"room":3},
    "layer":0,
    "expected_layout_sha256":"e97dfecebd260237038bef074a750420a705c87a6d6bd27e90386a23d7397b23",
    "cells":[{"x":10,"y":5,"expect":53,"value":49}]
  }]
}
```

Use the runnable workshop for a complete example with paired save-room routing. Each entry accepts exactly room, layer, expected_layout_sha256 and a nonempty cells list. One batch per room. Each row accepts x,y,expect,value; coordinates are zero-based 32px cells, and expect/value are exact u16 words. Duplicate coordinates, booleans, unchanged cells, out-of-range values and missing metatile references fail. The full current layout hash and each old cell must match.

Initial write scope is deliberately only sector 0 room 3, main layer 0, registered in profile geometry_edit_rooms. Read-only inspection supports the tested type-2 layers beyond this write target. Type 1/3, empty layers, dimensions outside 1..15 screens, mismatched visual/collision counts and missing metatile references are rejected rather than guessed. Existing flip bits can be preserved/authored as native words; native regression currently tests an unflipped stone block only.

Do not expand the write registration just to bypass an error. Inspect the candidate room's sharing, scripts, doors, saves and geometry, then add native acceptance evidence. Room size changes require camera/map/save compilation and are not supported here.

## Isolation and composition

The builder clones the selected raw layout, selected 16-byte metadata and entire 36-byte layer list into declared ROM free space. It changes only the selected layer's layout pointer, the selected list entry's metadata pointer and the room's layer-list pointer. Other layer entries retain original references. Original shared layouts and compressed visual/collision resources are never overwritten. Native graphics/palette loading lists, entities, doors and map identity remain unchanged by geometry_edits itself.

This copy-on-write design prevents one room edit from silently changing every room sharing its layout/resources. It allocates ROM only; it does not allocate VRAM or new graphics resources. The workshop's paired room_edits are separate and explicitly reported.

Order: ability/frame callback first, content/resource edits, blobs/native tables, high-level room/entity/door operations, geometry edits, then raw patches (which cannot be combined with geometry_edits). Geometry can compose with the supported paired-door/move layer. Preserve the hook's fixed linked origin. Shared conflict ledger rules remain authoritative. Build APIs are not transactional: discard an in-memory image after any exception. Static validation cannot prove safe terrain placement or event reachability.

## Native verification and fixtures

Run python -m unittest discover -s tests, then python scripts/verify_geometry.py with the local exact host, libretro core and Python/Pillow. The example itself builds through bundled Python without those development tools.

Verification reconstructs native data, validates literal recompression, proves only one selected layout cell differs, preserves the original shared layout/resources and map, and compares native movement against the baseline. It declares an identical camera-relative player-X/zero-velocity fixture beside the step, retains settled native Y, and waits for area-title control locks to finish. It does not inject terrain/collision into RAM.

Native player X is camera-relative; compare world X by adding camera X. Moving a raw Y value without its camera context can put Soma below a floor or into a doorway. The verifier records that correction rather than treating a screenshot as collision evidence. Jumping, traversal to the native save room, fresh-session continue and natural return walking are separate native checks. Save-route changes use the already-tested paired-door example.

Private evidence is local/geometry-verification.json and local/geometry-*.png. Unit tests cover literal/backreference/overlapping LZ behavior, malformed bounds, inner-header preservation, export metadata guards, isolated layer copying and rejected edits. Exact-host tests reconstruct twelve selected layers across rooms 0,3,6,31; this is bounded coverage, not all-room certification.

## Important files

| File | Responsibility |
|---|---|
| aria/compression.py | bounded LZ10, Aria inner header and exact/semantic resource reconstruction |
| aria/geometry.py | selected type-2 layer inspection/export, reconstruction, validated cell plans and isolated copies |
| aria/cli.py | geometry commands, manifest integration/order and reports |
| framework/aos-usa-r0.json | initial tested geometry write registration |
| examples/geometry-workshop/mod.json | numeric existing-metatile step and paired native save route |
| tests/test_geometry.py | synthetic format/safety checks and private-host roundtrips |
| scripts/verify_geometry.py | native collision/jump/traversal/save/return evidence |
| tools/references/DSVEdit/dsvlib | local independent-development format sources; excluded from distribution |

## Next extensions toward conversions

Static selected-layer graphics/palette inspection and previews are now implemented in ROOM-PREVIEWS.md; complete brush availability and multi-layer effects remain unfinished. Next add an original small tileset/collision definition with explicit ROM/VRAM budgets and isolated resource lists. Verify native movement, reentry and saves before allowing more rooms. Room resizing, new campaign identity, arbitrary sprites, event editing and map/save compilation remain separate milestones described in TOTAL-CONVERSIONS.md.

## Verified native result

On the exact USA r0 host, all eight geometry checks pass. Baseline walking reaches world X329; the new step blocks at X311; default native A jumping reaches X458. After native saving, fresh-session continue and natural return walking stop at X360 on the opposite face. The default native B button attacks. The output SHA-256 is `4768b6f5f4ecd0c23a0df2bebfb35c11f6f96d549d2bcd25519fb4559badc8a4`. All 101 unit tests pass, as do room, resource, content, ability and framework native regressions after the rename.


## Custom terrain and tracked completion (v0.5)

Read [CUSTOM-TERRAIN.md](CUSTOM-TERRAIN.md) for newly authored type-2 metatiles, explicit empty/solid collision, loaded-resource validation and isolated visual/collision streams. `examples/custom-terrain-workshop/mod.json` is runnable; `python scripts/verify_geometry.py --custom-terrain` verifies native pixels, walking, jumping, save/continue and return. All 127 unit tests pass. Original character/palette imports, VRAM allocation, other collision families and broader room writes remain unfinished.

[COMPLETION-ROADMAP.md](COMPLETION-ROADMAP.md) and `framework/roadmap.json` track the total-conversion scope and weighted maturity estimate (currently about 21%). A GUI application is deferred; work belongs in reusable framework APIs. At the end of every development turn, report progress/validation, next milestone and estimated framework completion. Next: original room graphics/palette imports with isolated load lists and explicit resource budgets. Current package: `release/Tactical-Soul-Framework-0.5.0.zip`.


## Two-room original art (v0.14.0)

See [TWO-ROOM-ART.md](TWO-ROOM-ART.md) for hallway plus save-room registered main layers, contrasting original graphics/palettes, native entry/return/save/death/fresh-continue evidence and limits. Run examples/two-room-art/mod.json. Full suite: 163 tests. Current estimate: 25%. No arbitrary-room or multiplayer permission.


## Three-room original-art route (v0.15.0)

See [THREE-ROOM-ART.md](THREE-ROOM-ART.md) for registered room 0,6 plus hallway/save targets, native contrasting-resource route and lifecycle checks, effect-aware fixed-rectangle capture and campaign limits. Run examples/three-room-art/mod.json. 164 tests; current estimate 26%. No arbitrary-room registration or repaired full campaign graph.
