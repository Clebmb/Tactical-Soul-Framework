# Tactical Soul Framework — handoff to Muse Spark 1.3

You are Muse Spark 1.3 taking over a real, existing Aria of Sorrow ROM-modding framework. Read this entire document, then the listed source/docs, inspect the current files and continue implementation. This is a working backend, not a request to invent a new project or replace the native game with a browser demo.

## Standing user instructions — keep these in force

- When the user says **continue**, autonomously make concrete, useful progress toward a documented total-conversion framework. Select the next meaningful incomplete capability from the current roadmap, implement it, verify it and document it. Do not merely repeat tests, revisit the same narrow experiment indefinitely, ask what continue means, or stop at a plan. Ask a concise question only when a material decision truly needs the user's input; continue independent work when possible.
- Keep all important APIs, files, examples, constraints and native evidence documented so another agent can extend or radically repurpose the framework.
- A GUI level editor is a future goal. Build reusable headless authoring/inspection/testing APIs now; do **not** start the GUI unless asked.
- The user wants eventual full conversions: levels, terrain/collision, graphics/animation, weapons, enemies, souls/abilities, mechanics, sound/music, progression/events/maps and saves. They also want future mashups. Do not confuse current narrow demonstrations with total-conversion readiness.
- At the end of **every generation/turn**, update this exact `handoffprompt.md` before sending the final response. This applies to implementation, documentation and planning turns. Do not skip it. Preserve standing instructions and useful architecture; replace the latest-status section with what actually changed, current tests/evidence, incomplete work and the next concrete steps. If updating is technically blocked, explicitly disclose it instead of claiming it happened.
- Every final response must state concrete progress, verification and material limits; what is next; the current estimated framework completion percentage from the roadmap; and brief examples of mods currently possible. Say that the handoff was updated. Never increase percentages just to satisfy a status request. Also avoid getting stuck on narrow validation at the expense of missing authoring capabilities.
- After every generation, refresh the README status block near the top (current version, estimated completion percentage, and what can be built today) so it never goes stale.
- Original code is MIT and remixes are allowed. This does not grant rights to commercial game material. No public publishing/upload is authorized. The multiplayer question was feasibility discussion only; multiplayer implementation is not a current task.

## Latest status — refresh at the end of each turn

<!-- STATUS START -->
Updated (UTC): 2026-10-11T12:30:00+00:00

Current framework: **0.38.0-foundation**. Estimated completion: **32%** (32.0/100 weighted maturity points). Public git live: **https://github.com/Clebmb/Tactical-Soul-Framework**.

**Completed this turn:** v0.38 custom item/enemy names (`aria/labels.py`, `docs/LABELS.md`, `examples/label-workshop`): named resolution plus checked in-place renames (ASCII, fits original length, space-padded, terminator preserved, preimage ledger, batch-validated, duplicate-claim rejection). `label_edits` works in manifests and project modules. Natively proven by `scripts/verify_labels.py`: Knife→Fangs build changes exactly 5 ROM bytes (1 ledger entry); a 26-snapshot menu tour twin-diffed original vs renamed shows deterministic control and 12 differing frames in tight menu-text cells. An early address/offset mixup and an original-vs-patched readback bug were found and fixed for cause during testing. README status + build-today list refreshed per standing rule.

**Verification actually run:** 268 unit tests pass with private host (265 existing + 3 new label tests; exit 0). Native label proof re-ran in background with exit status preserved (EXIT:0, deterministic control, 12/26 localized diffs). Example mod builds clean (patch_count 1, SHA matches proof build). Original ROM unchanged.

**Next concrete work:** Campaign/event compiler slices, audio binding or soul grant APIs; other rooms/actors through the attribution library (writer only with a tracer-named consumer set).

**Remaining limits / unfinished work:** 32% (32.0/100 weighted). Longer-than-original names need a string allocator (pending); widget frontend pending (deferred); sprite rendered-consumer proof withdrawn; REA GBA unsupported; GUI deferred.

**Git publication (user request, no version bump):** hardened `.gitignore` (ROMs/saves, build/, local/, tools/, bundled runtimes, all but latest release zip, venvs, `.freebuff/`, OS leftovers); `assets/tsf_banner.png` moved from root and shown at README top; README gained a self-sourced-files table (`CastlevaniaAoS.gba` + hash, libretro DLL, Zig, Pillow Python, runtimes from release zip) and a "What's to come" section; pruned 35 old release zips leaving 0.36.0 (latest by mtime); `git init`, committed 265 files, pushed `main` to public Clebmb/Tactical-Soul-Framework. Verified via dry-run and `git ls-files`: no .gba/.sav, no local/build/tools/runtime-binaries in git. Kept tracked deliberately: handoffprompt.md/AGENTS.md (release process and contributor instructions depend on them), chirp.wav and runtime.bin files (original MIT content/code), latest release zip (runnable distribution with runtimes).

<!-- STATUS END -->

## Required REA skill and MCP workflow (explicit user request)

Use the **reverse-engineer-anything (REA) skill and connected REA MCP** for ROM/native-binary reverse engineering. Read [REA workflow and host status](docs/REA-WORKFLOW.md) before the next binary investigation. The skill is installed on this host at `%USERPROFILE%/.agents/skills/reverse-engineer-anything/SKILL.md`; on another host, locate it through the agent's skill catalog and read the current SKILL.md. Prefer actual connected REA MCP analysis/evidence tools, bind the exact private ROM, reuse existing matching sessions, and retain source-bound Evidence IDs/limits. Do not invent REA calls or evidence when tools are absent.

Verified at the v0.25 handoff: the skill file exists, but no REA MCP tools are exposed; Codex config lists only `node_repl` and `melty` MCP servers, with no REA registration. The read-only REA doctor attempt failed on package-registry DNS. No REA setup/configuration/provider installation occurred. This is not proof of another computer's status. If unavailable, document the limitation, follow the skill's read-only diagnostic/setup-review workflow, and continue independent framework work/local native checks. Obtain required setup approval before modifying host configuration or installing providers. Do not confuse local mGBA evidence with REA/decompiler evidence. Ordinary Python repository analysis does not require REA.

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
- `aria/projects.py`: schema-1 `tsf-project` documents with 1–64 ordered modules. Supported terrain/room-art/room-edit/encounter/balance/resource/table fields compose into a normal manifest; split terrain cells batch by room/layer, door/move ownership conflicts name both modules. Assets resolve under their owning module folder; provenance records source/module/asset hashes. `apply_manifest` stages projects on a clone and commits only after all checks pass. Hooks/abilities/general content/raw patches/full lists are excluded from projects and remain single-manifest features. Read `docs/PROJECT-COMPOSITION.md`.
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
