# Winged Skeleton cast/projectile trace (bounded observation)

A read-only native observation toward
[custom tear-style projectile abilities](CUSTOM-PROJECTILE-ABILITIES.md). It does
not grant projectile authoring, rendering, collision/damage or gameplay SFX
dispatch. All private evidence stays under `local/`; no ROM, screenshot or audio
ships in the source release.

## Static descriptor (pinned)

`aria/soul_projectiles.py:describe_winged_skeleton` reads `red_souls[1]` only:

| Field | Value |
|---|---|
| `code` | `0x08026009` (Thumb bit set; odd) |
| `use_animation` | 0 |
| `mana_cost` | 12 |
| `max_at_once` | 6 |
| `damage_multiplier` | 45 |
| `effects` | 1 |
| `var_a` | 0 |

Field widths do not establish call signatures or projectile semantics.
`tests/test_soul_projectiles.py` pins these values on the private exact host and
runs the remaining observer contracts synthetically without a ROM.

A bounded static search for the little-endian `code` pointer finds exactly one
hit: file offset `0x80E15A8`, the record itself (`0x080E1598 + 16`). There are no
other exact pointer-byte matches in the ROM. This is a byte-search fact, not a
consumer census: near-pointer arithmetic, copied immediates, or Thumb-relative
branches would not match.

## Native route (reused, controller-only)

`scripts/trace_soul_projectile.py` reuses the verified
`scripts/verify_soul_menu.py` opening and Start → Soul Set open/close so the
first red soul is owned (`0x0201331C == 1`) and equipped (ID 1) before casting:

1. Fresh core, 1000 frames, keys `[3, 8, 8, 8, 3, 3, 8]` with 100-frame settles.
2. Sixty A-press cycles with 90-frame settles (vanilla opening grant).
3. Assert ownership byte and equipped ID are both 1.
4. Open the soul menu (Start, confirm), screenshot it, close with B twice.
5. Assert gameplay state 4 / substate 1 / player state 0.

One Up+B cast (`[4, 0]` one frame, six settle frames) spends exactly 12 MP
(80 → 68), HP unchanged, ownership/equipped unchanged. World position at cast is
approximately (168, 703) in the vanilla opening room.

## Actor-window observation (single run, 2026-10-12)

Window: 224 slots at `0x020004E4`, stride `0x84`, 4-byte code at each slot base
(established by `scripts/scan_soul_spawn.py`). Baseline snapshot precedes the
cast; post-cast sampling runs every 2 frames for 120 frames; a further 30 idle
frames form a calm-phase negative.

| Fact | Value |
|---|---|
| Baseline codes | `0x801B0D9@[0]`, `0x804306D@[22]`, `0x805B511@[27]`, `0x805B749@[28,29]`, `0x804F771@[31,32,33]` |
| Novel at first post-cast sample (frame +7) | `0x8026009` at slot 2, `0x8025F71` at slot 3 |
| Persistence | both present in all 28 samples from frame +7 through +61, fixed slots |
| Despawn | both absent from frame +63 onward through +125 |
| Calm-phase novelty (30 idle frames) | none |

The soul record `code` itself (`0x08026009`) appears verbatim as a live actor
code in slot 2 for the cast window, alongside a nearby code (`0x08025F71`) in
slot 3. Both are cast-correlated in this run: absent before, present
immediately after, stable, then gone, with a clean idle negative. This names two
candidate projectile/effect actors and their slots/timing; it does not prove
rendering, OAM/palette ownership, position/velocity, damage, collision, facing,
cooldown, or which of the two codes is the damaging body versus an effect.

Screenshots (private): `local/soul-projectile/menu.png`, `baseline.png`,
`cast-plus7.png`, `cast-plus37.png`, `cast-plus127.png`. Report (private):
`local/soul-projectile-trace.json`.

## Audio windows (exploratory, not SFX proof)

A 60-frame idle capture precedes a 7-frame cast capture (both 65,536 Hz stereo
mixed output). The two windows differ (idle peak 2688 / RMS ~740; cast peak
5760 / RMS ~2314), but window lengths differ and the output mixes BGM with any
effect. This does not isolate a firing SFX, prove impact audio, or certify
BGM/SFX coexistence. Gameplay sound dispatch remains unimplemented.

