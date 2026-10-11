# Existing-room stone-step workshop

From Tactical Soul Framework, run `TacticalSoul.cmd play examples/geometry-workshop/mod.json`.

The first hallway (sector 0 room 3) gains a 32px stone step at cell 10,5 by replacing existing metatile 53 with existing metatile 49. Native visual/collision resources are reused. Soma should stop when walking into it and cross using native A jump. A paired existing door connects the hallway's right end to native save room 31 and back.

Layout, selected metadata and layer list are cloned into free ROM space. Original shared data, room dimensions, map identities, native resources and scripts are preserved. The manifest contains numeric references only; no commercial geometry/art payload is distributed.

Read docs/ROOM-GEOMETRY.md for schema, format evidence, write restrictions, native fixtures, important files and extension guidance. The initial write API supports this room's main layer only. The native verifier's controlled position fixture is a test technique, not part of the shipped mod.

