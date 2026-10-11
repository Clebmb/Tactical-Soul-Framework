# Toolchain, references and reproducibility

## Included local development tools

- Zig 0.15.2, Windows x86_64: tools/zig/zig-x86_64-windows-0.15.2/zig.exe.
  Source/release: https://ziglang.org/download/ . Used as ARM7TDMI Thumb C compiler,
  linker driver and objcopy. Distribution licenses are in the copied tool folder.
- armips 0.11.0: tools/armips.exe. Source: https://github.com/Kingcom/armips .
  The Mario example assembles its trampoline; the generic core uses original
  precompiled wrapper/entry templates. Do not confuse template binaries with
  extracted commercial code or runtime assets.
- Python 3.14.0 Windows embeddable: runtime/python/. Official source/release:
  https://www.python.org/downloads/release/python-3140/ . License included.
  Standard library builds; no installed Python required for player launching.
- mGBA 0.10.5 portable: runtime/emulator/. Official source:
  https://github.com/mgba-emu/mgba/tree/0.10.5 . Notices/source link retained.
- mGBA libretro DLL: tools/libretro/mgba_libretro.dll, a locally downloaded
  development core. Its exact file hash is recorded by the split inventory.
  It is a development dependency, not the same executable/version as GUI 0.10.5.
- Pillow 12.2 was available in the original system Python. It is used for actual
  frame capture by the ctypes harness; it is not required for ROM builds/Play.

The libretro core is not pinned to a reproducible source revision by the current
project. Preserve its file hash alongside test results and revalidate after
upgrading it. Tool presence does not establish authenticity beyond the original
official downloads/reference history; no signature audit is claimed.

## Reference knowledge

DSVEdit: https://github.com/LagoLunatic/DSVEdit . Local selected docs/constants are
under tools/references/DSVEdit. Important: AoS RAM map, ROM free space, room/entity/
door structures, native enemy/item/soul layouts. DSVEdit code is a source of facts,
not a bundled general room editor integration. Consult its own license/source
before redistributing derived code. This project's original APIs are independent.

SMA2 disassembly: https://github.com/KarisaAdvynia/sma2-disasm . Used for exact
companion identity/source offsets and native asset bank interpretation. The full
research clone remains in the original workspace tools folder; neither copied
project requires it to build. It is not packaged with a commercial ROM.

mGBA sources: https://github.com/mgba-emu/mgba . Used for emulator/libretro behavior.
Local Capstone and temporary probes helped inspect native code and tile banks;
they are research dependencies, not required player components.

## Compilation contract

Zig target thumb-freestanding-eabi, CPU arm7tdmi, -mthumb -Os -ffreestanding,
-fno-builtin -fno-stack-protector -nostdlib. Linker sets exact ROM origin and keeps
entry tick first. Wrapper calls tick through its Thumb address. Inspect ELF for
unexpected support routines/global data when expanding code. The generic compiler
tracks C/linker/bin hashes. Legacy Mario default build uses precompiled bins;
use Build.cmd --compile after C/ASM/generated-ABI changes.

Within Codex's restricted Windows sandbox, Zig sometimes cannot resolve its own
executable path; the earlier builds succeeded with an approved local compilation
escalation. This is an execution-environment issue, not a reason to alter native
addresses or remove version checks. Network downloads also required escalation;
no network is needed for ordinary copied-project builds or Play.

## Reproducibility boundaries

Hash-check exact originals, record output hash, record tool versions/file hashes,
keep code/data/ABI in agreement and run actual emulation. A binary hash is not a
proof of every gameplay behavior. Keep player saves isolated by output mod path.
The copied development folders include the user's private originals for local
continuity; allowlist packaging excludes them.
