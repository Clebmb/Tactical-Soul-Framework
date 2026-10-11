# Byte-index backgrounds (v0.9.0)

This is a read-only structural API for tileset types 1 and 3. It makes additional
native layers available for investigation and future authoring clients. It does
not add an 8bpp viewport renderer or permission to modify those layers.

## Agent commands

From the framework directory:

```
TacticalSoul.cmd inspect-background 4 0 --layer 1
TacticalSoul.cmd export-background 4 0 --layer 1 --out local/background-4-0.json
```

Both accept `--host` and `--mod` like existing inspection commands. Export files
must be JSON under this project's `local/` and cannot overwrite the host or mod
manifest. Exports include private game definitions; never distribute them.
The CLI layer default is zero, so select the intended background explicitly.

## Important files and API contracts

`aria/backgrounds.py` implements `inspect_background(rom, sector, index,
layer=1, full=False)` and `verify_background_roundtrip(bundle)`. They read through
the same bounded RomImage and exact-host gate as existing tools. Empty layers,
unsupported types, invalid dimensions, incomplete compressed definitions and
out-of-range layout references raise PatchError. This API returns diagnostics
through exceptions, rather than silently substituting missing data.

The common layer list contains three 12-byte records. Each points to the existing
16-byte metadata record. Width/height remain 1..15 screens, with 8x8 metatiles per
screen. Layout entries remain 16-bit values: the low 14 bits identify a metatile;
the two high bits are preserved. No runtime flip behavior is certified here.

Type 3 uses bounded Aria LZ10 visual resources. Type 1 uses a fixed raw 4096-byte
visual block. Each visual metatile contains sixteen byte-sized character indices
in stored order; there are no per-minitile palette/flip fields in this format.
An implicit blank metatile precedes stored definitions. The fixed type-1 block
therefore exposes 257 definitions including blank; do not truncate it to 256.
Compressed definitions must be nonempty, divisible by 16 and at most 8192 bytes.
The collision pointer is retained as an opaque address, including zero; it is
not decoded or assumed to match the visual definition count.

Summary responses include dimensions, addresses, source hashes, definition counts
and referenced metatile IDs. `full=True` additionally includes cells, metadata
hex and the private visual resource. The roundtrip verifier checks source hashes,
metadata consistency, definition references and the original compressed stream;
it returns exact source bytes as hex without patching a ROM. It is not an importer
or a hostile-document schema validator. No write path consumes these exports.

`aria/cli.py` exposes inspect/export commands. `tests/test_backgrounds.py` tests
raw/compressed fixtures, rejection paths, drift and all native byte-index layers.
`scripts/verify_backgrounds.py` writes a private reproducible survey. Existing
type-2 geometry, custom metatile authoring, room catalog and resource-audit format
support retain their prior contracts. Use this API separately for types 1/3;
those older consumers still report unsupported geometry for them.

## Evidence, limits and next steps

The implementation uses local DSVEdit `dsvlib/layer.rb` and `tileset.rb` format
evidence, not copied code. No reference tool is required by the release.
All 11 type-1 and 13 type-3 base-state layers inspect and rebuild visual/layout
source bytes exactly. The original ROM, ledger and allocations remain unchanged.
Run `python scripts/verify_backgrounds.py` with the private supported host, and
`python -m unittest discover -s tests -q` (149 tests at this milestone).

Structural roundtripping does not establish correct rendered pixels. Next,
establish native character addressing, palette residency, scroll/affine behavior
and transparent pixels using a controlled room fixture. Then add a format-aware
renderer and integrate catalog/dependency APIs. Keep type-2 collision writing
isolated. New background write permissions require native load/transition tests
and explicit allocation ownership evidence. GUI work remains deferred.


## Static background source rendering (v0.10.0)

See [BACKGROUND-RENDERING.md](BACKGROUND-RENDERING.md) for preview-background, 8bpp source APIs and native memory evidence. 153 tests; native character loads, declared palettes and a 1024-byte type-3 tilemap verified. Native viewport pixel matching remains unresolved; no new write permissions.
