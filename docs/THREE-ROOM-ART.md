# Three-room original-art route (v0.15.0)

The registered custom-art/main-layer targets are now sector 0 rooms 3, 6 and 31:
hallway, gallery corridor and save room. Each supports the existing fixed-size
raw 4bpp chunk-24 load and palette-bank-8 import with isolated ROM load lists.
Unregistered rooms and arbitrary slots remain rejected. Dimensions stay fixed.

```
TacticalSoul.cmd play examples/three-room-art/mod.json
TacticalSoul.cmd preview-room 0 6 --mod examples/three-room-art/mod.json --out local/gallery.png
python scripts/verify_geometry.py --three-room-art --lifecycle
```

## Authoring and source files

`framework/aos-usa-r0.json` adds only room 0,6 to the existing terrain and room-art
permissions. The checked installation/geometry APIs remain unchanged. Follow
ROOM-ASSETS.md, CUSTOM-TERRAIN.md and TWO-ROOM-ART.md before extending this example.

`examples/three-room-art/mod.json` pairs hallway door 2 with gallery door 0,
then gallery door 1 with save-room door 0. Destination endpoint spawns are
hallway (1040,0), gallery left (0,0), gallery right (528,0), save room (0,0).
Native doors still handle the transition placement. This is an intentional local
route; old neighboring rooms retain displaced incoming links and original map
positions. It is not a repaired full campaign graph or a new-room compiler.

The gallery keeps its original entities and dimensions. One main-layer cell at
(10,3), previously blank, uses appended metatile 144, sixteen descriptors 0x8200
and sixteen collision-zero bytes. Hallway and save-room edits retain their prior
contracts. Do not turn the mural into a solid tile without checking traversal,
landing, enemies and return travel. Other authored layouts need their own tests.

Gallery source pixels remap the original MIT procedural example's color indices
1 and 3; its palette rotates RGB components. All three rooms have distinct raw
graphics and palettes. The same physical memory slot is overwritten on each
transition, so correct room-specific reload is part of the acceptance evidence.
No extracted commercial artwork enters the example or source release.

## Native verifier contracts

`scripts/verify_geometry.py --three-room-art --lifecycle` traverses the complete
route, saves, continues in a fresh emulator, walks back through the gallery,
pauses/resumes in the hallway, triggers native death/Game Over, continues from
post-death SRAM and walks back again. The gallery room pointer is 0850F32C.

The gallery checker waits for gameplay state 4/substate 1 before testing loads.
A room pointer can change during transition before graphics loading completes;
checking immediately produced a misleading failure during development. It then
requires the full 2048-byte chunk and 32-byte palette to match native memory.

The fixed gallery sample is world X324..343, Y100..119: all 400 opaque pixels must
match at native 5-bit color depth in one capture. Transient actors/effects produced
unmatched frames. The verifier retries during bounded ordinary controller
traversal, never deleting individual mismatched pixels or injecting graphics.
Recorded unmatched attempts were 1 outbound, 3 on fresh-continue return and 3 on
post-death return. This certifies the fixed clear sample, not effect composition
or every frame. Capture-attempt counts remain in the private evidence.

Gallery samples match all 400 pixels at all three stages. Save-room samples also
match 400 pixels on entry, fresh continue and post-death continue. The hallway
matches its 384-pixel step sample, blocks at X311 against baseline X329, allows
native jumping to X458, and blocks natural return at X360. Contrasting room loads
are preserved across all tested transitions.

Initial comparison writes only player X/velocity; settled Y is retained. Death
forces HP zero. Fresh emulator instances receive copied SRAM. No terrain,
collision, graphics or palette RAM is injected. Same-session Game Over-menu
continue, hardware, unrelated events and all neighboring routes remain unverified.

Private evidence: local/three-room-art-verification.json and stage screenshots.
Output SHA256:
`10e002682d906fb4f25c090aa1988d2fdea368c7aa3f5092213cbd7b8c5fba3f`.
`tests/test_room_assets.py` checks three distinct loads, original resource/layout
preservation, one authored cell per room, route destinations and rejection of an
additional unregistered room. Full suite: 164 tests. Earlier examples retain
their output hashes.

Next generalize resource planning with explicit dependency/ownership contracts,
then repair/inventory whole-route door graphs before claiming authored campaigns.
This milestone does not complete the roadmap's original-content campaign gate:
most terrain, actors and world structure still belong to the original game.


## Static world graph (v0.16.0)

See [WORLD-GRAPH.md](WORLD-GRAPH.md) for world-graph, incoming/outgoing edges, observed direct returns and mod routing deltas. Three-room example: four displaced incoming links explicitly identified. 170 tests; no automatic repairs, progression certification or new room permissions. Current estimate: 26%.


## v0.17 connection proposals

See [Connection planning](CONNECTION-PLANNING.md) for the isolated existing-door planner, input/output contracts, four restored static return links, and required native landing verification. `plan-connections` emits review evidence only. Current completion remains 26%; 174 tests pass with the private supported host.


## v0.18 native endpoint evidence

[Native connection testing](NATIVE-CONNECTION-TESTING.md) documents four controlled bidirectional crossings, settled landings and movement checks. Independent endpoint position fixtures are explicit; continuous room5 traversal and repaired-campaign lifecycle remain pending. The planner remains static-only; existing playable examples are unchanged.
