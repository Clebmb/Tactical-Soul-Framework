# Native ability workshop

From the Tactical Soul Framework root run `TacticalSoul.cmd play examples/ability-workshop/mod.json`.
Start a new game and advance the original dialogue. After taking damage, stand
still to heal 1 HP per 120 eligible frames. Press R to heal 5 HP for 3 MP, with a
180-eligible-frame cooldown. Holding R does not repeat casts. Full HP costs no MP.
Native guardian soul behavior may also use R; this callback does not consume it.

JSON parameter edits need no compiler. SDK C/header/linker edits need --compile.
Native names, equipment and original room topology remain intact. The save-route
shortcut used by the verifier is a private test fixture, not part of this mod.
See ../../docs/ABILITIES.md for the full contract, state/RAM ABI, custom-runtime
copy workflow, native test fixtures, limits and extension guidance.
