# Original finite boot melodies

`TacticalSoul.cmd play examples/boot-melody/mod.json` replaces the verified
boot-song slot with four original notes. It plays once, then stops; it does
not replace gameplay music. No commercial audio is extracted or distributed.

An ordinary manifest accepts `boot_melody` with required `tempo`, `volume`,
and `notes`, plus optional `repeats` (total passes, default1). Each note has exactly `key`, `velocity`, `ticks`. The example
uses keys60,64,67,72, velocity80, ticks24, tempo75 and volume64. Bounds:
tempo30..120, volume0..100, keys48..84, velocity1..100, 1..64 notes and total
at most1536 ticks per pass. Repeats are1..8 total passes, with at most6144
expanded ticks. Tick lengths must be in `aria.audio.NOTE_LENGTHS`.
Numeric strings are accepted; booleans, extra keys, infinite loops and arbitrary
commands are rejected. Volume0 is an intentional silent control.

`aria.music.plan_boot_melody` validates without ROM IO. `install_boot_melody`
requires the registered exact host and original slot26 pointer `0x0848E7B8`
at table entry `0x0827CE10`. It stages a deep copy, allocates four isolated
resources and repoints only that entry's four-byte header pointer. Source
metadata and other songs stay unchanged. Allocation failure, precondition
failure or ledger conflict leaves the caller unchanged. An entire ordinary
manifest retains its existing application contract; this guarantee covers
the melody writer itself. Source project modules now support singleton melody ownership and confined
asset rebasing; see [project composition](PROJECT-COMPOSITION.md).

Resources: a framework-authored40-sample signed8-bit sine cycle, looping
WaveData (frequency word10512*1024, loop0), a single sampled voice with fixed
ADSR255/240/180/200, a sequential explicit-note/wait track ending in FINE,
and a one-track song header. The sample loops during a note; finite sequence repetition is compiled by
unrolling the bounded note list, followed by FINE. No native GOTO/REPT or
unbounded control flow is emitted. Nominal MIDI60 pitch is10512/40=262.8Hz. Original WAV imports are now supported through the explicit optional sample
contract in [Music samples](MUSIC-SAMPLES.md). No
PSG bank, chords, rests, pan control, release configuration, additional
playback slots, event triggers, channel allocation or callable audio ABI
is exposed. Output goes through declared free-space budgets and overlap ledger.
The API returns a report and retains `rom.music_report`.

## Native acceptance

`python scripts/verify_boot_melody.py` builds private outputs, boots two fresh
melody cores plus a volume0 control, then captures180 frames after440 warmup
frames. Both non-silent captures are byte-identical; the silent control is
all zero. The live header matches the allocated original header. Four100ms
left-channel windows measure262.791,331.094,393.547,525.582Hz, all within1%
of the authored pitches. The final200ms is silent. Core reports65536Hz;
197504 stereo frames, peak3072. Five ledger writes: four resources plus the
header pointer. No native code, RAM, SRAM or controller fixture writes.
Original ROM remains unchanged.

Private WAV/ROM/report are under `local/audio/`, with report
`original-melody-report.json`. PCM SHA256:
`0251846b9b4d87656b1fdeadefeb9aca6695df83a955c73046fa28b957e56700`.
Seven tests cover source contracts, budgets, linked payload decoding,
scheduled notes, repeated install, allocation exhaustion and ledger rollback.
Full suite:417 tests. REA's unsupported-GBA limitation remains; runtime evidence
is local mGBA, not decompiler evidence. Human ear approval, exact note timing,
hardware fidelity, gameplay/channel coexistence and save/transition lifecycle
are unproven. Next: explicit original sample imports and broader lifecycle evidence before
additional slots.

## Bounded finite repeats

`examples/boot-melody-loop/mod.json` sets `repeats:3`: the four notes play
three times, then stop. `ticks` in reports remains per-pass; `total_ticks`
includes repetitions. The default and explicit repeats1 produce identical
ROM bytes and ledgers. Three added tests cover repeat/total budgets, exact
scheduled strike times and backward compatibility.

