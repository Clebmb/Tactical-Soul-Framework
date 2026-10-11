# Multiplayer feasibility: proposal, not an implemented feature

The Tactical Soul Framework could support future AoS multiplayer research.
There is currently no second-player engine, transport, synchronized world state,
remote actor renderer or multiplayer save format. Nothing in this document
is a supported manifest option or a promise of a complete co-op conversion.
Multiplayer is optional future scope, outside the current completion estimate.

## Distinct targets

| Target | Design | New work |
|---|---|---|
| Shared-seed race | Separate games with identical patches and agreed rules | Seeded authoring, session identity, timer/progress observations; networking optional |
| Ghost companion | Remote position shown in the same room, without combat | Read-only snapshots, transport, interpolation, remote rendering and room IDs |
| Local combat co-op | Two controllable actors in one simulation | Second actor lifecycle, independent input/combat/animation, camera, rewards and transitions |
| Online shared-world co-op | Independent clients agree on actors and progression | Co-op simulation plus authority, replication, latency handling, disconnects and save ownership |

These are engineering directions, not chronological requirements. A ghost does
not automatically evolve into combat co-op; its presentation layer can be reused,
but synchronized enemies and damage are a separate problem. A race can be useful
without modifying the single-player engine, though seed/session tooling is not
implemented by the current framework.

## Why emulator linking is insufficient

The [official mGBA README](https://github.com/mgba-emu/mgba/blob/master/README.md)
lists local link-cable support and lists networked link-cable support under
planned features as checked on 2026-10-10. This is upstream documentation, not
a test of this project's bundled build. Emulator linking transports the
communication a game implements; it does not create a second controllable Soma,
shared enemy simulation or co-op progression. Controller-sharing likewise does
not create two independently controlled characters.

An emulator companion could exchange high-level game observations independently
of GBA serial I/O. That route would be emulator-specific unless a separate native
link protocol were implemented. Do not assume an existing fork is compatible
or production-ready without checking its source, exact build and runtime behavior.

## Framework pieces that help

Exact ROM identity, separate outputs and checked patches make reproducible builds
possible. Stable base-state room IDs can identify locations, but alternate/event
states still need identities. The native hook/ability SDK offers a controlled
extension point, but its current HP/MP helpers and input assumptions are for the
existing player. Resource audits help plan graphics memory; they do not establish
remote sprite/OAM ownership. The native emulator harness can capture evidence,
but is not currently a dual-client synchronization or network test framework.

## Missing engine contracts for combat co-op

Inventory player-global reads/writes before introducing a second actor: movement,
collision, health, equipment, souls, hitboxes, invulnerability, targeting, animation,
room entry, death and menus. Do not clone a RAM block and assume engine pointers
will follow it. Establish actor creation/destruction and native call signatures.
Budget OBJ tiles, palettes and OAM independently of background tiles.

Define whether players must stay in one room, how the camera follows them, what
happens at doors, whether a menu pauses everyone, who receives drops, and how
death/revival works. Initially one room and shared camera would reduce scope.
General separate-room co-op would require substantially more world-state work.

For online play choose explicit authority: a host could own enemy health, loot
and progression; clients could send input/intent and receive validated outcomes.
This is a proposed architecture, not an established native hook set. Identify
enemies by stable session IDs, not raw RAM addresses. Define deterministic ticks,
sequence numbers, duplicate/stale message handling and reconnect behavior. Do
not synchronize arbitrary raw RAM across different builds or save states.

## Suggested first research milestone

Start with a read-only per-frame observation contract: exact build identity,
room/state identity, player world position, facing/animation observations and
timestamp/tick. Verify each field's width and lifecycle behavior. Capture a local
trace and replay a noninteractive marker; do not write into player/enemy/save RAM.
Next establish safe rendering ownership, then attempt two local instances and
room-gated ghosts. Only after reproducible evidence decide whether combat co-op
is worth the engine changes. No such prototype was implemented in v0.12.

Acceptance for any eventual co-op release must include new game, room transitions,
pause, player death, boss/event state, loot, save/fresh continue, mismatched builds,
disconnects and simulated latency. Do not equate a second sprite appearing with
a working multiplayer game. Keep multiplayer changes in an independent module
so total-conversion and single-player work can continue without requiring it.
