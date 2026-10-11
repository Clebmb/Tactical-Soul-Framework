# Custom content: agent implementation and authoring guide

E adds asset conversion and explicit native ROM bindings. It composes with the D native mechanics SDK. The playable workshop replaces native item icon graphics and palettes with original diamond artwork. PCM sound import is implemented; native sound playback, music sequencing and instrument allocation are not. These distinctions matter: a successful ROM allocation does not mean the engine consumes an asset.

## Start and edit

From the independent Tactical Soul Framework folder:

```bat
TacticalSoul.cmd play examples/content-workshop/mod.json
TacticalSoul.cmd inspect --mod examples/content-workshop/mod.json
```

Start a new game, finish the entrance dialogue, press Start, select Item Use (Down twice), and press A. Obtain a Potion normally to see its original diamond icon. The first of three native icon pages is replaced, so not every game icon changes. Passive regeneration and R-button healing are inherited from the shared ability SDK. The original synthesized chirp is intentionally an unbound import fixture and is not audible in-game.

Copy examples/content-workshop into a new folder and change its manifest id before editing. Output and emulator save files are isolated by mod id. Edits never modify the original commercial ROM or the independent Mario project. No companion game is required.

## Asset source formats

Builds need only bundled Python's standard library. Asset files must resolve inside the manifest directory, including symlink resolution. Each content entry requires a unique safe lowercase id, format, source and nonempty provenance string. Report provenance is a declaration by the author, not automated license verification.

* `palette_rgb8`: JSON list of 1..256 `[R,G,B]` integer colors in 0..255. Each channel is truncated from 8 to 5 bits. Output is little-endian GBA RGB555: red bits 0..4, green 5..9, blue 10..14. No header or transparency metadata is emitted. Native palette entry zero commonly serves as transparency; its behavior belongs to the consumer.
* `tiles4`: JSON object containing exactly width, height and pixels. Dimensions are multiples of eight, 8..1024. Pixels are a flat row-major list with exactly width*height entries, each 0..15. Output traverses 8x8 tiles in row-major order, packs each row left pixel in low nibble, next in high nibble. Each tile is 32 bytes. This is raw character graphics, not a sprite animation, tilemap or resource wrapper.
* `pcm_s8`: uncompressed mono unsigned 8-bit WAV, 4000..32768 Hz, 1..32768 samples. Output flips the sign bit to signed 8-bit PCM. It preserves the sample count and records sample rate in reports. It does not resample, infer loop points, add a native instrument/sample header, assign channels, replace songs or call playback routines. Encoding with LZ77 is suitable only for a consumer that explicitly decompresses it.

Boolean numeric values fail. RGB conversion is deliberately lossy; index assignment and transparency are never guessed. Unknown formats and encodings fail.

For pixel artists, optional Pillow authoring adapter:

```bat
python scripts/import_indexed_png.py local/my-icons.png --out examples/my-content/art --palette-banks 7
```

Use a palette-mode PNG with indices 0..15 and index zero as the only transparent index. The adapter writes tiles.json and palette.json; it does not edit the manifest or quantize RGB artwork. Seven repeated palette banks match this workshop's icon palette replacement size; other targets need their actual consumer layout. Pillow is a development dependency, not required by TacticalSoul.cmd. The adapter handles static images only.

## Manifest contract and binding modes

```json
{
  "schema_version":1,
  "id":"my-content",
  "content":[{
    "id":"icons",
    "format":"tiles4",
    "source":"art/tiles.json",
    "provenance":"Original art by me, MIT",
    "replace":{
      "address":"0x081C5E04",
      "size":8192,
      "expected_sha256":"COPY THE EXACT TARGET PREIMAGE HASH FROM THE WORKSHOP"
    }
  }]
}
```

The example hash placeholder is deliberately nonfunctional. Use the runnable workshop for exact hashes. Manual bindings are expert-facing address-based contracts. Named target bindings for the four registered icon resources now provide a checked alternative; see RESOURCE-AUTHORING.md.

`replace` requires exactly address, size and expected_sha256. The encoded size must equal size; the current preimage hash must match. Every replacement uses the shared bounds and conflict ledger. Preserve native wrapper headers and change only their verified payload. A bigger image cannot silently overwrite neighboring ROM data.

Without replace, the encoded asset is allocated at four-byte alignment in declared free space. Optional `pointers` is a list of objects with exactly address and expected. Each expected value is the existing full u32 pointer; the builder writes the allocated address. Every site is checked and conflict-logged. Empty/absent pointers produces stored, unbound data. Reports identify mode, address, size, payload/source hashes, encoding, pointer count, provenance and PCM rate/sample count. Allocated addresses can move after changes; consume generated reports rather than hardcoding the current allocation address in C.

Optional encoding is raw (default) or lz77. LZ77 emits a standard GBA type-0x10 stream using literal groups, a 24-bit uncompressed size and four-byte padding. This encoder prioritizes correctness over compression ratio. It does not emit Aria-specific inner headers or choose a decompression destination. Some Aria structures require additional headers; generic compression alone is insufficient for those targets.

Content installs after the ability/frame callback, followed by sparse resource edits and then generic blobs/tables/rooms. This preserves the callback's fixed linked origin. Overlapping content/raw/table edits fail rather than choosing a winner. Failed in-memory builds are not transactional; discard the RomImage after errors and rebuild from the original.

