# Tactical Soul Framework — handoff to Muse Spark 1.3

You are Muse Spark 1.3 taking over a real, existing Aria of Sorrow ROM-modding framework. Read this entire document, then the listed source/docs, inspect the current files and continue implementation. This is a working backend, not a request to invent a new project or replace the native game with a browser demo.

## Standing user instructions — keep these in force

- When the user says **continue**, autonomously make concrete, useful progress toward a documented total-conversion framework. Select the next meaningful incomplete capability from the current roadmap, implement it, verify it and document it. Do not merely repeat tests, revisit the same narrow experiment indefinitely, ask what continue means, or stop at a plan. Ask a concise question only when a material decision truly needs the user's input; continue independent work when possible.
- Keep all important APIs, files, examples, constraints and native evidence documented so another agent can extend or radically repurpose the framework.
- A GUI level editor is a future goal. Build reusable headless authoring/inspection/testing APIs now; do **not** start the GUI unless asked.
- The user wants eventual full conversions: levels, terrain/collision, graphics/animation, weapons, enemies, souls/abilities, mechanics, sound/music, progression/events/maps and saves. They also want future mashups. Do not confuse current narrow demonstrations with total-conversion readiness.
- At the end of **every generation/turn**, update this exact `handoff.md` (renamed from `handoffprompt.md` on 2026-10-11; same contract, shorter name) before sending the final response. This applies to implementation, documentation and planning turns. Do not skip it. Preserve standing instructions and useful architecture; replace the latest-status section with what actually changed, current tests/evidence, incomplete work and the next concrete steps. If updating is technically blocked, explicitly disclose it instead of claiming it happened.
- Every final response must state concrete progress, verification and material limits; what is next; the current estimated framework completion percentage from the roadmap; and brief examples of mods currently possible. Say that the handoff was updated. Never increase percentages just to satisfy a status request. Also avoid getting stuck on narrow validation at the expense of missing authoring capabilities.
- After every generation, refresh the README status block near the top (current version, estimated completion percentage, and what can be built today) so it never goes stale.
- Original code is MIT and remixes are allowed. This does not grant rights to commercial game material. No public publishing/upload is authorized. The multiplayer question was feasibility discussion only; multiplayer implementation is not a current task.

## Latest status — refresh at the end of each turn

<!-- STATUS START -->
Updated (UTC): 2026-10-14T20:30:00+00:00

Current framework: **0.54.0-foundation**. Estimated completion: **36%** (35.8/100 weighted maturity points).

