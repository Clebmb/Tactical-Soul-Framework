# Ghidra query plan (GhidraMCP bridge)

Status: BOTH PATHS LIVE. Headless (`local/GhidraDecompileSouls.java`) produced
the first decompilations — see [SOUL-DECOMPILE.md](SOUL-DECOMPILE.md). The
bridge is also live against the operator's GUI session (xrefs + dispatcher
decompiles done); that session still lacks functions at `0x08026008` /
`0x08025f70` (manual D+F never stuck), so headless remains the path for new
addresses. All addresses are exact-host AoS USA r0;
ROM SHA-256 `910f88d3…36430a5`.

## Setup checklist for the operator

1. Open Ghidra, enable the GhidraMCP extension (Edit → Plugin Path / Configure).
2. Create a project, import `CastlevaniaAoS.gba` with the GBA Loader
   (base `0x08000000`, ARMv4T little-endian), run auto-analysis.
3. Keep Ghidra open; the bridge listens at `http://127.0.0.1:8080/`.

## Query order (evidence-backed targets first)

1. `get_program_info` — confirm base, language, image size 8,388,608.
2. `decompile_function_by_address` `0x08026009` — Winged Skeleton soul `code`
   (Thumb; strip the low bit → `0x08026008`). Expected: spawn/update routine
   for the slot-2 projectile actor. Record Evidence ID.
3. Same for `0x08025F71` → `0x08025F70` — companion actor in slot 3.
4. Xrefs/callers of both; xrefs of actor-window base `0x020004E4`
   (if data refs resolve) to find the spawn allocator.
5. Actor record layout: confirm 0x84 stride; identify which words the
   decompiled update writes at frames 7–61 (candidates: words 16/17 movers,
   word-8-zero observation, slot-29 word-4 hit flag).
6. SFX dispatch: search functions referencing the SFX song bank
   (`0x0827CD40`-family per docs/AUDIO-RECON.md) or voicegroup pointers;
   find the play-effect call and its sample/voice argument convention.
7. Fizzle gate: find the Up+B soul-cast path (MP check at `red_souls[1]`
   cost 12) and the count/arm state behind the first-two-casts-fizzle.
8. HP: locate the zombie damage path (30 HP) — the field our record scans
   could not find.

## Evidence rules

- Retain GhidraMCP references/Evidence IDs per finding in
  `local/ghidra-evidence/` (private, never packaged).
- Distinguish decompiler output (trusted) from our prior black-box
  inferences; correct docs where they disagree.
- No ROM writes from Ghidra; read-only analysis.