## Twin determinism + position note (2026-10-12, second slice)

`scripts/trace_soul_projectile_twins.py` repeats the same opening, menu and
single Up+B cast on two fresh cores using `compare_cast_twins`:

- Menu and pre-cast baseline pixels are byte-identical across twins.
- Both runs spend exactly 12 MP with ownership/equipped unchanged.
- Both runs report the same novel actors, slots and timing: `0x08026009` at
  slot 2 and `0x08025F71` at slot 3, frames +7 through +61 (`identical: true`,
  no diffs). Spawn timing/slot placement is repeatable, not just observed once.
- Calibrated world-x (record word 8 low halfword / 256, v0.44) reads **0.0** in
  all 28 samples for both slots in both runs. The zombie-calibrated mapping
  does not transfer to these projectile records: their position lives in other
  words or another layout. No velocity, facing or speed model follows.

Private report: `local/soul-projectile-twins.json` with per-frame trajectories
and twin screenshots.

## 33-word record scan (2026-10-12, third slice)

`scripts/scan_soul_projectile_words.py` captures the full 33-word records of
slots 2–3 at nominal frames +7/+16/+25/+34/+43/+52/+61 after one cast, with a
still Soma (168,703) as reference. Slots are live through nominal +52 and
cleared (code word zero) by +61. Report: `local/soul-projectile-words.json`.

Varying words across the live window (rest are static IDs/pointers/flags):

| Slot | Varying indices | Notes |
|---|---|---|
| 2 | 2, 3, 10, 11, 16, 17, 19, 25 | prime movers: 16 (`0xb80000`→max `0xe80000`), 17 (`0x726000`→max `0x83a000`), 10 (`0x25900`→max `0x6d740`); 2 grows one high-halfword step (`0x1fe14`→`0x2fe14`); 11 low halfword grows under a stable `0x100` high half; 25 ends `0xff` |
| 3 | 16, 17 | 16 (`0xc7d3a0`→max `0xf676b0`), 17 (`0x74b900`→max `0x8a7740`) |

Words 16/17 grow in **both** projectile slots over the flight window and are
the prime position-accumulator candidates (fixed-point scale unproven). Static
identity fields include self-address word 5 (`0x20004E4`/`0x20005EC`), a
pointer-like word 1 (`0x803B9D1`, slot 2) and word 28 (`0x3050105`, slot 3);
word 8 stays 0x0. Despawn zeroes the code word while other words go stale
(idx25 reads `0xff` after clearing), so presence must be tested on word 0, not
any other word. Monotonicity is inferred from first/max only at 9-frame
sampling — dense per-frame series for words 16/17/10/2 to fit a velocity model
is the next step, then OAM/palette capture bound to those slots.

## Dense velocity track (2026-10-12, fourth slice)

`scripts/track_soul_projectile_velocity.py` samples words 16/17/10/2 on slots
2–3 every 2 frames for one cast until both code words clear. Report:
`local/soul-projectile-velocity.json`. Soma stays still the whole window.

27 live samples (~54 frames). Slot 2: words 16, 17, 10 and 2 all monotonic
increasing; slot 3: words 16 and 17 monotonic, words 10 and 2 flat. Motion is
steady but not constant — zero-delta steps occur, so sub-frame accumulation or
alternating updates are in play:

| Slot | Word | Displacement | Mean Δ / 2 frames | Max Δ |
|---|---|---|---|---|
| 2 | 16 | `0x400000` | ~161,319 | 524,288 |
| 2 | 17 | `0x130000` | ~47,892 | 270,336 |
| 2 | 10 | `0x60e50` | ~15,265 | 51,328 |
| 2 | 2 | `0x10000` | ~2,521 | 65,536 |
| 3 | 16 | `0x3e7ba0` | ~157,495 | 520,496 |
| 3 | 17 | `0x190e50` | ~63,156 | 317,392 |

Words 16/17 advance in **both** slots at similar rates and a similar ratio,
consistent with two actors flying the same direction — but fixed-point scale,
axes, screen mapping and the zero-step cause are unproven. `fit_word_series`
reports deltas/monotonic/constant facts only.Next: OAM/palette capture bound to slots 2–3, then a zombie-room hit attempt with HP/EXP attribution.

