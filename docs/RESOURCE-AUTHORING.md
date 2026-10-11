# Native resource authoring and agent handoff

This milestone makes existing native graphics addressable by stable resource names, adds lossless local exports and sparse edits, and supplies two runnable examples. It is an authoring foundation for larger conversions. It does not implement arbitrary new sprite animations, background geometry, VRAM allocation or native audio playback.

## Implemented resources

Run these commands from the independent Tactical Soul Framework folder:

```bat
TacticalSoul.cmd content-catalog
TacticalSoul.cmd content-catalog --mod examples/sparse-content-workshop/mod.json
TacticalSoul.cmd play examples/named-content-workshop/mod.json
TacticalSoul.cmd play examples/sparse-content-workshop/mod.json
```

| Resource ID | Format | Payload | Units |
|---|---|---:|---:|
| item-icons-0 | tiles4 | 8192 bytes | 256 8x8 tiles |
| item-icons-1 | tiles4 | 8192 bytes | 256 8x8 tiles |
| item-icons-2 | tiles4 | 8192 bytes | 256 8x8 tiles |
| item-icon-palettes | palette_rgb8 | 224 bytes | seven 16-color banks |

All IDs are exact and profile-specific. A resource ID is neither an item ID nor an inventory index. An item can use several tiles, and multiple consumers can share tiles or colors. No item-name-to-tile mapper is implemented. Do not assume item-icons-1 means armor-only or item-icons-2 means weapons-only: the catalog names describe physical pages, not exclusive semantic ownership.

The named workshop replaces all three pages with original checker patterns and all seven banks with original colors. The sparse workshop changes two page-0 tile fragments and one color in each palette bank. These are deliberately distinct examples: whole-resource replacement for a reskin, selective edits for preserving unrelated graphics. Neither changes in-game text, native item effects or animations.

To see Equipment, finish entrance dialogue, press Start, Down once, A. To see Item Use, select Down twice from the first pause option and press A. Ordinary play needs an owned item such as Potion for its item-menu icon. The native verifier declares one Potion ownership byte in every baseline/custom capture, without injecting graphics or palettes into RAM. A fragment edit is not a promise that the complete Potion icon has been independently remapped.

## Export, edit, preview, diff and play

Native exports contain private original game artwork. Export/diff commands enforce outputs under this framework's local/ directory, excluded from distribution. They refuse to overwrite the host, input manifest, or diff source. Keep private working mods under local/mods/ if they retain native art; the release examples contain original artwork only.

```bat
TacticalSoul.cmd export-content item-icons-0 --out local/mods/my-icons/tiles.json
TacticalSoul.cmd export-content item-icon-palettes --out local/mods/my-icons/palette.json
```

The tile export is a directly importable width/height/pixels object. Palette export is a directly importable RGB array. There is no metadata wrapper to strip. Catalog output provides original/current hashes and provenance separately. Export with --mod to view an in-memory patched resource while still using the exact original as --host.

Palette RGB exports expand five-bit channels by shifting left three; this guarantees byte-identical RGB555 re-encoding for the supported palette. It does not reconstruct the pre-quantized artist colors. A palette with bit 15 set is rejected because the RGB format cannot preserve that extra bit. Every supported native resource has a byte-for-byte export/re-encode roundtrip test.

Edit the JSON or use an external pixel editor and the optional indexed PNG importer described in CUSTOM-CONTENT.md. No automatic quantization or item mapping occurs. For an optional preview (development Python with Pillow):

```bat
python scripts/preview_content.py local/mods/my-icons/tiles.json local/mods/my-icons/palette.json --bank 1 --scale 4 --out local/mods/my-icons/preview.png
```

The preview applies one 16-color bank to the entire sheet. It cannot reproduce per-item palette selection or OAM arrangements. Index zero is transparent in the preview. Scaling uses nearest-neighbor; scale is 1..8. Outputs stay under local/. Builds do not require Pillow.

