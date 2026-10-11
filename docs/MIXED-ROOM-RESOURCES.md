# Mixed room graphics resources (v0.8.0)

Read this alongside ROOM-RESOURCE-AUDIT.md and ROOM-PREVIEWS.md. This milestone
extends resource inspection, not the registered room-art write targets.

## What is implemented

`aria/rendering.py:read_graphics` accepts raw and Aria LZ10 wrappers declaring
4bpp or 8bpp. It returns physical 2048-byte character-memory chunks and ordered
load records. Source and destination bounds, termination, compressed output
limits and payload lengths remain checked. A chunk is a memory unit; an 8bpp
character uses 64 bytes rather than the 32 bytes used by 4bpp characters.

`graphics_chunk_modes(records)` resolves the final bpp for each chunk. Later
loads replace earlier entries, matching the byte mapping. Preserve these records
when building frontend resource models; bytes alone cannot identify the format.

`minitile(..., chunk_modes=None)` preserves the existing bytes-only caller API.
Callers supplying a mode map must provide every referenced chunk as 4bpp.
`render_layer` and custom-metatile validation always supply this map. They reject
8bpp chunks rather than interpreting them as 4bpp pixels. Do the same in new
authoring APIs. The optional argument is compatibility, not format detection.

`aria/room_resources.py` reports `character_chunk_bpp` and per-metatile
`incompatible_character_chunks`. A present 8bpp chunk referenced through a 4bpp
definition is unavailable, but is not reported missing. JSON object keys for the
chunk map are strings; in Python they are integers. Implicit blank metatile zero
has no graphics dependencies. Existing audit fields remain available.

## Evidence and reproduction

Independent reader implementation was checked against local DSVEdit source
(`dsvlib/gfx_wrapper.rb`, `room.rb`, `renderer.rb`), synthetic raw/compressed
fixtures, and the exact supported private host. Reference tools and host data
are not release dependencies.

Run `python -m unittest discover -s tests -q` (145 tests at this milestone),
`python scripts/verify_room_resources.py`, and `python scripts/verify_rendering.py`.
Native verification needs the development libretro core and Pillow; the packaged
CLI renderer does not. Survey output remains private under `local/`.

The static survey covers 343 base-state room slots: 901 inspected layers, 104
empty layers, 24 unavailable layers. Rooms with load diagnostics fell from 32 to
6. Sector 4 room 0 mixes both bpp formats; its supported layer zero previews
without ROM or ledger mutation, while its type-3 layer remains unavailable.
Existing native 4bpp rendering regression is separate evidence; it does not
establish native 8bpp pixel decoding.

## Boundaries and next agent work

No 8bpp terrain renderer, 256-color palette model, type-1/type-3 geometry writer,
new import registration, inherited state resolver or GUI is implemented here.
Five palette ranges exceed the wrapper's declared row count; the guard remains
strict pending native evidence. One empty/inherited room has both unavailable
load lists. These diagnostics do not establish that the original game is broken.

Static unloaded slots do not prove safe allocation. Preserve background tilemap
exclusions and existing room-art registrations. To extend this work, establish
type-3/8bpp layer indexing and palette behavior using a native fixture, then add
format-specific readers and pixel comparisons before granting write access.
Keep inherited loads explicit until a prior-state contract is implemented.