## OAM + palette capture (2026-10-12, fifth slice)

`scripts/capture_soul_projectile_oam.py` captures OAM (`0x07000000`, 1 KB) and
the OBJ palette (`0x05000200`, 512 B) at baseline, after a 30-frame no-cast
control, mid-flight (slots 2–3 live) and post-despawn. Report:
`local/soul-projectile-oam.json`. The control changes **zero** bytes, so Soma
idle drives nothing here and every mid-flight change is cast-caused:

- OAM entries 0–8 (9 sprites, 54 bytes) rewritten by the cast.
- OBJ palette 2 (bytes 64–95, all 16 colors) fully replaced.
- Nothing reverts post-despawn: mid and post SHAs match, so the engine leaves
  stale OAM/palette loaded with no observed unload. Candidates rest on the
  control, not on reverting.

Open: which of entries 0–8 belong to slot 2, slot 3, or a muzzle flash; tile
art provenance; palette-2 color contents.

## Zombie-room hit attempt (2026-10-13, sixth slice)

`scripts/attempt_soul_projectile_hit.py` walks vanilla Soma right into the
zombie room and casts Up+B facing right (MP-bounded, HP-guarded), recording
per-attempt MP/HP/EXP, projectile liveness, cast context
(state/substate/player/velocities), Soma world-x and actor codes. Report:
`local/soul-projectile-hit.json`. Reproduced identically across three runs:

| Attempt | Soma x | MP spent | Projectile live | EXP Δ | Notes |
|---|---|---|---|---|
| 0 | 6 | 0 | no | 0 | fizzle; context 4/1/0 |
| 1 | 30 | 0 | no | 0 | fizzle; context 4/1/0, zero velocity |
| 2 | 35 | 12 | yes | +1 | live cast; burst codes `0x807b311`/`0x807b3c9` already present pre-cast |

Findings and open questions:

- **Cast fizzle:** the first two Up+B presses spend no MP and spawn nothing,
  under the same 4/1/0 context (and both zero and nonzero velocity) as the
  successful third cast. State/velocity gating does not explain it;
  attempt-order or proximity pattern only. Any soul binding must handle
  unreliable casting in this room.
- **+1 EXP kill, victim unidentified:** the live cast correlates with +1 EXP,
  but the vanilla zombie pays 7 EXP, so a zombie kill is **unproven**. The
  pre-cast burst-family codes plus a growing `0x807a9ed` count (1→2→3) as Soma
  advances suggest next attribution must map those codes (zombie parts, aggro,
  or a second 1-EXP entity) before claiming damage.
- Per-hit HP reactions below a kill remain uninstrumented; zombie HP has no
  established RAM address.

## Sword-kill control (2026-10-13, seventh slice)

`scripts/attribute_zombie_kill_codes.py` sword-kills the same zombie
(B-attack loops) and classifies codes with `classify_transition`. Report:
`local/zombie-kill-codes.json`. The sword kill lands at roll 10 and pays
**+1 EXP (0→1)** — exactly the hit attempt's payout. The edited-record 7-EXP
figure from `verify_enemies.py` does not apply to this vanilla room, so +1 is
now the zombie-consistent payout, not an anomaly.

- Kill remnants (`new_persistent`): `0x8042d4d`, `0x8042de9`, known burst
  `0x806e525`, known zombie-death `0x807b3e5`, **plus `0x807b311`/`0x807b3c9`** —
  the hit-attempt unknowns sit in the zombie kill-remnant class.
- `0x807a9ed` is a calm resident (likely the live zombie), not a victim:
  nothing vanishes in the 60-frame post window, matching the v0.44 remnant
  verdict pattern.
- During the hit attempt's live-projectile window no sword was swung and Soma
  contact deals no damage, so the projectile is the only damage source for the
  +1 kill — first kill-level attribution, still without per-hit HP proof.

Next: per-hit HP instrumentation (zombie HP address open), input-hold variants
for the fizzle, tile-art provenance, and equal-length isolated audio.

## Tile provenance (2026-10-13, ninth slice)

