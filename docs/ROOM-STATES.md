# Bounded room-state discovery (v0.13.0)

This read-only API follows the alternate-state metadata pointer without evaluating
event conditions or choosing inherited graphics. It is preparation for authored
campaigns, not a new state editor or proof that alternate states work in gameplay.

```
TacticalSoul.cmd room-states 0 3
TacticalSoul.cmd room-states 11 40 --max-states 32 --out local/empty-room-states.json
```

The command accepts `--host` and `--mod`. Output files must be JSON under local/
and preserve inputs. Report addresses and load hashes remain private development
data. No definitions, extracted artwork or ROM images enter the report.

## Important files and agent API

`aria/room_states.py:inspect_room_states(rom, sector, index, max_states=32)` starts
at the public base-room lookup and follows each 36-byte metadata record's next
pointer. Source evidence is local DSVEdit `dsvlib/room.rb`: AoS records contain
LCD control, state-swap event flag and alternate-room pointer before the usual
layer/resource/entity/door pointers. Linked records use the same metadata shape.

The limit must be an integer 1..64. Repeated pointers produce `state_cycle` with
the prior ordinal. A remaining link at the bound produces `state_limit`. Invalid
or unaligned metadata produces `invalid_state_metadata`. Traversal stops while
preserving observations already made. Base lookup and invalid options still raise
PatchError. The report's `chain_complete` means pointer traversal terminated
without these diagnostics, not that every layer or load resolved.

Each state records its metadata hash, event flag, pointers, door count, lightweight
layer headers, graphics/palette load records and checked tilemap ranges. Layer
header status `metadata_read` certifies only a bounded 16-byte read, not geometry
validity. Full geometry/rendering through alternate pointers is not implemented.
Load failures stay local to that resource so other observations remain available.

Null resource pointers and terminated empty lists yield `inherited_or_empty`
with `prior_state_required: true`. This does not assert that inheritance actually
occurs in native execution; an empty/unused room can have no needed resources.
Do not automatically copy base-state loads or the preceding linked record's
loads. That link describes an event alternative, not the previous traversed room.

IDs retain the base ID for ordinal zero and use `alternate:NN` suffixes afterward.
They are contextual IDs within a base slot's chain. Shared metadata can appear
under different base slots; addresses and hashes identify that relationship.
Reordering links can change ordinal IDs. They are not persistent save/network
identities. `write_registered` is deliberately false for every state report;
existing base-room terrain permissions remain in the original profile/catalog.

`aria/cli.py` exposes room-states. `tests/test_room_states.py` covers linked records,
cycles, limits, invalid pointers, resource-failure isolation, identity and
nonmutation using synthetic fixtures. `scripts/verify_room_states.py` surveys
the private original and writes local/room-state-verification.json. The full
suite contains 161 tests at this milestone.

## Original-host findings and limits

All 343 original base-room slots have zero alternate-state pointers. Therefore
there are 343 observed state records, no native alternate-chain fixture, and no
evidence here for event-triggered transitions. Support for chain structure is
source-backed and synthetically tested, not natively certified.

Five palette load ranges remain outside their declared wrapper rows and are
unavailable under strict checks. One empty-room slot has empty graphics and
palette lists. Those findings remain explicit; none were resolved by guessing
prior resources. See ROOM-RESOURCE-AUDIT.md for their scope.

Next establish a controlled native event-state fixture or prior-room transition
contract before adding state authoring/inheritance. The main custom-content
priority remains resource ownership in additional ordinary rooms, followed by
expanded original-art registration with native lifecycle tests. Multiplayer
research remains optional and unimplemented.