**Completed this turn:** pushed the working tree to `origin/main` (v0.38.0 → v0.54.0-foundation); Ghidra project files (`Tactical Soul Framework.gpr`/`.rep/`) left untracked as local toolchain state; ROM/saves/`local/`/`build/` excluded by `.gitignore`. 48th slice: SOUL FOLLOWS FACING — Left tap reverses flight (first sample dx +1.67M→−3.44M) but the skeleton still escapes (gap widens to −4.75M, freeze by frame 6; 5th miss, zero EXP). Next: skeleton-velocity check or boost-mailbox check; zombie formula untouched. 47th slice: MISS SEEN — soul-vs-skeleton tracking (words 16/17, no RAM writes) shows the soul already +1.67M right of the skeleton at first live sample, racing to +7.4M while |dy| closes: wrong-direction (victim left-behind, muzzle faces right). Prescription: face-left tap before cast. Full suite untouched 485/485 (no lib changes). 46th slice: MIRROR MISS (4th skeleton miss: zombie-exact timing from X115, 3 casts, stable boost, zero skeleton falls) ends blind retries — next is frame-by-frame soul-vs-skeleton position tracking (words 16/17) to see the miss distance; plus `casts_to_kill_for(hp, def)` framework helper + test asserts. Full suite 485/485. 45th slice: THIRD POINT CONFIRMS — parametrized probe at DEF 5 lands exactly 20 (200→180 single-frame, def_at_cast 5; `predicted` field baked in). Formula (45−DEF)//2 is three-for-three on distinct DEFs; `damage_vs_defense` test + docs promoted. Full suite 485/485. 44th slice: DEF ISOLATED — DEF-10 zombie mod takes exactly 17 (200→183 single-frame, n=2, victim def_at_cast 10; mod DNA verified DEF-only edit; fixed apply_manifest path-vs-dict crash at the cause). Formula damage = (45−DEF)//2 (`damage_vs_defense` + test, two-point fit; predicts skeleton 22; descriptor 27 out as raw damage). Full suite 485/485. 43rd slice: skeleton advance (X402) + 3-cast variant still misses (stable boosts on slots 29/37/43, zero skeleton falls/EXP); `0x80c43c5` statically eliminated (no DNA create/update hit in 113 rows — its +0x34 is not HP, all its falls are noise). Sharper plan fixed: zombie-DEF-raise mod (1→10, editable field) on the working zombie route isolates DEF in one variable. 42nd slice: second-victim census (zombie DNA[1] HP18/DEF1 vs skeleton DNA[2] HP20/DEF0, fixed 22-vs-23 decision table; `scripts/census_damage_candidates.py`, exit 0) + native skeleton pin harness proven but missing twice deterministically (workshop-shortcut route, 12→200 stable boost on slot 29, verified cast, ROM unchanged; boosted skeleton unhit while slot-31 `0x80c43c5` fell 12→0, `local/damage-pin-skeleton.json`; `scripts/pin_damage_skeleton.py`). Formula stays open; same miss-then-catch pattern as the zombie pin's early runs. 41st slice: pinned the 40th-slice 22-damage zombie result as framework API (`aria/projectiles.py`: `SOUL_ZOMBIE_PER_HIT_DAMAGE` 22, `total_damage`, `casts_to_kill`, +1 synthetic test; `docs/OWNED-PROJECTILES.md` item 3 updated from clamped 18 to single-frame 22, n=2). Full suite 484/484. FIRST DECOMPILER EVIDENCE (soul system) + owned-projectile budgeting model (483 tests). Headless `GhidraDecompileSouls.java` decompiled `FUN_08026008` (spawn/fly/burst/cleanup state machine) and `FUN_08025f70` (companion follower: pos = parent pos + vel); record map pins words 9/10 velocity and 16/17 position. Bridge xrefs/decompiles name shared spawner `FUN_080256ac` and global SFX dispatcher `FUN_080d7910` (652 callers) with soul spawn sound `0xe4`. New `docs/SOUL-DECOMPILE.md`; `docs/OWNED-PROJECTILES.md` binder items 1/2/4 now evidence-backed. New `aria/projectiles.py` + 9 synthetic tests. Full suite 483/483. New `scripts/trace_sfx_0e4.py` (20th slice, exit 0): SFX `0xe4` → song `0x08399BEC` → one C4 note → voice 92 (sampled-no-resample) → sample `0x083AE488` at 10,512 Hz / 0.30 s (`local/sfx-0e4.json`). New `scripts/render_sfx_0e4.py` (21st slice, exit 0): diagnostic WAV render (0.55 s, peak 128, RMS 39.9; energetically consistent in order with the cast excess, scales differ, no ear check; `local/sfx-0e4-render.wav`). Bridge round on the soul's callees (22nd slice): `FUN_0806d128` is an on-screen cull, `FUN_08001a00`/`1f3c` are tilemap probes (state-2 burst is terrain contact), `FUN_0803e058` writes OAM matrices, `FUN_0803b924` allocates the hitbox slot (word 25 = index, `0xff` = released), `FUN_08031ea4` sets spawn position — no enemy-damage write in the soul update; HP FOUND (25th slice, bridge): zombie update `FUN_0807a9ec` with +0x65 hit-mailbox hook; `FUN_0803f17c` overlap test; `FUN_0806b1fc` packet queue; HP is the short at record+0x34 gated by `FUN_0806ad24`, drained by `FUN_0806ae54`, death via `FUN_080421ac`. Per-hit damage MEASURED (26th slice): press-budgeted cast, one live projectile, slot 32 +0x34 falls 18->0 with +1 EXP kill (`local/soul-hit-damage.json`; `scripts/measure_soul_hit_damage.py`). Lifecycle probe (27th slice): east-door crossing clears slot 2 (tears cannot ride rooms); Start-menu pause mid-flight unproven (state stayed 1, natural despawn; `local/projectile-lifecycle.json`). Hitbox descriptor read (28th slice): `PTR_080260a0` -> struct `0x080e13bc` word 2 = descriptor `0x082308e8`; u16[0] = 27 is the damage candidate, consistent with the 18-HP one-cast kill as overkill clamped at zero (`local/hitbox-descriptor.json`; `scripts/read_hitbox_descriptor.py`, exit 0). HP-store site located statically (29th slice): exactly one `STRH #0x34` near drain/queue/gate at `0x0806b06a` (`strh r0,[r1,#0x34]`, fn prologue `0x0806af98`); its stanza is a ×36 table lookup (`ldrh [.., #0xc]`, twin store at `+0x2e`), no `LDRH #0x34` nearby — damage operand needs dataflow/Ghidra (`local/hp-drain-scan.json`; `scripts/scan_hp_drain.py`, exit 0; fixed a swapped STRH/LDRH-imm encoding mid-slice). Store table resolved (30th slice): stanza index-base pool is `0x080e9644` (36B records, damage-like `+0xc` values 1–650) with 27 absent in all 64 entries, same for `0x084f0b14`/`0x08118d24` — soul-27 does not flow through that table (`local/store-table.json`; `scripts/resolve_store_table.py`, exit 0). Render determinism + listening guide (31st slice): SFX WAV reproduces byte-identically; transient burst (centroid ~2,045 Hz, brightest 500–2,000 Hz, −20 dB at 0.30 s); operator ear check now a seconds-long listen (`local/sfx-0e4-listen.json`; `scripts/analyze_sfx_render.py`, exit 0). Twin-store census (32nd slice): one `STRH #0x2e` (twin `0x0806b07a`), zero `LDRH #0x2e` — the HP+angle pair write reads like spawn-init, not a damage subtract; zombie HP 18 = table index-1 `+0xc` is hypothesis only (`local/hp-drain-scan.json`; `scripts/scan_hp_drain.py`, exit 0). Spawn-copy CONFIRMED (33rd slice): the `0x080e9644` table is enemy DNA per ENEMIES.md; zombie DNA[1] (update `0x0807a9ed`) has HP 18 / EXP 1, exactly the native victim — the twin store is DNA→instance spawn copy, damage was never in that table; HP-subtract site still open (`local/spawn-copy.json`; `scripts/confirm_spawn_copy.py`, exit 0). Queue-builder decode (34th slice): bl targets land exactly on `080428b4`/`08042848`/`08001a00`, corroborating the bridge decompiles; no other `+0x34` access in `0x0806b000`–`0x0806b300` (`local/queue-builder.json`; `scripts/decode_queue_builder.py`, exit 0; fixed systematic +2 in BL resolution). Drain bounded (35th slice): `FUN_0806ae54` = `0x0806ae54..0x0806b0a2`, DNA stanza inside; zero register stores/subtracts/`LDRH #0x34`/death calls in body — subtract lives in callees or needs dataflow (`local/drain.json`; `scripts/decode_drain.py`, exit 0; fixed no-increment end-scan bug). Drain callees ELIMINATED (36th slice): all five decoded, zero SUB/register-store/struct-`+0x34` idioms (3 bounded-clean, 2 unboundable); fixed pc-relative `#0x34` false positive + prologue underflow crash (`local/callees.json`; `scripts/decode_callees.py`, exit 0). Remaining suspects: packet helpers, queue body, dataflow/Ghidra. Packet helpers + death path ELIMINATED (37th slice): both entries clean, both call death `0x80421ac` (corroborates 25th slice); death body clean too; most-called undecoded primitive `0x080415a8` named next (`local/packet-helpers.json`; `scripts/decode_packet_helpers.py`, exit 0). Static wall (38th slice): primitive windows + queue body clean, 4/7 bounded 0 idioms — HP write uses no halfword idiom; last static stone is full-word STR, else dataflow/Ghidra (`local/packet-helpers.json` rerun, exit 0). Word-store scan (39th slice): zero word-stores/loads at `+0x34`, zero register-STR across six decoded ranges — static elimination complete; fixed dropped-zero address typo caught by bounds guard (`local/word-stores.json`; `scripts/scan_word_stores.py`, exit 0). Lifecycle close (24th slice, bridge): allocator has one caller, `FUN_0803e6bc` is sprite release, `FUN_08000e14` despawns with word25=`0xff`; pool base has no other session readers. Hitbox round (23rd slice, bridge): `FUN_08039614` is a pooling dedup allocator, registrar `FUN_0803b924` has 396 callers (universal actor path), `FUN_08000fbc` is the 0x84-stride slot allocator (index to record+8); HP-subtracting match pass still open. Prior this log: pinned MP regen (19th slice): new `scripts/measure_mp_regen.py` fires one verified cast (80->68) then samples MP 11x30 frames, climbing 68->73 (~1 MP per 60 frames; `local/mp-regen.json`) — confirms the 18th slice's net-11 regen explanation and sets the spend-accounting rule. Prior this log: fizzle press-gate (17th slice) + equal-window audio with BGM-phase control (18th slice); headless-Ghidra Java decompile path launched (pending). New `scripts/probe_cast_hold.py` (holds 1/5/15 frames all fizzle on first casts: the count-gate counts presses, not held frames; `local/cast-hold-variants.json`) and `scripts/capture_soul_audio_equal.py` (cast window 1.75x peak / 1.7x RMS over a flat idle-vs-idle control: cast-attributed audio difference, still mixed BGM+SFX output; `local/soul-audio-equal.json`; first run exposed an MP-regen accounting confound — net spend 11, not 12 — corrected in-script, rerun confirmed (spent 11/fired True, cast-attributed verdict reproduced). New `local/GhidraDecompileSouls.java` headless postScript (plain headless runs no Python); first headless run executed it but failed compile (String vs Register at line 49) — fixed, relaunched as TSFHeadless3, decompile output pending. Prior this log: tracked the attributed zombie holder (narrowed negative). New packaged `scripts/track_zombie_hp.py` snapshots the `0x807A9ED` holder slots across all sword rolls to the kill; `docs/SOUL-PROJECTILE-TRACE.md` gains the narrowed section. No lib/test changes. Existing work preserved; no commits/uploads.

