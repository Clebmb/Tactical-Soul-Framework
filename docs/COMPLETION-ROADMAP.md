# Total-conversion framework completion roadmap

The goal is a documented, reusable AoS framework that agents can use to build full conversion mods, including custom levels, assets, behavior, audio, progression and campaign/save integration. A GUI application is deferred and excluded from completion scoring; reusable backend APIs remain a goal. No framework can promise every conceivable engine modification without new investigation.

`framework/roadmap.json` is the machine-readable checklist and completion estimate. Update it alongside new implementation/evidence. `framework/capabilities.json` remains the implemented-versus-unimplemented API list. Historical guides may describe earlier milestone scope; use current capability flags and the newest domain guide for present contracts.

## Current estimated completion: 36%

The weighted maturity estimate is 35.1/100, rounded to 35%. This replaces the initial rough ~20% estimate with an explicit scope. It is engineering judgment, not elapsed work, test coverage, readiness to ship a conversion or time remaining. A working narrow example earns partial domain credit, never full-system credit. Revise estimates if investigation exposes larger dependencies; explain the change rather than quietly inflating progress.

| Domain | Weight | Current estimated points | Remaining acceptance |
|---|---:|---:|---|
| Verified build core | 8 | 6.3 | Broader dependency/budget planning and transactional composition |
| Native records and actors | 10 | 4.5 | Custom equipment effects, AI, resource provisioning and event-safe actors |
| Rooms, terrain and collision | 18 | 6.7 | Original graphics loads, additional rooms/formats, collision families, resizing and new rooms |
| Graphics and animation | 16 | 6.2 | Native sprite/frame/OAM/animation pipelines and ownership across actor types |
| Sound and music | 10 | 2.9 | Verified driver binding, audible samples, sequences/instruments and lifecycle regression |
| Mechanics and lifecycle | 10 | 2.0 | Native grants, behavior dispatch, persistent custom mechanics and safe APIs |
| Campaign, events, map and saves | 16 | 1.0 | Campaign compiler, progression, new-game/save identity and migration |
| Agent authoring contracts | 6 | 3.4 | Authored project model, composition, symbols, templates and frontend-ready contracts |
| Validation, docs and release | 6 | 2.8 | Broad campaign/hardware/resource coverage and conversion acceptance |

The JSON contains individual checklists within every domain. A domain reaches full credit only when its end-to-end contract, documentation, clean rebuild and relevant native lifecycle tests exist.

The [static campaign audit](CAMPAIGN-AUDIT.md) adds start-relative route and return observations; event/progression certification remains pending. This follow-up adds no maturity points.

## Implementation sequence and dependencies

1. **Original room graphics/palettes:** isolate a room's graphics/palette load lists, import a small original character set, calculate ROM/VRAM/palette budgets and prove native rendering/collision/reentry/save behavior. Current custom metatiles arrange existing characters; this next milestone supplies original pixels.
2. **Broader terrain support:** validate more ordinary rooms, complete brush/resource diagnostics, support collision families with individual native tests, then resizing/new-room records with entity/door bounds. Keep event/boss rooms separate until their lifecycle is understood.
3. **Actor visual pipeline:** inspect sprite/frame/animation/resource graphs, reskin one existing ordinary enemy without changing AI, verify all combat states, then add original animation/resource provisioning. Extend to weapons and player streaming independently.
4. **Native audio vertical slice:** identify actual driver/header/voice/sequence and playback contracts, bind one original effect, capture audible output and test coexistence with music and lifecycle transitions. Music authoring follows this verified consumer.
5. **Mechanics and events:** establish native grants, stat/UI refresh, behavior dispatch and persistence; expose validated APIs only after state/side-effect evidence. Add progression/event tooling with original identity preserved until a campaign compiler exists.
6. **Mini-campaign compiler:** integrate three original-content rooms, new-game start, doors/spawns, map identity, progression and native save/continue/death/return. This is the critical total-conversion acceptance slice.
7. **Authoring and scale:** reusable project/document models, manifest composition, symbols/dependencies, validation reports and templates; broaden the mini-campaign contracts to full campaigns and clean conversion releases. Headless workflows remain first-class; the GUI can be built later on these APIs.

Some actor/audio investigation can happen independently when authorized, but each milestone must leave a working bounded implementation and agent handoff. Avoid building an expansive editor UI before the engine contracts exist.

