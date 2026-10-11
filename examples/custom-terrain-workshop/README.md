# Custom terrain workshop

Run `TacticalSoul.cmd play examples/custom-terrain-workshop/mod.json` from the framework root. The first hallway gains a new authored stone metatile with solid collision; jump with native A to cross it. The existing paired save-room shortcut supports saving and returning.

The example creates a new arrangement of existing room characters. It allocates isolated visual/collision resources and leaves shared original tilesets, graphics and palettes intact. It does not import new pixel artwork. See `docs/CUSTOM-TERRAIN.md` for the schema, code guide, evidence and remaining limits.

Native verification: `python scripts/verify_geometry.py --custom-terrain`. Requires the local exact host, development libretro core and Pillow-enabled test Python; normal build/play needs only bundled runtimes. Keep generated games, images and private evidence out of releases.