**Verification actually run:** 484 full-suite tests pass (targeted `test_projectiles` + `test_soul_projectiles` 22/22). Holder track (`local/zombie-hp-track.json`, 31 rolls, kill at 31, +1 EXP): start slot 30 static in words 4–15 (word 6 only 0→2); extended words-16–31 track (`local/zombie-hp-track.json`, prior 4–15 snapshot preserved): slot-30 word 16 drifts only from roll 26 (approach), slot-33 word 16 falls then flatlines and despawns 11 rolls pre-kill — HP record hunt exhausted (no u32/halfword fall); damage comparison done instead (`local/soul-hits-to-kill.json`): 1 live soul cast kills the zombie vs 8–31 sword rolls — soul out-damages sword ~10x per action, count-gate repeats (2 fizzles then fire). Slot-2 track stays negative (slash flashes only). Prior gate test (`local/cast-fizzle-gate.json`): count-gate, ~3-press budget. Prior probes (close1/close2 at x=36, context 4/1/0) disproved proximity; the watch shows zombie burst codes without our projectile, so liveness without MP spend is not a projectile. Standing pattern: first casts fizzle 5/5, third casts fire 3/3 (time-vs-count open). Tile set (`local/soul-projectile-tiles.json`) stays concrete. Prior HP hunt (`local/enemy-hp-scan.json`): slot 29 word 4 toggles per hit — a hit-confirm/invuln flag, not 30-HP. Per-pair kill-loop tracking separates hit-linked drops from 1/frame word-7 timers and approach-step bursts (slots 34/35); slot-2 words 4/23 zero early (roll 4) while EXP pays at roll 9, so slot 2 is not cleanly the victim. Next: absolute-value track of slot 2 from full HP to kill. REA retry after user-installed Java 25 + Ghidra (`GHIDRA_INSTALL_DIR=C:\Ghidra` verified) + GBA Loader extension: `open_binary` on the exact ROM still fails `unsupported binary format` — the server's format gate rejects GBA before any provider engages, and no provider/doctor tool is exposed. User setup correct; blocker is server-side. User installed ghidra-mcp bridge (LaurieWired, v2.0.0); a `ghidra` MCP server is now visible with decompile/xref tools, but `get_program_info` fails BACKEND_UNAVAILABLE (nothing listening at 127.0.0.1:8080) — Ghidra GUI with plugin + open ROM still needed. Wrote docs/GHIDRA-PLAN.md (setup checklist + ordered queries: soul code 0x08026009/0x08025F71, spawn allocator, SFX dispatch, fizzle gate, zombie HP). Awaiting user opening Ghidra. All prior evidence remains local mGBA/static work, not REA evidence. Original immutable. Inventory/package refreshed after final handoff edit.