## Completion gates

- An original-content three-room campaign passes new-game, forward/return traversal, death, native saving and fresh-session continue.
- Original graphics, animations, audio and mechanics load through verified native paths with explicit resource ownership/budgets.
- Campaign identity, maps, progression and save compatibility have documented compiler contracts and regression evidence.
- Another agent can reproduce a clean build using the source project and its own exact private original, without undocumented local files.
- Release packaging includes only redistributable source/content and licensed runtimes, with provenance and test evidence.

These gates are not met today. Existing tools are useful for smaller mods; current scores must not be presented as total-conversion readiness.

## Required end-of-turn report

For each development turn, report concrete progress and validation, the next useful milestone, and the current estimated completion percentage. Mention material limitations or estimate changes. Keep this summary concise and link the relevant detailed guides; do not claim completed systems from roadmap entries alone.

The v0.6 milestone implements original characters/palettes and isolated load lists in one registered room (ROOM-ASSETS.md), raising the estimate from 21% to 23%. General resource ownership/slot selection, broader rooms, death/pause/event coverage and animation remain pending; the next step is dependency/budget auditing and broader lifecycle evidence.

The v0.7 static dependency audit and original-art pause/death/fresh-continue evidence raise the estimate from 23% to 24%. The full 343-slot survey identifies unsupported/static-dependency coverage gaps; it does not add import permissions. Resolve those gaps and prove additional ordinary-room ownership before widening registration. See ROOM-RESOURCE-AUDIT.md.


The v0.8 mixed-resource reader improves inspection coverage without adding a new authoring system. The completion estimate remains 24%; 8bpp rendering, other layer formats and broader write permissions remain pending.


The v0.9 read-only type-1/type-3 background API covers 24 additional structural layer records. Estimated completion remains 24%: native rendering and new authoring permissions still require separate acceptance evidence.


The v0.10 static 8bpp source raster has native load and tilemap evidence, but viewport pixel matching remains unresolved. Completion remains 24%; this does not complete the native graphics authoring pipeline.


The v0.11 catalog/resource integration makes byte-index backgrounds discoverable with explicit source-render scope and incomplete-palette diagnostics. Estimated completion remains 24%; this improves backend coverage without completing general authoring or total conversions.


The v0.12 format-aware tilemap budget correction is validated across all base rooms and the native affine fixture. Completion remains 24%. Multiplayer feasibility documentation describes optional future research and does not count as an implemented capability or enlarge the current completion denominator.


The v0.13 bounded state-discovery contract adds structural preparation for future campaigns. Original base slots contain no alternate links, so no native state-transition claim is made. Completion remains 24%; authoring and inheritance still need native evidence.


The v0.14 second registered room passes native original-art entry/return/save/fresh-continue/death checks, including contrasting resources sharing one physical slot. Terrain gains 0.5 and graphics 0.2 maturity points (24.6 total, rounded to 25%). This remains narrow partial credit; general room allocation and full conversions are unfinished. Earlier milestone estimates above are historical.


The v0.15 third room passes native contrasting-art route/return/save/death checks. Terrain gains 0.7 and graphics 0.3 maturity points (25.6 total, rounded to 26%). The original-content three-room campaign gate remains pending: this route reuses original rooms/entities and leaves displaced neighboring links unresolved. Earlier estimates are historical.


The v0.16 world graph inventories 343 rooms/725 doors and identifies four displaced incoming links in the three-room example. Campaign maturity gains 0.4 points for read-only graph/delta groundwork (26.0 total, still 26%). No route repair or progression certification is claimed.


### v0.17 — isolated route proposals

Checked connection proposals clone the image and allocation state, enforce the image preimage and conservative graph policy, and expose review evidence through CLI/API. The three-room neighbor proposal restores four observed returns statically. Native landings and progression remain unverified; no additional maturity points awarded. Current estimate remains 26.0/100 (26%). Next: isolated native traversal fixture for the four proposed endpoints, followed by campaign/event integration.


### v0.18 — controlled native endpoint regression

All four proposed neighbor door crossings pass active-state, settled in-bounds landing and movement-away checks in mGBA. A checked separate harness and two declared endpoint position fixtures isolate door behavior. Continuous room5 traversal and repaired campaign lifecycle remain pending. Completion remains 26.0/100 (26%); the full campaign gate is not awarded.


