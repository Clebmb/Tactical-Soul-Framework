# Background discovery and resource contracts (v0.11.0)

Catalog and resource-audit schema version 2 integrate byte-index backgrounds.
This expands inspection and preview coverage, not modification permissions.
Read BACKGROUND-RENDERING.md for the unresolved native viewport comparison.

```
TacticalSoul.cmd room-catalog --sector 4 --offset 0 --limit 1 --check-rendering
TacticalSoul.cmd audit-resources 4 0 --out local/mixed-room-audit.json
```

## Agent and frontend migration

`aria/room_catalog.py:inspect_layer` dispatches type 2 to the existing terrain
reader/renderer and types 1/3 to `aria/backgrounds.py`. Unknown types remain
unsupported; malformed layers fail independently without aborting a page.
Stable room IDs and pagination are unchanged. Responses include no raster buffers
or private definition blobs, even when checking rendering.

Both catalog and resource-audit responses now declare `schema_version: 2`.
Consumers assuming every available geometry has collision data must migrate.
Check `geometry_format`: `terrain_4bpp` or `background_byte_index`. A background's
`geometry` summary follows inspect_background, including an opaque collision
pointer; it does not supply type-2 collision semantics. Preserve unknown fields
and check status before reading format-specific data.

With `--check-rendering`, background render summaries say
`static_source_raster_no_affine_viewport`. Available means source decoding
succeeded, never native viewport equivalence or safe edit permission. The
`viewport_pixels_verified` field remains false; a general catalog result is not
a claim about a previously verified narrow native fixture. Existing room-level
`terrain_write_registered` stays constrained by profile permissions.

`aria/room_resources.py:background_dependencies(indices, base, chunks, banks,
modes)` computes 64-byte character dependencies and inspects their texels to
identify needed palette banks. Color zero requires no palette data. Missing
chunks, incompatible load modes and truncated characters are distinct findings.
`palette_dependencies_complete` is false if required character data cannot be
decoded, so an empty palette list cannot be mistaken for no palette dependency.
`available` additionally requires every observed palette bank to be loaded.
Implicit blank metatile zero has no dependencies.

Audited layer entries identify tileset_type and format. Background entries retain
the existing metatile IDs, referenced flags, missing dependencies and
unavailable_referenced_ids shape. `source_preview_constraints` records unverified
flagged cells or missing 8bpp control separately from byte-level dependencies.
Neither availability nor dependency_observations_complete establishes brush
write safety, dynamic resource ownership, or native pixel correctness.

## Evidence and important files

`tests/test_room_catalog.py` checks mixed-room dispatch, scope and unchanged
write registration. `tests/test_room_resources.py` checks actual used colors,
incomplete palette knowledge, incompatible/truncated chunks, and layer isolation.
The full suite has 156 tests. `scripts/verify_room_catalog.py` surveys all slots
and all 24 byte-index source rasters. `scripts/verify_room_resources.py` surveys
static dependencies without altering the image, ledger or allocation state.

The exact private original has 343 base-state room slots, 925 readable nonempty
layers and 104 empty layers. All 24 byte-index backgrounds produce source rasters.
Six rooms retain load diagnostics; 34 rooms have unavailable referenced
definitions in at least one layer. These observations do not imply corrupted
native rooms: strict palette bounds and inherited loads remain unresolved.
The load-budget tilemap exclusions retain the earlier conservative reservations;
this milestone does not authorize allocating apparently unused memory.

Next: verify affine/scanline behavior, alternate-state and inherited loads, and
additional room resource ownership. Authoring expansion still needs native
transition/save/death tests. The GUI application remains deferred.


## Tilemap accounting and multiplayer feasibility (v0.12.0)

See [TILEMAP-MEMORY.md](TILEMAP-MEMORY.md) for corrected text/affine byte ranges and partial-chunk reservations, with 157 tests and native fixture evidence. No new write slots. See [MULTIPLAYER-FEASIBILITY.md](MULTIPLAYER-FEASIBILITY.md) for optional multiplayer research directions; no multiplayer feature is implemented.
