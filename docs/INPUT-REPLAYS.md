# Input replay and native checkpoint contracts — v0.19.0

These backend APIs let agents reproduce gameplay experiments and branch from one known emulator state. They support future editor testing without implementing a GUI. No full continuous route through room5 or repaired campaign has been established.

## Files and responsibilities

- `aria/input_routes.py`: standard-library-only descriptor validation, bounded input replay and native observation assertions. Importing this module does not load the emulator or Pillow.
- `scripts/emulator.py`: private libretro driver, now with `capture_state()` / `restore_state(checkpoint)` for isolated in-memory experiments.
- `scripts/verify_room5_search.py`: native determinism checks and bounded jump-timing sweep against the separate door harness.
- `tests/test_input_routes.py`: validation before input, first-failure stopping, observation failures, budgets and caller-data isolation.
- `examples/input-routes/room5-left-jump.json`: diagnostic replay after the declared room5 bootstrap. It intentionally documents a jump that does not cross the central platform.

## Route schema 1

Top-level fields are exactly `schema_version: 1`, `id` (1–80 characters), and `segments` (1–1024 entries). Each segment has unique `label` (1–80 characters), integer `frames` (1–3600), unique `keys` (list of integer libretro joypad IDs 0–15), and optional `expect`. Total duration is at most 36000 frames. Booleans are rejected where integers are required. These are libretro IDs, not keyboard scan codes: B=0, Start=3, Up=4, Left=6, Right=7, A=8. An empty list releases all inputs. Some valid libretro buttons have no GBA action.

Allowed expectation fields are `room_address`, `state`, `substate`, `world_x`, `world_y`, `hp`. Each expects an exact integer or an inclusive two-integer range. Unknown fields, reversed ranges, duplicate keys and duplicate segment labels fail before any input runs. Validation returns a deep copy so callers can reuse descriptors safely.

`replay_input_route(emulator, spec, observer=observe_native)` validates the entire descriptor before running. After each segment it records the label, elapsed/segment frames, keys, observations and assertion failures. It returns schema 1, route ID, `status` (`passed` or `failed`), and samples. The first failed expectation stops later input. A missing or non-integer observation fails. Observer/core exceptions propagate to the caller. The API does not write files or modify position, velocity, abilities, HP or ROM data.

Expectations are evaluated only at segment boundaries. A route can enter another room, die, hit an obstacle or miss a goal during a segment without an assertion detecting it. Use short segments and explicit state/room/HP/position checks where those properties matter. `passed` means descriptor expectations passed; goal achievement is a separate assertion. The native sweep records `goal_reached` separately.

`observe_native()` reads the currently established AoS USA RAM ABI: room pointer `02000088`, state byte `02000010`, substate byte `02000064`, HP halfword `0201327A`, world X/Y as player halfwords `02000526`/`0200052A` plus camera halfwords `0200A09A`/`0200A09E`. This observer does not detect the ROM version. Supply a previously verified target image, and do not infer this ABI for another game/profile. Unsigned coordinate reads are only meaningful in appropriate settled gameplay states. A custom observer can support other explicit test contracts.

## Checkpoint lifetime and boundaries

`Emulator.capture_state()` asks the native core to serialize into a bounded buffer (1 byte–16 MiB), returning a private `NativeCheckpoint`. `restore_state()` requires the same live emulator owner, matching ROM SHA256 and exact current native serialization size. Wrong-owner, wrong-ROM and truncated states reject before loading the core. Closed emulators reject capture/restore. A false native serialize/unserialize return raises an error; a native restore failure does not promise transactional rollback of core state. Dispose of that emulator instead of continuing a trusted test.

Checkpoints are in-memory development fixtures, not game SRAM saves, portable save files, or a build artifact. Do not print or package their payloads; they contain private game state. They are not intended for untrusted data loading. The owner/ROM guards prevent accidental mixing of experiments, not malicious forgery of Python objects. They cannot be shared between emulator instances, core versions or sessions. Keep one libretro emulator active at a time in the current process; the loaded DLL has global state.

Restoring clears held input and invalidates `image`; the next positive-frame `run()` refreshes the framebuffer. Observation reads can occur after restore, but screenshots must wait for a refreshed frame. This implementation uses the existing memory mappings; only the locally tested mGBA core is evidenced. Do not use native checkpoints to claim SRAM persistence across a fresh boot.

## Reproduce current evidence

With the private exact host, existing local mGBA libretro DLL, and Python with Pillow:

```powershell
C:/Python314/python.exe scripts/verify_connection_traversal.py
C:/Python314/python.exe scripts/verify_room5_search.py
C:/Python314/python.exe -m unittest discover -s tests -q
```

The first command builds and verifies the separate endpoint harness. The second requires its ROM hash and successful evidence to match. It boots naturally into room5, positions Soma once at world `(32,180)` with zero velocity, and lets native collision settle him to `(32,159)`. No position/HP/ability/collision changes occur inside branches. Branching restores the exact same checkpoint for each candidate.

Native checkpoint verification repeats the same route and compares the complete observation trace, all 256 KiB of EWRAM and the framebuffer byte-for-byte. It also rejects foreign-owner, wrong-ROM and truncated checkpoints without EWRAM changes, and rejects restore after closure. This is a concrete single-core/fixture determinism result, not a universal emulator guarantee.

The bounded sweep varies the initial Right walk from 20 through 74 frames in steps of two (28 candidates), followed by 30 frames Right+A and 40 frames Right. All maintain the asserted room/active state/positive HP at the final segment. None reaches the final-position goal `world_x >= 480 and world_y <= 170`. The greatest final X is 193 at y=255, after a 48-frame approach. That candidate is reproduced for the private screenshot. No claim of impossible traversal, a softlock, required ability or optimal route follows: release timing, multiple jumps, intermediate platforms, reverse approaches and native abilities were not exhaustively tested.

Evidence is saved under `local/room5-search-verification.json`, with full per-candidate input traces and assertions. The inventory embeds a bounded summary excluding the full trial list. Old evidence on disk is not proof that a new invocation passed; require process success and matching fixture hash.

## Extend this work

First add multi-segment jump/release sequences and inspect intermediate positions instead of only final X. Use checkpoints to compare identical starts. If testing an ability, establish its native grant/lifecycle contract separately and declare the changed prerequisite; do not silently grant it inside input branches. A successful route must cross continuously with no intervening position writes, remain alive, return, and demonstrate the intended campaign access. Only then build a separate playable repaired example and repeat save/fresh-continue/death checks. Terrain redesign is another valid option, but room5 is not currently registered for production geometry writes; investigate and register it with resource/collision evidence before authoring a new bridge.


## v0.20 terrain authoring milestone

[Rectangle terrain authoring](TERRAIN-PAINTING.md) adds `plan-terrain`, checked room5 support and the separate bridge-route example. Input-only full bridge crossings pass in both directions; the final build separately passes main-route save/death/fresh-continue and art regression. 184 tests pass. Estimated framework completion is now 27%; prior milestone percentages are historical.