### v0.19 — reproducible input branches

Added bounded input replay descriptors and same-instance private native checkpoint forks. Native repeat checks match complete EWRAM, observations and framebuffer; 28 room5 single-jump timings do not reach the stated route goal. This improves reusable validation, but continuous traversal and repaired campaign lifecycle remain pending. Completion stays 26.0/100 (26%); no campaign gate awarded.


### v0.20 — terrain authoring and continuous bridge

Completion advances to 27.1/100 (27%): terrain +0.6 for fourth-room checked support and a native-verified redesign; authoring +0.3 for reusable rectangle compilation; campaign +0.1 for continuous repaired-neighbor crossings; release +0.1 for final-build lifecycle evidence and clean-package authoring checks. These are partial maturity credits, not full-domain completion. Broad event/campaign access, new rooms, sprites/animation, audio playback and persistent mechanics remain incomplete. The original-content campaign gate is still pending.


### v0.21 — support discovery and durable handoff

Read-only paginated terrain support and brush dependency diagnostics identify 311 static candidates, 4 existing registrations and 28 blocked base rooms without widening write access. A detailed Muse Spark 1.3 handoff and mandatory per-turn refresh workflow now preserve project continuity. Authoring maturity gains 0.2 points for reusable support discovery: 27.3/100, still rounded to 27%. Further progress requires actual authoring expansion/native support, not promoting static candidates automatically.


### v0.22 — composable source projects

Added ordered supported modules, per-room geometry/level batching, source/asset fingerprints, targeted ownership conflicts and atomic project application. A five-module example matches the flat verified ROM/ledger/allocator exactly. Authoring gains 0.9, build core 0.3 and release 0.1 for this reusable source workflow and clean-package evidence: 28.6/100, rounded to 29%. Native content coverage itself has not expanded; sprite/animation, audio playback, new rooms and campaign/save compilation remain major gaps.


### v0.23: sprite inspection prerequisite

Registered common, Julius and background-bats frame/hitbox/animation inspection now works with bounded record reads and byte-preserving checks. 209 tests pass. Actor rendering and replacement are pending; weighted maturity remains 28.6/100, rounded to 29%. See [sprite guide](SPRITES.md).


### v0.24: static actor artwork previews

Registered raw/LZ 4bpp page/palette resolution and static sprite-frame rendering now cover all 216 common/Julius/background-bat frames. Pixel tests cover packed 8x8 source addressing, parts/flips/transparency and bounds; private contact sheets were visually reviewed. 222 tests pass. Graphics maturity rises from 3.9 to 4.4; total is 29.1/100, still rounded to 29%. Native sprite pixel comparisons, writes, ownership and animation lifecycle remain pending. See [sprite guide](SPRITES.md).


### v0.51: PSG synthesis and sampled envelopes

Web research (Bregalad's Sappy notes, GBATEK sound pages,
GbdevWiki/Pan Docs, Tonc, pret `m4a.c`/`m4a_tables.c`) separates
instrument format from hardware behavior and corrects a v0.50
renderer assumption: PSG voice key bytes are percussion-only, so
pitched PSG pitch comes from the note key (documented C4 = 261.6 Hz
square, wave one octave down). `aria/audio.py` gains three
reconstruction aids with three synthetic tests: `DUTY_PATTERNS`
(exact 8-step patterns), `psg_tone_freq` (equal temperament matching
the C4 point) and `sampled_envelope` (reference endpoints, linear
attack, multiplicative decay/release, raw preset unity). Engine
integer timing is explicitly not reproduced. The private renderer
synthesizes square/wave/noise (hardware LFSR, key-scaled clock;
exact NR43 key table untraced), applies sampled envelopes, and
re-renders BGM song 0 (60 s, 971 mixed with 120 rhythm skips,
up from 459 sampled-only) and song 1 (30 s, 715 mixed with 170
rhythm skips, up from 226). 329 tests pass (two consecutive green
full-suite runs). Audio rises from
1.8 to 2.2; total is 35.1/100, still rounded to 35%. See [audio
reconnaissance](AUDIO-RECON.md).


### v0.50: sequence event renderer and song renders