After changing the sheet:

```bat
TacticalSoul.cmd diff-content item-icons-0 --source local/mods/my-icons/tiles.json --provenance "Local edited artwork; private working mod" --id my-icons --out local/mods/my-icons/mod.json
TacticalSoul.cmd build local/mods/my-icons/mod.json
TacticalSoul.cmd play local/mods/my-icons/mod.json
```

The diff command produces a complete runnable manifest containing only changed tile units, compared with immutable original bytes. For palettes, use the palette resource and palette source instead. To combine generated tile and color changes, merge their resource_edits entries into one manifest with a unique mod id. A generated diff can contain retained original pixels within a changed tile; it is not automatically a redistributable original-art asset.

No encoded changes is an error. Tiny RGB adjustments can disappear after five-bit quantization. Tile diffs require the original sheet dimensions, even if a differently shaped sheet would have the same byte length. Diff output cannot overwrite its source. Run diff without --mod: the baseline is always the immutable original, not an already-patched preview.

## Named full replacements

A content entry may now select a target instead of manual ROM bindings:

```json
{
  "schema_version":1,
  "id":"my-original-icons",
  "content":[{
    "id":"my-sheet",
    "format":"tiles4",
    "source":"art/page.json",
    "target":"item-icons-0",
    "provenance":"Original artwork by me, MIT"
  }]
}
```

Use a complete 128x128 indexed sheet for this resource. A target requires exact resource format, raw encoding and exact encoded size. It cannot combine with replace or pointers. The profile supplies known bounds, immutable original payload hash, native header bytes and source provenance. The current header is checked and the original payload is the expected write preimage. A preceding edit to the same payload fails rather than stacking patches.

Generic content allocations and address-based bindings remain available under their prior contracts. They are useful for explicit expert targets, not proof that the engine consumes newly allocated data. A named replacement stays at the native address and does not allocate ROM or VRAM. Reports include target and mode=named_replace.

## Sparse resource_edits contract

```json
{
  "schema_version":1,
  "id":"selective-colors",
  "resource_edits":[{
    "resource":"item-icon-palettes",
    "expected_sha256":"COPY original_sha256 FROM content-catalog",
    "provenance":"Original selective color change, MIT",
    "colors":[{"index":17,"rgb":[248,40,224]}]
  }]
}
```

The placeholder must be replaced; runnable examples contain exact hashes. Each resource occurs once per batch and requires resource, expected_sha256 and nonempty provenance, plus exactly one appropriate nonempty row list:

* tiles4 resources use tiles rows: index and pixels, exactly 64 indices 0..15 in row-major 8x8 order.
* palette resources use colors rows: index and rgb, three integer channels 0..255.

Unit indices are zero-based across the complete resource. Palette index = bank*16+color. Duplicate, boolean, out-of-range and unknown fields fail. The entry hash must match the registered immutable original hash. Every changed unit is checked against original bytes and claimed independently in the shared ledger. Tile claims are 32 bytes; color claims are two bytes. Header bytes and unclaimed payload bytes are preserved. Disjoint edits within one resource are supported through one batch; overlapping raw/content/table edits fail.

Planning validates the complete sparse batch before writing, but the overall manifest API is not transactional. A later shared-ledger conflict can leave its in-memory RomImage partially modified. Discard it after any error; CLI failures do not emit a normal build. A whole-resource content replacement claims the whole page, so it cannot be followed by sparse overrides to that page in the same build.

Order: ability/frame hook, generic/named content, sparse resource edits, blobs, native tables/equipment/enemies, room arrays/high-level room operations, raw patches. Existing hook origin is preserved. Reports include resource, format, indices, units_changed, bytes_claimed and provenance; final catalog hashes describe the complete patched resource.

## Profile registration and extending the catalog

framework/aos-usa-r0.json owns content_resources. The initial four entries derive from DSVEdit aos_constants.rb ITEM_ICONS_GFX_POINTERS and ITEM_ICONS_PALETTE_POINTER, plus exact original bytes:

