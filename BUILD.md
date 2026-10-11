# Tactical Soul Framework build and launch

Use TacticalSoul.cmd (or Framework.cmd) from this root:

- inspect --table enemies --index 0
- inspect --room 0 0
- build examples/native-balance/mod.json
- play examples/native-balance/mod.json
- play examples/frame-counter/mod.json --compile

Bundled Python is runtime/python/python.exe; mGBA is runtime/emulator/mGBA.exe.
The isolated-Python entrypoint is scripts/aria_tool.py. Installed Python can use
python -m aria. Host defaults to this root's CastlevaniaAoS.gba; --host or
TSF_HOST_ROM (or legacy ARIA_HOST_ROM) overrides it. No companion is needed. No network is needed.

Code compilation uses tools/zig/zig-x86_64-windows-0.15.2/zig.exe and the example's
link.ld/runtime.c. --compile updates runtime.bin and runtime.build.json. Default
build checks source/linker/bin hashes. Linker origin and hook must agree.
The compiler does not implement BSS/global initialization or arbitrary API ABIs.

Source wrapper is src/hook-template.asm. Its .open target is a private
build/hook-template.gba; assembling this template is not part of normal builds.
Original runtime/hook.bin and entry.bin already contain that wrapper/trampoline.
aria/hooks.py relocates the callback literal; do not blindly patch another entry.

Tests: python -m unittest discover -s tests -v; python scripts/verify_framework.py.
Native test capture requires Pillow in the test Python and local libretro core.
Package: python scripts/package_framework.py. Dev compiler/reference tools and
commercial inputs are excluded. Read docs/TESTING.md and docs/KNOWN-LIMITS.md.

Read-only native terrain previews: `TacticalSoul.cmd preview-room 0 3 --out local/previews/hallway.png`. Add `--mod examples/geometry-workshop/mod.json` to see the step. Outputs are private PNG/atlas/JSON, with no Pillow required. See docs/ROOM-PREVIEWS.md. Source-only packaging: update inventory, then run scripts/package_framework.py for version 0.3.0.

Custom authored terrain: `TacticalSoul.cmd play examples/custom-terrain-workshop/mod.json`. Run `python scripts/verify_geometry.py --custom-terrain` for bounded native validation. Current source-only archive is version 0.5.0; update inventory before packaging.