`scripts/capture_soul_projectile_tiles.py` casts in the opening room, decodes
OAM entries 0–8 live (`decode_oam_entry`, hardware format) and hashes the
referenced OBJ tiles plus palette-2 colors. Report:
`local/soul-projectile-tiles.json`. The 9 entries reference 6 distinct tile
contents (all 4bpp, 1-D mapping assumed):

| Entries | Tiles | Size | Palette | Position | Read |
|---|---|---|---|---|---|
| 0 | 668 | 32×32 | 2 | (212,113) | shares bytes with 912/920 |
| 1–2 | 912, 920 | 64×32 | 0 | (88,96/128) | same bytes as 668: one graphic region |
| 3–4 | 400, 272 | 16×8, 16×32 | 11 | (225,136/104) | second cluster near entry 0 |
| 5–6 | 150, 146 | 8×8, 32×8 | 10 | (114/82,136) | left cluster, plausibly Soma's cast pose |
| 7–8 | 0 | 8×8 | 0 | (480,0) | parked offscreen spares |

Palette 2 (all 16 colors, ending `0x7FFF`) is the cast-loaded palette from the
OAM slice. The reskin target set is now concrete: tiles 146/150/272/400/668
plus the 912–943 region and palette 2. Entry-to-actor binding (which cluster
is slot 2 vs slot 3 vs Soma) stays open. Next: per-hit HP, fizzle variants,
and isolated audio.

## Zombie HP hunt (2026-10-13, eighth slice, open)

`scripts/scan_enemy_hp.py` walks to the zombie room, lands isolated single
sword hits between full 224-record scans (`scan_decreases`), then tracks every
pairwise drop across the kill loop. Report: `local/enemy-hp-scan.json`. No HP
address is established yet; the scene is livelier than the method:

- Slot 29 word 4 toggles `0x10001`↔`0x10000` (drop 1) on hit rolls — a
  per-hit confirm/invulnerability flag, not HP (30 HP cannot toggle 1/0).
- Word 7 across many slots drops 26 per 26-frame roll: 1/frame countdown
  timers, unrelated to damage.
- Slots 34/35 words 4/23 drop in bursts (34/35/18): zombie approach steps,
  not damage.
- Suspects needing a dedicated re-test: slot 2 words 4 (−2 twice) and 23
  (−14 twice), both ending `0x0` — but they zeroed at roll 4 while the kill
  paid EXP at roll 9, so slot 2 is not cleanly the victim.
- Per-pair timing (new `kill_pair_leads`) separates hit-linked drops from
  timers/approach; absolute-value tracking of slot 2 from full HP to kill is
  the next run.

## Reusable API

`aria/soul_projectiles.py` (read-only; no writes, no grants):

| Function | Use |
|---|---|
| `describe_winged_skeleton(rom)` | static record descriptor |
| `snapshot_actor_window(read)` | nonzero slot → code snapshot from a paused core |
| `code_to_slots(snapshot)` | code-hex → slot list |
| `novel_codes(baseline, current)` | cast-correlated candidate codes |
| `count_pointer_occurrences(data, pointer)` | bounded static pointer-byte search |
| `compare_audio_windows(first, second)` | peak/RMS/equality facts, not attribution |
| `slot_base(slot)` / `read_slot_word(read, slot, index)` | validated actor-record addressing |
| `slot_world_x(read, slot)` | calibrated world-x (word 8 low halfword / 256; X only) |
| `compare_cast_twins(first, second)` | twin spawn timing/slot equality facts |
| `read_slot_record(read, slot)` | full 33-word actor record read |
| `diff_records(before, after)` | changed word indices with before/after/delta facts |
| `fit_word_series(values, step_frames)` | per-step deltas, monotonic/constant/motion facts |
| `diff_bytes(before, after)` | changed offsets collapsed into runs |
| `scan_decreases(before_records, after_records, min_drop, max_drop)` | bounded-drop (slot, word) leads |
| `classify_transition(before, during, after)` | victim/transient/new-persistent timing classes |
| `decode_oam_entry(block)` | hardware OAM decode: x/y, tile, palette, size, flags |

## Fizzle probe (2026-10-13, tenth slice)

