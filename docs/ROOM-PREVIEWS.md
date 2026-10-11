# Static room previews and frontend rendering contract

Tactical Soul Framework can now render a selected native type-2 room layer to a PNG, with a metatile atlas and a machine-readable resource report. This is a working backend milestone for a future GUI level editor. The preview is generated from ROM data without running the game and without changing ROM bytes.

## Use it

From the framework folder in PowerShell:

```powershell
.\TacticalSoul.cmd preview-room 0 3 --out local/previews/hallway.png
.\TacticalSoul.cmd preview-room 0 3 --mod examples/geometry-workshop/mod.json --out local/previews/hallway-step.png
.\TacticalSoul.cmd preview-room 0 3 --layer 1 --out local/previews/hallway-layer1.png
```

`--host` selects another copy of the exact supported original; `TSF_HOST_ROM` and the legacy `ARIA_HOST_ROM` fallback also work. `--mod` applies an existing manifest in memory before rendering, using the same validation/allocation order as builds. It does not write a patched ROM. `--layer` selects 0, 1 or 2; empty or unsupported layers fail with an explanation.

For `hallway.png`, outputs are `hallway.png`, `hallway.atlas.png`, and `hallway.json`. The atlas filename uses the input stem, and the report contains pointers, hashes, graphics/palette load mappings, geometry metadata, referenced metatile IDs and scope. Outputs must be distinct, end in `.png` for the main image, stay inside this framework's `local/` after path resolution, and preserve host/manifest inputs. A successful render may overwrite earlier previews at those paths. Rendering validates and encodes both images before writing files; a filesystem error can still leave a partially written output set.

Images contain private commercial game artwork. Keep images, resource reports, screenshots and extracted data local. The source packager excludes them. The package contains the renderer, tests and documentation, enabling users with their own exact original to generate previews offline with bundled Python. Pillow is not required for preview generation.

## Backend API for future agents

`aria.rendering.render_layer(rom, sector, index, layer=0)` accepts an already verified `RomImage`, including any in-memory manifest edits. It returns:

| Key | Contract |
|---|---|
| `width`, `height` | Full selected-layer dimensions in native pixels |
| `rgba` | Row-major, straight-alpha RGBA bytes, exactly width × height × 4 |
| `atlas_width`, `atlas_height`, `atlas_rgba` | 16 metatiles across, 32px per metatile, rows sufficient for the native metatile count |
| `report` | JSON-compatible metadata and evidence; no binary image objects |

The renderer has no dependency on CLI argument parsing, a window, an emulator, an image library, or a global document session. A frontend should upload this RGBA buffer to its own canvas/texture. It should not parse CLI stdout to implement editing. `png_rgba` is a small standard-library PNG adapter for local output; it is not an asset importer.

The atlas currently renders only metatiles referenced in the selected layout, plus the implicit blank tile. Other atlas slots remain transparent. **Use `report.rendered_metatile_ids` to distinguish unrendered slots from a valid blank metatile.** Some unused definitions reference characters that this room does not load. Do not offer an unrendered slot as a validated paint brush. A complete brush browser requires resource-availability analysis and additional native tests.

The renderer does not mutate `rom.data`, its ledger or allocation cursors. Previewing a mod applies the manifest before invoking the renderer; that separate operation does mutate the in-memory image. Persistent writes continue through the checked build APIs described in ROOM-GEOMETRY.md.

## Source-backed data pipeline

The local DSVEdit source established these layouts. Relevant local references are under `tools/references/DSVEdit/dsvlib/`; development references are excluded from source releases. This is an independent Python implementation, with synthetic tests and native comparisons.

1. Resolve the room via the existing sector tables and exact-host profile.
2. Read AoS room metadata: layer list at room+8, graphics list at room+12, palette list at room+16. These differ from Harmony of Dissonance's room fields. `room.rb`'s AoS branch is the reference.
3. Decode the selected layer through `geometry.inspect_geometry`: checked type-2 metatile definitions, collision resource relationship, raw layout and native BG controls.
4. Read graphics list entries as `<IBBBB>`: wrapper pointer, destination chunk, first source chunk, chunk count and unknown byte. A zero wrapper pointer terminates the bounded list.
5. Read graphics wrapper's four-byte header: storage type, bpp, preserved reserved byte, raw length in 512-byte units. Type 0 embeds raw graphics at wrapper+4; type 1 stores a compressed resource pointer there. Aria LZ resources retain the inner header rules in ROOM-GEOMETRY.md. This milestone accepts 4bpp only.
6. Build the final character-memory map in ordered 2KB chunks. Each 4bpp chunk contains 64 consecutive 8×8 tiles. Later loads overwrite earlier destination chunks. Destination chunks must fit the 64KB background memory range and source selections must fit the decoded payload.
7. Read palette entries as `<IBBBB>`: source list, destination bank, first source bank, count, unknown. The palette source begins with four bytes; bytes 0 and 3 must be zero, byte 2 is its count of 16-color rows. Copy selected RGB555 rows into the final 16-bank map, in load order. This is the AoS format, not HoD's foreground/background palette wrapper.
8. Render minitile descriptors: bits 0–9 select the character relative to the BG character base, bit 10 flips horizontally, bit 11 vertically, bits 12–15 select the palette bank. Character base is `(bg_control >> 2) & 3`, in 16KB units. Thus destination chunk = base × 8 + character // 64; byte offset within that chunk = (character % 64) × 32.
9. Decode each byte low nibble first, then high nibble. Palette index zero is transparent in every bank. RGB555 channels expand using `(channel << 3) | (channel >> 2)`.
10. Assemble sixteen minitiles in 4×4 order into a 32×32 metatile. Native metatile zero is implicit transparent blank. Apply the layout's bit-14 horizontal/bit-15 vertical flip to the entire assembled metatile, moving its minitiles as well as their pixels. Assemble layout cells row-major across the full room width.