`iter_events` turns a track into `(tick, event)` tuples — note
strikes with key/velocity/voice/length, tempo and VOL changes,
inline pattern expansion, backward-GOTO unroll with a `loop` marker
and FINE `end` — with `ticks_to_seconds` at the reference rule
(1 tick = 1 frame at tempo 75). Four synthetic tests cover
scheduling, loop unrolling, VOL/voice state and garbage-start
termination (the last added after a real native crash on a
mis-dereferenced table entry, which also hardened both parser
guards). A private renderer (`local/render_song.py`, not shipped)
mixes scheduled sampled notes at 13,379 Hz with linear resampling,
VOL/velocity gain, loop fill and mono sum; velocity defaults,
ADSR and PSG voices are explicit approximations. Native renders
under `local/audio/`: SFX-bank song 0 (1 note, 0.5 s), BGM-bank
song 0 (60 s window: 3,832 scheduled notes split 2,942 sampled /
186 square1 / 704 rhythm, 459 sampled notes mixed) and song 1
(30 s, 5,426 events, 226 mixed) — non-silent mixes, no ear
confirmation. 307 tests pass. Audio rises from 1.4 to 1.8; total
is 34.7/100, now rounded to 35%. See [audio
reconnaissance](AUDIO-RECON.md).


### v0.49: freq-word rates and first renders

Rate semantics are settled by web research (Bregalad's Sappy notes,
GBATEK BIOS `MidiKey2Freq`): a WaveData freq word is 1024x the C4
playback rate, with per-key scaling by 2^((key-60)/12). Both native
words decode to exact standard MP2K rates — `0x00A44000` = 10,512 Hz
(351 samples), `0x00D10C00` = 13,379 Hz, the documented default mixer
rate (9 samples). `sample_c4_rate` and `sample_c4_duration` implement
this with one test pinning both documented values. Three private WAVs
render at derived C4 rates under `local/audio/` (looped voice as
attack plus two loop passes): a 5.57 s full-range bed, a 0.16 s
looped hit and a 0.09 s blip, all full-scale with RMS 67-97. No ear
has confirmed them; mixer resampling, ADSR/envelope behavior and
song-event mapping stay open. 302 tests pass. Audio rises from 1.1
to 1.4; total is 34.3/100, still rounded to 34%. See [audio
reconnaissance](AUDIO-RECON.md).


### v0.48: WaveData sample census

Voices now bind to validated sample bytes: `decode_sample` covers the
16-byte WaveData header (u16 type 0, u16 status, u32 freq word, u32
loop, u32 size) with three synthetic tests, and all 360 distinct
sample headers in the ROM validate with zero failures (2,303,945
payload bytes, biggest 58,591). The size-at-+12 field order is proven
by next-strict-header landings at data end plus 1-4 byte gaps.
Status `0x0000` (287 one-shots) backs type-8 no-resample voices and
`0x4000` (73 looped) backs type-0 resampled voices; two freq words
(`0x00A44000` x351, `0x00D10C00` x9) with engine rate semantics still
open. Rate-independent shape stats look like audio (mean DC -0.8 LSB,
25% zero-crossing). REA MCP was bound per the skill workflow and
rejects GBA ROMs, as in v0.26 — the census is independent static
work, not REA evidence. 301 tests pass. Audio rises from 0.8 to
1.1; total is 34.0/100, still rounded to 34%. See [audio
reconnaissance](AUDIO-RECON.md).


### v0.47: full song tables and typed voice census

`iter_songs` decodes all six song tables end to end (400 songs,
578 tracks, zero failures): the 162-entry master at `0x0827D058`
reads as the SFX bank while `0x0827CD40` (45 songs, 206 tracks,
191 loop-structured) reads as looped BGM. Web research into pret's
`m4a_internal.h` / `music_voice.inc` corrects two v0.46 statements:
`ToneData` is uniformly 12 bytes for every voice type (no 8-byte
square shorthand, no group header) and type `0x08` is
fixed-frequency/no-resample sampled. `decode_voice_entry` now
covers all known types with kind-specific payloads and `iter_voices`
walks banks at uniform stride; the census over five banks finds 535
sampled voices, 59 square, 1 wave, 2 rhythm, 2 noise-alt and zero
key-splits, with four full 128-slot banks plus an 87-entry short
bank (`0x0827C7B4`). Pointer-occurrence scoping re-finds voicegroup
pointers in song headers (~408 refs for 400 songs, confirming the
header layout) but zero literal master-table refs, so driver code
identity remains open. 298 tests pass. Audio rises from 0.5 to
0.8; total is 33.7/100, now rounded to 34%. See [audio
reconnaissance](AUDIO-RECON.md).


