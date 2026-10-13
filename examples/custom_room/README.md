# custom_room — Flesh Sanctuary

Double-click **run_custom_room.bat**, choose an empty file and start a **New Game**.
Soma starts beside the save statue. Press Up to save. Walk right through the
room edge to enter the five-screen (1,280px) zombie corridor; walk left to return.
The corridor ends at a closed flesh wall. This is an isolated two-room demo.

```powershell
.\TacticalSoul.cmd build examples/custom_room/mod.json
.\TacticalSoul.cmd play examples/custom_room/mod.json
```

Both rooms have original pink/red flesh walls and flooring, with darker organic
material filling the backdrop. Three native zombie spawners populate the
corridor; nine simultaneous live zombies were observed in native testing.
Zombies, the save statue, its flame and its save sparkles have blood-red palettes.
Stats, AI, native animation and Soma's palette are preserved.

The backdrop is opaque, non-solid artwork in the main layer; it covers the old
background rather than editing native parallax layers. The original decorative
white glow/niche on the save room's left remains, but the working exit is on the
**right**. Save activation still includes the native white screen flash, which
temporarily washes out the red particles. No fleshy statue texture overlay or
animated blood tears are implemented. Palette tints affect the shared native
resources, including their consumers outside this route.

Use a new save file for this example. Existing saves retain their original
locations; the demo is not a campaign conversion or a repaired castle graph.
Builds preserve the exact original and write a separate ROM under
`build/mods/custom_room/`. No ROM or extracted game artwork belongs in this folder.

`flesh-tiles.json`, `flesh-palette.json` and `make_example.py` are original MIT
procedural artwork/code. The generator recreates these sources and numeric
bindings using the private verified host; running it is optional. Normal play
uses bundled Python and requires no compiler or Pillow.

Native regression (development dependencies only):

```powershell
python scripts/verify_custom_room.py
python scripts/verify_custom_room_palettes.py
```

See [framework contracts and evidence](../../docs/CUSTOM-ROOM.md).
