# Native connection testing — v0.18.0

The backend now has a reproducible private-host mGBA regression for the four proposed neighbor endpoints. This verifies controlled endpoint transitions and landing movement, not a completed campaign repair. The planner deliberately retains its static-only status: planning itself does not execute an emulator.

## Run and prerequisites

From the framework folder, run `C:/Python314/python.exe scripts/verify_connection_traversal.py` using a Python installation with Pillow. Requires the supported private `CastlevaniaAoS.gba` and the existing local `tools/libretro/mgba_libretro.dll`. Neither dependency is included in the release archive. The bundled standard-library CLI Python cannot run this graphical native test without Pillow. No downloads are performed.

All generated manifests, authored-JSON fixture copies, ROMs, screenshots and evidence remain under `local/`. The script preserves the original host and existing examples. Verification failure raises an exception and records a failed status once native execution begins. Missing dependencies/build errors fail before the native report is written; an older report on disk is not a new pass. Do not run concurrent copies against the same private output paths.

## Harness construction and exactness

1. Build the original three-room example in memory, reproduce the static proposal and stage its connections through the existing checked level writer. The proposed image must match SHA256 `a08505a0d2d355e20d37d8da88f92929938724c4d8c9103fd1c7c375cb299907`.
2. Build a separate harness from the exact original host. Combine all connections in a single manifest edit to obey array relocation/conflict rules. Its hallway shortcut enters room 5's lower-left door instead of the gallery. Original authored JSON graphics/palettes are copied into the private fixture workspace for normal relative-path resolution.
3. Assert all four proposed endpoint records are byte-identical between the proposed image and the harness. The harness additionally changes the hallway/room5 lower-left pair; it is not a shippable campaign example. Resource allocation addresses may differ due to composition order.
4. Boot naturally and hold jump long enough to clear the custom hallway step. After room 5 loads, position Soma near its upper-right endpoint at world `(480,180)` with zero velocity. Native collision settles him to y=159. This is a declared position fixture, not natural campaign reachability.
5. Walk right into room 9, then left back to room 5. Independently position Soma at room 5's upper-left endpoint `(32,180)`, settle, walk left into room 25, and right back. No destination position or collision writes occur.

Position writes use fixed-point camera-relative words at `02000524`/`02000528`; velocity reset uses `0200052C`/`02000530`. Read world coordinates as player halfwords plus camera halfwords. The two position fixtures are the only deliberate gameplay RAM changes.

## Acceptance checks and observed results

Every crossing must reach the expected metadata pointer, then settle for 90 frames in active gameplay state 4/substate 1 with positive HP. Require in-bounds coordinates and unchanged world Y over another 30 neutral frames. Hold the same travel direction for eight frames to move away from the destination entry; require actual X movement while remaining in the destination room. A pointer transition alone does not pass.

| Crossing | Settled world position | X after moving away |
|---|---|---|
| 5 to 9 | 6,1439 | 16 |
| 9 to 5 | 505,159 | 495 |
| 5 to 25 | 232,159 | 221 |
| 25 to 5 | 6,159 | 17 |

Native horizontal placement is not simply the raw primary spawn X. These observations do not establish the complete door placement formula or all secondary offset semantics. Room 9's formerly speculative y=1280 primary spawn now has a controlled native landing observation at world y=1439.

The private `local/connection-traversal-verification.json` records status, image hashes, samples, checks, fixtures and limitations. PNGs show each landing and movement check. The source inventory embeds the bounded JSON evidence, never images or ROM bytes.

## What remains unproven

Walking straight across room 5 failed at its stair geometry. The harness therefore tests left/right endpoints independently; it does not prove a continuous route through that room. No claim of a campaign softlock or unreachable route follows from that failed walking attempt. Jump/climb traversal, event dependencies, castle-map meaning, save/death/fresh-continue and physical hardware are not certified for the repaired proposal. The existing three-room example and its separate lifecycle evidence are unchanged.

The next agent should inspect room 5's terrain and demonstrate a continuous input-only route between the tested endpoints. Then build a separate playable experimental mod, re-audit displaced graph edges and repeat campaign lifecycle tests. Do not overwrite the existing example or award the original-content campaign gate merely because these four transitions pass.


## v0.19 input replay foundation

[Input replay and checkpoints](INPUT-REPLAYS.md) documents bounded JSON input traces, boundary assertions, same-instance native forks and a 28-candidate room5 jump sweep. No candidate reached the continuous-route goal; this is not an impossibility proof. 180 unit tests pass. The original route examples and endpoint proof remain unchanged.