* resource headers at 0x081C5E00, 0x081C7E04, 0x081C9E08: 00 04 10 10; each payload begins four bytes later and is 8192 bytes.
* palette header at 0x082099FC: 00 04 07 00; payload begins 0x08209A00 and is 224 bytes.

Those known headers are checked, not interpreted as a universal wrapper parser. Do not register a new target from a guessed address or infer dimensions from a familiar-looking byte. Establish immutable bounds/hash, wrapper/encoding, load consumers, palette interpretation and native evidence first. Extend codecs explicitly if the target is compressed or not tiles4/palette_rgb8. Record resource-sharing constraints and tests. New enemy/player/background targets also need their own graphics loading and animation/geometry contracts.

The catalog's current_sha256 is calculated after optional --mod. original_sha256 remains the exact profile baseline. It does not certify compatibility with independently patched ROMs: the framework still requires its exact original host. New regional profiles need independent evidence.

## Important files for agents

| File | Responsibility |
|---|---|
| aria/resources.py | named descriptors, header/hash guards, catalog, decode/export, sparse plans, authored diff |
| aria/content.py | existing codecs and generic bindings; routes named target replacements into resource layer |
| aria/cli.py | content-catalog/export-content/diff-content, build order and reports |
| framework/aos-usa-r0.json | exact resource IDs, original hashes, headers, bounds and dimensions |
| scripts/preview_content.py | optional Pillow preview; no native item layout inference |
| scripts/import_indexed_png.py | indexed PNG to JSON authoring adapter |
| examples/named-content-workshop | original full-page/palette source artwork and named manifest |
| examples/sparse-content-workshop | original selective tile/color rows and exact expected hashes |
| tests/test_resources.py | synthetic contracts plus optional private-host lossless roundtrips |
| scripts/verify_resources.py | native Equipment/Item Use comparison, shared fixtures, sparse byte preservation |

Read CUSTOM-CONTENT.md for codecs, ABILITIES.md for mechanics, and TOTAL-CONVERSIONS.md before broad conversion work. Preserve separation from the Mario project.

## Validation and scope

Run python -m unittest discover -s tests, then python scripts/verify_resources.py. Native checks require private exact ROM, local libretro core and Python/Pillow. Both examples build with bundled Python without the development core. Evidence: local/resource-verification.json and local/resources-*.png.

Native regression observes distinct original custom patterns from all three pages in menu VRAM, compares visible native menus, proves the sparse sample claims only 78 bytes and preserves every byte outside those claims, and checks native headers/original immutability. These tests do not map every item, test every palette bank independently, establish new animation formats, certify hardware, or prove all campaign/save interactions.

Suggested agent task: "Read AGENTS.md, RESOURCE-AUTHORING.md and CUSTOM-CONTENT.md. Create a private local/mods project. Export one named resource, author a small indexed change, generate a sparse diff, build and verify native menu rendering. Keep retained game art under local/. Document exact edits, shared tiles/palettes, fixtures and launch command. Do not invent item-to-tile mappings or replace unrelated assets."

## Verified milestone (2026-10-10)

89 unit tests passed, including synthetic resource guards and exact-host roundtrips for all four registered resources. Four new native resource checks passed; distinct custom patterns from pages 0, 1 and 2 were observed in native menu VRAM. The sparse example claims 78 bytes and preserves every byte outside those claims. Existing content (4), ability (13), and hook/framework (6) native regressions also passed after integration. CLI export, preview, diff generation and generated-manifest build were exercised.

Named workshop SHA-256: `5e1f8ce65d8d6023b58682b96c48df0cf4440eac8931c5217750e7ee1f5f6e0e`. Sparse workshop SHA-256: `569c044ff0375cd289d92959890bb9e0433c66ca0a2309d3ffaff537b7511631`. Private native evidence remains under local/resource-verification.json.