`python scripts/verify_boot_melody_loop.py` captures420 frames after440
warmup frames from two fresh builds and a silent control. All12 notes pass
within1% pitch checks across three passes; fresh captures are byte-identical,
volume0 is entirely silent, and the last second is silent after FINE.
460844 stereo frames at65536Hz; PCM SHA256:
`6943b8f525f52a7d9ba2fc95593039b30498a405bacfd5f4aca8d4d9a7c7cb99`.
Private evidence: `local/audio/melody-loop-report.json` and
`local/audio/looped-boot-melody.wav`. One-shot native acceptance was rerun
and retains its prior PCM hash. No broader lifecycle or parameter-range
certification is implied. In particular, the example name does not promise
infinite looping or a native song-stop API.

Original WAV linkage is documented in [MUSIC-SAMPLES.md](MUSIC-SAMPLES.md);
older fixed-sine-only statements describe the earlier milestone.

## Rests and note gates

The `notes` list accepts note steps and explicit `{"rest":96}` steps.
A note's `ticks` advances the track clock; optional `gate_ticks` controls
its sounding gate and defaults to `ticks`. Both use registered NOTE_LENGTHS;
the gate must be positive and no longer than the step. Native release tails
can continue after the gate, so a rest does not instantly mute a voice.
At least one note is required. The 64-step,1536-tick per-pass and6144-tick
expanded budgets include rests. Existing manifests compile to identical bytes.
Project modules use the same validator and compiler.

Run `TacticalSoul.cmd play examples/phrased-melody/mod.json` for two short-gate
notes separated by an explicit rest. `scripts/verify_melody_phrasing.py`
checks selected native sound/silence windows, a full-gate control, mute and
fresh-run determinism. Private evidence is `local/audio/melody-phrasing-report.json`.
This proves selected boot timing only, not listening quality or broader lifecycle.

## Simultaneous tracks

`boot_melody.tracks` replaces `notes` with1..4 track objects, each containing
`notes` and optional `volume`(0..100, defaults to the global volume). Shared
tempo, repeats and instrument bank remain at melody level; per-track tempo,
repeats or asset ownership is rejected. Each clock starts at tick0. Leading
rest steps delay a track, and shorter tracks finish independently. Overall
`total_ticks` is the maximum expanded track duration, not the sum.

Per-track limits remain64 steps,1536 per-pass ticks and6144 expanded ticks.
The full song is capped at128 authored steps and12288 expanded aggregate ticks.
Gates cannot overlap within a track; at most four gates are active. Native
release tails may overlap those gates: `max_gated_notes` is not a total native
channel reservation or a guarantee against clipping/voice stealing. Select
modest volumes when mixing. No automatic gain normalization is performed.

All tracks share one staged sample bank. The header holds a count plus one
pointer per track; each stream initializes matching tempo, voice0, volume and
center pan, then emits its own sequence/FINE. `music_report.track_addresses`
lists streams in author order; the legacy `track` scalar denotes track0.
One-track wrappers and legacy notes compile to identical ROM bytes. Source
projects retain singleton ownership of the whole song; independently owned
track modules are not accepted.

Run `TacticalSoul.cmd play examples/polyphonic-melody/project.json` for a
simultaneous two-note original sine harmony. Flat and project builds match.
`scripts/verify_music_tracks.py` checks2/4-track low-volume chords with every
track isolated, fresh repeats, mute and final silence. All isolated pitches
are within1percent of expected; every component is present in the mix, and
the selected mixed window equals the integer sum of isolated windows exactly.
Private report: `local/audio/music-tracks-report.json`. These windows do not
certify arbitrary arrangements, hardware fidelity, SFX coexistence or broader
scene/save/death lifecycle. The existing lifecycle guide covers an earlier
single-track fixture only.

Sampled instruments now accept checked authored envelopes; see
[MUSIC-SAMPLES.md](MUSIC-SAMPLES.md#authored-sampled-envelopes) for inheritance,
raw-byte bounds and native evidence. Historical fixed-envelope limits above
apply to the earlier fixtures.
