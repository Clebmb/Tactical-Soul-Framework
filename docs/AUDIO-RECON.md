# Audio reconnaissance (v0.46.0)

The ROM uses the standard GBA MusicPlayer2000 ("Sappy", m4a) driver: no
distinction between BGM and SFX, songs are multitrack command streams plus
a voicegroup (instrument bank). Command semantics below follow the VGMDocs
"Summary of GBA standard sound driver" reference (Bregalad/ipatix), itself
grounded in `ipatix/agbplay`'s sequence parser.

## What is established

- Six song tables, every entry decoded (`iter_songs`): 400 songs,
  578 tracks, 0 failures. Master table ROM `0x0827D058` (162 single-track
  songs: 153 FINE, 9 loop) reads as the SFX bank; table `0x0827CD40`
  (45 songs, 206 tracks, 191 loop-structured) reads as the looped-BGM bank.
  Entries are 8 bytes (song pointer, song-number metadata).
- Track prologues are musical: `BC 00` KEYSH transpose 0, `BB 35` TEMPO 53
  (106 BPM), `BD/BE` VOICE/VOL selects. Drum tracks show wait/running-status
  note grids exactly as the reference predicts.
- Five voicegroups, uniform 12-byte stride everywhere (pret `m4a_internal.h`
  / `music_voice.inc` via web research: all voice types share one 12-byte
  `ToneData`; there is no 8-byte square/noise shorthand and no group
  header). Typed census over valid prefixes (`iter_voices`): 91 resampled
  sampled (type 0), 444 fixed-frequency sampled (type 8), 55 square1, 4
  square2, 1 wave, 2 rhythm (`0x80`), 2 noise-alt. No key-split (`0x40`)
  voices exist in this game. Four banks fill all 128 slots; `0x0827C7B4`
  is a short bank (87 valid entries, unused tail).
- Correction to v0.46: type `0x08` is fixed-frequency/no-resample sampled,
  type `0x00` is resampled sampled — not generic "sampled" either way.
- Song header layout: u8 tracks, u8 blocks, u8 priority, u8 reverb/voice,
  u32 voicegroup, then u32 track pointers.
- Pointer-occurrence scoping (v0.26 precedent: scope only, no consumer
  proof): voicegroup pointers recur in song headers (~408 refs, matching
  the 400 decoded songs — independent confirmation of the header layout).
  The master table pointer has zero literal occurrences, so the driver's
  song-number lookup is not statically scoped this way; driver code
  identity remains open.

## Sample data census (v0.48.0)

Voices bind to `WaveData`: 16-byte header (u16 type 0, u16 status,
u32 freq word, u32 loop start, u32 size) plus 8-bit PCM payload.
Field order was settled empirically: size-at-+12 is the only reading
under which the next strict header lands exactly at data end plus a
1-4 byte gap. All 360 distinct samples validate (`decode_sample`):
2,303,945 payload bytes (~2.3 MB), biggest 58,591 bytes.

- Status `0x0000` (287: one-shot, loop field 0) backs type-8
  no-resample voices; status `0x4000` (73: looped, loop <= size)
  backs type-0 resampled voices, plus 15 loop-flagged zero-loop edges.
- Two freq words: `0x00A44000` (351) and `0x00D10C00` (9). Engine
  fixed-point rate semantics are unconfirmed, so no durations are
  claimed; rate-independent shape stats look like audio (mean DC
  offset -0.8 LSB, 25% mean zero-crossing rate, worst DC 25.9 on a
  bass-heavy sample with a 3% crossing floor).
- Sample packs show 1-4 byte inter-sample gaps; 28 samples have no
  strict header within 64 bytes past their end (pack tails).

## Rate semantics and first renders (v0.49.0)

