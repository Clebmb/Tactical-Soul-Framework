# Registered native sprite artwork replacement

v0.25 adds the first checked actor-art writer: the existing Castle Corridor
decorative bats/clouds page and its optional palette. The `sky-invaders` example
contains original procedural UFOs. These are native game sprites, loaded and
drawn by AoS; no overlay or gameplay graphics RAM injection is used.

This is a **global reskin of one existing shared page**. Every native user of the
page/palette receives the replacement. It is not a per-room import, an enemy AI
editor, a new actor slot, a general OBJ allocator or a Soma streaming writer.
The existing 15 frames, four animations, part layout, behavior and resource size
stay unchanged. Read [sprite formats and previews](SPRITES.md) first.

## One-command workflow

From the framework root:

```
TacticalSoul.cmd build examples/sky-invaders/mod.json
TacticalSoul.cmd play examples/sky-invaders/mod.json
TacticalSoul.cmd preview-sprite background-bats --mod examples/sky-invaders/mod.json --frame 11 --out local/sprite-previews/invaders.png
```

Build/play create a separate ROM under `build/mods/sky-invaders/`. Walk right from
the opening courtyard into the first hallway. UFOs replace flying decorative bats
and clouds in the broken-window background. The engine's cloud blending remains,
so large saucers appear translucent. These decorative objects do not become
enemies or acquire collision. Existing actor AI and foreground enemies remain.

Copy the example folder for a new mod; change its safe lowercase manifest ID and
edit its sources. `invaders.json` is a 128x32 row-major indexed image, with 4096
integer pixels in 0..15. Zero is transparent. `palette.json` has exactly 16 RGB
triples with channels 0..255; output is quantized to RGB555. Values should normally
be multiples of eight for predictable colors. Palette index zero is transparent
regardless of its RGB color. `make_art.py` reproduces both files without reading
any ROM or extracted artwork. Regeneration overwrites authored edits to these two
files; run it only when that is intended.

## Manifest contract

Normal schema-1 manifests accept exactly one `sprite_assets` entry:

```json
{
  "schema_version": 1,
  "id": "my-sky-mod",
  "sprite_assets": [{
    "resource": "background-bats",
    "scope": "all_registered_consumers",
    "source": "invaders.json",
    "expected_page_sha256": "6f854783fd52be168b512c169451fa8b38ab96cbd8f3d788df7091706a8d3f3c",
    "palette_source": "palette.json",
    "expected_palette_sha256": "a7cc42d2dd4da92f764c24b7bd57d97718ada87709706cdfc33d4c3d8297df54",
    "provenance": "Describe your original artwork and license here"
  }]
}
```

The two palette fields are optional but must occur together. Omitting both keeps
the original shared palette. Unknown properties/targets, empty provenance,
incorrect hashes, changed wrappers/literals/current payloads, invalid pixels or
dimensions, and allocation/patch conflicts fail. Sources must be relative `.json`
paths resolved inside the manifest folder, at most 512 KiB each. Native writes
use the ordinary ROM allocator and conflict ledger. Build/report paths may not
overwrite the manifest or either sprite source.`sprite_assets` cannot combine with raw `patches`. It can combine with supported ordinary manifest sections, including room edits. Since v0.26 it is also accepted in **`tsf-project` modules**: `source`/`palette_source` resolve inside the owning module folder and are rebased to project-root-relative paths with asset fingerprints, duplicate resource names across modules fail naming both owners, and the composed manifest flows through the ordinary installer/ledger. See [project composition](PROJECT-COMPOSITION.md). `examples/sky-invaders/project.json` (module `modules/art.json`, shared art under `modules/assets/`) builds byte-identical ROM bytes to the flat `mod.json` (SHA256 `3b17a2fd90da7c332d0181c66da55583432d56b1a3013af3378ae9ed4b02f1bd`). The installer still requires exactly one entry per manifest, so multi-module sprite projects must provide a single entry today.

`install_sprite_assets(rom, entries, folder)` deep-copies the ROM and commits only
after the whole sprite batch succeeds. Late allocation/ledger errors preserve
the caller. This transaction covers the sprite batch; normal flat-manifest
application does not promise rollback of unrelated earlier/later domains. Source
files should remain stable during a build; this is not a concurrent asset store.

## Fixed source layout

Keep content inside the existing part rectangles. The page uses 8x8 packed tiles
on a 16-tile-wide source canvas; the author-facing JSON remains ordinary row-major
pixels. `aria/content.py:tiles` performs packing.

| Frames | Source rectangles (x, y, width, height) |
|---|---|
| 0, 1, 2 | (8,0,8,16), (16,0,8,16), (24,0,8,16) |
| 3, 4, 5 | (32,0,8,8), (40,0,8,8), (48,0,8,8) |
| 6, 7, 8 | (32,8,8,8), (40,8,8,8), (48,8,8,8) |
| 9, 10 | (56,0,8,8), (56,8,8,8) |
| 11 | (96,0,32,16) and (64,0,32,16) |
| 12 | (96,16,32,16) and (64,16,32,16) |
| 13, 14 | (0,16,32,16), (32,16,32,16) |