### v0.46: Sappy driver structures identified

`aria/audio.py` adds a pure read-only MusicPlayer2000 parser:
`parse_track` (running status across waits, PATT/PEND call stack,
GOTO loops, FINE/loop verdicts), `decode_song_header` and
`decode_voice_entry` (12-byte sampled layout, type-gated). Eleven
synthetic tests cover status, patterns, loops, the top-level-PEND
no-op assumption and both struct decoders. Natively, the master
song table at `0x0827D058` fully decodes (162 songs, 153 FINE + 9
loop tracks, zero failures, three voicegroups) and a 201-song /
366-track corpus across six table candidates parses clean with
musical prologues (KEYSH 0, TEMPO 53 = 106 BPM). Voicegroup
`0x0827BCEC` (41 songs) decodes as type-`0x08` sampled entries.
Top-level PEND (136 tracks) is an explicit assumed no-op:
non-fatal by construction since the shipped game plays those
songs, but no driver trace confirms it. Audio rises from 0.2 to
0.5; total is 33.4/100, still rounded to 33%. No playback,
sample or voice writer ships. See [audio reconnaissance](AUDIO-RECON.md).


### v0.45: second verified new-game start

`aria/starts.py` is now a registry of verified room/landing pairs:
(0,31) at (128,141) plus (0,14) at (128,160), the latter found by
scanning all base slots for the save-statue entity signature (28
matching rooms). `scripts/verify_second_start.py` proves fresh
landing, statue save at spawn with SRAM change, and
fresh-instance continue in room 14. 283 tests pass. Campaign
0.9→1.0; total is 33.1/100, still rounded to 33%. Next:
campaign/event slices, audio binding, or soul-RAM/menu proof.


### v0.44: kill-transient lifecycle verdict

Fine-grained private probes closed the v0.43 undecided codes:
actor world-x reads as record word 8's low halfword over 256
(calibrated on a 254→93 zombie approach); the zombie death code
lives ~15 frames while `0x806e525` animates ~16 frames then
freezes permanently, surviving 300 idle frames with Soma on its
position and corpse-line walkovers. Magnetizing pickups cannot
behave that way, so the kill-locked transients are burst-particle
remnants (about four per kill), not soul crystals; the skeleton
pair keeps the same verdict class. No code changes; docs and
method only. Records 4.4→4.5; total is 33.0/100, still rounded
to 33%. Next: soul-RAM/menu proof, campaign/event slices, or
audio binding.


### v0.43: soul reconnaissance — drop-table mapping and spawn-scan boundary

`soul_catalog`/`resolve_soul` map all 113 enemy soul references
(111 distinct souls; (0,0) shared by three final bosses; all seven
rarity-zero holders are bosses) with a `enemies --soul 2:12` lookup.
`scripts/scan_soul_spawn.py` watchdogs EWRAM actor spawns across
zombie rarities 0/1/255 and skeleton rarity 1: slash effect
`0x80221cd` and a hit transient attributed, kill-locked transients
identified per victim (zombie death-state page flagged), and no
persistent crystal actor at any rarity. Reassignment stays rejected:
collection, soul RAM, menu proof and the rarity formula are named
blockers. 282 tests pass. Records 4.3→4.4; total is 32.9/100, still
rounded to 33%. Next: campaign/event slices, audio binding, or the
soul-collection proof itself.


### v0.42: project modules for full entity/door lists

`compose_project` now accepts `entity_lists`/`door_lists` with
whole-room ownership: duplicate room claims fail naming both owners,
and any full list alongside staged `room_edits`/`enemy_encounters`
fails with both owners named, mirroring the writer's combination
guard. Proven on the private host: the entire `custom_room` example
as six modules applies byte-, ledger- and allocation-identical to
the flat manifest. 280 tests pass. Authoring 3.3→3.4; total is
32.8/100, still rounded to 33%. Hooks, abilities, raw patches and
blobs stay single-manifest. Next: campaign/event slices, audio
binding or soul grant APIs.


### v0.41: bridge-deck reskin on a fourth art slot

