# Narrow native ownership barrier demonstration

`TacticalSoul.cmd play examples/soul-gate/mod.json` starts unowned in the verified
save room `(0,14)`. An **invisible** barrier at world X80 prevents tested ordinary
leftward walking, jumping and attacking from reaching the original west exit.
This is a blocking demonstration: it supplies no soul pickup or unlock route.
Use another example or restart to leave this demonstration.

The original standalone after-update callback releases the barrier when the first
red-soul ownership low nibble at `0x0201331C` is nonzero. It owns the single frame
hook, so cannot combine with `abilities` or another `frame_hook`. Source, linker,
manifest and binary fingerprints must match. Native edits require:

```powershell
TacticalSoul.cmd build examples/soul-gate/mod.json --compile
python scripts/verify_soul_gate.py
```

Player builds use the verified original runtime binary without a compiler.
No native grant call, custom save schema or custom RAM state is used. The callback
checks active gameplay/substate, Soma mode, positive HP, clear modal-lock bit and
the exact room pointer `0x0850F7EC`. Only player states 0 and 1 are admitted.
It compares signed native screen X (`0x02000524`, 16.16) plus signed camera X
(`0x0200A09A`, pixels) with world X80. If unowned and west of that boundary,
it restores screen X to the boundary and clears negative X velocity at
`0x0200052C`. It does not change Y, camera, inputs, ownership or SRAM.

## Native acceptance and limits

The verifier checks unowned walking, an actual jump and an actual attack against
the barrier, pause/resume, native statue save and fresh continue with count zero,
then continued blocking. A separate owned probe retains the original opening
acquisition, redirects the entrance door to this save room, saves and continues
with count one, then crosses the save room's **unchanged original west door**.
That crossing matches an image-bound authored policy requiring ownership.
Game actions use controller input; the only RAM fixture is transporting saved
SRAM into fresh cores. Original inputs stay unchanged. Reports and probes remain
under `local/`. The redirect is explicit and is not original-campaign proof.

This is not a general door-lock implementation. The after-update barrier can
only catch positions while the native core still reports this room. Arbitrary
speed, forced position changes, hurt/knockback, transformations, scripted
transitions and other player states are not certified; states outside 0/1 are
skipped. Do not rely on it for adversarial lock enforcement or expose arbitrary
room/coordinate settings. It has no visible gate art, collision resource, generic
gate manifest API or ability-dispatcher integration. No new room/start permissions
are introduced. Broader locks need an independently verified transition or
collision hook and lifecycle coverage.

A separate [custom SDK composition](../soul-gate-abilities/README.md) combines this bounded behavior with standard healing. The standalone example remains unchanged.
