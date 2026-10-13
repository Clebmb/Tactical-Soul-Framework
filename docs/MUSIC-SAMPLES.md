# Original WAV instruments for boot melodies

`examples/imported-melody/mod.json` imports the bundled original triangle.wav
and plays it through the registered boot-melody voice. The file contains an
original40-sample triangle cycle, mono unsigned8-bit PCM at8000Hz, licensed
with the framework. No commercial audio is extracted.

Optional `boot_melody.sample` requires exactly `source`, `provenance` and
`loop_start`. Source must be a nonempty relative file path confined to the
manifest folder after resolution. Provenance must be nonempty text. An integer
loop_start must index a decoded sample (zero is valid); explicit null disables
sample looping. Without sample, the existing generated sine stays unchanged.
The melody sequence still ends after its finite repeats, independently of
whether the instrument sample loops during each note.

The shared `aria.content.decode_pcm_wav(bytes)` validates immutable WAV data
at most128KiB, uncompressed mono unsigned8-bit PCM, rates4000..32768Hz and
1..32768 samples. Truncated declared payloads fail. It returns signed PCM,
rate, count and source SHA256; existing `encode('pcm_s8', path)` now shares
this decoder. Melody import carries rate*1024 into WaveData's frequency word,
sets the explicit loop status/index and retains source fingerprints in
`rom.music_report.imported_sample`. No resampling, loudness normalization or
automatic pitch detection is performed. MIDI60 plays the source at its WAV
rate; an author must supply an appropriately tuned waveform for conventional
MIDI pitch. The example's40-sample8000Hz cycle has200Hz base pitch, not C4.

`install_boot_melody(rom, value, folder=None)` requires the owning manifest
folder when sample is provided. CLI passes it automatically. Schema, path,
format and loop failures preserve the caller; resource allocations and the
boot header pointer still use the staged writer and patch ledger. Source
project melody modules now support singleton ownership, asset rebasing and
fingerprints; see [project composition](PROJECT-COMPOSITION.md). Other instruments/slots, stereo,
16-bit/compressed WAVs, arbitrary sample effects and sample ownership during
gameplay remain outside this contract.

## Native evidence

`python scripts/verify_imported_melody.py` runs fresh native cores with the
imported looped instrument, its repeat, volume0, and nonlooping sample control.
Looped captures are byte-identical, volume0 entirely silent, and final200ms
silent. Measured pitches200.126,251.984,300.339,399.985Hz are within1% of
expected transpositions. A2048-sample first-note window matches the authored
triangle shape at best phase correlation0.984687. This is a bounded waveform
check, not full hardware/mixer equivalence. The nonlooping control produces
note bursts but exhausts before the next note; its initial/final200ms windows
in the capture are silent. No ROM-original/RAM/SRAM/controller fixtures.

197504 stereo frames at65536Hz, peak2880, looped PCM SHA256:
`a789e7f56013c7f1a385f052749cf1ad6e7f9428ddd48d0074d0c0827118726a`.
Private report `local/audio/imported-melody-report.json`; outputs remain local.
Nine added tests cover conversion/fingerprints, formats/rates, malformed and
truncated WAVs, budgets, schema/loop policy, native payload linkage and
transactional loop/path rejection. Full suite426 tests. Only the bundled8000Hz
sample and loop0/null are natively checked, not every accepted rate/loop.
Human listening, other assets and gameplay/save/transition lifecycle remain
pending. Next establish native coexistence/scene-transition evidence before
adding playback slots; project ownership/fingerprints can be extended separately.

[Boot music lifecycle](MUSIC-LIFECYCLE.md) now verifies native scene takeover
through the selected menu/new-game/pause/resume route. Broader channel, room,
save/death lifecycle remains pending.

## Bounded instrument banks

`boot_melody.instruments` optionally replaces `sample` with a list of1..8
WAV specifications using the same source/provenance/loop_start contract.
Declaring both fields fails. Per-note `instrument` selects a zero-based bank
index; omission selects0 on each note, including after another instrument or
across repeats. Rest steps contain only `rest`. The compiler emits VOICE before
a changed selection and allocates contiguous12-byte ToneData entries.
Existing single-instrument manifests retain byte-identical output.

Each source remains confined to its manifest/module directory, with individual
WAV limits unchanged. Total decoded PCM is bounded at65536 bytes per bank
(including repeated sources). All samples/voices/track/header and pointer writes
remain transactional: a late path/format/loop/budget/allocation failure leaves
the caller unchanged. Project composition rebases and fingerprints every bank
source under the singleton melody owner. No cross-module instrument sharing or
commercial bank reuse is supported. `music_report.instrument_bank` records each
source fingerprint, sample address/rate/count/loop; legacy scalar fields describe
instrument0. Generated sine remains available when neither sample field is set.

`examples/instrument-melody` has flat and project manifests with original MIT
triangle/square cycles. `scripts/verify_music_instruments.py` proves six sequential
notes across two passes: waveform correlations exceed0.984(triangle) and0.992
(square), square windows differ from an all-triangle control, first windows
match, fresh capture repeats exactly, mute is zero and the final tail is silent.
Evidence is private in `local/audio/music-instruments-report.json`. This is one
sequential track, not simultaneous-channel, hardware/listening or broad lifecycle
certification. Per-note sample pitch tuning remains the author's responsibility.

## Authored sampled envelopes

Optional `boot_melody.envelope` sets the shared sampled-voice default; an
optional `envelope` on `sample` or each `instruments[]` entry overrides it
for that instrument. Track objects cannot own envelopes. Each envelope must
contain exactly `attack`, `decay`, `sustain`, `release`. These are raw native
ToneData bytes, not milliseconds: attack1..255, decay/sustain0..255 and
release0..254. Attack0 and release255 are conservatively excluded. Zero
sustain is allowed. Omission retains the established255/240/180/200 bytes.
The writer stores the four values at offsets8..11 of each12-byte voice.
Report envelope fields record effective settings, including inherited defaults.

The pure `aria.music.plan_envelope` validates and normalizes these settings;
plan_boot_melody uses it before mutation. Project modules share this validator.
Invalid global or later instrument envelopes leave the image/ledger/allocations
unchanged. Existing default payloads remain byte-identical. Envelope authoring
does not reserve channels: tails can still overlap between notes/tracks.

Run `TacticalSoul.cmd play examples/envelope-melody/project.json` for an original
sine with a soft attack and short release; flat mod.json is equivalent.
`scripts/verify_music_envelopes.py` compares native controls with identical notes:
attack8 early RMS363 versus attack255 RMS1312, with identical held RMS1319;
decay192/sustain32 held RMS135; release224 retains RMS184 in the selected
post-gate window while release128 is zero. Fresh slow-attack playback repeats
exactly, mute is zero and all final windows are silent. Private report:
`local/audio/music-envelopes-report.json`. These are selected behavioral contrasts,
not exact envelope-clock equivalence, exhaustive byte-range certification,
listening approval or broad SFX/multitrack/save/death lifecycle proof.
