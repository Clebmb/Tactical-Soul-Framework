# Observed progression trace comparison

`aria.progression_traces.compare_progression_trace(graph, spec, trace)` compares
explicit checkpoints against an authored [progression policy](PROGRESSION-POLICIES.md).
It performs no ROM writes, native execution or gate installation. Graph, policy
and trace must identify the same profile and exact analyzed image SHA256.

Trace schema 1 has exactly `schema_version`, `profile`, `image_sha256`, `samples`.
There must be 1..4096 samples, each with exactly:

- `room`: a known stable base room ID.
- `flags`: every declared policy flag mapped to a Boolean observation.
- `via`: the single unambiguous door crossed since the previous sample, or null
  for a checkpoint in the same room. The first sample must have null `via`.

The caller must supply trustworthy samples and identify crossings accurately.
The comparator does not authenticate a trace, discover skipped rooms, resolve
ambiguous room pointers or infer which of several doors was used. A claimed
door is checked against the preceding and current room. Aliased/unsupported
doors and malformed snapshots fail. Schema/policy validation reuses the planner
with one-state/one-transition budgets, rather than exploring the whole graph.

`matches_policy` is false for a wrong start, a room change without a door,
wrong door endpoints, missing observed pre-crossing requirements, or any mismatch
between observed flags and the modeled initial/room-entry grants. Violations
retain sample indexes and details. Gate requirements use the preceding sample's
observed flags, so a grant at the destination cannot satisfy that crossing.

`required_rooms_observed` and `itinerary_observed` are separate from policy
matching. A matching partial trace need not complete its objectives. Consumers
must require both matching and their requested objective results. Itinerary
progress counts initial occupancy and explicit door arrivals; another checkpoint
in the same room does not advance a repeated waypoint. A self-loop crossing does.
Reports retain policy and trace SHA256, sample count and graph completeness.
Malformed inputs raise `PatchError`; valid conflicting observations yield a report.

## Native soul route example

`python scripts/verify_soul_progression.py` now plans and compares its diagnostic
entrance-to-save-room route. The policy starts **after** the native opening
acquisition, with `first_red_soul_owned` declared initially true; it does not
misrepresent that scripted acquisition as a room-entry grant. The existing
redirected door has that authored requirement and the itinerary is room `(0,14)`.
The static witness is one door, and two settled native checkpoints match it.

Private policy, trace and comparison files are under `local/soul-progression/`.
The native verifier separately checks saving and fresh continue; the reload is
not included as another continuous traversal checkpoint. It verifies the graph
image hash equals the generated probe ROM hash. The original ROM is unchanged.

This confirms one observed route with an acquired flag. It does **not** show
that the door blocks an unowned player: no native gate is installed. The fixture
redirects one existing door and does not certify the original campaign. See
[native observations](NATIVE-EVENTS.md) for ownership/source/evidence limits.
A separate [native barrier demo](../examples/soul-gate/README.md) now tests an
unowned negative case and owned exit in room14. Its skipped player states and
after-update scope still prevent a general key/ability-locked campaign claim.