`examples/bridge-art` registers room5 for chunk-24 / bank-8 art import
and redefines its bridge-deck metatile 6 through
`metatile_replacements` onto original ironwood-and-bronze pixels.
Collision is byte-identical; all other visual bytes preserved.
`scripts/verify_bridge_art.py` proves exact native VRAM/palette loads,
input-only bidirectional crossings and exact art reload on return.
277 tests pass. Graphics maturity rises from 6.0 to 6.2; total is
32.7/100, now rounded to 33%. No new write permissions or campaign
access. See [room assets](ROOM-ASSETS.md).


### v0.40: project modules for the newest sections

`compose_project` now accepts the singleton `new_game_start`, per-target
`palette_tints` and `metatile_replacements` in geometry entries, with
both-owners-named conflicts and the single-provider rule extended to
replacements. Proven on the private host: a four-module project built
from the real custom-room sections applies byte-, ledger- and
allocation-identical to the equivalent flat manifest. Full
entity/door lists stay single-manifest by design. See [project
composition](PROJECT-COMPOSITION.md). Authoring 3.1→3.3; total is
32.5/100, still rounded to 32%. Next: campaign/event slices, audio
binding or soul grant APIs.


### v0.39: flesh sanctuary — new-game start, replacement terrain, palette tints

`examples/custom_room` starts a fresh game in a flesh-themed save room
(0,31), exits right into a five-screen zombie corridor (0,3) and returns
left, with original flesh artwork, blood-red statue/flame/save-sparkle/
zombie palette tints and three native spawners. New framework contracts:
`new_game_start` for exactly one verified room/position
(`aria/starts.py`), isolated fixed-record `metatile_replacements` with a
native 256-definition write ceiling, and snapshot-verified shared
`palette_tints` (`aria/palette_tints.py`). Natively proven end to end:
fresh landing, exact VRAM/palette loads, both crossings, nine concurrent
zombie slots, statue save and fresh-instance continue with exact art
reload. See [custom room](CUSTOM-ROOM.md). Campaign 0.8→0.9, terrain
6.6→6.7, graphics 5.9→6.0; total is 32.3/100, still rounded to 32%.
Next: campaign/event slices, audio binding or soul grant APIs.


### v0.38: custom item and enemy names

`aria/labels.py` renames native item/enemy labels through checked
in-place edits (ASCII, fits original length, space-padded, terminator
preserved, one ledger entry, whole batch validated first). `label_edits`
works in manifests and `tsf-project` modules; `examples/label-workshop`
is runnable. Natively proven: a Knife→Fangs build (exactly 5 changed
bytes) twin-diffed over a 26-snapshot menu tour — deterministic control,
12 frames differ in tight menu-text cells. See [labels](LABELS.md).
Records maturity rises from 4.0 to 4.3; total is 32.0/100, still rounded
to 32%. Next: campaign/event slices, audio binding or soul grant APIs.


### v0.37: viewer contracts with room-viewer wiring

`aria/viewer.py` defines the headless data backend a future graphical
viewer would render: viewport math, room view models (visible cells,
entity/door markers, cropped layer pixels, audit notes) and document
views proven over two clean builds. Covered natively on the hallway,
including a real-manifest document view of the geometry workshop. See
[viewer contracts](VIEWER.md). Authoring maturity rises from 2.9 to 3.1;
total is 31.7/100, still rounded to 32%. Next: deeper native authoring
coverage (campaign/event slices, audio binding, grant APIs).


### v0.36: document-driven room previews

`preview_document` renders a room layer from a document's manifest state:
two clean builds, two renders, identical pixels required — the headless
equivalent of `preview-room --mod` for documents. See [editor
documents](EDITOR-DOCUMENTS.md). Authoring maturity rises from 2.7 to
2.9; total is 31.5/100, still rounded to 32%. Next: viewer frontend
contracts with a first room-viewer wiring.


### v0.35: clean-rebuild application of documents

`build_from_document` applies a document's manifest state to two clean
images and requires byte- and ledger-identical rebuilds (covered path:
`sprite_assets` through `install_sprite_assets` on synthetic images).
See [editor documents](EDITOR-DOCUMENTS.md). Authoring maturity rises
from 2.5 to 2.7; total is 31.3/100, still rounded to 31%. Next: viewer
frontend contracts and real-manifest preview wiring.


