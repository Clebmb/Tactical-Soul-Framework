# Static world door graph (v0.16.0)

This read-only backend inventories normal base-room doors and exposes routing
changes for review. It does not repair doors, evaluate events or certify a campaign.

```
TacticalSoul.cmd world-graph --out local/original-world.json
TacticalSoul.cmd world-graph --mod examples/three-room-art/mod.json --out local/three-room-world.json
```

The optional mod is applied to an in-memory copy after capturing the original
graph. No output ROM is written. JSON files must remain under local/ and preserve
host/manifest paths. The CLI returns `{schema_version, graph, changes}`; changes
is null without a mod. Reports contain addresses/routing records, no game artwork.

## Important APIs and client contracts

`aria/world_graph.py:audit_world_graph(rom)` enumerates each bounded base-slot
table. Nodes use the existing stable slot IDs; each door ID appends `:door:NNN`.
Nodes list incoming/outgoing edge IDs. Edges retain boundary coordinates, primary
and secondary destination offsets, destination address and all matching slot IDs.
Shared metadata addresses are represented as aliases, not silently resolved to
one slot. Unknown destination addresses are `outside_base_catalog`, even if they
could be valid native metadata not in these tables. Invalid sectors, rooms and
door arrays produce independent diagnostics; enumeration_complete is then false.

`direct_return_observed` means at least one enumerated door goes from the target
metadata address back to the source metadata address. It does not pair a specific
door or validate opposing sides, landing, map adjacency, conditions or accessibility.
Self-links and multiple returns are not automatically errors. Missing data can
hide a return; consult diagnostics before interpreting negative observations.

`compare_world_graphs(before, after)` matches door IDs and reports added, removed,
or changed endpoints, boundaries and spawn offsets. Profiles must match. IDs
depend on door array order; reordering can appear as multiple changes. Each
changed source includes surviving incoming edges from its old target that no
longer have an observed direct return. This is a displaced-neighbor review list,
not an automatic repair plan. Multiple changed doors can identify the same
incoming edge; deduplicate when presenting a global count. Different paths or
events can provide a valid return, so the finding is not proof of a softlock.

`aria/cli.py` implements the command and private-output guard.
`tests/test_world_graph.py` covers reciprocal edges, outside destinations, aliases,
changed/added endpoints, displaced links, failure isolation, profile mismatch and
private-host nonmutation. `scripts/verify_world_graph.py` persists reproducible
private reports. Full suite: 170 tests.

## Original and three-room example findings

The exact original has 343 base-slot nodes and 725 door edges. All destinations
resolve to known slots; three edges have no observed direct return. These are
observations about original routing, not newly introduced errors.

The three-room art route changes four endpoints and leaves these original
incoming links without an observed direct return:

| Surviving source | Door index | Review context |
|---|---:|---|
| Sector 0 room 5 | 0 | Former hallway neighbor |
| Sector 0 room 5 | 1 | Former gallery left neighbor |
| Sector 0 room 9 | 1 | Former gallery right neighbor |
| Sector 0 room 25 | 1 | Former save-room neighbor |

The native demonstration route remains verified under THREE-ROOM-ART.md. This
audit explains why that demonstration is not a globally repaired campaign.
Do not reconnect these four links mechanically: decide intended progression,
incoming endpoints, physical door sides, map presentation and safe landing first.

Next add an explicit authored-route policy and reviewable repair proposal, with
native traversal and save checks for every affected endpoint. Alternate states,
scripted teleports, progression locks, collision reachability, map ownership and
resource lifecycles remain separate contracts. No GUI or multiplayer is added.


## v0.17 connection proposals

See [Connection planning](CONNECTION-PLANNING.md) for the isolated existing-door planner, input/output contracts, four restored static return links, and required native landing verification. `plan-connections` emits review evidence only. Current completion remains 26%; 174 tests pass with the private supported host.
