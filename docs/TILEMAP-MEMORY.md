# Format-aware tilemap memory accounting (v0.12.0)

`aria/room_resources.py:bg_tilemap_ranges(rom, listing)` now reads each active
layer's tileset kind before deriving its physical background-memory interval.
The returned `{layer,start,end}` shape is unchanged; intervals are half-open.
This corrects the earlier text-map estimate applied to affine backgrounds.

| BGCNT size bits | Type-2 text map bytes | Type-1/type-3 affine map bytes |
|---|---:|---:|
| 0 | 2048 | 256 |
| 1 | 4096 | 1024 |
| 2 | 4096 | 4096 |
| 3 | 8192 | 16384 |

Map start remains `screen_base * 2048`. Empty layer pointers are skipped;
unknown metadata kinds, truncated metadata and ranges past 65536 are rejected.
Do not guess an unknown kind's size from its palette depth: text backgrounds
can also use 8bpp graphics. This contract uses the supported AoS metadata kinds.

The resource audit reserves every 2048-byte character chunk touched by a map,
including partial final chunks: end-chunk rounding uses `(end+2047)//2048`.
For example, the 1024-byte map at 61440 still excludes chunk 30. An exact
sub-chunk interval does not authorize sharing the unused half of that chunk.
The room-art importer consumes the same checked ranges, and retains explicit
profile registration and existing-load exclusions. No slots were added.

Evidence: hardware layout is documented in
[Tonc affine backgrounds](https://gbadev.net/tonc/affbg.html) and
[regular backgrounds](https://gbadev.net/tonc/regbg.html). Unit tests exercise
all eight size/format combinations, wrap rejection, unknown kinds and partial
chunk reservation. `scripts/verify_background_rendering.py` additionally checks
that sector 4 room 0 layer 1's computed range is exactly the 1024-byte expanded
map verified against native BG2 memory. All 343 base-room audits terminate;
925 nonempty layers inspect and no character/map overlaps are reported.

This remains static evidence. Native viewport matching, dynamic allocation,
alternate states, inherited loads and arbitrary room-art writing remain pending.
Schema version 2 is retained: the interval shape is unchanged, while previously
approximate affine interval values are corrected. Recompute stored audits and
budgets rather than assuming old intervals were exact.