### v0.34: authored-change diffs and manifest IO

Editor documents gain a review flow: `changes_since_saved()` emits
deterministic `{path, kind, old, new}` records via `diff_states`, and
`save_manifest`/`load_manifest_state` round-trip authored states as
canonical JSON (`.json` only, validated). See
[editor documents](EDITOR-DOCUMENTS.md). Authoring maturity rises from
2.4 to 2.5; total is 31.1/100, still rounded to 31%. Next:
preview/build application of documents and viewer contracts.


### v0.33: immutable editor documents with undo/redo

`aria/editor_docs.py` implements the long-pending editor foundation as a
headless backend (no GUI): immutable authored states with deep-copy
commits, bounded history (1..256), redo clearing, stable SHA-256
fingerprints, dirty/save tracking and validated JSON round-trips, plus 6
synthetic tests. Previews must apply the current state to a clean image
per build, never accumulate allocator claims. See
[editor documents](EDITOR-DOCUMENTS.md) and the
[GUI editor roadmap](GUI-EDITOR-ROADMAP.md). Authoring maturity rises
from 2.2 to 2.4; total is 31.0/100, still rounded to 31%. Next:
document-to-manifest authoring and viewer-frontend contracts.


### v0.32: spawn-anchored twin negative

`scripts/attribute_spawn_events.py` (private) kill-then-respawns the
hallway walker and twin-diffs snapshot windows around the EWRAM-observed
respawn on the original vs the magenta diagnostic: spawn frame 8 in all
three runs, world-x 35 throughout, control exactly deterministic, zero
differing frames in spawn-pre (3) and spawn-post (20 over 60 native
frames). The page is not rendered at the hallway spawn moment either.
Graphics maturity rises from 5.8 to 5.9; total is 30.8/100, still rounded
to 31%. See [enemy binding](ENEMY-BINDING.md). Next: other rooms/actors,
then a writer only with a tracer-named consumer set.


### v0.31: reusable attribution library; hallway Soma-art negative

`aria/sprite_attribution.py` promotes the twin-run framebuffer diff into a
reusable snapshot-anchored API (`diff_framebuffers`, `heat_cells`,
`diff_scenes`; 4 synthetic tests) with no OAM-map dependence; the private
tracer now delegates to it with an identical report shape. Reading the
existing hallway evidence through it, the post-kill scene (walker dead via
the HP-zero fixture, Soma on screen) still shows zero differing frames,
so page `0x08635990` is not Soma art in these hallway scenes either.
Graphics maturity rises from 5.7 to 5.8; total is 30.7/100, still rounded
to 31%. See [enemy binding](ENEMY-BINDING.md). Next: spawn-event diffs
and other rooms/actors, then a writer only with a tracer-named consumer
set.


### v0.30: walker twin-run negative; player/enemy attribution corrected

`scripts/trace_sprite_consumers.py` repoints all three copies of page
`0x08635990` at one rebuilt solid index-1 stream (plus magenta in one
palette instance) and twin-runs hallway idle/walk/fight-contact/kill
scenes with verified determinism: zero differing pixels everywhere, zero
magenta rendered, although the diagnostic art demonstrably reaches VRAM.
No walker writer ships. Kinematics (Soma world-x minus bank-0 OAM-x
pinned at 32; entries persist across a room transition) show the tracked
bank-0 tall entries follow Soma, not the walker, and a full manual render
of those entries matches 0 of 2320 snapshot pixels — OAM-map reads are
untrusted for render attribution. v0.29 stands only as art-content
identity (page bytes, palette byte-match, table grouping); its rendered-
consumer proof is withdrawn. Graphics maturity returns from 5.9 to 5.7;
total is 30.6/100, still rounded to 31%. See [enemy
binding](ENEMY-BINDING.md). Next: snapshot-anchored attribution with no
OAM-map dependence, other rooms/actors, and testing the Soma-art
hypothesis for the page.


### v0.29: walker art source identified (render proof withdrawn in v0.30)