**Next concrete work:** Skeleton-velocity / boost-mailbox check on the skeleton catch; then match-pass internals and tear-art acceptance; operator ear check (guide ready); dataflow/Ghidra (or native RAM watchpoint) for the HP write; then tear-art acceptance; then Ghidra follow-ups (xrefs/spawn/SFX/HP), a bounded owned-projectile subsystem proposal before any tear-art binding, and a BGM-mute control if one exists for true audio isolation.

**Remaining limits / unfinished work:** Framework 36% (35.8/100), no new maturity credit. Isaac-style tears with matching custom gameplay SFX are not supported yet: cast reliability (count-gate budgets ~3-6 presses), tile-art replacement permission, actor-to-entry binding, calibrated velocity, lifecycle (pause/room/death/save), and custom SFX dispatch remain unfinished — but per-hit damage (22 single-frame vs zombies, 200→178 n=2; supersedes clamped 18→0 overkill), kill attribution, the record map, the spawn sound chain, and the reskin target set now exist. Ability SDK still has no projectile/SFX API. Single-room/direction evidence only; broad audio lifecycle and hardware coverage pending. REA connected does not mean configured provider or GBA support.

<!-- STATUS END -->

## Required REA skill and MCP workflow (explicit user request)

Use the **reverse-engineer-anything (REA) skill and connected REA MCP** for ROM/native-binary reverse engineering. Read [REA workflow and host status](docs/REA-WORKFLOW.md) before the next binary investigation. The skill is installed on this host at `%USERPROFILE%/.agents/skills/reverse-engineer-anything/SKILL.md`; on another host, locate it through the agent's skill catalog and read the current SKILL.md. Prefer actual connected REA MCP analysis/evidence tools, bind the exact private ROM, reuse existing matching sessions, and retain source-bound Evidence IDs/limits. Do not invent REA calls or evidence when tools are absent.

Current tool observation (2026-10-12): the REA MCP advertises170 tools and
`binary_session({})` answered `open:false`. Ghidra provider reports unavailable:
GHIDRA_INSTALL_DIR is unset and the Java runtime was not found. Historical v0.26
`open_binary` rejected this GBA ROM as unsupported; no GBA analysis session or
REA decompilation/Evidence IDs were established. These are separate boundaries:
a connected MCP is not a configured provider or proof of GBA support. No provider,
configuration or host software was changed. Do not repeat the rejected ROM open
or setup diagnostics without a changed capability or resolved blocker.

### Muse Spark 1.3: execution expectations and next slice

