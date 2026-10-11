# Enemy visual-binding discovery (v0.27–v0.28)

This guide records how the framework traces an ordinary enemy subtype to its
native graphics/palette/structure resources. The headline result is a
**corrected negative**: the single-referenced actor-table entry first
suspected to be the zombie's is disproven for every hallway zombie visual by
a deterministic magenta tracer. Its consumer is unknown, and no enemy reskin
writer exists. Do not describe the `unknown-actor` registration as zombie
artwork.

## What was established

- **Actor resource table with debug strings.** Around `0x08118680` the ROM
  holds 16-byte resource rows (four ROM pointers each) followed by ASCII
  names such as `./graph/dr_objhi`. Neighbor rows hold independently valid
  sprite structures (e.g. `0x082587BC` parses as 12 frames/5 animations; a
  row at `0x08118720` holds the Julius 75-frame/31-animation struct), so this
  region is an actor resource manifest. Field order is not uniform across
  rows and entry↔subtype indexing is unproven; row labels below are
  positional, not semantic.
- **Unidentified entry at `0x081186F0`.** Four pointers: a raw 4KB 4bpp
  graphics page (`0x082052F8`, header `00 04 10 08`, data `0x082052FC`),
  a 1-bank palette (`0x0820C550`, header `00 04 01 00`), a sprite structure
  (`0x0825847C`: 21 frames, 9 animations, zero diagnostics, 122 records
  roundtripped, all parts on graphics page 0), and a second raw 4KB page
  (`0x082062FC`, purpose unknown). Each address occurs exactly once in the
  ROM, inside this entry. The table is indexed, not pointer-linked: the entry
  address itself has zero occurrences, so no code-literal checks exist.
- **Native OAM tracking.** `scripts/probe_actor_binding.py` boots the
  hallway, confirms live Zombie actor slots (enemy index 1, update code
  `0x0807A9ED`; room (0,3) holds one type-1 entity, the spawner at
  (128,176)), and tracks tall OAM parts: the zombie moves on OBJ palette
  bank 0 (64x32 parts) while Soma stands static on bank 10. HP-zeroing every
  Zombie slot clears them (declared death fixture; no graphics/OAM/palette
  writes).
- **Registered read-only inspection.** `inspect-sprite unknown-actor` and
  `preview-sprite unknown-actor` expose the 21 frames with the entry
  palette (128x64 source, packed 8x8 tiles). The private contact sheet
  covers all 21 frames; the verifier suite covers 237 frames across four
  registrations.

## Magenta-tracer verdict (v0.28)

A whole-page magenta replacement of the entry page (plus palette) was built
privately and run against the original with **identical inputs**. The twin
runs are exactly deterministic (same HP, same positions, zero pixel
difference at baseline), so any differing pixel would name a consumer:

- 900 idle hallway frames: zero differing pixels.
- 1200 fighting frames walking to and past the spawner (Soma HP 320→292):
  zero differing pixels.
- 120 post-kill frames after HP-zeroing all Zombie slots: zero magenta
  pixels rendered.
- Consumer sweep walking right through `0x0850F15C` into `0x0850F294`:
  zero magenta pixels; Soma stalls at a wall (px 120), so rooms past the
  second door need door-aware navigation, not blind walking.

The entry page is never rendered in any observed hallway scene: not
walkers, not the spawner mound, not spawn effects, not deaths. Earlier
VRAM disappearance observations (9 page-matching tiles vanishing on kill)
are attributed to generic tile-byte collisions, not proof of use — the
21-frame struct covers 127 of 128 page tiles, so any page tile trivially
"matches" it. The walker's true source is established in the next
section; the v0.28 claim that it uses "not any of five LZ table pages"
was a comparison-method error (see correction).

## Walker art source identified (v0.29; render proof withdrawn in v0.30)

A read-only live capture (`scripts/dump_walker_source.py`, no RAM writes:
boots the hallway, records the moving bank-0 tall actor (later shown to
track Soma, not the walker), saves VRAM/OAM/
OBJ palettes to `local/zombie-live/`) plus static analysis establishes the
full chain from a new actor table to live pixels. Two independent live
confirmations anchor it: the OBJ palette and the art tiles both match the
ROM sources byte-for-byte.

