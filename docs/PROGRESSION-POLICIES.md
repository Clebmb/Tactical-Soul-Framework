# Authored progression policies

`plan-progression` explores declared flags and door requirements over the static
world graph. It helps authors review proposed key/ability routes before native
implementation. These declarations neither discover nor enforce Aria events.
Use [the source demonstration](../examples/progression-policy/README.md) for
generated exact-image policies and runnable CLI commands.

## Policy schema 1

Required fields: `schema_version: 1`, `profile`, `image_sha256`, `start`, `flags`,
`required_rooms`. The image hash must match the graph after applying `--mod`.
Room/door IDs are the stable IDs from `world-graph`. Required rooms are independent
destinations, not an itinerary or a promise that all can be visited in one run.

Optional fields:

- `initial_flags`: flags owned before entry.
- `room_grants`: map from room ID to flags granted automatically on entry.
- `edge_requirements`: map from door ID to flags all required before crossing.
- `itinerary`: ordered list of up to 64 known room IDs to visit in one journey.
  Each arrival advances at most one waypoint; initial occupancy counts once.
  Repeated adjacent IDs require leaving and returning (a self-loop also counts).
  Visiting a later waypoint early does not satisfy it. Intermediate rooms are
  allowed; this is an ordered subsequence of arrivals, not an exact route.

Flags are unique lowercase names (`[a-z][a-z0-9_]{0,47}`), maximum 16. Every
reference must be declared. Flags are monotone: no clearing, consumption,
exclusive choices, counters, timed flags or negative requirements. Start-room
grants happen before considering its outgoing doors. Grants are automatic and
idempotent; the policy cannot model item pickup positioning within a room.
Unsupported/unknown fields and unknown targets fail early. Requirements on
ambiguous/out-of-catalog doors are rejected rather than silently ignored.

## API and search contract

`aria.campaign_progression.plan_progression(graph, spec, max_states=20000,
max_transitions=200000)` reads schema-1 world graphs without mutation. Graph
validation and exclusion follow [campaign audit](CAMPAIGN-AUDIT.md).
The search visits `(room, flags, itinerary progress)` states, not just rooms. A junction can be
revisited with new abilities, while separate one-way branches cannot combine
their inventories. Sorted door IDs give deterministic shortest witnesses by
door count. No flags are invented from native actors or room appearance.

Budgets accept 1..100,000 states and 1..1,000,000 examined transitions. Graph
and required-room bounds are inherited from the campaign audit. State/transition
exhaustion returns `search_complete: false` plus `limit_reached`; a destination
not yet reached is `not_reached_before_limit`, not an unreachable verdict.
Graph completeness and search completeness are separate fields.

Reports include analyzed image and canonical policy SHA256, reachable rooms,
required-room witness door paths and flags on arrival, state/transition counts,
excluded edges and source diagnostics. `gate_observations` lists missing flags
seen in explored states and whether that door was traversable in another state.
These observations can include gates unlocked later; they are not all permanent
blockers. `all_required_paths_observed` can be true before search completion,
and is vacuously true for an empty required list. It is never native certification.

`itinerary_route` is null when no itinerary was requested. Otherwise it reports
an independent `status`, shortest `door_path`, `flags_on_arrival` and the maximum
`waypoints_observed` over single paths. An empty itinerary has an observed empty
path. Incompatible branches cannot combine waypoint progress. A witness already
found stays observed if later exploration hits a budget; an unfinished itinerary
then reports `not_reached_before_limit`. To request a round trip, append the
start room to the desired waypoint list. Required-room results remain independent
queries; `all_required_paths_observed` does not imply itinerary success.

The CLI applies an optional manifest/project in memory, writes no ROM, and
requires private report `.json` paths under `local/` that preserve host, policy
and manifest. No observed policy path grants new write/start permissions.

## Validation and remaining work

364 tests pass. Synthetic tests cover acquisition/revisits, a key behind
its own gate, start/initial grants, incompatible branches, both search budgets,
ambiguous/incomplete graphs, bad policy identity/references and deterministic
cycles. One private-host test proves declared before/behind-gate outcomes on
the flesh-sanctuary graph with byte/ledger nonmutation. Both CLI policies run.
Five itinerary tests additionally cover incompatible branches, ordered acquisition
and return, repeated/start/empty waypoints, invalid input, budget limits and a
witness found before later exhaustion. The private-host test also checks a
two-door hallway round trip. This is static author-defined evidence; no native
event or gameplay check was added. Framework maturity remains 35% (35.1/100).

Next establish one native flag/ability/event binding with source/runtime evidence
before using a policy as an acceptance oracle. Native event enforcement, collision
and landings, scripted transitions, alternate states, consumption, save persistence
and a campaign compiler remain unfinished. Original playable examples stay separate.

Compare explicit observed checkpoints with a policy using [progression traces](PROGRESSION-TRACES.md). This comparison does not enforce native gates.