Web research (Bregalad's Sappy notes, GBATEK `MidiKey2Freq`) gives the
freq-word semantics: rate at MIDI C4 = word / 1024, per-key playback
scaling by 2^((key-60)/12). Both native words decode to exact
standard MP2K rates: `0x00A44000` = 10,512 Hz (351 samples),
`0x00D10C00` = 13,379 Hz, the documented default mixer rate
(9 samples). `sample_c4_rate` / `sample_c4_duration` implement this
with a test pinning both documented values.

Three private sample WAVs render at derived C4 rates under `local/audio/`
(one-shots raw; the looped voice as attack plus two loop passes):
a 5.57 s full-range bed (58,591 B @ 10,512 Hz, RMS 96.9), a 0.16 s
looped hit and a 0.09 s 13,379 Hz blip, all swinging the full 8-bit
scale (peak 128). Rendered bytes are structurally sound; no ear has
confirmed them, and mixer-rate resampling/ADSR/envelope behavior is
still untraced.
- REA MCP (`reverse-engineer-anything`, connected) was bound for
  this question per the skill workflow and rejects the GBA ROM as
  an unsupported binary format, matching the v0.26 finding; the
  census above is independent static work, not REA evidence.

## Explicit assumption (not reference text)

A top-level PEND (empty pattern stack) is treated as a no-op section
separator. It fires across the corpus and the shipped game plays those songs
songs, so the engine behavior there is non-fatal by construction — but no
driver trace confirms no-op versus ignore-with-side-effects. Native
confirmation is the next audio step.

## API contracts (`aria/audio.py`, pure, read-only)

- `parse_track(rom, start, rom_base, budget)` -> `{"ok", "fine"}` or
  `{"ok": False, "why", "at"}`. PATT pushes a return address (max depth 4);
  PEND pops; loop detection is over (pc, stack depth, running status).
  Running status survives waits and flow commands, matching the engine.
- `decode_song_header(rom, offset)` -> tracks/voicegroup/track pointers.
- `decode_voice_entry(rom, offset)` -> type/key/kind plus kind-specific
  payloads (sample/wave pointers and ADSR, duty/period bytes, or key-split
  table pointers); ValueError only for unknown type bytes.
- `iter_songs(rom, table_offset, count, rom_base)` and
  `iter_voices(rom, offset, count)` -> indexed iteration over tables and
  banks. `iter_voices` is structural: callers bound short banks (like the
  87-entry `0x0827C7B4`) by payload validity.
- `decode_sample(rom, offset)` -> WaveData type/status/freq/loop/size plus
  the payload file range; ValueError unless every field validates.

## What remains (no writer ships)

## Sequence event renderer (v0.50.0)

`iter_events` schedules a track as `(tick, event)` tuples: note strikes
with key/velocity/voice/length, tempo and VOL changes, pattern-inline
expansion, backward-GOTO unroll (one extra pass, then a `loop` marker)
and FINE `end`. `ticks_to_seconds` converts at the reference rule
(1 tick = 1 frame at tempo 75). A private renderer (`local/render_song.py`,
not shipped) mixes scheduled notes at 13,379 Hz: per-note rate from
freq/1024 transposed by (note key - voice base key), linear resample,
VOL/velocity gain, looped voices filling the note gate, mono sum.

Approximations (engine-mix equivalence unconfirmed): flat velocity
(default 64 when omitted), no ADSR/envelope, tempo kept per track,
PSG (square/wave/noise/rhythm) voices not synthesized. Hardened this
turn: out-of-image starts terminate instead of raising (regression test).

Native renders under `local/audio/`: SFX-bank song 0 (1 note, 0.5 s);
BGM-bank song 0 as 60 s (3,832 scheduled note events: 2,942 sampled,
186 square1, 704 rhythm; 459 sampled notes mixed, PSG skipped) and
song 1 as 30 s (5,426 events, 226 mixed). Mix peaks pre-normalization
are non-silent (53-180); no ear has confirmed them.

## PSG synthesis and sampled envelopes (v0.51.0)

Shared-authorship turn: a concurrent in-repo pass landed a corrected
scheduler model, `aria/audio_synthesis.py`, and renderer upgrades
(described below); this turn added PSG/pitch/envelope aids,
integrated, verified, documented and released. Read both modules'
docstrings for roles: `audio.py` holds structural decoders plus
approximate per-sample reconstruction aids, `audio_synthesis.py`
holds the stricter integer engine-update ADSR model and the
seam-aware resampler (both honest about untraced engine timing).

Corrections to v0.50 assumptions: scheduler timing is now gate-based
(waits-only advance time, W00 = 0, notes carry independent gates so
chords schedule; third note arg extends the gate); PSG voice key
bytes are percussion-only — pitched PSG pitch comes from the *note*
key (C4 = 261.6 Hz square, wave one octave down). `aria/audio.py`
aids: `DUTY_PATTERNS` (exact 8-step 12.5/25/50/75% patterns),
`psg_tone_freq` (equal temperament from A4 = 440, matching the C4
point) and `sampled_envelope` (reference endpoints, linear attack,
multiplicative decay/release, raw preset unity) — consumed by the
renderer's square/wave/noise synthesizers. Tests pin table sums,
the C4 point, envelope endpoints, chord/gate scheduling and every
wait opcode.

The private renderer mixes through the integer model (per-song tempo
map, no-resample voices at output rate, 1 s release tails, rhythm
percussion-table voices skipped and counted): BGM song 0 at 60 s
mixes 971 notes (120 rhythm skipped), song 1 at 30 s mixes 715
(170 rhythm skipped). Mixes stay non-silent; no ear has confirmed
them.

## What remains (no writer ships)

Driver-trace confirmation of top-level PEND and the timing/velocity/
ADSR defaults, ear-confirmed playback, PSG synthesis, song-number-to-
game-event mapping, and any composition/replacement writer.
Voicegroup strides are settled (uniform 12); key-splits need no
support (absent from this ROM).

## Source reconstruction follow-up (2026-10-11)

The v0.50 scheduler incorrectly added note gates to track time and indexed
waits one entry late. Corrected: W00 is zero, W06 is six ticks, W96 is 96;
only waits advance time. Simultaneous notes remain simultaneous. Note gates
include the optional third argument (byte wrap); omitted key/velocity retain
their track values. Bare VOICE running status now changes the selected voice.
Prior private WAVs and their timing statistics are historical approximations;
regenerate them before listening comparisons.

`aria.audio_synthesis.sampled_envelope(attack, decay, sustain, release,
gate_frames=..., frames=...)` returns immutable byte levels, bounded to one
million mixer updates. Attack adds with saturation; decay/release multiply
then shift right eight; decay clamps to sustain. Release can interrupt attack.
Frame zero applies attack; gate zero cancels startup.

Provenance: [pret reference mixer and sequence implementation](https://github.com/pret/pokeemerald/blob/master/src/m4a_1.s),
`SoundMainRAM` envelope branches, `ply_note`, and `MPlayMain` wait dispatch;
[command definitions](https://github.com/pret/pokeemerald/blob/master/sound/MPlayDef.s).
This is external source evidence, not an Aria driver trace or REA evidence.
No binary investigation or REA setup was needed for these Python changes.

The caller supplies mixer-update counts: musical ticks are not frames.
Pseudo echo, channel stealing, sample exhaustion, pan/master gain, PSG and
Aria's exact update phase remain outside the helper. TIE/EOT, REPT,
conditional MEMACC, pitch controllers and shared tempo remain incomplete in
`iter_events`; it is not a complete sequencer. Ear confirmation and native
envelope matching remain pending. No new audio writer or native ABI.

Regression: 314 full-suite tests pass; seven new tests cover every wait,
chord/gate/key state, voice running status, integer ADSR transitions,
release interruption, zero gates and input bounds. Maturity stays 34.7/100.

## Checked PCM rendering follow-up (2026-10-11)

`aria.audio_synthesis.render_sample(pcm, source_rate, output_rate=...,
frames=..., loop_start=None, envelope=None, envelope_rate=60)` is a pure
diagnostic resampler. Input is immutable **signed** 8-bit PCM; output is a
tuple of float sample levels. Linear interpolation wraps at the loop seam,
including a loop starting at zero. One-shots hold their last value until
the next source boundary, then emit silence. Rates must be positive/finite,
loop indices valid, frame count at most one million, and envelope levels
integer bytes. Envelope update rate is separate from output sample rate;
an exhausted envelope is silent. No file IO, ROM mutation or mixer ownership.

Five synthetic tests cover signed extrema/one-shot exhaustion, fractional
loop seams across many passes, single-sample loops and large rate steps,
independent envelope clocks and invalid inputs. Full suite: 322 tests pass.
The older `aria.audio.sampled_envelope` remains an approximate compatibility
helper; the new renderer uses the integer model in `audio_synthesis`.

Private `local/render_song.py` now uses the exact-host loader, this resampler,
the integer envelope at an assumed 60 Hz, and a shared integrated tempo map.
No-resample voices use the output rate. Sample release tails are capped at
one second. Unresolved rhythm instruments are counted/skipped, rather than
misrepresented as noise. Existing approximate PSG oscillators remain.
New private `*-corrected.wav` files preserve previous renders. Two 12-second
BGM extracts mix 176/254 notes and skip 10/69 rhythm notes; RMS is 19.439/35.836
on signed 8-bit output. SFX song 0 mixes one note, RMS 12.296. Exact hashes and
counts are in `local/audio/corrected-render-report.json`. WAV parameters and
non-silence were checked; these are offline reconstructions, not native audio
captures or listening approval. Host hash is unchanged.

Native mixer equivalence, hardware filtering/quantization, PSG envelope/noise
pitch, rhythm bank resolution, TIE/EOT, conditional sequencing, pitch
controllers and human ear confirmation remain open. Next: resolve rhythm
instruments with guarded sub-bank lookup and fixtures, then compare against
native captured audio. Weighted maturity stays at the existing 35.1/100.

## Guarded rhythm lookup follow-up (2026-10-11)

`resolve_note_voice(rom, bank_offset, voice_index, note_key, rom_base=...)`
returns `{voice, offset, playback_key, rhythm_pan}`. Bank/selected offsets
are file offsets, while embedded bank pointers are ROM addresses. Direct
voices retain the note key. Rhythm uses note key as a 12-byte child index,
then uses the child's key for pitch and its optional forced pan (-128..126).
No recursion: nested banks, key-splits, unknown types, invalid MIDI arguments,
truncated records and out-of-image pointers fail with ValueError. The lookup
checks image bounds, not semantic ownership of every neighboring record;
callers must use an established bank. It does not validate sample payloads.
The existing structural decoder's `table_b` field is unused for rhythm and
must not be interpreted as a required second pointer by this resolver.

Provenance: [pret `ply_note` instrument selection](https://github.com/pret/pokeemerald/blob/master/src/m4a_1.s)
and [ToneData/SoundChannel field offsets](https://github.com/pret/pokeemerald/blob/master/constants/m4a_constants.inc).
This is reference-source behavior, not an Aria driver trace. Seven synthetic
tests cover direct/child pitch, forced pan, pointers/truncation, nested banks,
unknown children, bad arguments and a custom ROM base. Full suite: 329 tests.

The private renderer now resolves rhythm voices, and transposes resampled PCM
from WaveData's C4 rate using the resolved playback key, rather than subtracting
the direct instrument's key byte. It remains mono and does not apply forced pan.
New `local/audio/bgm-{0,1}-rhythm.wav` diagnostics preserve earlier files.
In the same 12-second windows, notes mixed rise from 176/254 to 186/323,
including all previously skipped 10/69 rhythm notes. No voices were skipped in
these windows. RMS: 19.454/32.408; WAV format/non-silence and original host hash
checked. Details: `local/audio/rhythm-render-report.json`. These are offline
reconstructions; no native or REA evidence or human ear confirmation is claimed.

No audio writing or native ABI changed. Native pitch/envelope comparison,
PSG/noise fidelity, pan/mix ownership, TIE/EOT and conditional sequencing remain
open. Next: native audio capture comparison or a bounded campaign/event slice.
Completion remains 35% (35.1/100), with no added maturity points this turn.

## Tied notes and explicit releases (2026-10-11)

`iter_events` now emits `("tie", key, velocity, voice)` for TIE and
`("release", key)` for EOT, including running-status forms. Neither advances
time. Omitted keys/velocities retain track state; explicit EOT updates the
retained key. Existing finite-note/controller tuple formats remain unchanged.
Reference source: [pret `ply_note` and `ply_endtie`](https://github.com/pret/pokeemerald/blob/master/src/m4a_1.s).
The reference releases the newest eligible matching original MIDI key, rather
than every same-pitch note. This source behavior is not an Aria native trace.

`aria.audio_synthesis.gate_tied_events(events, final_tick=...)` converts a
bounded scheduler sequence into finite note gates for diagnostic rendering.
It preserves controller order, shortens the newest active matching note at
release, ignores unmatched/expired releases, and caps unclosed ties at
end/loop or the explicit final tick. Maximum 20,000 input events; ordered
integer ticks within the final bound are required. Input is not mutated.
This models keys/gates, not native channel priority/stealing. Terminal events
cap gates; the renderer still applies its diagnostic release tail, rather
than reproducing a native hard track stop. It does not add a sequencer writer.

Ten synthetic tests cover explicit/omitted/running arguments, key retention,
pattern returns, scheduler budgets, polyphony, repeated-key newest selection,
expired/unmatched releases, unclosed caps and bounds. Full suite: 339 tests pass.
Private renderer uses this helper. BGM 0/1 schedules expose 8/6 ties and the
same numbers of releases over the bounded unroll. New 12-second extracts mix
189/323 notes (RMS 28.519/32.408), with no unresolved voices in these windows.
Private report: `local/audio/tie-render-report.json`; WAVs `bgm-*-ties.wav`.
Formats/non-silence and unchanged exact original hash checked. No ear approval,
native audio capture or REA evidence is claimed.

The latest TIE/EOT support supersedes earlier missing-feature notes above.
Conditional MEMACC/REPT sequencing, pitch controllers, native PSG/envelope/mix
fidelity and human listening remain open. Next: native capture comparison or
a bounded campaign/event slice. Maturity remains 35% (35.1/100).

## Shared tempo clock

`aria.audio_synthesis.TempoMap(schedules, initial_tempo=75)` compiles scheduler
tracks into a shared diagnostic clock. `seconds_at(tick)` integrates tempo
changes; `duration(start_tick, end_tick)` handles gates spanning changes.
Same-tick commands sort by track index then event order; the last wins. This
is explicit diagnostic ordering, not an Aria driver trace. Tempo zero fails.
Inputs are bounded to 16 tracks, 20,000 total events and integer ticks through
one billion. Per-track ordering and tempo bytes 1..255 are checked. Inputs
are copied into compiled segments; later schedule mutations do not affect it.
Queries use binary search and extrapolate the final tempo. Native clock drift,
conditional sequencing and mixer behavior remain outside this helper.

Five synthetic tests cover integration, shared ordering, extrapolation, bounds
and malformed inputs. Full suite: 390 tests pass. The private renderer now uses
this API; BGM 0 still produces 189 notes over 12 seconds with byte-identical WAV
SHA256 `9f6e52e449945cf2161801629119957843c918ffdb48b30116caa99c01f7604c`.
Private output: `local/audio/bgm-0-tempo-map.wav`. No listening approval or
native audio capture is claimed.

## Native emulator audio capture (2026-10-12)

`scripts/emulator.py` now exposes opt-in `start_audio_capture(max_frames)` and
`stop_audio_capture()`. Capture is disabled by default. Both libretro audio
callbacks collect signed-16 stereo frames in a bounded buffer; batch callbacks
copy only remaining capacity. Overflow is recorded inside callbacks and raised
when stopping, rather than silently delivering a truncated recording. Starting
twice, stopping without a capture and starting after close fail. Frame budgets
are 1..10,000,000. Checkpoint restoration does not rewind captured audio; start
a new capture after restoring when comparing forks. This Windows harness uses
little-endian PCM and does not resample or normalize the captured stream.

Timing comes from `retro_get_system_av_info` after game loading, following the
[libretro lifecycle contract](https://docs.libretro.com/development/cores/developing-cores/).
This core reports 65,536 Hz and 59.727500915527344 fps.
`python scripts/verify_audio_capture.py` runs two fresh exact-host cores with
1,000 warmup frames and 300 controller-free captured frames. Both yield exactly
329,172 stereo frames (5.022766 seconds), byte-identical PCM, peak 17,280 and
RMS 4,404.403. State is game 1/substate 0. Initial 200,000-frame capture correctly
failed its budget; the final verifier uses 500,000. No game RAM, SRAM or ROM
writes are used. Original hash remains unchanged. Four collector contract tests
and the full 394-test suite pass.

Private evidence: `local/audio/native-boot.wav` and
`local/audio/native-capture-report.json`. PCM SHA256:
`6a38e113249fbf87c1dc0327506335586f8573adef9b22fd5134254607d4c61e`.
This establishes deterministic native emulator output capture, not song-table
identity, sequence start alignment, physical hardware fidelity or listening
approval. REA's previously established unsupported-GBA boundary is unchanged;
these are mGBA observations, not REA analysis. Next identify the captured song
and align a reconstruction before making pitch/envelope/mix comparisons.

## Boot-song playback binding (2026-10-12)

`aria.audio_binding.match_song_headers(memory, memory_base, catalog)` is a
read-only candidate matcher over aligned 32-bit little-endian RAM words.
Explicit `(identity, header_address)` catalog entries preserve aliases and
repeated locations. Limits: 1 MiB aligned immutable memory, 4,096 catalog
entries and 20,000 output matches. Invalid ranges/pointers fail; a match
alone never establishes activity or a player-structure ABI. Five synthetic
tests cover aliases, empty results, bounds, malformed catalogs and output caps.

`python scripts/verify_audio_binding.py` provides separate native binding
evidence. At controller-free boot frame 1,000, the 45-entry BGM catalog has
one header match across full EWRAM and IWRAM: IWRAM `0x03005360` contains
`0x0848E7B8`, table `0x0827CD40` index 26 (seven tracks). Two fresh cores
observe the same live-field transitions: zero at frame 1, `0x084F08C0` at
frame 5, and song 26 at frame 433. Initial frame-zero IWRAM probing was
unavailable before the core supplied memory maps; the verifier begins at frame 1.

An isolated diagnostic changes exactly the four-byte table-entry-26 header
pointer to entry 0's `0x084D8E60`. At frame 433 the live field now points
to song 0; the 300-frame capture after the same 1,000-frame warmup changes
PCM hash from `6a38e113249fbf87c1dc0327506335586f8573adef9b22fd5134254607d4c61e`
to `25243f1caa21c1e755a8ebb533624765fbefc84d67d5c4845982d7e6419d4145`.
Timing, capture length and game/substate remain equal. The original is unchanged;
no RAM/SRAM/controller fixtures are used. This establishes the boot playback
lookup for this slot, not every table's semantics or a generalized music writer.

Private report/diagnostic: `local/audio/boot-binding-report.json` and
`local/audio/boot-song-redirect.gba`. The private offline renderer also produces
`local/audio/bgm-26-binding.wav`: 231 notes, 10 rhythm notes, no skipped voices
in 12 seconds. Full suite: 399 tests pass. Existing native capture starts
567 emulated frames after the header transition; that transition is a frame
anchor, not a proven sample-accurate audible onset. Reconstruction alignment,
clock drift, pitch/envelope/mix fidelity and human listening remain pending.
REA's unsupported-GBA boundary remains; all runtime evidence here is local mGBA.

## Coarse native/reconstruction comparison (2026-10-12)

`aria.audio_comparison.rms_windows(samples, sample_rate, window_seconds=0.02)`
returns complete RMS bins on a seconds grid, dropping the partial tail.
`align_envelopes(reference, observed, max_offset_bins=...)` scans nonnegative
full-fit offsets using Pearson correlation; ties prefer the earliest offset.
It reports the best and runner-up scores and usable candidate count, with no
confidence threshold. The caller must supply matching time grids. No stretching
or negative offsets are supported. Flat observed envelopes/no varying reference
windows fail rather than inventing a score. Inputs are bounded to one million
samples, 20,000 bins, 20,000 offset bound and two million alignment comparisons;
finite nonnegative envelope levels and finite samples are checked.

Five synthetic tests cover gain-independent known offsets, repeated-phrase ties,
RMS grid/partial tails, constant inputs and validation/work budgets. Full suite:
404 tests pass. The private `local/compare_boot_audio.py` renders 18 seconds of
song 26 (315 notes, 11 rhythm notes, no skips), converts the native signed-16
stereo capture to a mono average and the offline unsigned-8 WAV to centered
mono, and compares 20ms RMS windows. Mono folding and 8-bit reconstruction
quantization limit what this comparison can establish.

Private report: `local/audio/boot-comparison-report.json`; reconstruction:
`local/audio/bgm-26-comparison.wav`. Full-window best offset is 9.42 seconds,
Pearson 0.666692, runner-up 0.504978. The header-frame estimate is 9.493114
seconds, so the best coarse match is 73ms earlier. First-half correlation is
0.692017 at 9.42s. A globally searched second half prefers a repeated phrase
(implied start 8.16s, correlation 0.626247); constrained to within 200ms of
the first-half prediction, its best implied start is 9.42s, correlation 0.621825.
This shows why a single global maximum cannot certify onset or clock drift.

Do not treat these measurements as sample-accurate alignment, a validated
60Hz/59.7275Hz clock correction, pitch/envelope/mix equivalence, or listening
approval. Next use isolated note/onset windows and compare explicit clock
hypotheses before changing the reference timing model. No ROM writes or native
ABI changes are introduced by comparison; private audio stays excluded.

## Explicit sequence-clock hypotheses (2026-10-12)

`TempoMap(..., frame_rate=60)` now supports an explicit diagnostic frame rate
(finite numeric 1..1,000 Hz; booleans rejected). All integrated segments and
duration queries scale consistently; the default 60Hz result is unchanged.
This affects sequence time only, not pitch, output rate or the ADSR update
clock. Three added tests pin compatibility, scaling across tempo changes and
invalid clocks. Full suite: 407 tests pass.

Private `local/compare_audio_clocks.py` compares two 18-second song26 renders
against the same native capture on a 10ms RMS grid. The 60Hz render is
byte-identical to the preceding 18-second model. At 60Hz the best full offset
is 9.42s/correlation0.526361; at the core-reported59.727500915527344Hz it is
9.47s/correlation0.619274. The latter is closer to the9.493114s header anchor.
Scores differ from the previous20ms experiment because the window grid changed.

Three largest separated native RMS rises select0.5second onset-candidate
windows centered at1.78,2.40,3.04seconds of the capture; these remain mixed
audio, not isolated instruments. Searching within200ms of each full alignment:
60Hz implied starts9.42,9.42,9.41s with correlations0.8403,0.6095,0.7231;
core-rate implied starts9.47,9.48,9.47s with correlations0.8440,0.4590,0.7222.
The mixed local scores and10ms granularity do not certify a clock correction,
audible onset, drift, or hardware/mixer equivalence. Default timing stays60Hz.

Report: `local/audio/clock-comparison-report.json`; WAVs are private
`bgm-26-clock-*.wav`. No native code, ROM, RAM or SRAM edits. This finishes
the bounded clock comparison; prioritize checked original sequence/sample
authoring next instead of repeatedly optimizing this same reconstruction.

## Original music authoring milestone

[Original boot melodies](BOOT-MELODY.md) now provide the narrow checked writer
for original PCM, voice and sequential notes at the verified boot slot. Earlier
no-writer statements describe historical scope. Broad playback slots, loops,
imports and audio lifecycle remain pending.
