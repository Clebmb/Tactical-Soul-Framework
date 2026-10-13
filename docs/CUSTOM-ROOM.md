# Flesh sanctuary example and narrow authoring contracts

`examples/custom_room/mod.json` is a native two-room example, launched with its
`run_custom_room.bat` or normal TacticalSoul build/play. It starts a fresh game
in save room (0,31), exits right to hallway (0,3), provides a left return, imports
original flesh artwork and recolors statue/flame/save sparkles/zombies red.
This adds no GUI or campaign compiler. Framework estimate moves 32.0→32.3/100, still rounded to 32% (v0.39).

## New-game start

`aria/starts.py` adds ordinary-manifest `new_game_start` through a
registry of verified room/landing pairs: `{sector:0,room:31,
position:[128,141]}` and, since v0.45, `{sector:0,room:14,
position:[128,160]}` — a second ordinary save room found by scanning
all base slots for the statue entity signature (type 2, subtypes
28/29; 28 rooms match). Other starts/positions are rejected until
separately verified. The (0,14) landing is natively proven by
`scripts/verify_second_start.py`: fresh boot settles at world
(128,191) on the native floor, statue save at spawn changes SRAM,
and fresh-instance continue restores room-14 gameplay. It writes sector/room bytes at `084F0D8C`, resets camera
halfwords at `084F0D8E/90` to zero, and writes player coordinates at
`084F0D92/94`. All original preimages are checked before writing. Offsets come
from local DSVEdit `constants/aos_constants.rb` and the existing background
fixture; saved camera/player fields are described in its AoS RAM Map. Native
new-game testing establishes this exact room/camera/position combination.
This edits data constants; it introduces no callable ABI, hook or RAM claim.
Existing saves are unchanged. No intro progression or full-world certification
is implied. Since v0.40, project modules accept `new_game_start` (singleton), `palette_tints` and replacement terrain; full entity/door lists stay single-manifest by design.

## Isolated replacement terrain

`geometry_edits` now also accepts `metatile_replacements`, mutually exclusive
with appended `metatiles`. Each of 1..32 entries has the existing
`{id,minitiles,collision}` schema. IDs must be distinct, existing nonzero
definitions; sixteen descriptors resolve against actual room resources;
collision is still restricted to 0/3. Every replacement must occur in the
resulting layout. Existing layout preimages, registered main-layer allowlist,
dimensions, resource budgets and shared-source protections apply.

The installer rewrites those fixed records in newly allocated visual/collision
streams, preserving all other records, then installs cloned layout/metadata/
layer-list pointers. Original streams remain byte-identical. The report has
`custom_metatiles_replaced`; replacements leave the native definition count
unchanged. The example replaces IDs 1..4 in each room with two bright solid and
two dark empty panels, paints complete ceilings/floors/backdrops, seals the save
room left edge and corridor right end, and retains open crossing edges.

**Native failure boundary:** appending four definitions to the save room's 255
produced a black screen, startup substate 0/2 and no active palette. A single
appended ID255 loaded successfully; replacing four existing IDs also loads and
passes the final route/save checks. This is bounded empirical evidence, not a
complete diagnosis of the engine's decoder. New append writes reject counts
above 256. Read-only inspection still accepts the former structural range.

The dark backdrop covers underlying layers with non-solid main-layer pixels.
Native type-1/type-3 background writing and parallax composition remain absent.

## Native object palette bindings

`aria/palette_tints.py` adds ordinary-manifest `palette_tints`. An entry is
`{target:"zombie",style:"blood",scope:"shared-native-palette"}`. Four targets
are registered, with fixed 32-byte SHA-256 preimages and no arbitrary addresses:

| Target | ROM palette data | Observed consumer |
|---|---|---|
| save-statue | 0820C3A8 | Statue silhouette, 1,002 pixels in the idle magenta diagnostic |
| save-flame | 0820C3C8 | Small flame at statue chest, 126 idle pixels |
| save-particles | 0820C3E8 | Native saving sparkles, absent from the idle frame |
| zombie | 0820A630 | Corridor zombies, 1,811 pixels in the magenta diagnostic |

Source-bound method: native OBJ palette bytes were matched to exact original
ROM sequences, then one source palette at a time was replaced with magenta in
private ROMs. Repeated untinted controls had identical framebuffer snapshots.
Magenta statue/flame differences stayed in their respective silhouettes;
particle differences occurred during saving; corridor differences followed
zombie silhouettes while Soma retained native colors. Diagnostic address
observations and screenshots stay under `local/`. This establishes these
palette consumers, **not** the zombies' graphics page or general OAM ownership;
the earlier withdrawn art-page attribution remains withdrawn.

The blood transform preserves transparent index zero and maps every other
RGB555 color to luminance-weighted red with small green/blue contributions.
All entries validate before any writes. Duplicate/unknown targets, styles,
unacknowledged shared scope and changed preimages fail. The original Soma
palette is untouched. These are shared source edits, not room-local copies;
other native consumers have not been exhaustively surveyed. No texture overlay,
sprite animation edit or blood-tear effect is claimed. The white save flash
remains native and temporarily overwhelms particle colors.

## Route and encounters

Existing full `door_lists` serialize a right boundary x=1 in save room31 and a
left boundary x=255 in hallway3, with opposite destination/spawn pairs and
cleared secondary offsets. Only these doors remain in this isolated example;
external incoming links/map ownership are not campaign-repaired. The original
left decorative glow remains independent of the actual relocated door.

Existing full `entity_lists` retain hallway objects and move its original zombie
spawner to x256, with two identical-parameter spawners at x640/1024 and unique
IDs8/9. Original native AI and stats remain unchanged. This example-specific
native proof does **not** relax the conservative high-level encounter clone
templates or grant arbitrary spawner/resource provisioning elsewhere.

## Validation and important files

The full private-host suite passes **272 tests**. Normal build/inspect and the
static save-room preview succeed with bundled Python. The final ROM SHA-256 is
`8274a4ae94cf0afc41c85e29b344612666d7346553c5a7591909645853f18c11`.

`tests/test_custom_room.py` verifies exact starts/preimages, rejected inputs,
shared palette scope, transparency, deterministic clean builds, cloned resource
isolation, unchanged non-replaced records, reciprocal door boundaries and the
256-definition rejection. `scripts/verify_custom_room.py` checks fresh new-game
landing, exact VRAM and palette loads, controller-only right exit/left return,
nine simultaneous zombie slots, actual SRAM changes on native saving and
fresh-instance continue/resource reload. No position/HP/art RAM writes occur;
only native SRAM is transported for continue.

Since v0.42 the whole example composes as a six-module project
(start, tints, art, terrain, entities, doors) with byte-, ledger- and
allocation-identical results to this flat manifest; see [project
composition](PROJECT-COMPOSITION.md) and `tests/test_projects.py`.
Full entity/door lists use whole-room ownership and never combine with
staged room edits in one project.

`scripts/verify_custom_room_palettes.py` compares two identical untinted controls
to the final example: 1,128 idle statue/flame pixels differ, saving has visible
red sparkles, and 1,513 zombie pixels differ in the selected corridor frame.
It checks native zombie palette bytes and a player-only crop. Private evidence:
`local/custom-room-verification.json` and
`local/custom-room-palette-verification.json`. Native death, long sessions,
hardware and all-world palette consumers remain unverified.

REA skill was read and tool availability checked. No REA MCP tools are exposed
in this session; its read-only doctor failed with npm-registry DNS ENOTFOUND.
No setup/configuration was changed and no REA Evidence IDs/decompilation are
claimed. Evidence here is local source, static contracts and mGBA execution.