Use the full applicable REA toolset and the established local tools to sustain
concrete implementation and verification. Select tools by the question and actual
session availability; calling every advertised tool is not useful evidence. Read
the installed REA SKILL.md first. Reuse exact-target sessions; use focused
`analyze_function`, `procedure_references`/`xrefs`, `read_function_instructions`,
`read_bytes`, call/value tracing and retained evidence views when the provider
admits the target. Preserve exact SHA/address/search bounds and unknowns. Use
`get_evidence_bundle`/`export_evidence_bundle` where available, under local/;
keep inline evidence when retained references are unavailable. Do not label
ordinary Python scans or mGBA observations as REA output. Summarize large session
responses in the tool orchestration layer instead of dumping their full catalog.

The user's concrete target is a custom soul firing Isaac-style tears plus
firing/impact SFX. **This is not supported yet.** Read
[custom projectile boundary](docs/CUSTOM-PROJECTILE-ABILITIES.md). Prioritize one
bounded native Winged Skeleton projectile consumer/spawn/render/collision/SFX
investigation, using its already verified acquisition/cast input route in
`scripts/verify_soul_cost.py`, before granting any new writer permissions. Build
an evidence-backed reusable API where feasible; do not spend repeated turns on
boot-song polish as a substitute for the missing gameplay capabilities.

Tools and reusable evidence to carry forward:

- PowerShell, `rg`/`rg --files`, Python standard library and `tools.apply_patch`
  for source work; preserve all existing staged/uncommitted changes. No commits.
- `TacticalSoul.cmd inspect/build/play`, exact-host `aria.cli.load_image`, staged
  domain writers, conflict ledger, source fingerprints and allocation budgets.
  Native C/header/linker edits require build `--compile` and regression tests.
- `scripts/emulator.py`: local ctypes mGBA core, controller-only routes, RAM reads,
  native screenshots and bounded audio capture. Only one core per process.
  The private tools/libretro core is not shipped. Keep ROMs/media/reports local/.
- `scripts/verify_music_tracks.py`, `verify_music_envelopes.py`,
  `verify_arrangement_lifecycle.py`: isolated/mixed controls, envelope contrasts,
  scene takeover and the unresolved Start-input sound probe. The probe produces
  no isolated SFX; its mixed/passive difference is not SFX coexistence proof.
- `docs/NATIVE-EVENTS.md`, `docs/SOULS.md`, `docs/ABILITIES.md`,
  `docs/ENEMY-BINDING.md`, `docs/SPRITE-AUTHORING.md`: prior bindings and withdrawn
  attribution claims. No existing generic projectile or gameplay SFX API.
- Full check: `python -m unittest discover -s tests -v`; retain log under local/.
  End every turn with exact handoff/README refresh, then
  `python scripts/update_inventory.py` and `python scripts/package_framework.py`.
  Verify inventory hashes, archive CRC/SHA/exclusions and an extracted bundled
  runtime feature build. Keep immutable original SHA gate; never package ROMs,
  saves, commercial assets or private development tools. No uploads/publishing.

If REA cannot admit the ROM, continue bounded source/static/local-native work;
state the blocker precisely. Any repair follows the installed skill's read-only
plan and required setup approval. Do not install a decompiler just to satisfy a
tool-count request or infer native ABIs from table fields.

## Framework location

The framework root is the folder containing this file: **Tactical Soul Framework**. The parent legacy workspace also contains a separate **Aria of Mario World** project and older files. All framework code edits, commands and outputs belong inside this framework folder. Set the working directory explicitly; the chat may start in the legacy parent. Do not edit or add dependencies on the Mario sibling while continuing this task. The framework was previously named Dominance; old command aliases remain for compatibility.

The user's private exact original is `CastlevaniaAoS.gba` in this root: AoS USA revision 0, 8,388,608 bytes, SHA256 `910f88d3701e6c9f99c0d63660c14c61d8b79b0c17bfd7b35a15185be36430a5`. Never modify it. `aria/core.py` verifies the host and keeps immutable original bytes. Patched ROMs go to `build/mods/<id>/`; private experiments and reports go to `local/`. Do not distribute ROMs, saves, extracted commercial artwork, native screenshots or private developer tools. The allowlist packager is the only release route currently evidenced.

## First reading and source navigation

1. `AGENTS.md`, `README.md`, this file, `docs/START-HERE.md`.
2. `framework/capabilities.json` for implemented versus unimplemented features; `framework/roadmap.json` and `docs/COMPLETION-ROADMAP.md` for weighted maturity and next work. Later milestone sections override older historical descriptions. The GUI application is excluded from the score.
3. `docs/FILE-GUIDE.md`, `docs/TESTING.md`, `docs/NATIVE-INTEGRATION.md`, `docs/ROM-AND-RAM.md`, `docs/DATA-CONTRACTS.md`, `docs/KNOWN-LIMITS.md`.
4. For the latest terrain work: `docs/PROJECT-COMPOSITION.md`, `docs/TERRAIN-PAINTING.md`, `docs/TERRAIN-SUPPORT.md`, `docs/NATIVE-CONNECTION-TESTING.md`, `docs/INPUT-REPLAYS.md`, `examples/bridge-route/README.md`.
5. For total-conversion/custom-content plans: `docs/TOTAL-CONVERSIONS.md`, `docs/RESOURCE-AUTHORING.md`, `docs/ROOM-ASSETS.md`, `docs/CUSTOM-TERRAIN.md`, `docs/GUI-EDITOR-ROADMAP.md`. Read the relevant domain guide before changing a binary ABI.

