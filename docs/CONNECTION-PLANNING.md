# Connection planning for agents — v0.17.0

This backend stages pairs of existing doors on an isolated ROM object. It produces reviewable JSON evidence, not a playable ROM. Use it before applying route changes to a mod. GUI applications can call the same Python function later; no GUI is implemented.

## Reproduce the example

From the Tactical Soul Framework folder:

```powershell
.\TacticalSoul.cmd plan-connections --mod examples/three-room-art/mod.json --spec examples/three-room-art/neighbor-repair-plan.json --out local/neighbor-repair-review.json
```

Use `runtime/python/python.exe scripts/aria_tool.py` instead of the command wrapper when automating. Output files must be JSON under `local/`, and cannot overwrite the host, manifest or specification. Without `--out`, the report goes to stdout. No output ROM is written.

## Input contract

`aria.connection_plans.plan_connections(rom, spec)` accepts an already loaded, optionally patched `RomImage`. The specification has exactly three fields: integer `schema_version: 1`, `expected_image_sha256` matching the current patched image, and `connections` containing 1–32 pairs. Each pair uses the existing level writer's `a` and `b` endpoints: `room: {sector, room}`, an existing `door` index, and primary `spawn: [x, y]`. Coordinates are pixels in the target room, not viewport coordinates or map cells. See the checked-in example for complete JSON.

The SHA preimage binds the proposal to the complete base mod, including allocation decisions. Changing any module requires regenerating and reviewing the proposal against the new image. Never update the hash merely to suppress an error without reviewing that image.

The planner deep-copies the image, ledger, allocator cursors, allocation records and profile. All validation and mutations run on this copy. Both success and failure leave the supplied object unchanged. Caller-owned specification arrays are copied too. Existing checked door writing rejects invalid indices, duplicate endpoints, non-opposing boundaries, out-of-bounds spawns and newly introduced room audit errors. It cannot stack another write onto an already modified door array if the existing ledger or allocation rules reject it; combine those connections in one level edit instead of bypassing guards.

The complete base-room graph is required before and after staging. Proposals are rejected if they introduce any additional edge ID without an observed direct return, introduce unresolved destinations, or produce no routing changes. An observed return means some door in the destination metadata points back; it does not certify the paired endpoint, collision clearance, event reachability or softlock safety. Existing one-way links are allowed only when no additional such edge IDs appear. This conservative policy does not support authoring new intentional one-way routes.

## Output contract and example evidence

Schema 1 reports `static_proposal_not_gameplay_verified`, input/proposed image hashes, copied connections, checked room reports, before/after graph summaries, routing delta, restored return edge IDs and staged ledger writes. Allocation/write evidence describes a hypothetical in-memory image. It is not a build manifest or a reusable binary patch.

The three-room example displaced links from rooms 0:5, 0:9 and 0:25. The proposal pairs 5:door0 with 25:door1, and 5:door1 with 9:door1. Four endpoint changes restore four observed returns: missing-return edges fall from 7 to the original 3; all 725 doors across 343 slots still resolve. Proposed image SHA256 is `a08505a0d2d355e20d37d8da88f92929938724c4d8c9103fd1c7c375cb299907`.

These spawn coordinates are statically bounded guesses. The existing connection writer clears secondary spawn offsets, including original signed-looking vertical values. The room 0:9 landing at y=1280 especially needs native vertical placement and collision checks. Do not describe this proposal as a repaired campaign or add it to the playable example without testing both directions of every changed endpoint.

## Next agent acceptance sequence

1. Reproduce `scripts/verify_connection_plans.py` and the full unit suite. Keep the original and existing three-room build hashes unchanged.
2. Create a separate experimental manifest composing all affected connections in a single level edit. Preserve the existing three-room example.
3. Verify all four endpoints in both directions using native mGBA, including grounded landing, movement, camera, return traversal, actor interference and transition settling. Record exact inputs and full-frame evidence privately.
4. Repeat save/fresh-continue/death/pause lifecycle checks and inspect displaced links again. Inspect event/progression context; the static graph has no event model.
5. Only promote a playable example after evidence passes. Update roadmap/capabilities honestly. Intentional one-way route policy, automatic spawn selection, progression analysis, new rooms and map layout generation remain unimplemented.

## Important files

- `aria/connection_plans.py`: isolated staging and conservative graph policy.
- `aria/level.py`: checked door endpoint writing and room/map audit boundaries.
- `aria/world_graph.py`: stable base-slot graph observations and deltas.
- `aria/cli.py`: command and private-output boundary.
- `examples/three-room-art/neighbor-repair-plan.json`: proposal input, not a mod manifest.
- `tests/test_connection_plans.py`: deterministic success, schema/preimage and failure nonmutation coverage.
- `scripts/verify_connection_plans.py`: private-host reproducible evidence; never distributes host data.

The four planner tests require the private supported host and skip when absent. A passing source-only suite alone does not reproduce the native-ROM-backed result.


## v0.18 native endpoint evidence

[Native connection testing](NATIVE-CONNECTION-TESTING.md) documents four controlled bidirectional crossings, settled landings and movement checks. Independent endpoint position fixtures are explicit; continuous room5 traversal and repaired-campaign lifecycle remain pending. The planner remains static-only; existing playable examples are unchanged.
