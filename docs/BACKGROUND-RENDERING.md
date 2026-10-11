# Static 8bpp background rendering (v0.10.0)

This milestone adds a source-raster preview for byte-index backgrounds. Read
BYTE-INDEX-BACKGROUNDS.md first for the underlying type-1/type-3 records.
Source pixels are distinct from the transformed, composed native viewport.

```
TacticalSoul.cmd preview-background 4 0 --layer 1 --out local/cloud-source.png
```

The command writes a private PNG and JSON report under `local/`. It accepts
`--host` and `--mod`; it preserves input paths and rejects outputs elsewhere.
It needs no Pillow or emulator. Generated artwork remains private.

## Agent APIs and important files

`aria/backgrounds.py:expand_background_map(bundle)` validates a full export and
returns `(width_in_characters, height_in_characters, bytes)`. Stored metatiles
expand to a row-major byte-index tilemap. Implicit blank cells expand to character
zero. Flagged layout cells are rejected: their native behavior is unverified.

`minitile_8bpp(index, base_block, chunks, banks, modes)` reads character indices
0..255 at 64 bytes per character. Physical chunk address is
`base_block*8 + index//32`; byte offset is `(index%32)*64`. The final load mode
must be 8bpp, rather than inferring it from raw bytes. Palette indices address
the full 256-color BG palette as sixteen 16-color banks. Only actually used
nonzero indices require loaded banks. Missing banks raise PatchError; they are
never invented or inherited implicitly. Color zero is transparent.

`render_background(rom, sector, index, layer=1)` returns width, height, RGBA and
a report. It renders referenced characters only, requires the BGCNT 8bpp bit,
and preserves transparent implicit blank metatiles in its source raster. It
does not simulate camera scroll, affine matrices, scanline effects, mosaic,
animation, blend, backdrop, actors or other layers. Existing `preview-room`,
room-catalog and audit consumers retain their type-2 contracts. This standalone
API does not grant any new writes or claim every original background previews.

`tests/test_backgrounds.py` covers stride boundaries, sparse palettes,
transparency, incompatible modes, map expansion, flagged-cell rejection and a
private raster regression. The full suite contains 153 tests at this milestone.

## Native evidence and unresolved viewport comparison

Run `python scripts/verify_background_rendering.py` with the exact private host,
development mGBA libretro core and Pillow. The script creates a separate diagnostic
ROM with source-backed new-game constants set to sector 4 room 0 and position
128,128. Every patched constant has an expected original value. Constants come
from local DSVEdit `constants/aos_constants.rb`: sector 084F0D8C, room 084F0D8D,
X 084F0D92 and Y 084F0D94. These are fixture-only facts, not a new start-edit API.

Controller input boots the fixture. After the target room loads, verification
reads memory without runtime writes: all 20 declared 2KB character chunks, five
declared palette banks, and all 1024 expanded affine tilemap bytes match. BG2
control matches the selected layer except priority bits. Private screenshots,
fixture ROM and JSON evidence remain under `local/`; none enter the release.

The static source raster hash is
`bb6391f2a63b8aea7e46634e330feea74d2dd5369cec1a9ec09ea8b20f82e259`.
This deterministic hash is not proof of native viewport pixel equality.
An attempted viewport comparison using captured affine registers did not match.
A scanline effect is a hypothesis, not an established cause. Evidence records
`viewport_pixels_verified: false`. Do not cite this milestone as a pixel-perfect
8bpp viewport renderer. Type-1 native rendering and lifecycle reloads remain
unverified as well.

Next agent: establish how native affine state changes during a frame, or build
a controlled native fixture with those effects disabled through verified engine
calls. Then compare framebuffer pixels at native 5-bit color depth. Do not write
MMIO through raw libretro memory pointers and assume hardware side effects:
that diagnostic attempt did not produce a valid isolated display. No such writes
are used by the shipped verifier. After native validation, integrate background
catalog/dependency support and separately plan authoring ownership and transitions.


## Integrated background discovery (v0.11.0)

See [BACKGROUND-DISCOVERY.md](BACKGROUND-DISCOVERY.md) for catalog/audit schema version 2, format-aware dispatch and texel-derived palette dependencies. 156 tests; 925 nonempty layers inspect and all 24 byte-index source rasters render. No new write permissions or viewport verification. See [MODS-YOU-CAN-MAKE-NOW.md](MODS-YOU-CAN-MAKE-NOW.md) for current playable-mod examples and scoped agent prompts.