Missing graphics/palette banks, inherited empty lists, unsupported bpp/storage/type, malformed source ranges and unterminated lists fail explicitly. No placeholder colors or prior-room resources are silently invented. Ordered loads and source indices matter: the first hallway selects palette rows far into the original palette list.

## Scope and effects

The PNG represents one static selected layer, at its own dimensions. It does not composite the other layers, room backdrop, entities, HUD, blend/brightness settings, color effects, scrolling/parallax, animated characters, alternate event states, slopes or collision overlays. The report preserves native layer controls and room `color_effects` for subsequent work; it does not claim to simulate them. Transparent pixels display according to the image viewer's background.

Type-1 and 8bpp layers, resources inherited from another room, full metatile brush availability and general VRAM allocation are unfinished. Inspection support does not expand the geometry write allowlist: terrain writes still target only the registered first-hallway main layer. Read GUI-EDITOR-ROADMAP.md before extending the editor-facing model.

## Verification and precise evidence

Run `python -m unittest discover -s tests` and `python scripts/verify_rendering.py` with the local private original, libretro core and Pillow-enabled development Python. Normal preview commands require only bundled Python.

The native verifier enters the first hallway through controller input, with no RAM writes. For the original and geometry-workshop ROMs separately it compares all eight loaded 2KB graphics chunks and all eight loaded palette banks exactly against the renderer's resolved resources. It then compares **7,217 opaque wall pixels per ROM** against the native viewport at GBA 5-bit color depth. All match. Native camera offsets are read from memory, not inferred from a screenshot. The sample is x48..207, y24..87 in the viewport, above actors and away from Soma; transparent pixels are excluded because other layers/backdrop render behind them.

An earlier sample started at x32 and overlapped Soma's head, producing forty mismatches. The documented actor-free rectangle fixes the test's scope; it does not tolerate mismatched terrain. The assertion still requires every sampled opaque pixel to match. The camera for this bounded fixture is [0,48]. Baseline/edited resource loads are identical, as expected when reusing existing metatiles. Separate geometry native tests validate walking/jumping/save/return at the edited step.

Synthetic tests cover nibble order, local and whole-cell flips, character base/page offsets, transparency, source/destination palette indices, malformed wrappers, missing resources, inherited-list rejection and PNG CRC/decoded scanlines. A private-host test proves rendering causes no mutation and that all changed preview pixels fall inside the one edited 32×32 cell. This does not certify every room or a whole-screen renderer.

Private evidence: `local/rendering-verification.json`, `local/rendering-{baseline,step}.png`, and corresponding `rendering-native-*.png` captures. `scripts/verify_rendering.py` leaves a private local patched fixture; it is not packaged.

## Important files and extension discipline

| File | Responsibility |
|---|---|
| `aria/rendering.py` | Bounded resource resolution, RGBA rendering and dependency-free PNG adapter |
| `aria/geometry.py` | Existing layer format, layout and checked terrain writes |
| `aria/compression.py` | Bounded LZ10 and Aria inner-header handling |
| `aria/cli.py` | `preview-room`, manifest application and private output guards |
| `tests/test_rendering.py` | Synthetic contracts and private-host pixel isolation |
| `scripts/verify_rendering.py` | Native resource/palette/pixel evidence |
| `docs/GUI-EDITOR-ROADMAP.md` | Frontend architecture, milestones and acceptance criteria |

Before adding another format, obtain source/runtime evidence, create synthetic orientation/addressing tests, then compare native loaded bytes and a bounded uncontaminated pixel sample. Keep GUI concerns separate from resource decoding. Never loosen the original-ROM hash gate to make an unsupported room render. Add clear capability flags and limitations when establishing new contracts.

A bounded read-only audit also renders all three selected layers in sector 0 rooms 0, 3, 6 and 31 (12 layers total). This establishes decode/render coverage only; native pixel/resource equivalence is checked in room 3 as described above. Private audit: `local/rendering-layer-audit.json`.


## Mixed resource inspection (v0.8.0)

See [MIXED-ROOM-RESOURCES.md](MIXED-ROOM-RESOURCES.md) for raw/LZ 4bpp and 8bpp load inspection, format guards, agent API contracts and remaining limitations. Full suite: 145 tests. Static survey: 343 slots, 6 rooms with load diagnostics. No additional write targets or 8bpp terrain rendering.


## Byte-index background inspection (v0.9.0)

See [BYTE-INDEX-BACKGROUNDS.md](BYTE-INDEX-BACKGROUNDS.md) for the separate read-only type-1/type-3 API and private lossless exports. All 24 native byte-index layers roundtrip; 149 tests pass. Rendering, collision semantics and write permissions remain pending. Existing type-2 consumers retain their contracts.


## Static background source rendering (v0.10.0)

See [BACKGROUND-RENDERING.md](BACKGROUND-RENDERING.md) for preview-background, 8bpp source APIs and native memory evidence. 153 tests; native character loads, declared palettes and a 1024-byte type-3 tilemap verified. Native viewport pixel matching remains unresolved; no new write permissions.