- **Actor table at `0x080E13C0`: 32 rows × 12 bytes**
  `(palette_ptr, graphics_ptr, struct_ptr)`. Palettes stride `0x24`
  (4-byte header + 32 bytes) with one gap (rows 9→10 stride `0x44`);
  graphics pointers ascend through `0x08230xxx`–`0x08235xxx`; struct
  pointers ascend through `0x081CCxxx`–`0x081DBxxx` (row 31 ends at
  `0x0825EB14`). No code holds the table base as a literal, so the
  loader computes `base + row * 12`; the subtype→row index formula is
  not yet established (hallway Zombie subtype 1 sits in row 8).
- **Walker row 8 at `0x080E1420`**: palette `0x0820B164` (header
  `00 04 01 00`, one 16-color bank), graphics struct `0x0823199C`, third
  field `0x081D08E8`. The live OBJ bank-0 palette (32 bytes captured
  while the walker moves) equals the ROM palette at `0x0820B168`
exactly. That palette occurs twice in ROM: headered here and unheadered
  inside a palette array at `0x082097D8` — sharing evidence any writer
  must enumerate.
- **Graphics struct `(a, b, parts_ptr, frames_ptr, anim_ptr)`** (16 bytes;
  all 32 rows share the shape). Walker: `a=12, b=2`, frames
  `0x0823195C`, parts header `0x0823189C` (192 bytes = 12 entries ×
  16 bytes `(0, flags, top_ptr, bottom_ptr)`; entry 0 is blank; several
  top-part lists are shared with the neighboring row's frame area),
  animation entry `0x086398FC` (one 4-byte slot in a consecutive
  per-row array `0x086398F8…`; each slot points back at its row's
  frames). The 12 entries match the walker's 12-pose cycle; live OAM
  shows two stacked 64×32 parts (tiles 912, 920) per frame.
- **Art page: LZ stream at `0x08635990`** (Aria LZ10, decodes to
  `0x2004` bytes = 4-byte inner header + 8 KB / 256 tiles). Nearly every
  nonzero live walker tile is found in the decoded page (bottom-half
  tiles at page offsets `0x1600`–`0x1BA0`; both walk frames share them).
  Referenced once, from the wrapper table at `0x082052DC` (flag
  `0x10100401` sibling entries hold the other LZ pages). Byte-identical
  page copies exist at `0x086457A0` (ref `0x0826C844`) and `0x0864CFBC`
  (ref `0x08277990`) — per-area duplicates a writer must not disturb.
- **Top-half tiles stream raw**: the remaining live tiles (frame 0
  tiles 11–12, frame 1 tiles 3–4/27–28) match ROM bytes at `0x08166D18`
  (`+0x20` spacing) with further copies at `+0x1000`-separated mirrors
  (`0x08166718`, `0x0816718`-family). No code references these
  addresses literally, so the loader copies them via computed addresses.
- **Full-ROM negatives**: no LZ10 stream in ROM contains four or more
  nonzero walker tiles together except the three page copies above (all
  4,326 LZ10 candidates decompressed and checked); the bottom-half
  tiles match no raw, byte-swapped, nibble-swapped, reversed, or
  even-byte (8bpp) pattern anywhere in ROM.
- **Correction of v0.28**: the art page `0x08635990` was already on the
  five-page LZ candidate list, but the v0.28 check compared page
  *residency* instead of tile *content*, and compared against blank
  OAM base tiles (live bases 912/920 are zero padding; real art sits at
  nonzero offsets within each 32-tile part). Content search with nonzero
  tiles names the page unambiguously.
- **Still open**: subtype→row index formula; loader function identity
  (Zombie create/update hold no graphics literals — binding arrives via
  a callee reading the tables); frame-list/OAM record field semantics;
  full consumer enumeration of the shared page (sibling tiles, shared
  top-part lists, palette copy). Per the rule below, the writer waits
  for a tracer-named consumer set.

## Second unidentified struct (v0.29 correction)

A premature `zombie` registration (struct `0x08217464`, 35 frames/10
animations; page `0x081CBF84`; palette `0x0820A608`) claimed the hallway
walker on static code-pool evidence alone. That claim is withdrawn for
cause, and the writer entry has been removed from `aria/sprite_assets.py`
(`background-bats` is again the only production resource):

- The v0.28 magenta twin-run disproves hallway walker/mound/death use of
  page `0x081CBF84` (zero differing pixels across idle/fight/kill/sweep).
- The v0.29 live capture disproves it a second way: the walker's real
  palette is `0x0820B168`, not `0x0820A60C`, and its art is page
  `0x08635990` plus raw tiles at `0x08166D18`-family.
- Function-owner analysis (Thumb PUSH-prologue delimiting, not ±windows)
  shows the pools belong to Arachne create (enemy 23, function
  `0x080799FC`: wrapper `0x081CBF84` plus struct `0x08217464`) and two
  non-DNA helper functions (`0x0807A848`, `0x0807A970`: wrapper plus
  palette `0x0820A608`), never to Zombie create/update — whose own pools
  hold zero graphics literals.

The registration survives under the neutral name `unknown-actor-2`
(35 frames/10 animations render statically; 272 registered frames total).
The Arachne-create pool pair (wrapper + struct in one function) is a
concrete static hypothesis for a future Arachne-room tracer or OAM match,
not a binding: no live consumer is proven. Re-register a writer only with
a tracer-named consumer set and fully enumerated sharing evidence.

## Walker twin-run negative and attribution correction (v0.30)

`scripts/trace_sprite_consumers.py` (private; builds under `local/`, no
production writer entry) repoints **all three** page copies at once
(slots `0x082052DC`, `0x0826C844`, `0x08277990` → one rebuilt solid
index-1 stream, 5 ledger entries) plus palette index 1 → magenta in the
`0x0820B168` instance. Twin runs are exactly deterministic (original vs
original: zero diffs), yet original vs diagnostic also shows **zero
differing pixels in every scene**: idle, walk-right, fighting with enemy
contact (Soma HP 320→299), and post-kill. Zero magenta-ish pixels render
anywhere. The diagnostic art demonstrably reaches VRAM (128 solid tiles
read back), so the page is loaded but never sampled by anything visible
in these hallway scenes. Per the rule below, **no walker writer ships**.

Two attribution corrections follow from the same investigation:

- **Bank-0 tall entries track the player, not the walker.** Paired
  EWRAM/OAM samples show Soma world-x minus OAM-x pinned at 32 (world
  36→114→120 vs OAM 4→82→88) with a fixed camera, and the entries
  persist across a room transition (`0x0850F15C` → `0x0850F294`, same
  tiles 912/920) that no hallway walker can follow. The v0.27/v0.29
  "moving bank-0 = walker" reading was inverted: bank 0 follows Soma,
  while the walker waits (static) at its spawner. The v0.29 palette
  capture (`0x0820B168` byte-match) therefore matched a Soma-adjacent
  palette instance, not proof of walker use — and the game demonstrably
  loads the live bank-0 palette from the *other* instance (the
  `0x082097D8` copy; the repointed instance's magenta never appears in
  live `0x05000202`).
- **OAM reads via emulator memory maps are untrusted for render
  attribution.** A full manual render of OAM 4/5 (64×32 parts, live
  tiles, live bank-0 palette) matches 0 of 2320 expected opaque snapshot
  pixels; a direct VRAM scribble through the map pointer missed its
  target bank (descriptor starts at `0x06000000`, so tile N needs offset
  `0x10000+N*32`, a real bug found in the throwaway probe, not the
  framework). Snapshots, EWRAM and VRAM-content reads remain trusted;
  OAM-bank tracking does not establish who renders what. The kill
  fixture still clears live Zombie slots (EWRAM-verified), but bank-0
  tall entries survive it via respawns, so they never associated the
  deaths either.

Net status of the v0.29 chain: **content identity stands** (page bytes =
actor art bytes found in VRAM; palette byte-match; 12B table grouping;
full-ROM LZ/raw/transform negatives), but the **rendered-consumer proof
is withdrawn** — "binding PROVEN" is corrected to "art source
identified, consumer unproven". The page may be player art, a shared
bank, or preloaded-but-unsampled art in these scenes. Next: a
snapshot-anchored attribution path with no OAM-map dependence (e.g.
kill-footprint or spawn-event diffs), other rooms/actors, and a direct
test of the Soma-art hypothesis.

## Snapshot-anchored attribution library and Soma-art negative (v0.31)

`aria/sprite_attribution.py` promotes the v0.30 twin-run diff into a
reusable headless API with synthetic tests (`tests/test_sprite_attribution.py`):
`diff_framebuffers`, `heat_cells` and `diff_scenes` over 240x160 RGB
snapshots on an 8px grid. No OAM, tile or palette-bank reads are used,
so the v0.30 OAM-map warning does not apply. `scripts/trace_sprite_consumers.py`
now delegates to this library (identical report shape).

Snapshot-anchored reading of the existing `local/tracer-walker.json`
(idle 30, walk-right 60, fight 60, kill 12 frames; control deterministic):
the kill scene runs after HP-zeroing every observed Zombie slot, so the
walker is dead while Soma remains on screen, yet original vs diagnostic
still shows zero differing frames and zero heat cells. Page `0x08635990`
is therefore not Soma art in these hallway scenes either — the Soma-art
hypothesis fails alongside the walker hypothesis for this page here.
Spawn-event/kill-footprint diffs stay available through the same library
for other rooms/actors; no writer ships.

## Spawn-anchored twin negative (v0.32)

`scripts/attribute_spawn_events.py` (private; builds under `local/`, no
production writer entry) implements a kill-then-respawn protocol with no
OAM-map dependence: HP-zero every observed Zombie slot, wait for the
first EWRAM-observed live-slot reappearance, and capture snapshot
windows before/after the spawn frame on the original and the magenta
diagnostic (all three page copies plus palette, same build as v0.30).
Result: spawn frame 8 in all three runs (control A/B plus diagnostic),
world-x 35 throughout, control pair exactly deterministic, and
original-vs-diagnostic shows zero differing frames in both the spawn-pre
(3 frames: post-kill Soma-only baseline) and spawn-post (20 frames over
60 native frames covering the respawn) windows. The page is not rendered
at the hallway spawn moment either — the third snapshot-anchored
negative after walker-presence (v0.30) and Soma-presence (v0.31). The
pre window is thin because respawn is fast (8 frames); the post window
is the material one. Other rooms/actors remain unproven; no writer ships.

## Reusable method: deterministic twin-run tracer

1. Build a private high-visibility replacement (solid index-1 art plus a
   clashing palette) for the candidate page with `install_sprite_assets`.
2. Run identical input scripts on the original and the build; assert
   baseline determinism (positions, HP, zero diff without the trigger).
3. Diff framebuffers per room/scene with `aria/sprite_attribution.py`;
   heat-map differing 8px cells. Only rendered consumers can differ.

## Extension rules

Register a new writer resource only with a tracer-named consumer set plus
fully enumerated sharing evidence and palette-bank ownership. The
v0.30 hallway twin-run on page `0x08635990` (all three copy slots plus
one palette instance) named **no** rendered consumer, so no walker
writer exists; the Aria LZ rebuild path in `read_aria`/`rebuild_aria`
and the raw in-place path (synthetically tested via an injected registry
entry in `tests/test_sprite_assets.py`) stay ready. `background-bats`
remains the only production resource. v0.31 added the snapshot-anchored
library and disproved hallway Soma-art for page `0x08635990`; v0.32
disproves hallway spawn-moment rendering too, so the next candidate work
is other rooms/actors. Player streaming, new animations and general OBJ
allocation stay separate.