These rectangles are decoded from the verified host, not new frame definitions.
Part origins/order/flips still come from native records. Previews preserve signed
origins; a tight PNG's top-left is not necessarily the actor pivot. Blending,
movement, animation timing and spawning stay native.

## Binding and evidence boundaries

The exact host is enforced by `load_image`. Registration constants are in
`aria/sprite_assets.py` and source resolution in `aria/sprite_rendering.py`:

- Graphics wrapper `081CBE5C`: original eight bytes `0104100420bf5f08`, compressed
  source `085FBF20`, decoded 2048 bytes (128x32, 4bpp).
- Palette wrapper `08209EE8`: `00 04 01 00`, bank data `08209EEC`, 32 bytes.
- Sprite structure `0820FE44`: 15 frames, four animations.
- Observed graphics literals at `0804F1A0`/`0804F540`, palette literals at
  `0804F1A4`/`0804F544`, sprite literals at `0804F1A8`/`0804F5B4` are checked.
  These are ROM word observations, not recovered function signatures or proof
  that no indirect consumers exist. All users of the shared resources can change.

The writer preserves the original compressed stream and relocates a rebuilt
Aria-LZ stream into the checked ROM arena. It changes only the existing wrapper's
data pointer and, if requested, the existing palette's 32 color bytes. Source
length and inner header are preserved. It introduces no OBJ palette/VRAM grants,
frame expansion or runtime hooks. Three writes occur in the example: allocation,
pointer binding and palette. The original host file remains immutable.

`scripts/verify_sprite_assets.py` boots the original and final example naturally
and checks engine-loaded bytes, source palette and ordinary OAM parts. Native
2D OBJ loading uses a 32-tile destination row stride for the 16-tile source rows.
The harness finds the complete four-row pattern instead of assuming a fixed
allocation address. Initial observations put it at VRAM `06012200`, OBJ palette
bank 11. Those are observations, not allocation permissions for other actors.
The composed save-return/fresh-continue checks instead observed `06010200` and
bank 10. This confirms why neither graphics destination nor palette bank should
be hardcoded into a general actor authoring tool.

Opaque part pixel comparisons use actual native OAM position/size/flips and
RGB555 colors. Affine, 8bpp and blended cloud parts are deliberately excluded
from those comparisons. Their tile/palette bytes still receive the page checks.
Foreground occlusion is handled by seeking visible, fully matching ordinary
parts; this is sampled coverage, not certification of every rendered pixel.

Run `python scripts/verify_sprite_assets.py --lifecycle` for the final-example
entry/pause/reentry checks plus a **separate composed** room-workshop save shortcut
harness. The latter tests statue save, fresh continue and forced-HP death/fresh
continue followed by natural return to the hallway. SRAM is transported between
fresh emulator instances; HP is set to zero only for the death fixture. No
graphics, OAM, palette, position or terrain RAM is written. The composed harness
has a different ROM hash and does not certify the final example's full campaign.
Private evidence/screenshots and the harness ROM stay under `local/`.

## Agent responsibilities and next extension

- `aria/sprite_assets.py`: registration, input contract, original hash guards,
  literal checks, codec binding, staged write transaction and reports.
- `aria/sprite_rendering.py` / `aria/sprites.py`: independent static decoding and
  previews; inspect the same staged image that will be built.
- `aria/cli.py`: manifest dispatch, source protection, reports and `--mod` preview.
- `tests/test_sprite_assets.py`: original synthetic ROM fixture, format/path/hash
  failures, late rollback, deterministic private-host build and source guards.
- `scripts/verify_sprite_assets.py`: native proof and declared lifecycle fixtures.
- `examples/sky-invaders`: original art sources, reproducible generator and example.Static pointer-occurrence groundwork (2026-10-11, uninterpreted little-endian word counts, not consumer proof): the common structure/page words occur 77/90 times below `0x08700000`, Julius 7 times, and bats structure/page exactly twice each (the two checked literals). The common page is therefore broadly shared and an ordinary-enemy reskin must first identify per-subtype load paths before any writer is authorized. For the next actor type, establish its real graphics/palette/structure binding, all shared users, page sizes, native copies and lifecycle before authorizing a writer. Do not copy this registration's addresses or assume all enemies stream like bats. Prefer an ordinary enemy reskin with unchanged AI as the next slice;
player streaming and skeletal/boss effects require independent evidence. Add
native combat, damage/death, room transition and save/continue checks as relevant.
New frames/animations need source ownership, relocatable records and verified
native dispatch, beyond this fixed-page writer.