Do not assume a familiar engine format is fully established here. Distinguish local source evidence, static decoder observations, synthetic tests, native emulator evidence and remaining hypotheses.

## Architecture and current boundaries

- `aria/core.py`: exact image gate, bounds, mutation ledger/conflict detection, aligned allocations, immutable originals and separate output. Current arena is `08680000..08800000`. Do not bypass guards by patching the mutable bytearray directly. Planning APIs deep-copy the complete ROM object so failure cannot consume caller allocation state.
- `aria/projects.py`: schema-1 `tsf-project` documents with 1–64 ordered modules. Supported terrain/room-art/room-edit/encounter/balance/resource/table/full-list fields compose into a normal manifest; split terrain cells batch by room/layer, door/move/full-list ownership conflicts name both modules, and full lists exclude staged room edits. Assets resolve under their owning module folder; provenance records source/module/asset hashes. `apply_manifest` stages projects on a clone and commits only after all checks pass. Hooks/abilities/general content/raw patches/blobs are excluded from projects and remain single-manifest features. Read `docs/PROJECT-COMPOSITION.md`.
- `aria/sprite_assets.py`: v0.25 fixed 128x32 decorative bats/clouds page and optional 16-color palette writer. Explicit global shared scope, original hashes, wrapper/literal guards, confined JSON, relocated Aria-LZ stream and atomic sprite batch. Existing frames/animations untouched; no general OBJ grants. `examples/sky-invaders` is original MIT procedural artwork. `scripts/verify_sprite_assets.py --lifecycle` checks all 64 tiles/native palette/OAM opaque pixels; final example pause/reentry and separate room-workshop composed save/fresh/death/fresh-return are distinct hashes. Observed VRAM/palette changes on save return (06012200/bank11 to 06010200/bank10); do not hardcode engine allocation. Projects currently reject sprite_assets; normal manifests may compose supported sections. Read docs/SPRITE-AUTHORING.md.
- `aria/sprite_rendering.py`: explicit common/Julius/background-bats graphics/palette resolution and static frame RGBA. Pages use packed 8x8 tiles, 16 tiles per source row; never use a linear scanline stride. Source crops snap to eight pixels; earlier parts draw last, index0 transparent, whole-part H/V flips. Signed origins matter for frame pivots. CLI PNG output stays under local/. `scripts/verify_sprites.py` covers 237 frames and private contact sheets. No native pixel/OAM/resource ownership or sprite-write proof. Read docs/SPRITES.md and docs/ENEMY-BINDING.md.
- `aria/cli.py` and `scripts/aria_tool.py`: host-only inspect/build/play and authoring/diagnostic commands. Build/play take a **positional manifest path**; many inspection commands instead take `--mod`. Read `--help` for the current parser.
- `framework/aos-usa-r0.json`: verified host profile, memory symbols, narrow terrain registrations and room art slots. Adding a registration requires evidence, not changing JSON to suppress an error.
- `aria/rooms.py`: native metadata, entities, doors and sector spans. Twelve normal sectors contain 343 base room slots. Metadata is 36 bytes (`<HH8I>`). Room IDs refer to base table slots, not relocatable pointers. Alternate states have separate semantics.
- `aria/level.py`: sparse existing entity moves and paired existing door edits; original castle-map/save audit. Endpoints are `{room:{sector,room},door,spawn:[x,y]}`; spawn coordinates are pixels. Writer clears secondary offsets. One batch per touched door array avoids allocation/ledger conflicts. New room creation, map compiler and progression proof are absent.
- `aria/geometry.py`: type-2 main-layer read/roundtrip and checked cloned layout/metadata/list writes. Current registered rooms: `(0,3)`, `(0,6)`, `(0,31)`, `(0,5)`, layer 0 only, unchanged dimensions. Appended definitions are bounded, with collision bytes 0/3 only; full collision families are not established.
- `aria/terrain_plans.py`: rectangle paints of existing metatile descriptors, source-image/layout preimages, non-overlap/bounds checks, clone staging and emitted checked geometry edit. Dimensions use 32-pixel metatile cells. It is not an arbitrary-room editor or native collision certificate.
- `aria/terrain_support.py` if present: per-room static support/brush dependency diagnostics; a candidate is not write authorization or gameplay proof.
- `aria/room_assets.py`: original 2KB raw 4bpp chunk and palette import, isolated load lists and resource/preimage/budget checks. Room art imports currently registered for `(0,3)`, `(0,6)`, `(0,31)`, chunk 24/palette bank 8. Room5 terrain registration does not add room5 art provisioning.
- `aria/rendering.py`, `aria/backgrounds.py`, `aria/room_resources.py`, `aria/room_catalog.py`, `aria/room_states.py`: native source readers, static raster previews, dependency/tilemap diagnostics, paginated base-room catalog and bounded alternate chains. Type1/type3 byte-index backgrounds have read-only source-raster support; native affine viewport composition and all effects are not established. Static unused memory is not a runtime allocation grant.
- `aria/world_graph.py`: base-slot door observations and changes. Original graph: 343 nodes, 725 doors, no unresolved destinations, three edges without observed direct returns. A return means some destination door points back, not a guaranteed landing or progression-safe reciprocal endpoint.
- `aria/connection_plans.py`: isolated existing-door planning with exact patched-image hash and conservative no-additional-missing-return/no-unresolved policy. It produces review JSON, no output ROM. Intentional new one-way route policy is not implemented.
- Equipment/enemy/encounter/content modules and registered ability SDK exist. Arbitrary enemy AI, resource provisioning, complete native item/soul/EXP grants, persistent custom mechanics and full custom weapon behavior remain incomplete; read current guides/capability flags.
- PCM source import exists; native audible playback binding/music/instrument authoring do not. Sprite/frame/OAM/animation provisioning and global VRAM ownership remain major custom-content gaps.
- `aria/input_routes.py`: bounded input descriptors with segment-end assertions, standard library only. A passed descriptor is not automatically a completed gameplay goal.
- `scripts/emulator.py`: local ctypes libretro mGBA driver with Pillow video capture and same-instance in-memory checkpoints. Checkpoints are private transient core state, not SRAM saves or portable files. Restore clears keys and invalidates video until another frame runs. Keep one active native core per process.

