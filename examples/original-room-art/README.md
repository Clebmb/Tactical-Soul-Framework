# Original room art workshop

Run `TacticalSoul.cmd play examples/original-room-art/mod.json` from the framework root. The first hallway gains a neon-brick step with original pixels/palette and solid collision. Default native A jumps across it; the paired native save-room shortcut allows save/return tests.

`neon-bricks.json` and `neon-palette.json` are original procedural artwork under MIT. The importer copies room load lists, appends one registered graphics chunk/palette bank, and preserves shared originals. Authored metatile 144 references the new artwork. No commercial pixel data is included in this example.

Read `docs/ROOM-ASSETS.md` for fields, pointer records, budgets, evidence, code responsibilities and limitations. Native test: `python scripts/verify_geometry.py --room-art`. Normal build/play and preview use bundled Python/mGBA; native tests additionally require local development libretro/Pillow. Keep generated games, screenshots and saves out of source releases.