`scripts/probe_cast_fizzle.py` walks deep into the zombie room (Soma x=36)
before the run's FIRST Up+B cast. Reports: `local/cast-fizzle-close1.json`,
`local/cast-fizzle-close2.json`. Both close-range first casts fizzle (0 MP)
under context 4/1/0 — disproving proximity as the gate (far first casts at
x≈6 fizzled 3/3; close first casts at x=36 fizzle 2/2).

The watch window still shows novel `0x807b311`/`0x807b3c9`: at close range the
zombie itself acts (attack/burst parts) while our cast fizzles — liveness
without MP spend must never be read as a projectile. Standing pattern: first
casts fizzle 5/5, third casts fire 3/3, leaving a time-vs-count question
(room-entry lockout curve vs arming count).

## Fizzle gate verdict (2026-10-13, eleventh slice)

`scripts/test_cast_fizzle_gate.py` fires 2 early + 2 quick late casts in one
run. Report: `local/cast-fizzle-gate.json`. Result — early: fizzle, fizzle;
late: **fizzle (0 MP, but liveness true), then FIRE (12 MP)**. Verdict:
**count-gate**: the engine arms the soul over attempts, not room time. Note
the late fizzle shows liveness without spend (zombie activity again), so the
gate must be read from MP spend, never liveness. Soul bindings must budget at
least ~3 presses per real cast in this room.

## Slot-2 absolute track (2026-10-13, twelfth slice, negative)

`scripts/track_slot2_hp.py` snapshots slot 2 after every sword roll to the
kill. Report: `local/slot2-hp-track.json`. Result: slot 2 is **not** the
zombie — it holds only transient `0x80221CD` slash flashes (7 of 31 samples)
and its words track the slash effect (16/17 rise, 26/27/28 pointers), never a
monotonic HP fall. No word falls monotonically to zero at the kill roll (30,
+1 EXP). Soma takes 7-HP contact ticks from roll 9 (zombie damage: 7), which
independently confirms a live zombie elsewhere in the window.

Lesson: slot indices recycle per effect; victim identity must come from the
kill-attribution code set (calm `0x807A9ED` → remnants), not a guessed slot
number.

## Zombie-holder track (2026-10-13, thirteenth slice, narrowed)

`scripts/track_zombie_hp.py` snapshots the `0x807A9ED` holder slots (start:
slot 30) across all sword rolls to the kill. Report:
`local/zombie-hp-track.json`. No monotonic HP fall in words 4–15: slot 30 is
static (word 6 only 0→1→2), so the zombie's HP does not live in the
low-word window there. Word-7 countdowns (1/frame) dominate the late holders
32/33/34 and grow with approach, not damage. Kill at roll 31 (+1 EXP).

Narrowed next: slot 30 words 16–31 (position/state half) plus a two-hit
sword-vs-soul damage comparison on the same holder, rather than another
full-window sweep.

## Slot-30 high words (2026-10-13, fourteenth slice, negative)

`scripts/track_zombie_hp.py` now snapshots words 4–31 (prior
`local/zombie-hp-track-words4-15.json` preserved). Kill at roll 31 (+1 EXP).
No HP fall anywhere: slot-30 word 16 drifts `0x800000`→`0x6b0000` only from
roll 26 (approach motion, not damage); slot-33 word 16 falls `0x830000`→
`0x412d54` over rolls 3–15 then flatlines and despawns at roll 19, eleven
rolls before the kill — a dying/respawning actor's word, not the victim's HP.
Slot-34 word 28 flips once (`0x22030008`→`0x22010008`, pointer-ish). HP is not
a plain u32 word in this record layout, or it lives split across halfwords.
Next: halfword-split scan on slot 30, then a sword-vs-soul two-hit damage
comparison on the same holder.

## Halfword split (2026-10-13, fifteenth slice, hunt exhausted)

Pure-static analysis of the saved 31-roll series (`local/zombie-hp-track.json`,
no new native run needed): every halfword of slot-30 words 4–31 across all
rolls. Only two halfwords ever change — word-6 low (0→1→2 counter) and word-16
high (`0x80`→`0x6b`, non-monotonic, motion-correlated) — and **neither falls
monotonically**. HP is exhausted in this record: not a u32 word, not a
16-bit halfword, in words 4–31 of the holder. Remaining hypotheses: HP in
words 0–3 (unlikely — code/pointer territory), a shared enemy-HP table indexed
by spawn, or damage resolved without a persistent HP field. Next: sword-vs-soul
two-hit comparison (same holder, count hits-to-kill per weapon) — damage
numbers without the address.

