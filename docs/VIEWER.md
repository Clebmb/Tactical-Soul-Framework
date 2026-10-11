# Room viewer contracts (v0.37)

Headless view models for a future graphical viewer. No GUI is implemented;
`aria/viewer.py` is the data backend a viewer frontend would render from.

## What a view model holds

`room_view(rom, sector, index, layer=0, camera=(0, 0), viewport=(240, 160))`
returns one JSON-ready record per room view:

- `dimensions_cells` / `dimensions_px` (32 px per metatile cell).
- `visible_cells`: inclusive clamped cell ranges for x and y.
- `entity_markers` in view plus `entity_count_total`: `{id, x, y, type,
  subtype}` in native pixel positions.
- `door_markers` (all doors, not just in-view ones) plus
  `door_count_total`: `{index, x, y, side, destination}`. `side` comes
  from the room-editing boundary rule; off-boundary doors report
  `interior`. Door positions are native metatile units.
- `viewport_rgba` / `viewport_size`: the static layer render cropped to
  the camera/viewport overlap, plus `image_sha256` of the full render.
- `audit_errors` / `audit_warnings`: the static structural notes for the
  room. Markers are positions, not gameplay certification.

## Pure helpers

- `visible_range(room_cells, camera_px, viewport_px)`: clamped inclusive
  cell range for one axis; empty range when the camera sits past the room.
- `markers_in_view(markers, camera, viewport)`: point filter returning
  deep copies.
- `crop_rgba(rgba, width, height, camera, viewport)`: byte-exact crop of a
  `W*H*4` buffer to the overlap, possibly empty at the edges.

## Documents

`document_view(state_or_doc, room, fresh_image, manifest_applier,
renderer, folder)` builds the document's manifest state on two clean
images and requires identical viewport pixels and markers. `room` holds
`sector`/`index` plus optional `layer`/`camera`/`viewport`. The covered
native path previews the real `geometry-workshop` manifest on the hallway.
Real sprite/terrain sections beyond the existing renderer support stay
future work.

## Rules for frontends

Render from these records; never read emulator memory maps for layout.
Cameras outside the room yield empty ranges, never an error. Keep view
state (camera, selection) separate from authored document state.

## Tests

`tests/test_viewer.py`: pure-math tests always run; two native tests
(hallway view model, real-manifest document view) run with the private
host and skip without it.
