# Sprite structure inspection

This is a read-only backend for planning original actor artwork and a future
editor. It inspects structures and renders static frames, but does not yet replace
actor graphics or change native animation behavior. The separate
[registered sprite artwork writer](SPRITE-AUTHORING.md) now supports one fixed
bats/clouds page and optional palette replacement; icon and registered room-art
writers are also available. This inspector/renderer remains read-only.

Run from the framework directory:

```
TacticalSoul.cmd inspect-sprite common
TacticalSoul.cmd inspect-sprite julius
TacticalSoul.cmd inspect-sprite background-bats
TacticalSoul.cmd inspect-sprite unknown-actor
TacticalSoul.cmd preview-sprite julius --frame 0 --out local/sprite-previews/julius-0.png
TacticalSoul.cmd preview-sprite common --frame 30 --palette-bank 2 --out local/sprite-previews/common-30.png
TacticalSoul.cmd preview-sprite unknown-actor --frame 0 --out local/sprite-previews/unknown-actor-0.png
```

Inspection emits JSON to stdout and works with bundled Python. Keep any redirected
host-derived report under `local/`; do not ship extracted frame data. v0.25 adds
`--mod` to both commands. Python consumers can call `inspect_sprite(rom, pointer)` on a
staged RomImage; the normal host gate applies when loading that image.

## Contract and provenance

