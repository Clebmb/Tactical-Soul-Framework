# Static campaign reachability

For authored flag/grant/door policies, see [Progression planning](PROGRESSION-POLICIES.md).
Those declarations remain separate from native event enforcement.

`audit-campaign` gives authors an image-bound routing review from a chosen
base-room slot. It does not alter doors, start constants, maps, events or saves.
An arbitrary audit start is a graph query, not authorization to install a new
native landing. Existing `new_game_start` registrations remain unchanged.

```powershell
TacticalSoul.cmd audit-campaign 0 31 --require 0 3 --require 0 6 --out local/campaign-original.json
TacticalSoul.cmd audit-campaign 0 31 --require 0 3 --mod examples/custom_room/mod.json --out local/campaign-custom-room.json
```

The optional manifest/project applies in memory through the existing checked
applier. No output ROM is emitted. Private reports require `.json` under
`local/` and cannot overwrite the host or manifest. Without `--out`, JSON prints
to stdout. A missing route is a report finding, not a command execution failure.

## API and output contract

`aria.campaign_audit.audit_campaign(graph, start, required=())` consumes schema-1
`audit_world_graph` output. Start and required destinations use its stable node
IDs, such as `aos-usa-r0:s00:r031:base`. Required destinations are independent
queries from the start, not an ordered campaign itinerary. Duplicates collapse
in first-request order. Unknown start/required IDs, duplicate node/door IDs,
unsupported schema and excessive graph/request sizes raise `PatchError`.
Limits: 4,096 nodes, 32,768 edges and 256 required destinations.

Only edges with one known target and `destination_status=resolved` participate.
Aliased and out-of-catalog edges are retained in `excluded_edges`, never chosen
arbitrarily. Source diagnostics are preserved. `graph_complete_for_audit` means
enumeration completed and no edges were excluded; it is not campaign safety.

Breadth-first searches find deterministic shortest paths by door count, with
door IDs sorted for ties. Output includes:

- `reachable_rooms` and `unreachable_rooms` in the included directed graph.
- `reachable_without_observed_return`: reachable nodes with no included path
  back to the start, including multi-room one-way branches.
- `required_routes`: outward and return door-ID lists per destination. Null
  means no observed path; an empty list means the destination is the start.
- Independent outward/roundtrip observation flags, summary, profile and exact
  analyzed-image SHA256. Empty requirements make both flags vacuously true.

Return routes can differ from outward routes and need not use directly paired
doors. Resolve edge IDs against `world-graph` from the same image hash to inspect
spawn/boundary data. The API reads no files and does not mutate the supplied graph.
CLI audits do not add writes beyond applying an explicitly selected mod in memory.

## Actual static findings and validation

On the exact private original, start 0,31 reaches 302/343 slots; 41 lie outside
that directed component. All 302 have an observed path back. Required room 0,3
has a 15-door outward and 15-door return path; room 0,6 has 13 in each direction.
No edges are excluded and enumeration completes.

With `examples/custom_room/mod.json`, start 0,31 reaches two slots, with a
one-door route to room 0,3 and one-door return; the other 341 are outside this
component. This correctly exposes the example's narrow campaign scope.
These observations do not imply the original's other rooms are inaccessible
through scripted transitions, or that any reported path is physically traversable.

347 full-suite tests pass. Seven synthetic tests cover multi-hop/different
returns, sinks/disconnected rooms, self-links/start requirements, alias exclusion,
incomplete diagnostics, deterministic shortest paths and invalid inputs.
One private-host test checks original/mod paths plus byte and ledger nonmutation.
Both CLI examples ran and emitted private JSON reports. Native gameplay was not
rerun for this read-only Python change; prior example evidence retains its scope.

## Limits and next work

The model ignores event/ability locks, collision within rooms, alternate states,
teleports, landings, boss/resource lifecycle, save stations and progression flags.
No observed route grants editing permissions or certifies a campaign. Unknown
edges and incomplete source data make negative findings less conclusive.

Next: an explicit authored progression policy with event/ability gates and
native evidence, then an original-content mini-campaign acceptance run covering
new game, traversal, return, death, save and fresh continue. Keep static reports
separate from those acceptance results.
