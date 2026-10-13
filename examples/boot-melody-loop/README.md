# Three-pass original boot melody

Run `TacticalSoul.cmd play examples/boot-melody-loop/mod.json` from the root.
`repeats:3` plays the original four-note phrase three times, then stops.
Repeats count total passes, not additional passes. There is no infinite loop
or new song-stop ABI. See [contracts](../../docs/BOOT-MELODY.md).
Native evidence covers all12 pitches, repeatability, zero-volume control and
silence after completion. Other playback slots/lifecycle remain pending.
