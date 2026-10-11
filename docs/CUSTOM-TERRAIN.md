# Authored metatiles and isolated collision definitions

This milestone adds new type-2 metatile definitions to the registered first-hallway main layer. Each new 32×32 metatile defines sixteen 8×8 character descriptors and sixteen collision bytes. Visual and collision resources are extended in newly allocated copies; the original shared resources remain unchanged.

This is new terrain composition from existing loaded graphics, not imported original pixel artwork or a general VRAM allocator. It advances the total-conversion backend without implementing a GUI. Original graphics/palette imports and explicit room resource budgets are the next prerequisite.

## Run the example

```powershell
.\TacticalSoul.cmd build examples/custom-terrain-workshop/mod.json
.\TacticalSoul.cmd play examples/custom-terrain-workshop/mod.json
.\TacticalSoul.cmd preview-room 0 3 --mod examples/custom-terrain-workshop/mod.json --out local/previews/custom-terrain.png
```

The example appends metatile 144, an authored alternating-flip arrangement of an existing stone character in palette bank 1. All sixteen collision subcells use the existing full-solid byte 3. Cell x10,y5 changes from native metatile 53 to the new 144. The paired native save-room route is retained for regression. The manifest contains authored numeric bindings and layout instructions; no extracted graphics are packaged.

## Manifest contract

The existing `geometry_edits` entry may now include `metatiles`. Its original room/layer/layout-hash/cells fields remain required. Existing manifests remain compatible.

```json
{
  "id": 144,
  "minitiles": [4222,5246,4222,5246,5246,4222,5246,4222,4222,5246,4222,5246,5246,4222,5246,4222],
  "collision": [3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3]
}
```

IDs must append contiguously beginning at the current native count including implicit blank metatile zero. The hallway has 144 existing IDs (0..143), so the first appended ID is 144. One entry allows 1..32 definitions, with a total ceiling of 512 including blank. Every minitile is a JSON integer u16; every collision list contains exactly sixteen integers from **0 (empty)** or **3 (full solid)**. Booleans, slopes, hazards, one-way and other native collision kinds are rejected in this initial authoring contract.

Character descriptors use bits 0..9 for character index, bit 10 for horizontal flip, bit 11 for vertical flip, and bits 12..15 for palette bank. Arrange descriptors row-major in a 4×4 grid. Collision subcells use the same 4×4 spatial order. The current native test verifies an all-solid metatile; mixed empty/solid grids are encoded but do not have separate native gameplay certification yet.

Every authored descriptor must resolve against the room's actual graphics and palette loads, using the selected BG character base. Missing characters, missing palettes, inherited/unsupported resources and malformed wrappers fail before allocation. Definition IDs must exist when referenced by edited cells. At least one edited cell must use an appended metatile; an unused-definition-only entry is rejected. Layout dimensions, room identity and supported write allowlist are unchanged.

## Implementation and isolation

`aria/terrain.py` validates/encodes definitions and constructs new literal LZ10 resources. It preserves original decoded records, appends authored records and updates the Aria inner length while preserving the original low flag byte. `aria/geometry.py` plans all entry validation first, checks loaded characters/palettes through the rendering backend, clones the layout, allocates new visual/collision streams, clones selected metadata and the layer list, then patches only the room's layer-list pointer. The other layer entries retain their original pointers.

Original compressed resources are never overwritten. A different room referencing them continues to use the original definitions. Other layers in this room also retain their original tilesets. Existing graphics and palette lists are unchanged. New streams use the normal ROM allocation ledger and bounds. This is not an all-or-nothing rollback system for allocation/write failures; callers should discard a failed in-memory build and rebuild from the immutable original, as for existing build APIs.

Important files:

| File | Responsibility |
|---|---|
| `aria/terrain.py` | Definition bounds, native record serialization and isolated compressed stream extension |
| `aria/geometry.py` | Optional metatile schema, loaded-resource checks and copy-on-write pointer installation |
| `aria/rendering.py` | Character/palette resolution and previews of the resulting definitions |
| `examples/custom-terrain-workshop/mod.json` | Runnable authored arrangement and save route |
| `tests/test_terrain.py` | Definition bounds, preserved headers, isolation, rejection and determinism |
| `scripts/verify_geometry.py --custom-terrain` | Native custom-tile rendering/collision/jump/save/return evidence |

## Evidence and boundaries

All 127 unit tests pass. New tests reject wrong IDs, oversized definitions, invalid shapes, unsupported collision, missing graphics/palettes, unused definitions and duplicate cells; rejected validation leaves bytes, ledger and cursors unchanged. Isolated-resource tests preserve original compressed streams and prove repeated clean builds produce identical ROM bytes and ledgers.

`python scripts/verify_geometry.py --custom-terrain` passes the original geometry checks plus native custom-tile rendering. Baseline walking reaches world X329; the new custom solid tile blocks at X311; native A jumping reaches X458. Native saving, fresh-session continue and natural return walking stop at X360 on the other face. All **384 opaque pixels** in the sampled actor-free right portion of the new tile match the native viewport at 5-bit color depth. This validates native consumption of newly compressed visual/collision definitions, not merely a static preview.

Initial comparison uses the declared identical camera-relative X/zero-velocity fixture, retaining native settled Y. Return travel uses ordinary controller movement. No terrain, collision, graphics or palette data is injected into RAM. Private evidence is `local/custom-terrain-verification.json` and `local/custom-terrain-native-step.png`. The output ROM SHA-256 is `76ed49e31890762356c2c18f0aeafdcb59acc414abbef48be31d6c8a690aea82`.

Death, hardware, all collision kinds, other writable rooms, room resizing, new character imports and full-campaign interactions remain unverified/unimplemented. The native verifier currently shares generic geometry screenshot filenames for some captures; the custom summary and custom native-step capture have distinct names. Read ROOM-GEOMETRY.md, ROOM-PREVIEWS.md and the tracked roadmap before extending the contract.
