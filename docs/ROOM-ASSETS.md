# Original room graphics and palette imports

The framework can now import original 4bpp character artwork and an RGB555 palette into isolated room load lists. It composes with authored metatile/collision definitions, previews and normal build/play. The first supported contract is one registered static load in sector 0 room 3: a 2KB character chunk at BG VRAM offset 0xC000 and palette bank 8. This is a bounded original-art pipeline, not a general VRAM allocator or arbitrary sprite/animation importer.

## Example and commands

```powershell
.\TacticalSoul.cmd build examples/original-room-art/mod.json
.\TacticalSoul.cmd play examples/original-room-art/mod.json
.\TacticalSoul.cmd preview-room 0 3 --mod examples/original-room-art/mod.json --out local/previews/original-art.png
.\TacticalSoul.cmd inspect --mod examples/original-room-art/mod.json
```

The example supplies original procedural neon-brick pixels and a sixteen-color palette, authored for this project under MIT. It appends a new full-solid metatile using those pixels, replaces the first hallway's cell x10,y5, and retains the paired native save-room route. Default native A jumps across the step. Artwork is original and redistributable; the host game, generated ROMs and screenshots remain private.

## `room_assets` contract

A manifest may include a nonempty `room_assets` array. Each entry has exactly these fields:

| Field | Meaning |
|---|---|
| `room` | Exact object with integer `sector` and `room` |
| `target_chunk` | Registered destination 2KB chunk index, currently 24 |
| `palette_bank` | Registered destination sixteen-color bank, currently 8 |
| `graphics_source` | JSON tile source contained within the manifest folder |
| `palette_source` | JSON palette source contained within the manifest folder |
| `provenance` | Nonempty authorship/license description |
| `expected_graphics_list_sha256` | SHA-256 of the current graphics load-list entries plus its terminating zero word |
| `expected_palette_list_sha256` | Corresponding palette load-list preimage |

The source graphics schema is existing `tiles4`: `{width,height,pixels}` with exact row-major pixel count, dimensions divisible by eight and integer indices 0..15. This initial contract requires exactly 64 tiles (2,048 encoded bytes), such as a 64×64 sheet. The palette is exactly sixteen RGB triples, channels 0..255. Colors are quantized by the existing RGB555 codec; palette index zero remains transparent when rendering. PNG authoring can use the existing indexed-PNG adapter to produce tile JSON; it is optional.

The profile's `room_asset_slots` contains the approved room/chunk/bank combination. Unknown combinations are rejected even if they appear unused. Do not edit the profile merely to bypass a failed import. Establish resource and lifecycle evidence for each additional registration. One batch per room is allowed; duplicate room batches fail. Source paths must resolve within the manifest folder. Provenance text is recorded, not automatically verified for licensing.

Raw patches cannot combine with `room_assets`. Other supported high-level changes can compose through the normal patch ledger. Room assets install after room/entity edits and before geometry definitions, so newly authored minitiles can reference the imported characters. Native callbacks still allocate first where required by their fixed linked origin. Failed builds should be discarded and rebuilt from an immutable original; there is no general rollback transaction for allocation/write failures.

## Source-backed records and pointer isolation

The implementation uses the already documented AoS formats from local DSVEdit `room.rb`, `gfx_wrapper.rb` and `palette_wrapper.rb`, validated by native load/pixel evidence. These references are development-only; no external source or extracted art is included in releases.

`aria/room_assets.py` first plans all entries without mutation. It resolves actual existing graphics and palette loads, requires unused destinations, checks preimage hashes, verifies all active text-background tilemap ranges and encodes source files. The example's three tilemaps occupy 0xE800..0xF000, 0xF000..0xF800 and 0xF800..0x10000. The imported character chunk occupies 0xC000..0xC800 and overlaps none of them. Existing character chunks 16..23 and palette banks 0..7 remain unchanged.

The installer allocates a raw graphics wrapper/payload, a one-row palette resource and copies of both room load lists with appended entries. It changes only the room's graphics-list pointer at room+12 and palette-list pointer at room+16. Original wrappers, original list bytes, graphics and colors remain unchanged, so other rooms sharing them keep their original loads. Appended entries use first source chunk/bank zero, count one and unknown byte zero; original entries preserve their unknown fields.

Graphics wrapper bytes are `[0,4,0,4]`: raw type, 4bpp, reserved zero, four 512-byte length units, followed by 2KB of tile bytes. The palette resource begins `[0,0,1,0]`, followed by sixteen RGB555 colors. Both load lists use native `<IBBBB>` entries and zero termination. Compression, multiple imported chunks/banks and inherited loads are intentionally unsupported in this initial importer.

## Descriptor mapping and budgets