## Commands and environment

Use PowerShell from the framework root. `TacticalSoul.cmd` uses the bundled standard-library Python and supports ordinary builds without system packages:

```powershell
.\TacticalSoul.cmd --help
.\TacticalSoul.cmd build examples/bridge-route/mod.json
.\TacticalSoul.cmd play examples/bridge-route/mod.json
.\TacticalSoul.cmd plan-terrain --spec examples/bridge-route/terrain-plan.json --out local/terrain-review.json
.\TacticalSoul.cmd world-graph --mod examples/bridge-route/mod.json --out local/bridge-graph.json
.\TacticalSoul.cmd terrain-support --limit 32 --out local/terrain-support.json
.\TacticalSoul.cmd plan-project examples/bridge-project/project.json --out local/project-plan.json
.\TacticalSoul.cmd build examples/bridge-project/project.json
```

Use the locally installed Python with Pillow for native verification; this environment has `C:/Python314/python.exe`. Bundled `runtime/python/python.exe` has no Pillow and runs isolated path configuration; CLI bootstraps the root itself, while ad-hoc imports/unittest may require inserting the root into `sys.path` explicitly. The harmless Python location warning has appeared on successful runs; judge by exit status and assertions.

```powershell
C:/Python314/python.exe -m unittest discover -s tests -q
C:/Python314/python.exe scripts/verify_bridge_route.py
C:/Python314/python.exe scripts/verify_geometry.py --bridge-route --lifecycle
```

Native tests require the private host and existing local `tools/libretro/mgba_libretro.dll`. Do not claim native evidence if those are unavailable. Many private-host tests skip without the ROM, so distinguish a source-only passing suite from a fully reproduced run. Native source callback changes require compilation and relevant checks (`--compile`); ordinary JSON/terrain changes do not need native compilation.

Before packaging, update documentation/handoff and source inventory, then package sequentially:

```powershell
C:/Python314/python.exe scripts/update_inventory.py
C:/Python314/python.exe scripts/package_framework.py
```

Read/modify Markdown with UTF-8 explicitly. Do not race inventory/package commands against unfinished processes. Validate archive CRC, inventory hashes, private-file exclusion, clean extracted bundled CLI and deterministic build hashes. Never change source/handoff after inventory/packaging without refreshing both. Record final package SHA in the chat or package inventory, not inside an already-hashed handoff file.

## Native evidence and known traps

Keys: Right=7, Left=6, A jump/confirm=8, B attack/cancel=0, Start=3, Up=4. Hold A long enough for the intended jump; one-frame taps failed to clear the authored hallway step. Wait for gameplay state 4/substate 1; room pointer changes before loads settle. World position is player halfword plus camera halfword: X `02000526 + 0200A09A`, Y `0200052A + 0200A09E`. These are observed AoS USA addresses, not a universal API.

Native pause must settle before B cancellation. HP `0201327A` can be set to zero only as an explicitly declared death fixture; native death reaches player state 16 and later game state 5. Fresh post-death continue uses SRAM copied after GameOver; same-session GameOver-menu continue remains unverified. Neither a transient core checkpoint nor a room pointer observation proves save compatibility.