## Verified native icon binding and evidence

Source provenance: local tools/references/DSVEdit/constants/aos_constants.rb identifies ITEM_ICONS_GFX_POINTERS `[0x081C5E00,0x081C7E04,0x081C9E08]` and ITEM_ICONS_PALETTE_POINTER `0x082099FC`. These constants point at resources, not mutable pointer slots. The first resource begins with original four-byte header `00 04 10 10`; the workshop preserves it and replaces 8192 bytes starting 0x081C5E04. The palette header is `00 04 07 00`; the workshop preserves it and replaces seven 16-color banks, 224 bytes, starting 0x08209A00. These sizes are bounded by the following known resource/observed header, not a general claim that every graphics header shares this layout.

Native menu loading selects needed icon tiles rather than copying the whole page contiguously. The verifier searches actual VRAM for nonzero custom tiles absent from the baseline, compares native menu rendering, and checks original ROM immutability. The test declares a one-Potion ownership fixture in both captures; no graphics/palette RAM injection is used. This verifies the demonstrated existing item-menu icon consumer, not animation metadata, all pages, hardware, campaign compatibility or every palette bank independently.

## Custom mechanics and agent workflow

Use abilities and content in the same manifest. Read ABILITIES.md before changing native code. Copy native/abilities into your mod as runtime and declare abilities.runtime to isolate changes. Preserve the single hook, state guards and RAM ownership; declare all headers as dependencies and use --compile. The const module registry composes mechanics, while content reports describe imported resources. There is no dynamic asset lookup ABI or auto-generated C asset header yet; establish one explicitly before consuming relocated data from a custom module.

Suggested agent prompt: “Read AGENTS.md, CUSTOM-CONTENT.md and ABILITIES.md. Copy content-workshop to a new mod id. Replace the indexed diamond artwork with original goofy potion icons while preserving source dimensions and checked native bindings. Build and verify native item-menu graphics. Document exact files, hashes, provenance and limits. Keep the original ROM and Mario project untouched.”

For a new sprite/weapon/enemy target, first establish wrapper format, decompression, load lists, palette bank ownership, VRAM capacity, tile indices, frame/OAM layout and animations. Replacing raw tile bytes cannot supply those missing contracts. Prove the target's new-game/continue/room reload/death behavior before expanding the catalog. Graphics allocation is distinct from allocating ROM bytes.

For sound playback, first establish Aria's actual driver, sample header and alignment, loop/rate fields, voice/instrument tables, sequence linkage and playback ABI. Add checked native bindings and an original audible fixture, capture emulator audio, verify timing/looping, pause/room/save behavior and coexistence with native audio. Do not write sound registers from the frame hook or guess an m4a header merely because both systems run on GBA. PCM import is a useful preparation step, not a completed sound engine integration.

## Files and checks

* aria/content.py: dependency-free codecs, source path rules, fixed-size/hash binding, allocation/pointer installation and reports.
* aria/cli.py: content manifest integration, build/inspect output and shared ordering.
* scripts/import_indexed_png.py: optional authoring adapter with Pillow.
* examples/content-workshop: original indexed pixel/color JSON, original chirp WAV and composed mod manifest.
* tests/test_content.py: colors, tile order/ranges, LZ literal layout, PCM sign conversion, preimages/conflicts/path escape and allocated pointer binding.
* scripts/verify_content.py: real native menu/VRAM comparison using private host and local libretro core.

Run `python -m unittest discover -s tests` and `python scripts/verify_content.py`. Native checks require local Pillow and the private libretro development core; these tools/private ROMs are excluded from the release. JSON builds and bundled GUI mGBA launching require neither development dependency. Evidence lives under local/content-verification.json and local/content-original.png / content-custom.png, excluded from distribution.

Unimplemented: arbitrary sprite/animation and palette-bank allocation, 8bpp graphics, native music/sample playback bindings, sequence composition, loop/instrument authoring, automatic asset discovery, dynamic native asset registry, scene text/font authoring, and full geometry/tileset integration. Extend these as explicit tested APIs, not unchecked manifest promises.

## Run evidence (2026-10-10)

73 unit tests passed; four native content checks passed. Custom icon bytes were observed at native VRAM 0x06013800. Existing ability lifecycle (13 checks) and hook/framework (6 checks) regressions passed after CLI integration. Optional indexed PNG import reproduced the workshop pixel/color JSON exactly. Output ROM SHA-256: `fc426aa22278dd36c2e5d4bd3f70e100f1990e4672abee36d5697b5566bf28b0`. The native fixture sets Potion ownership to one in both captures to expose the item-menu consumer; ordinary play requires obtaining an item normally. Palette conversion is unit-tested and included in the native example; the native verifier does not independently certify all seven banks.

## Named authoring extension

See [RESOURCE-AUTHORING.md](RESOURCE-AUTHORING.md) for all three native icon pages, named full replacements, selective tile/color changes, lossless local exports, automatic authored diffs and previews. The original content-workshop remains compatible. [TOTAL-CONVERSIONS.md](TOTAL-CONVERSIONS.md) separates current capabilities from the remaining conversion subsystems and defines the next engineering steps.