A read-only live capture (hallway OAM tiles plus OBJ bank-0 palette, no RAM
writes) plus static analysis identified walker art content: actor table
`0x080E13C0` row 8, palette `0x0820B164`, graphics struct `0x0823199C` with
12-frame part lists, LZ art page `0x08635990` and raw top-half tiles at
`0x08166D18`-family — both live-matched byte-for-byte. The v0.28 "not any
LZ page" claim was a residency-vs-content comparison error. A premature
`zombie` registration is withdrawn for cause (live palette/art mismatch; its
pools belong to Arachne create plus helpers) and renamed `unknown-actor-2`;
its writer entry is removed. 248 tests pass; 272 frames render. Graphics
maturity rises from 5.6 to 5.9; total is 30.8/100, still rounded to 31%.
See [enemy binding](ENEMY-BINDING.md). Next: twin-run magenta on page
`0x08635990` to name every rendered consumer, then a checked walker writer.


### v0.28: tracer verdict and raw writer infrastructure

A deterministic magenta twin-run tracer proves the v0.27 candidate page is
never rendered in hallway idle/fighting/kill scenes or a two-room sweep, so
the zombie attribution was withdrawn (registration renamed to
`unknown-actor`) and earlier disappearance evidence reclassified as generic
tile collisions. The writer is now registry-driven with synthetically tested
raw in-place replacement; `background-bats` stays the only production
resource. 240 tests pass. Graphics maturity rises from 5.5 to 5.6; total is
30.5/100, still rounded to 30%. See [enemy binding](ENEMY-BINDING.md). Next:
door-aware tracer sweeps of new candidates, then a checked writer.


### v0.27: enemy binding discovery (no writer yet)

Registered the zombie spawn-candidate struct (21 frames/9 animations), raw 4KB
page and 1-bank palette for read-only inspection and true-palette static
previews (237 frames total); native OAM tracking was then believed to
separate a moving bank-0 zombie from static bank-10 Soma (v0.30 corrects
this: bank-0 tracks Soma, and OAM-map reads are untrusted for render
attribution) and the HP-zero kill fixture clears every
Zombie slot. No reskin writer was authorized: hallway-combat VRAM captures
prove the walker streams from none of the candidate page, common pool or five
LZ table pages, so dedication is unproven. Graphics maturity rises from 5.3 to 5.5; total is 30.4/100, still rounded to 30%. See [enemy
binding](ENEMY-BINDING.md). Next: loader trace plus zombie-pinned capture to
name the walker source, then a checked writer.


### v0.26: composed sprite projects

Sprite asset modules compose into `tsf-project` documents with confined source rebasing, asset fingerprints and duplicate-resource ownership errors naming both modules. The single-module `examples/sky-invaders/project.json` reproduces the flat reskin ROM/ledger/allocations exactly (SHA256 `3b17a2fd90da7c332d0181c66da55583432d56b1a3013af3378ae9ed4b02f1bd`); 238 tests pass and native entry/pause/reentry plus composed save/death/fresh-continue evidence was re-run against the relocated sources. Authoring maturity rises from 2.0 to 2.2; total is 30.2/100, still rounded to 30%. Static pointer-occurrence counts (common 77/90, Julius 7, bats 2/2) scope the next enemy-binding investigation without proving consumers. See [project composition](PROJECT-COMPOSITION.md) and [sprite authoring](SPRITE-AUTHORING.md).


### v0.25: first native sprite artwork writer

The fixed shared bats/clouds page supports original indexed artwork and an optional palette through a checked, staged writer. Sky Invaders is playable; native full-page/palette and ordinary OAM pixel checks pass on final entry, pause/resume and room reentry. A separate composed save shortcut passes native save return, fresh continue and forced-HP death/fresh continue, with engine-selected VRAM/palette relocation observed. 234 tests pass. Graphics maturity rises from 4.4 to 5.3, total 30.0/100 (30%). General actors, frame/animation expansion and runtime resource allocation remain unfinished. See [sprite authoring](SPRITE-AUTHORING.md). REA skill/MCP successor requirements are documented in [REA workflow](REA-WORKFLOW.md).

The v0.53 original one-shot boot melody earns0.5 audio points for native original
PCM/voice/sequence playback and pitch/silent controls. Total35.6/100 rounds to36%.
Looping, other slots, imports and audio lifecycle remain incomplete; this is
partial credit, not full music-authoring certification.

V0.54 confined original WAV linkage earns0.2 audio points for native waveform,
pitch and sample-exhaustion controls. Current35.8/100 rounds to36%; broad audio
slots/lifecycle and arbitrary instruments remain incomplete.