Room5's original central platform resisted a 28-candidate single-jump sweep; that was not proof of impossibility. Do not spend repeated turns on that old sweep. The separate bridge redesign clears columns 2..13 in rows 3..4 and paints solid surface metatile 6 in row 5. Thirty-six cells are painted, twenty-two change. Reused original visual/collision resources and the source layout are preserved; a cloned layout chain is installed. Native input-only full bridge crossings now pass both directions. See the guide for exact fixture distinction.

The playable bridge-route build retains the three-room original-art main route, plus the neighbor repairs and room5 redesign. A **separate native entry harness** redirects the hallway to the bridge to test neighbor crossings. Main-route save/death/fresh-continue is tested separately on the actual final build. Do not describe these as one continuous campaign-access/save proof. Neighbor branch event/campaign access, physical hardware and full world regression remain unverified. No new rooms or total conversion are claimed.

## Golden images and evidence locations

- Unmodified original: `910f88d3701e6c9f99c0d63660c14c61d8b79b0c17bfd7b35a15185be36430a5`.
- Three-room-art example: `10e002682d906fb4f25c090aa1988d2fdea368c7aa3f5092213cbd7b8c5fba3f`.
- Static neighbor proposal against that example: `a08505a0d2d355e20d37d8da88f92929938724c4d8c9103fd1c7c375cb299907`.
- Separate bridge-route final build: `bbe3d4b0cc80eee76bec1c77322050caf4547b9641c4e450457bbf22fe7fe840`.

Primary private evidence: `local/bridge-route-traversal-verification.json`, `local/bridge-route-lifecycle-verification.json`, plus current terrain-support verification if present. Source index: `docs/PROJECT-INVENTORY.json`; it embeds bounded historical summaries, not proof that they were rerun this turn. Keep earlier example hashes unchanged unless a deliberate example change is required and documented.

## How to choose and finish the next continue turn

Prefer an incomplete capability that meaningfully increases what users/agents can author. Good next work: evidence-based broader terrain support; reusable authored project/manifest composition with conflict diagnostics; custom sprite/frame/animation resource preparation and verified native binding; original sound binding; native grant/lifecycle APIs. Choose a bounded vertical slice and carry it through implementation, useful tests/native evidence where relevant, agent documentation, examples and packaging. Do not promise all domains in one turn or infer binary semantics from field widths alone.

For candidate rooms, inspect static diagnostics, preserve shared resources, prove a narrow native edit and only then register explicitly. For custom content, source preparation without native loading is partial. For new mechanics, establish ABI, RAM ownership and lifecycle first. Keep existing playable examples separate and working.

Before final response: run appropriate checks, update capabilities/roadmap if justified, refresh this document's latest-status section (including unresolved work), refresh inventory and package if making a release, then report progress, next work, estimated percentage, current mod examples and that this handoff was updated. This update requirement is mandatory every turn.


## v0.23 sprite structure backend

See [Sprite inspection](docs/SPRITES.md) for `aria/sprites.py`, registered common/Julius/background-bats resources, bounded frames/parts/hitboxes/animations, and lossless fixed-record checks. Run `TacticalSoul.cmd inspect-sprite common`. For files under docs/, the guide is `SPRITES.md`. 209 tests pass with the private host. This is read-only: actor rendering/replacement and real Soma animation binding remain unfinished. Next: registered page/palette resolution and static sprite previews, then native original-art replacement. Completion remains 29%; this prerequisite does not complete sprite authoring.


## v0.24 static sprite previews

[Sprite guide](docs/SPRITES.md) documents `aria/sprite_rendering.py`, explicit page/palette registrations, packed 8x8 source addressing, transparent RGBA composition, source bank selection, bounds and origin contracts. `TacticalSoul.cmd preview-sprite julius --frame 0 --out local/sprite-previews/julius-0.png` works with bundled Python. `scripts/verify_sprites.py` covers all 216 registered frames and creates private contact sheets; source releases exclude those images. 222 tests pass. Static previews do not prove native OAM/resource ownership or permit sprite writes. Next: verified native consumer binding and one checked original-art replacement. Completion: 29% (29.1/100).


## v0.25 original native sprite artwork

[Sprite authoring](docs/SPRITE-AUTHORING.md) documents `aria/sprite_assets.py`, the fixed shared bats/clouds page/palette, guarded compressed relocation, transaction/source protection, original `examples/sky-invaders` content and native evidence. Run `TacticalSoul.cmd play examples/sky-invaders/mod.json`; `preview-sprite` and `inspect-sprite` now accept `--mod`. `scripts/verify_sprite_assets.py --lifecycle` verifies final-example native entry/pause/reentry and a separate composed save/death/fresh-continue harness. 234 tests pass. Completion: 30% (30.0/100). Next: one ordinary enemy visual binding and combat lifecycle, plus checked project-module sprite composition. Read [REA workflow](docs/REA-WORKFLOW.md): user requires the skill and connected MCP for binary investigation; skill installed locally, MCP not registered/exposed here.