`aria/sprites.py` is an independent Python reader using format facts from
[DSVEdit sprite.rb](https://github.com/LagoLunatic/DSVEdit/blob/master/dsvlib/sprite.rb)
and registrations in the local DSVEdit AoS constants. No upstream implementation
was copied. Upstream master can change; the layouts below describe this reader.

All formats are little endian; addresses are GBA ROM pointers. Header `<HHIII>`
contains frame count, animation count, frame list, first animation and animation
pointer list. Frame `<IBBHII>` contains unknown32, hitbox count, part count,
unknown16, hitbox pointer and part pointer. Part `<bbH8B>` preserves signed x/y,
unknown16, graphics x/y, width/height, OBJ shape/size, graphics page, flip bits and
unused byte. Hitbox `<bbBB>` preserves signed x/y and unsigned width/height.
OBJ dimensions are decoded separately and discrepancies reported, never repaired.

Animation pointer entries retain nulls and aliases. Header `<HH>` gives step count
and function. Functions 1/2/3 have inline `<BBH>`, `<HHbbBB>` and
`<HHbbBBbbBB>` steps: frame/delay plus unknown16 or one/two hitboxes. Function 0
and unknown functions are diagnostic-only. Out-of-range frame references fail.
No delay timing, looping or sentinel behavior is inferred.

Counts are limited to 1024 frames, 256 animations, 128 parts/hitboxes per frame,
1024 steps per decoded animation and 32768 total record reads. Every fixed record
is repacked byte-for-byte during inspection. This validates decoding preservation,
not a writable sprite document or whole-resource serialization. Pointer alignment
and ROM bounds are checked. Unknown bits remain intact. Budgets are conservative
tool limits, not claimed native engine maxima.

Verified original registrations: common 126 frames/23 animations; Julius 75/31;
background bats 15/4; unknown-actor 21/9; unknown-actor-2 35/10. All inspect
without diagnostics and without ROM/ledger mutation. The unknown-actor
registration covers a single-referenced actor-table struct whose consumer is
unidentified (see [enemy binding](ENEMY-BINDING.md)); a magenta tracer
disproves hallway zombie/walker/mound/death use, and no writer exists.
unknown-actor-2 covers a second struct with static-only code-pool evidence
(Arachne create plus two helpers; live consumer unproven, hallway walker use
also disproven). Neither unknown registration may be described as zombie
artwork, and neither has a writer. Soma pointer 080E11C4 has one dummy frame but 83 animation entries whose
frame references exceed that frame list. It is deliberately not registered: real
player rendering dynamically swaps resources and needs a separate binding.

## Agent extension workflow

Start with `tests/test_sprites.py`: synthetic records cover unknown preservation,
aliases/nulls, unsupported functions, inline hitboxes and malformed boundaries.
The private-host test verifies the three registrations; it skips in source-only
packages. `aria/cli.py` supplies the command. No manifest field is added.

The first fixed-page original-art replacement is available separately in
[registered sprite authoring](SPRITE-AUTHORING.md), with native pixels and
transition/save/death evidence. Other actor types still need their own native
consumer and resource-sharing proofs. Do not interpret unused ROM/VRAM space as allocation rights.
General player reskins, new animation dispatch, enemy AI, extra actor slots and
arbitrary sprites remain unfinished.

## v0.24 graphics resolution and static previews

`aria/sprite_rendering.py` provides these reusable headless APIs:

- `read_sprite_page(rom, address)` returns indexed bytes plus wrapper/source
  addresses, length, dimensions, encoding and SHA-256. Raw pages begin after the
  four-byte header. Compressed pages use the pointer at wrapper+4 and validated
  `read_aria` decoding, including removal of the inner header.
- `resolve_sprite_resources(rom, name, palette_bank=None)` returns explicit
  registered pages, 16 RGB555 colors, and JSON-safe provenance. The default common
  palette bank is 3; some native consumers use bank 2. An override selects a
  **source** bank and does not allocate native OBJ palette memory.
- `render_sprite_frame(decoded_frame, resources)` returns `width`, `height`,
  `origin:[signed_x,signed_y]`, `part_count` and raw RGBA `pixels`. It has no file,
  emulator or GUI dependencies. Empty frames return a transparent 1x1 image.
- `preview_sprite(rom, name, frame_index=0, palette_bank=None)` combines inspection,
  resource resolution and rendering; its `report` includes provenance and RGBA
  hash. Python agents may supply a staged RomImage; the CLI previews the
  verified host, with v0.25 optional `--mod` applied on the staged image.

The CLI requires a PNG under the framework `local/` directory, resolves symlinks,
and preserves the host path. It writes the image and emits the report to stdout.
All extracted previews/contact sheets are private and excluded from release.

The sprite graphics canvas is **packed 8x8 tiles arranged 16 tiles per row (128 pixels), 4bpp**, low nibble first.
Each tile occupies 32 bytes. Source pixel (x,y) uses tile `(y//8)*16+x//8`, then byte `tile*32+(y%8)*4+(x%8)//2`. This is not a linear scanline byte stride. Source part coordinates
snap down to multiples of eight. Earlier part records draw last. Palette index
zero is transparent and does not overwrite lower parts. Flip bit 0 is vertical;
bit 1 is horizontal. Flips apply to the whole rectangle. Output is tightly bounded
to frame artwork; `origin` preserves the actor-relative pivot. Hitboxes are not
painted, and their bounds do not enlarge the image. Frames with different bounds
must be placed using their origins, not assumed to share a top-left pivot.

Only registered raw/Aria-LZ **4bpp** pages are supported. Each page must have
complete 128-pixel tile rows and be at most 8192 bytes; there is no implicit padding.
Raw size comes from header chunks*512; compressed size comes from the decoded
payload (the header chunk byte is retained as evidence). Palettes require the
observed 00/04/count/00 wrapper and a valid bank. Parts must have matching decoded
OBJ shape dimensions, supported flip bits, an available page and an entirely
in-bounds crop. Unsupported data fails instead of painting placeholders. Frames
are bounded to 512x512 pixels. These are tool budgets, not runtime grants.

The registrations use common page 081C15F4/palette 082099FC; Julius pages
081F42A4/081F52A8/081F62AC/081F72B0 and palette 0820C028; bats page 081CBE5C and
palette 08209EE8; unknown-actor raw page 082052F8 (4096 bytes) and 1-bank
palette 0820C550. Common has an 8192-byte raw page, Julius four 4096-byte raw
pages, and bats one 2048-byte decoded Aria-LZ page. All 237 source frames render
without synthetic padding. Common's shared resource serves multiple consumers;
one default palette cannot represent every native use.

`tests/test_sprite_rendering.py` tests nibble order, row stride, transparency,
layering, full-part flips, snapping, signed origins, compressed/raw decoding,
malformed wrappers, palette bounds, source crops, frame budgets and private output
guards. A private-host test renders all frames and checks no mutations.
`python scripts/verify_sprites.py` writes bounded metadata evidence to
`local/sprite-verification.json` and three private contact sheets. Contact sheets
center tight frames in frame-index order, row-major slots (12 columns, no labels); they are
inspection artifacts, not playable animation sheets. The RGBA hash of Julius
frame 0 is `169b79e78d8ead425f5a0370f265e8e88d88fc99e6407b1bca667fd2fceb85cc`.

Format/rendering provenance is the local DSVEdit `gfx_wrapper.rb`, `renderer.rb`,
palette wrapper and AoS constants. This original Python implementation has
synthetic pixel tests and exact-host static coverage. It has **no native pixel
comparison yet**. Runtime OAM ordering, transforms, blending, effects, resource
ownership, animation timing and transitions are not certified by a static preview.


## v0.25 native writer and evidence

The separate [sprite authoring API](SPRITE-AUTHORING.md) now replaces the fixed bats/clouds page and optional palette. Ordinary native OAM pixels match these static previews in the checked stages. Native cloud blending and arbitrary actor/runtime effects remain outside this static renderer. Historical v0.24 statements above describe that milestone; the v0.25 guide defines the newer writer and native evidence scope.
# Native palette tint example

See [CUSTOM-ROOM.md](CUSTOM-ROOM.md) for the snapshot-verified save-statue,
flame, save-particle and zombie source-palette tints. These shared palette
bindings do not establish zombie graphics-page identity or authorize general
sprite art replacement. The withdrawn hallway art-page render proof remains
withdrawn.
