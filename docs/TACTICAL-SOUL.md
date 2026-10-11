# Tactical Soul Framework

A native, agent-oriented foundation for modifying Castlevania: Aria of Sorrow
(GBA, USA revision 0). Broad modding is the goal; the current core supports
records, checked patches, allocation, native room/entity/door structures, a
verified per-frame hook, build/inspection/launch and actual emulator tests.
It is not yet a full visual level editor or a complete campaign/save compiler.

## Quick start (Windows x64)

From this folder in PowerShell:

```powershell
.\TacticalSoul.cmd inspect --table enemies --index 0
.\TacticalSoul.cmd inspect --room 0 0
.\TacticalSoul.cmd build examples/native-balance/mod.json
.\TacticalSoul.cmd play examples/native-balance/mod.json
.\TacticalSoul.cmd play examples/frame-counter/mod.json
```

The bundled Python and mGBA are found automatically. Outputs go to
build/mods/<id>/<id>.gba with a mutation manifest alongside. Original ROMs are
never overwritten. If your original is elsewhere, use --host "C:\path\game.gba"
or set ARIA_HOST_ROM. Exact SHA-256 and size are required. The private development
copy already includes the user's exact Aria original; it must never be distributed.

For C edits in frame-counter:

```powershell
.\TacticalSoul.cmd play examples/frame-counter/mod.json --compile
```

Zig 0.15.2 is copied into tools/zig. Source/linker/bin hashes prevent silent reuse
of stale callback code. Embedded player builds need no compiler. The simple
fingerprint tracks explicitly declared dependencies. Add every included header to build.json dependencies; transitive includes are not discovered automatically.

## Agent reading order

- AGENTS.md and docs/START-HERE.md: scope, working baseline, boundaries.
- docs/HOW-IT-WAS-BUILT.md: actual engineering history and corrected assumptions.
- docs/FILE-GUIDE.md: source files, dependencies and generated/private data.
- docs/NATIVE-INTEGRATION.md and docs/ROM-AND-RAM.md: hook/ABI/address knowledge.
- docs/DATA-CONTRACTS.md: native manifests versus Mario-specific data sheets.
- docs/EXTENDING.md and docs/FRAMEWORK-ROADMAP.md: full mods and future mashups.
- docs/TESTING.md and docs/KNOWN-LIMITS.md: tested behavior and missing systems.
- docs/TOOLS.md: toolchain versions, source references and reproducibility.

The Mario-specific portions of shared research references describe the separate
Aria of Mario World project. Their src/data/script paths are relative to that
project, not missing dependencies of Tactical Soul Framework. Tactical Soul Framework builds independently.

## Python API example

```python
from pathlib import Path
from aria.cli import load_image
from aria.tables import read_record, edit_record

original = Path("CastlevaniaAoS.gba")
rom = load_image(original)
print(read_record(rom, "enemies", 0))
edit_record(rom, "enemies", 0, {"hp": 18})
report = rom.output("build/my-mod.gba", original)
```

Raw patches require expected preimage bytes. Table edits rely on the verified
whole-original hash. Overlapping writes and allocation exhaustion fail. Native
entity arrays preserve identity and sorting; graphics and map/save changes need
separate implementation. Follow docs/EXTENDING.md for deeper modifications.

## Tests

```powershell
python -m unittest discover -s tests -v
python scripts/verify_framework.py
```

The first needs no game/runtime dependencies. The second needs the private Aria
copy, Pillow in the chosen Python, and the copied mGBA libretro DLL. It exercises
real GBA execution and reports limits. Player launching uses bundled Python;
test-time Pillow is a separate developer dependency. See docs/TESTING.md.

## Rights and packaging

Original integration code is MIT. Nintendo/Konami game content is excluded from
redistributable archives. Python, mGBA and toolchain licenses remain separate.
Do not zip this working folder: it contains private ROMs and generated games.
Use scripts/package_framework.py for an allowlist archive. No framework files
have been uploaded or published to an external service.


## Room geometry foundation and project rename (2026-10-10)

The project is now **Tactical Soul Framework**, in its independent folder of the same name. Use `TacticalSoul.cmd`; `Dominance.cmd` and `Framework.cmd` remain aliases. See [rename compatibility](RENAMING.md) for environment variables and retained native ABI identifiers.

Read [ROOM-GEOMETRY.md](ROOM-GEOMETRY.md) before terrain work. `aria/compression.py` implements bounded LZ10/Aria resource reconstruction; `aria/geometry.py` inspects type-2 layers and applies checked, isolated existing-metatile edits. `inspect-geometry` and private `export-geometry` expose the source-backed format. `examples/geometry-workshop/mod.json` adds one stone step in the first hallway and composes the paired save-room route. Writes currently support only this registered main layer, unchanged dimensions and existing metatiles. New graphics, collision definitions, room resizing and full campaign compilation remain unimplemented.

Validation: 101 unit tests pass. `scripts/verify_geometry.py` passes eight structural/native checks: original walking reaches world X329, the edited step stops Soma at X311, native A jumping reaches X458, and fresh save/continue plus natural return stops at X360 on the other face. Initial comparisons declare a camera-relative X/zero-velocity fixture and retain settled Y; terrain is never injected into RAM. Private evidence stays in `local/geometry-verification.json`. See the geometry guide for format provenance, contracts, file responsibilities and next extensions.


## Static room previews and GUI editor goal

Read [ROOM-PREVIEWS.md](ROOM-PREVIEWS.md) for the implemented renderer, private PNG/atlas/report command, resource formats, API contracts and native evidence. `TacticalSoul.cmd preview-room 0 3 --out local/previews/hallway.png` works with bundled Python. Add `--mod examples/geometry-workshop/mod.json` to preview checked terrain edits. `aria/rendering.py` returns GUI-independent RGBA buffers; it does not modify ROM data. The atlas currently includes referenced metatiles only. Native checks match all eight graphics chunks, eight palette banks and 7,217 opaque wall pixels for baseline and edited rooms. The suite now has 111 tests.

[GUI-EDITOR-ROADMAP.md](GUI-EDITOR-ROADMAP.md) makes a graphical level editor an explicit goal and describes frontend/model boundaries, document/undo semantics, milestones and acceptance. No GUI, room catalog, layer compositor, complete brush catalog, inherited resources or 8bpp preview is implemented yet. Current source package: `release/Tactical-Soul-Framework-0.3.0.zip`. Update the inventory with `python scripts/update_inventory.py` before packaging. Native verification requires local development tools; normal previews do not.