The hallway's selected BG character base is 2 (offset 0x8000). Destination chunk 24 is offset 0xC000, so the first imported 8px character has relative index `(24 - 2*8)*64 = 512`. Palette bank 8 plus character 512 gives descriptor `0x8200`. Sixteen instances form the example's new 32px metatile. Different layer character bases require different descriptors; a VRAM destination is not itself a character index.

Build and inspect reports include source file hashes, encoded graphics/palette hashes, provenance, allocated pointers and a budget object:

- New character bytes: 2,048; VRAM character range [49,152,51,200).
- New palette bytes: 32; destination bank 8.
- Excluded tilemap ranges for all active layers.
- ROM allocation payload: 2,152 bytes for this importer, plus 8 existing-room pointer bytes written. Alignment is four bytes and current allocations are already aligned. Geometry resources/layout copies consume separate ROM space reported by the normal ledger.

The allocator enforces ROM range limits. The budget describes this registered static load and known background tilemaps, not complete global runtime ownership. Pause UI, animated graphics, event-specific loads, other characters and every game scene have not been exhaustively audited. An apparently free chunk is not universally safe just because it is absent from one room's static list.

## Verification and evidence

All **134 tests** pass. New cases establish non-mutating planning, isolated list pointers, preservation of original resource loads, exact budget accounting, deterministic clean builds, and rejection of wrong slots, preimages, paths, schemas, duplicates and tilemap/graphics overlaps before mutation. Host-dependent tests skip without the private exact original.

Run `python scripts/verify_geometry.py --room-art` with the local libretro core and Pillow-enabled development Python. It verifies 384 opaque pixels in the new art against the native viewport at GBA 5-bit depth, then checks baseline/custom collision, A jumping, native saving, fresh-session continue and natural return. On return it checks all 2KB of the imported character chunk and all 32 bytes of palette bank 8 exactly against the authored assets, establishing reload after leaving the room and restarting the emulator.

Movement results remain baseline X329, blocked X311, jumped X458, return blocked X360. Initial comparison has the declared camera-relative X/zero-velocity fixture and native settled Y; return is controller traversal. No graphics, palette, terrain or collision RAM writes are used. The exact output ROM SHA-256 is `660a7a6892d43ec8dc56a03bf4ae09f7ddb136e02d245bbf4cdf37fc979570ca`.

Private summary: `local/original-room-art-verification.json`. Native screenshots: `local/original-room-art-native-step.png` and `local/original-room-art-native-return.png`. Normal previews and patched ROMs are also local/private. Source-only packaging includes only original source artwork, manifest, code, tests and guides.

Death, pause/effect/event ownership, hardware, compressed imported wrappers, animations, broader room support and all campaign interactions remain unfinished. The native verifier retains generic geometry screenshot filenames for other captures; the original-art summary and step/return images are distinct. Treat this example as a verified vertical slice, not full original-world authoring support.

## Files and next steps for agents

| File | Responsibility |
|---|---|
| `aria/room_assets.py` | Planning, load-list preimages, tilemap exclusions, source encoding, isolated installation and budgets |
| `aria/content.py` | Existing tiles4 and RGB555 codecs/path containment |
| `aria/cli.py` | Manifest acceptance, combination rules, application order and reports |
| `framework/aos-usa-r0.json` | Explicit tested static room asset registration |
| `examples/original-room-art/` | Original pixel/palette JSON and runnable source manifest |
| `tests/test_room_assets.py` | Non-mutation, isolation, rejection and build determinism |
| `scripts/verify_geometry.py --room-art` | Native art/collision/lifecycle fixture |

Next add a reusable resource dependency/budget audit across all layers and native runtime loads, establish death/pause/event behavior, and register additional ordinary rooms through native tests. Then generalize import sizes and slot selection with an explicit ownership plan. Keep original assets isolated, maintain expected-value guards and add source-only examples for each newly supported contract. Do not create a GUI to hide remaining backend limitations.

For v0.7 static dependency auditing and expanded pause/death/fresh-continue evidence, read ROOM-RESOURCE-AUDIT.md. Earlier lifecycle limitations above describe the initial v0.6 evidence; same-session Game Over continuation and general event ownership remain unverified.


## Two-room original art (v0.14.0)

See [TWO-ROOM-ART.md](TWO-ROOM-ART.md) for hallway plus save-room registered main layers, contrasting original graphics/palettes, native entry/return/save/death/fresh-continue evidence and limits. Run examples/two-room-art/mod.json. Full suite: 163 tests. Current estimate: 25%. No arbitrary-room or multiplayer permission.


## Three-room original-art route (v0.15.0)

See [THREE-ROOM-ART.md](THREE-ROOM-ART.md) for registered room 0,6 plus hallway/save targets, native contrasting-resource route and lifecycle checks, effect-aware fixed-rectangle capture and campaign limits. Run examples/three-room-art/mod.json. 164 tests; current estimate 26%. No arbitrary-room registration or repaired full campaign graph.
