# Two-room original art (v0.14.0)

Two main-layer targets now permit the existing checked room-art/terrain APIs:
sector 0 room 3 (first hallway) and sector 0 room 31 (save room). Each supports
one 2048-byte raw 4bpp character load at chunk 24 and one palette bank at 8.
Dimensions remain fixed; no other rooms or arbitrary slots are registered.

```
TacticalSoul.cmd play examples/two-room-art/mod.json
TacticalSoul.cmd preview-room 0 31 --mod examples/two-room-art/mod.json --out local/save-mural.png
```

The example composes the existing neon hallway obstacle and paired save-room
route with a contrasting non-solid mural in the save room. Both rooms use the
same physical character/palette slots but isolated ROM resources and load lists.
The save-room pixels exchange original procedural color indices and swap red
and green palette components. All source artwork is original MIT example data;
the patch requires the user's private original game.

## Agent authoring contract and important files

`framework/aos-usa-r0.json` adds only `[0,31]` to geometry_edit_rooms and its
explicit chunk-24/bank-8 room_asset_slots registration. `aria/room_assets.py`
retains preimages, source containment, fixed sizes, overlap checks and isolated
load-list installation. `aria/geometry.py` retains registered main-layer checks,
unchanged dimensions, definition/reference validation and collision bytes 0/3.
The implementation APIs are unchanged; this release expands tested permissions.

`examples/two-room-art/mod.json` edits one cell per room and appends one metatile
per selected visual/collision tileset. The save-room target is cell `(5,3)`,
original value zero, new metatile ID 255, descriptor 0x8200 repeated sixteen
times, collision zero throughout. The original save statue, entities, castle
map and room dimensions remain unchanged. The paired route is an intentional
existing example connection change; read ROOM-DESIGN.md before changing doors.

The save-room main layer has character base 2, so chunk 24 starts at relative
character 512. Existing graphics occupy other chunks; tilemap chunks 29..31
remain excluded. Palette bank 8 is not in the room's original static palette
loads. The initial audit is supporting evidence, not the permission grant:
native loading/reentry/save/death checks below establish the narrow registration.

The example's geometry and artwork are safe only within the tested scenario.
An agent can still create an impassable layout inside a registered room. Preserve
save-statue access, entry spawns and exits, inspect collision, and run native
tests for every meaningful authored layout. Registration is not certification
of every possible edit or engine event.

## Native evidence

Run `python scripts/verify_geometry.py --two-room-art --lifecycle` with the
development core and Pillow. It builds a separate example ROM, walks/jumps the
hallway step, reaches the save room, saves, continues in a fresh emulator, returns
to the hallway, pauses/resumes, triggers native death/Game Over, and continues
from post-death SRAM before returning again.

At save-room entry, fresh continue and post-death continue, all 2048 imported
character bytes and all 32 palette bytes match native memory, plus 400 opaque
mural pixels match the native framebuffer at 5-bit color depth at each stage.
The hallway separately matches 384 step pixels; return restores its different
art/palette and collision. Walking baseline X329 is blocked at X311 by the
step, native jump reaches X458, and return stops at X360.

Fixtures are explicit: initial hallway player X/velocity are set identically,
settled native Y is retained, HP is forced to zero for death, and SRAM is copied
between emulator instances. No terrain, collision, graphics or palette memory
is injected. Same-session Game Over menu continue and hardware are unverified.

Private evidence: local/two-room-art-verification.json and stage screenshots.
Output SHA256:
`762ba033bac901b96cd4bbdeaf068ced0aab451bbc99bcb3a5b37ccc023e341c`.
`tests/test_room_assets.py` checks two-room source isolation, contrasting loaded
assets, preserved original resources and rejection of an unregistered third room.
Full suite: 163 tests. Existing single-room output hash remains unchanged.

Next: a third ordinary room and validated traversal across a larger authored
sequence, then generalized resource planning. No resizing, new-room compiler,
general sprite animation, custom audible music or multiplayer is implemented.