## Sword-vs-soul damage comparison (2026-10-13, sixteenth slice)

`scripts/measure_soul_hits_to_kill.py` casts Up+B to kill-or-MP-out (HP
floor 100). Report: `local/soul-hits-to-kill.json`. Result: presses 0–1
fizzle (0 MP), press 2 fires (12 MP, live) — and the run ends killed (+1 EXP)
with Soma untouched (HP 320, no contact). **One live soul cast kills the
zombie; the sword needs 8–31 rolls** across runs. The soul out-damages the
sword per action by roughly an order of magnitude (consistent with record
`damage_multiplier` 45 and `max_at_once` 6 — possibly multi-hit per cast, not
proven). The count-gate repeats in a fourth context (2 fizzles then fire).
No sword was swung and no contact occurred, so the projectile is the only
damage source. Per-hit HP numbers stay open, but damage *ranking* no longer
needs the address.

## Input-hold variants (2026-10-13, seventeenth slice, press-gated)

`scripts/probe_cast_hold.py` fires the run's FIRST Up+B cast with the input
held 1, 5, or 15 frames (one fresh core per hold length, zombie room).
Report: `local/cast-hold-variants.json`. All three first casts fizzle
(0 MP, no liveness) — holding the input 15x longer does not arm the soul.
Verdict: the eleventh-slice count-gate counts **presses**, not held frames.
Bindings must budget presses, not hold time.

## Limits and next work

- Two twin casts in one room establish spawn timing/slot repeatability; broader
  determinism (other rooms, directions, MP states) is untested.
- Word-8 world-x reads 0.0 on the projectile slots; words 16/17 are the prime
  position candidates but their scale, axes and velocity model are unproven.
- OAM entries 0–8, OBJ palette 2 and the tile set are captured; actor-to-entry
  binding and tile replacement permission are not.
- One kill is attributed at EXP level; per-hit HP, terrain collision and
  `max_at_once`/cooldown proof are not.
- No pause/room-transition/death/save/continue lifecycle for the projectile.
- No SFX isolation, voice/sample ownership, or impact-audio binding.
- No new manifest writer, RAM claim, or native code permission follows from this
  trace; the Ability SDK still has no projectile/SFX API.

## Equal-length audio with BGM-phase control (2026-10-13, eighteenth slice)

`scripts/capture_soul_audio_equal.py` captures two consecutive 60-frame idle
windows (A, B) then a verified Up+B cast with a 60-frame window (C), all in
the opening room at one position. Report: `local/soul-audio-equal.json`.
First run's strict rule (net spend == 12, 2x RMS) misfired: net spend reads
**11** because MP regenerates during the 60-frame window, and the cast
audio signature sits at 1.7–1.8x, not 2x. Corrected rule (spend within a
regen bound of 12; cast peak/RMS > 1.5x the idle-vs-idle control):

| Window | Peak | RMS |
|---|---|---|
| idle A | 2688 | 741 |
| idle B (phase control) | 3840 | 796 |
| cast C | 6720 | 1348 |

Idle-vs-idle is nearly flat while the cast window runs 1.75x peak / 1.7x RMS
above the control — a **cast-attributed audio difference**. Still mixed
BGM+SFX output with no mute control, so no isolated SFX, voice/sample
ownership, or impact-audio binding follows.

## MP regen rate (2026-10-13, nineteenth slice)

`scripts/measure_mp_regen.py` fires one verified opening-room cast (80→68,
spend exactly 12) then samples MP every 30 idle frames x11. Report:
`local/mp-regen.json`. Series climbs 68→73 monotonically (+5 over 330
frames): **~1 MP per 60 frames**. This confirms the eighteenth slice's
regen explanation for net-11 spend readings and sets the accounting rule:
add back ~frames/60 MP to gross spend before comparing against cost 12.
Rate is for a full-MP-start opening room; dependence on max MP is open.

Next useful slices: a bounded owned projectiles subsystem proposal with
explicit storage/lifecycle before any tear-art binding.
