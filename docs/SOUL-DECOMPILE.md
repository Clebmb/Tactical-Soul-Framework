# Soul actor decompilation (first decompiler evidence, 2026-10-13)

First native code evidence for the soul system: the Winged Skeleton projectile
actor, its companion, the shared child spawner, and the global SFX dispatcher
with the soul's spawn sound ID. Private raw output stays under `local/`; no
ROM bytes ship here.

## Provenance

- Headless Ghidra (`C:\Ghidra`, GBA Loader, base `0x08000000`, ARMv4T LE),
  throwaway project `TSFHeadless3`, auto-analysis plus postScript
  `local/GhidraDecompileSouls.java` (disassemble in Thumb mode, create
  function, decompile, write text). ROM read-only; project deleted after.
- Target ROM SHA-256 `910f88d3…36430a5` (exact host, verified in-script).
- Raw output: `local/ghidra-soul-decompile.txt` (204 lines, two functions, no
  failures). Follow-up xrefs/dispatcher decompiles came from the live
  GhidraMCP bridge against the operator's GUI session with the same ROM.

## FUN_08026008 — soul projectile actor (slot 2)

Thumb `push {r4-r7,lr}` prologue (`f0 b5`). Signature `(actor_record*)`.
State machine on the byte at record+10:

| State | Behavior (decompiled) |
|---|---|
| 0 (spawn) | wires update pointer at +4, allocates the companion through `FUN_08023530` with entry `LAB_08025f70`, inits angle/accel words, **plays sound `0xe4` via `FUN_080d7910`**, advances to state 1 |
| 1 (fly) | integrates angle at +0x2c, trig through `FUN_080009e4`, writes velocity words +0x24/+0x28 (`<<4` fixed point), wall/actor probe via `FUN_08001a00`/`FUN_08001f3c`; on contact sets state 2 with counter +0xd = `0x20` |
| 2 (burst) | sets flag +0xf = 1, decrements +0xd to zero, then state 3 |
| 3 (cleanup) | unregisters via `FUN_0803e6bc`, zeroes slots, despawns via `FUN_08000e14` |

Tail dispatch is an unrecovered jumptable (actor engine is indirect — matches
zero direct xrefs to the spawn path in the GUI session).

## Record layout map (offsets → 33-word indices)

| Offset | Word(s) | Role (decompiled) | Prior black-box observation |
|---|---|---|---|
| +0x24/+0x28 | 9, 10 | velocity X/Y (`<<4`) | word-10 mover confirmed |
| +0x40/+0x44 | 16, 17 | position X/Y | prime candidates confirmed |
| +0x42/+0x46 | 16/17 halves | position sub-parts | — |
| +0x2c/+0x2e | 11 | angle / angle-step | low-halfword growth |
| +0x10 | 4 (byte 2) | state byte | — |
| +0x0d | 3 (byte 1) | countdown (spawn 10 / hit `0x20`) | — |
| +0x0f | 3 (byte 3) | burst flag | — |
| +0x14 | 5 | parent-actor pointer | pointer-like word 1/5 |
| +0x1a | 6 (high) | short index | word-6 counter |
| +0x48/+0x4c/+0x54 | 18, 19, 21 | accel/limit constants | word-19 mover (`0x726000`→) |
| +0x58/+0x59 | 22 | facing/flag bytes | — |
| +0x5c | 23 (low byte) | pose `0xd` | word-23 drops |
| +0x65 | 25 (byte 1) | cleared at spawn | ends `0xff` |
| +0x72 | 28 (byte 2) | flag OR 4 | pointer-like word-28 writes |

HP is nowhere in this layout: the update never reads a damage accumulator,
consistent with the exhausted word/halfword hunt. Damage likely resolves in
the callee helpers (`FUN_0806d128` family) or a shared table — still open.

## FUN_08025f70 — companion actor (slot 3)

Follower: `pos = parent_pos + parent_vel` per axis
(`+0x40 = parent+0x40 + parent+0x24`). One headless note: the TMode context
set reported a conflict here, but disassembly/decompilation still succeeded
with a clean prologue (`70 b5`); treat instruction boundaries as verified,
register allocation as usual decompiler approximation.

## FUN_080256ac — shared child spawner (bridge decompile)

Generic parent→child allocator used by the soul's state 0: table lookup by
parent halfword +0x1e, `FUN_08023530` allocation, vtable/position/facing
wiring, spawn counter +0xd = 10. Zero direct callers in the GUI session
(indirect actor dispatch, as expected).

## FUN_080d7910 — global SFX dispatcher, soul spawn sound `0xe4`

ID-masked dispatch (`param & 0xffff` vs table) with **652 caller sites**
across the ROM (bridge xrefs, first 50 reviewed — gameplay, UI, and actor
callers). The soul actor's spawn call passes **`0xe4`**: the Winged Skeleton
cast's spawn SFX ID. Sample/voice mapping behind the ID and any impact sound
remain open (m4a layer), but the call convention is one int ID — the same
dispatcher a custom soul would use.

## SFX `0xe4` static mapping (20th slice, `scripts/trace_sfx_0e4.py`)

Full static chain, exit 0, report `local/sfx-0e4.json`:

| Step | Value |
|---|---|
| Dispatcher threshold `DAT_080d7928` | `0x3FF`; `0xe4` takes `FUN_080d73b8` |
| SFX table / entry | base `0x0827CD38`; entry `0xe4` → song `0x08399BEC`, channel 2 |
| Song | 1 track; single note: key 60 (C4), velocity 127, voice 92, gate 23 |
| Voice 92 | type 8 sampled-no-resample, key 60, sample `0x083AE488`, ADSR 255/0/255/0 |
| Sample | C4 rate 10,512 Hz (exact standard rate), duration 0.30 s |

The soul's spawn sound is one C4 blip of a no-resample sampled voice. The
mapping is exact statically; native-play proof stays open (impact audio was
never observed — the cast makes no contact sound in the traces so far).

## Per-hit damage pinned at 22, single-frame (40th slice, `scripts/pin_damage_high_hp.py`)

Report: `local/damage-pin.json` (exit 0, ROM unchanged; RAM-only harness
writes in a throwaway session).

- Method: zombie-room route, every 18-HP zombie slot RAM-boosted to 200
  (boost stable across runs — DNA copy is spawn-time only), one verified
  cast, per-frame all-slot `+0x34` poll. Four native runs: single-boost
  missed (drop 0, kill elsewhere), boost-all missed (late spawner took
  it 18→0), continuous re-boost caught it twice.
- Result: **one cast deals exactly 22 damage in a single frame**
  (200→178, one change-point at frame 17, n=2, EXP 0 non-lethal both
  times). This supersedes the 26th slice's clamped 18-drop.
- Consequence: descriptor u16[0]=27 is **not** raw damage (or is mediated
  by an unknown −5 step). Zombie DNA DEF=1 does not explain the gap
  (27−1=26≠22). The soul record's multiplier 45 vs 22 (45/2=22.5 floored?)
  is an untested hypothesis — resolving the formula needs a second enemy
  type (different DEF) or the match-pass dataflow.
- Framework fact to keep: soul per-hit damage vs zombie = **22**, applied
  in one frame, one cast kills 18-HP zombies with 4 overkill.

## Second-victim census + skeleton miss (42nd slice, `scripts/census_damage_candidates.py`, `scripts/pin_damage_skeleton.py`)

Reports: `local/damage-candidates.json`, `local/damage-pin-skeleton.json`
(both exit 0, original ROM unchanged; workshop build regenerated under
`build/` as a throwaway artifact).

- Static census confirms the pair: zombie DNA[1] HP 18 / DEF 1
  (`0x0807a9ed`), skeleton DNA[2] HP 20 / DEF 0 (`0x080c34f9`) — the
  cleanest DEF contrast reachable early. Fixed decision table before
  running: skeleton 22 → DEF plays no role (`45//2` or `27−5` survive);
  skeleton 23 → DEF subtracts (`23−DEF` family survives); anything else
  falsifies all four hypotheses.
- Native probe reuses the proven workshop-shortcut route (zombie room
  `0x0850F15C` → skeleton room `0x0850F32C` per `verify_enemies.py`) on
  the enemy-workshop build, where skeleton DEF is unchanged (0) and HP
  is RAM-boosted 12→200 (so the workshop HP 12 edit is moot). Route,
  boost stability, and cast firing all proven: skeleton slot 29 boosted
  stable, one verified cast, ROM unchanged.
- Result is an honest miss, twice deterministically: the boosted
  skeleton (slot 29) takes no damage while slot 31 (`0x80c43c5`, HP 12
  native) falls 12→0 with zero EXP. Same slots, same change-points both
  runs — the projectile never meets the boosted victim (positioning or
  timing, same class of miss as the zombie pin's first two runs, which
  also missed before catching twice).
- Net: formula still open; the skeleton route + boost + cast harness is
  proven and ready. Next: vary cast timing/position or run further
  replicates until a boosted skeleton is caught, as the zombie pin
  required four runs.

## Advance + multi-cast variant misses; non-enemy code eliminated (43rd slice)

Report: `local/damage-pin-skeleton.json` (exit 0, original unchanged).

- `scripts/pin_damage_skeleton.py` now advances to world X>=400 before
  boosting (reached X402) and fires up to 3 verified casts with
  reposition walks: 3 casts, 5 presses, stable boosts on skeleton slots
  29/37/43 — still zero skeleton-coded falls, zero EXP.
- The recurring fall code `0x80c43c5` (HP-like 12/105 values) matches
  **no** DNA create/update pointer in any of the 113 rows (checked both
  offsets statically): its `+0x34` is not HP, so every skeleton-room
  "fall" on that code is actor noise, not damage. Only skeleton-coded
  (`0x080c34f9`) falls can count, and there are none in three runs.
- Sharper next step than more retries: isolate one variable in the room
  that already works — build a mod raising zombie DEF (1→10, an
  editable DNA field per ENEMIES.md), RAM-boost HP to 200 on the same
  zombie route/harness, and measure. Damage stays 22 → DEF ignored
  (`45//2` family); damage falls → DEF subtracts. No new route or
  positioning problem.

## DEF subtracts: 17 at DEF 10, formula `(45−DEF)//2` (44th slice, `scripts/pin_damage_def_raised.py`)

Report: `local/damage-pin-def10.json` (exit 0, original unchanged;
throwaway mod build under `build/mods/def-probe/`, manifest alongside).

- Isolation: mod DNA[1] verified HP 18 / ATK 9 / **DEF 10** / EXP 1 —
  only DEF edited. Same zombie route/harness, 18→200 boost, one
  verified cast, per-frame all-slot poll. Fixed a launch crash mid-slice
  (`apply_manifest` takes a manifest path, not a dict — fixed at the
  cause, manifest written next to the build).
- Result, n=2: **200→183 single-frame at frame 17, both runs** (slot 32,
  `0x807a9ed`, EXP 0 non-lethal). Run 2 logs the victim's live DEF:
  **def_at_cast 10**. (Run 1 read DEF off the spawner slot, which holds
  0 per ENEMIES.md's spawner caveat — documented, not hidden; the
  replicate closes it.)
- Formula: DEF 1→22, DEF 10→17 fits **damage = (45−DEF)//2** with 45 the
  soul-record multiplier (equivalently `22 − DEF//2`). Descriptor 27 is
  out as raw damage (27−1=26≠22); its role, if any, is upstream of this
  step. Predicts 22 vs DEF-0 skeletons — the pin that kept missing on
  positioning. Two points only: confirm on a third DEF before
  generalizing.

## Third point confirms: 20 at DEF 5 (45th slice, parametrized `scripts/pin_damage_def_raised.py`)

Report: `local/damage-pin-def5.json` (exit 0, original unchanged).

- The probe now takes DEF as argv (`5`) with the prediction baked in
  (`predicted` field): (45−5)//2 = **20**. Result: **200→180
  single-frame at frame 17**, slot 32, victim **def_at_cast 5**, EXP 0.
- Formula is now three-for-three on distinct DEFs (1→22 n=2, 10→17 n=2,
  5→20 n=1), all single-frame, all victim-DEF logged live on the later
  runs. `damage_vs_defense` stays labeled empirical, but the skeleton
  22-prediction is now the sharpest open test: same number as the zombie
  baseline, so a skeleton catch needs no new math — only positioning.

## Mirror miss makes four; position-tracking diagnosed next (46th slice)

Report: `local/damage-pin-skeleton.json` (`mode: mirror`, exit 0).

- `scripts/pin_damage_skeleton.py` takes argv `mirror` (zombie-exact
  timing: walk 70, idle 30, no combat advance) vs default `advance`.
  Mirror run: cast from X115, 3 verified casts, stable boost on slot 29
  — still zero skeleton falls; only a 1-point noise tick on non-enemy
  `0x80c3bd9`. Four misses across three strategies (entry, advance +
  combat, mirror) with the same signature: the projectile never meets a
  boosted skeleton.
- Blind retries stop here. The sharp next step is seeing the miss, not
  repeating it: track record words 16/17 (position, per the record map)
  of the live soul slot vs the boosted skeleton slot frame-by-frame
  through the flight window and measure the passing distance. That
  distinguishes wrong-lane (vertical miss) from wrong-range (despawn
  first) and prescribes the fix.

## The miss is seen: soul flies away from the skeleton (47th slice, `scripts/track_soul_vs_skeleton.py`)

Report: `local/soul-vs-skeleton.json` (exit 0, ROM untouched; no RAM
writes at all — pure observation).

- Method: mirror route, one verified cast (1 press), words 16/17 of soul
  slot 2 vs skeleton slot 29 every 2 frames x70, plus Soma world X/Y.
- Trajectory: at the first live sample the soul is already dx=+1.67M
  (raw units) right of the skeleton; dx grows ~262k/frame to +7.4M by
  frame 22 while |dy| shrinks 2.06M→0.34M. Frames 24–50 frozen
  (burst/despawn, stale slot), 56+ slot recycled. Soma stands at X115.
- Reading: the skeleton sits LEFT-behind Soma while the soul races
  RIGHT — wrong-direction, not wrong-lane or short-range. In the zombie
  room Soma walks into the pack and fires into it; here the arrival
  geometry leaves the victim behind the muzzle.
- Prescription (single variable): tap Left once to face left before the
  press-budget cast and re-poll. If the soul follows facing, it should
  fly into the skeleton and the 22-prediction finally gets its catch.

## Soul follows facing; tracked skeleton still escapes (48th slice)

Reports: `local/damage-pin-skeleton.json` (`face: True`), `local/soul-vs-skeleton.json` (face run) — both exit 0.

- `scripts/pin_damage_skeleton.py` takes `face` (Left tap + settle before
  the press budget; bare `face` implies mirror timing): 3 verified casts
  from X111, stable boost on slot 29 — still zero skeleton falls, zero
  EXP. Fifth miss.
- `scripts/track_soul_vs_skeleton.py face` confirms the mechanism but
  not the catch: first live sample now dx=−3.44M (soul LEFT of the
  skeleton — direction reversed, so **the soul follows Soma facing**),
  yet the gap widens to −4.75M by frame 6 and freezes (burst/despawn).
  Either the skeleton walks away during the window or the mirrored
  skeleton (slot 29, +0x65 mailbox zeroed by the boost loop?) never
  overlaps a leftward flight either.
- Honest status: direction control proven, catch still open. Tracker now
  logs a facing byte (`0x0200052E` reads 0→0, unconfirmed as facing — do
  not cite it as facing proof). Next: freeze the skeleton (track its
  words 16/17 velocity — if it walks, cast earlier/closer), or check
  whether per-frame boosting clears its hit mailbox; either way keep the
  zombie three-point formula untouched.
- Framework side: new `casts_to_kill_for(hp, def)` composes the damage
  model with ceiling division (skeleton 20/0 → 1 predicted cast), tested
  synthetically.

## SFX `0xe4` diagnostic render (21st slice, `scripts/render_sfx_0e4.py`)

Rendered the mapped voice (gate 23 ticks @ tempo 75, ADSR 255/0/255/0,
10,512 Hz → 32,768 Hz mono WAV). Exit 0; artifacts `local/sfx-0e4-render.wav`
(18,076 frames, 0.55 s with release tail vs 0.30 s static body) and
`local/sfx-0e4-render.json`. Peak 128 (full 8-bit scale), RMS 39.9 — an
audible-length blip, energetically consistent in order with the cast-window
excess (RMS 1,126 in 16-bit mixed units; scales differ — mixer gain, bit
depth, and BGM presence are unmodeled, so this is consistency, not a match).
No ear check performed; the WAV is private and never packaged.

## Render determinism + listening guide (31st slice, `scripts/analyze_sfx_render.py`)

Report: `local/sfx-0e4-listen.json` (exit 0, ROM unchanged).

- **Deterministic**: re-running `scripts/render_sfx_0e4.py` reproduces the
  WAV byte-identically (sha256 `0f6610f3…aa83e0`) — the render is a pure
  function of the ROM + scripts, so the operator hears exactly what was
  characterized.
- Spectral metrics (stdlib FFT): 0.55 s, peak ~1.0, RMS 0.31, crest 3.2,
  ~798 zero-crossings/s, onset at 0.0 s, −20 dB decay at 0.30 s (matches
  the 0.30 s static body), centroid ~2,045 Hz, brightest band 500–2,000 Hz
  (42% of energy). A transient burst, not a steady tone — SFX-plausible.
- Listening guide for the operator: play `local/sfx-0e4-render.wav`;
  expect a short percussive whoosh/pop; silence, a pure tone, or looping
  clicks falsify the mapping. The human ear check itself is still open.

## Damage-path round (22nd slice, bridge decompiles)

Attacker-side damage application is now mapped — and it contains **no HP
write**. Four helpers from the soul update, all via the live bridge:

| Function | Role (decompiled) |
|---|---|
| `FUN_0806d128` | on-screen cull check (camera bounds +0xf0/+0xa0); state 1 runs only when visible |
| `FUN_08001a00` / `FUN_08001f3c` | **tilemap collision probes** (metatile byte, slope/solidity bits); the state-1→2 burst is terrain contact, not enemy contact |
| `FUN_0803e058` | OAM affine-matrix writer (0x28-byte sprite slots, facing flips) |
| `FUN_0803b924` | **hitbox-slot allocator**: if byte at record+100 (word 25) is -1, claims a slot via `FUN_08039614`, stores the index, sets +0x5a bits |
| `FUN_08031ea4` | spawn-position setter (child = parent + facing-mirrored offset; soul passes +8/−26) |

Two black-box facts snap into place: word 25 reading `0xff` is -1 = hitbox
released at despawn, and `+0x65 = 0` at spawn is the allocator's reset. The
kill must resolve in the hitbox table + global match pass (`FUN_08039614`
allocator and its consumers) or the victim-side update — those are the next
targets, not the soul update.

## Hitbox system shape (23rd slice, bridge decompile + xrefs)

- `FUN_08039614` is a pooling allocator with dedup: it first walks a linked
  list of 0x14-stride entries for the same descriptor pointer, else pops a
  free slot (empty returns `0xff`). It stores the owner pointer and the
  descriptor pointer per slot and returns the slot index byte.
- `FUN_0803b924` (the registrar) has **396 caller sites**: every actor —
  projectiles and enemies alike — registers hitboxes/hurtboxes through this
  one path. The soul is an ordinary registrant.
- `FUN_08000fbc`, called right after registration, is the actor-slot
  allocator: `(record - base) / 0x84` via `FUN_080da988`, slot index to
  record+8 (word 2 low byte — matching the observed word-2 steps).
- The HP-subtracting match pass itself is still unidentified; the pool base
  (`*DAT_08039704`) and its readers are the next targets.

## Attacker lifecycle closed (24th slice, bridge decompile + xrefs)

- `FUN_08039614` has exactly one caller (the registrar): actors →
  `FUN_0803b924` → pool. Clean hierarchy, no hidden allocators.
- `FUN_0803e6bc(slotbits)` clears one bit in a 32-bit mask — sprite-slot
  release at state 3, not hitbox release.
- `FUN_08000e14` is the actor despawn: teardown helpers, a deferred-op
  queue write, and **record+100 (word 25) = `0xff`** — the hitbox-slot
  release marker. This closes the full attacker lifecycle: register →
  fly → terrain/enemy burst → sprite release → despawn with slot freed.
- Pool-base `DAT_08039704` has no other readers in the session: the match
  pass reaches the pool through an unresolved path (unmapped table or
  indirect call). Victim-side reaction code is the remaining door to HP.

## Victim-side chain + HP found (25th slice, bridge decompiles)

- `FUN_0807a9ec` is the zombie's own update (states 0 spawn / 1 walk /
  2 attack / 3 summon). Its hit hook: it snapshots byte +0x65, runs
  per-frame proc `FUN_0803f17c`, and on change calls `FUN_0806b1fc`.
  **+0x65 is the per-actor hit mailbox.**
- `FUN_0803f17c` dispatches on byte +0x5b; type 0 resolves the actor's
  hitbox slot (+100) to descriptor data and calls overlap routine
  `FUN_080da7a8`.
- `FUN_0806b1fc` reads the hit packet via +0x65 and dispatches on its
  type byte: types 1/2 queue 4-byte hit packets through `FUN_080428b4` /
  `FUN_08042848` (both guarded by flag +0x72 bit 0, indexed by +0x73);
  type 0 sets invuln bits.
- `FUN_0806ad24` is the HP gate: **victim HP is the short at record+0x34
  (word 13 high halfword)** — returns 0 (dead) when HP < 1, else drains
  the queued hits through `FUN_0806ae54` and returns 1 (alive).
- Why the record scans missed it: the u32/halfword hunts tracked the wrong
  holder slots at the wrong rolls; HP itself is an ordinary halfword that
  only falls on the true victim in the frames the queue drains.
- Complete chain: overlap → +0x65 mailbox → queued packet → `0806ae54`
  drain → HP(+0x34) falls → death path `FUN_080421ac`. Per-hit damage is
  now natively measurable: sample holder +0x34 across cast-separated hits.

## Per-hit damage measured natively (26th slice, `scripts/measure_soul_hit_damage.py`)

Press-budgeted zombie-room cast (6 presses: fizzles then fire, count-gate
again), projectile live, **exactly one slot's +0x34 falls: slot 32,
18 → 0 (drop 18), with +1 EXP kill**. Report: `local/soul-hit-damage.json`.
The +0x34 HP finding is now natively validated end to end: one live soul
cast deals 18 damage and kills the 18-HP zombie outright (consistent with
the 16th slice's one-cast kill vs 8–31 sword rolls). No other slot's +0x34
moves — victim identity comes from the fall, never the slot number.

## Projectile lifecycle (27th slice, `scripts/probe_projectile_lifecycle.py`)

Report: `local/projectile-lifecycle.json`.

- **Room transition clears**: east-door crossing with a live cast (252-frame
  walk, cast 45 frames before the door) — slot 2 is gone after the change;
  only room actors remain. A custom tear cannot ride across rooms without
  engine support.
- **Start-menu pause mid-flight unproven**: pressing Start 20 frames after
  a live cast left gameplay state at 1 (menu never opened), slots kept
  animating, and word 16 ran 0xdc0000 → 0x0 — the natural ~61-frame life
  completed, not a freeze. Whether Start is consumed differently during
  cast recovery or pause lives elsewhere is open; no freeze claim follows.
- Death mid-flight remains out of scope (needs HP manipulation).

## Hitbox descriptor read (28th slice, `scripts/read_hitbox_descriptor.py`)

Report: `local/hitbox-descriptor.json` (exit 0, ROM unchanged).

- Chain resolves from the exact image: `PTR_080260a0` -> struct
  `0x080e13bc`, words `[0x081cc0c4, 0x0820b044, 0x082308e8]`; word 2 is
  the descriptor the soul passes to `FUN_0803b924` as param_2.
- Descriptor at `0x082308e8` (32 bytes):
  `1b000700a006230850082308b8986308f8f8000000001010100000000f8f80000`,
  as u16 `[27, 7, 1696, 2083, 2128, 2083, 39096, 2147, 63736, 0, 0,
   4112, 16, 0, 63736, 0]`.

## HP-store site located statically (29th slice, `scripts/scan_hp_drain.py`)

Report: `local/hp-drain-scan.json` (exit 0, ROM unchanged).

- Exactly one `STRH [Rn, #0x34]` in ±0x400 of the drain/queue/gate
  functions: **`0x0806b06a` = `strh r0, [r1, #0x34]`** — the native HP
  store, in the function with prologue at `0x0806af98`.
- Its stanza is a table lookup, not a subtract: `ldrh r0, [r0, #0xc]`
  after a ×36 index build (`lsl #3`, `add`, `lsl #2`, `add r2`), then
  the store; a twin stanza ends in `strh r0, [r1, #0x2e]`. So the
  damage operand reaches HP through a looked-up halfword, and which
  descriptor field feeds the table index needs register dataflow.
- No `LDRH #0x34` exists near any of the three functions: HP is never
  loaded by immediate offset there (register-offset or another reader).
- Caution fixed in-script: Thumb `STRH`-imm is family `0x8000`,
  `LDRH`-imm is `0x8800` (an early run had them swapped and searched
  offset `0x6a`); the final run uses `0x8000|(0x1A<<6)` = `STRH #0x34`.
- Precise Ghidra follow-up (no GUI session needed to phrase): decompile
  the `0x0806af98` function, track r0 into the `0x0806b06a` store and
  name the table, the index byte, and the `+0xc` halfword's producer.

## Store table resolved, 27 absent (30th slice, `scripts/resolve_store_table.py`)

Report: `local/store-table.json` (exit 0, ROM unchanged).

- The stanza's index-base pool (`ldr r2, [pc, #0x4c]` at `0x0806b056`)
  is **`0x080e9644`: 36-byte records** (two pointers + params; `+0xc`
  halfword is a small int). First 64 `+0xc` values run 1–650
  (10, 18, 20, 20, 60, 42, 38, 25, 75, 25, 20, 95, …) — a damage-like
  by-kind table, but **27 appears zero times in all 64 entries**.
- Two more pool targets followed (`0x084f0b14` ×4, `0x08118d24` ×1,
  64 entries each): no 27 anywhere either (`0x084f0b14` reads as
  code-like junk under the x36/+0xc shape — not that table).
- Net: soul damage 27 does **not** flow through this table's `+0xc`
  halfword — a narrowing negative. The soul-kind hit either indexes
  past entry 63, uses the twin `+0x2e` stanza path, or reaches HP via
  the drain (`0806ae54`) operand directly. Next: Ghidra dataflow on
  `0x0806af98` (which index byte selects the soul kind) or the
  tougher-victim native pin.

## Twin-store census + spawn-init reframe (32nd slice, `scripts/scan_hp_drain.py`)

Report: `local/hp-drain-scan.json` (exit 0, ROM unchanged).

- Census: exactly one `STRH #0x2e` in ±0x400 of drain/queue/gate —
  `0x0806b07a`, the twin of the HP store — and **zero** `LDRH #0x2e`.
  The pair (table `+0xc` → record `+0x34`, table `+0xe` → record `+0x2e`)
  is written in exactly one place and read by immediate nowhere near.
- Record map says victim `+0x2e` (word 11 high) is angle-step and `+0x34`
  (word 13 high) is HP. One table row supplying **HP + launch angle**
  together reads like a **spawn-init write, not a damage subtract** —
  the `0x0806af98` function may initialize victims (HP/angle from the
  `0x080e9644` spawn-parameter rows) rather than drain them.
- Reframe hypothesis only: zombie measured HP 18 equals table index-1
  `+0xc` (18), but the zombie's kind-index byte is unproven, so no
  identity claim follows. Discriminating tests: zombie kind-index vs
  table (native/encounter data), or Ghidra dataflow into both stores.
  Either way the true HP-=damage subtract still lives elsewhere
  (drain `0806ae54` proper or a register-offset store).

## Spawn-copy confirmed via zombie DNA (33rd slice, `scripts/confirm_spawn_copy.py`)

Report: `local/spawn-copy.json` (exit 0, ROM unchanged).

- `docs/ENEMIES.md` names the mystery table: **enemy DNA, 113 × 36B at
  `0x080E9644`**, HP/MP/EXP at `+12/+14/+16`. The stanza's `+0xc`/`+0xe`
  reads are DNA HP/MP — not damage operands at all.
- Triple lock on the zombie: DNA row with update pointer `0x0807a9ed`
  (= `FUN_0807a9ec` Thumb) is **index 1 with HP 18 / MP 10 / EXP 1** —
  exactly the 26th slice's native victim (18 HP, +1 EXP kill).
- The `0x0806b06a`/`0x0806b07a` twin is therefore a **DNA→instance spawn
  copy** (HP/MP into `+0x34`/`+0x2e`), and the 30th slice's "27 absent"
  is explained: damage was never in that table. The HP-subtract site
  (drain `0806ae54` proper or register-offset store) is back to being
  the open target — with the misleading candidate eliminated.

## Queue-builder decode corroborates the decompiles (34th slice, `scripts/decode_queue_builder.py`)

Report: `local/queue-builder.json` (exit 0, ROM unchanged).

- Decoded `0x0806b000`–`0x0806b300` (384 ins, bl-pair + LDR-literal
  resolution). Call targets land **exactly** on the bridge-decompiled
  callees: `bl 0x80428b4` / `bl 0x8042848` (hit-packet queue helpers
  `FUN_080428b4`/`08042848`) and `bl 0x8001a00` (tilemap probe
  `FUN_08001a00`) — independent static corroboration of the 25th slice.
- Only **one** `+0x34` access in range (the spawn-copy store) and **zero**
  register-offset STRH: the HP subtract is not in this window either.
- One `ldrh #0x0` candidate (`0x0806b000`: `ldrh r0, [r4, #0x0]`);
  whether it reads a descriptor needs dataflow. Fixed a systematic +2
  in BL-target resolution (base is first-halfword + 4) in this and the
  30th-slice script — the exact-name matches above are the proof.

## Drain bounded: no subtract idiom inside (35th slice, `scripts/decode_drain.py`)

Report: `local/drain.json` (exit 0, ROM unchanged).

- `FUN_0806ae54` bounds `0x0806ae54..0x0806b0a2` (prologue at the named
  address; first pop at `0x0806b0a0`) — so the DNA spawn-copy stanza
  sits *inside* the drain body, not in a separate function.
- Its 35 memory ops: counter-style `ldrh/strh #0x0` RMW pairs, signed
  `ldrsh` overlap triples feeding helpers, one `ldrh [r4, #0x26]`, and
  the DNA twin. **Zero** register-offset stores, **zero** register
  subtracts, **zero** `LDRH #0x34`, **zero** death-path calls in the
  whole body — the drain cannot subtract HP by itself.
- Its callees are the next static targets: `0x0800a90`, `0x080daa00`,
  `0x0800da0`, `0x080dc264`, `0x0801d94`. The subtract lives in one of
  them, in the packet helpers, or via a path the linear decoder cannot
  see (register dataflow / Ghidra). Fixed a no-increment bug in
  end-bound scanning mid-slice (same halfword read 1024×); rerun bounds
  are sane (334 bytes).

## Drain callees eliminated (36th slice, `scripts/decode_callees.py`)

Report: `local/callees.json` (exit 0, ROM unchanged).

- Bounded and decoded all five in-body callees: `0x08000a90` (96 ins),
  `0x080dc264` (47 ins) and `0x080daa00` (degenerate 5-ins window,
  tail-calls `0x080da870`) are clean — **zero SUBs, zero
  register-stores, zero struct `+0x34`/`+0x2e`**; `0x08000da0` and
  `0x0801d94` have no prologue in range (mid-function targets or data,
  unboundable by heuristic).
- The lone early "candidate" was a false positive fixed in-script:
  `ldr r0, [pc, #0x34]` is a PC-relative pool load (mask `0xffff`),
  not a struct access — matchers now require `ldrh`/`strh` form.
- Fixed a shared-helper crash too: prologue back-scan ran past file
  start for low addresses (`struct.error`); now clamps at zero.
- Net: the HP subtract is in none of the drain's callees. Remaining
  static suspects: the packet helpers (`080428b4`/`08042848`), the
  queue-function body, or register dataflow / Ghidra.

## Packet helpers + death path eliminated; shared primitive named (37th slice, `scripts/decode_packet_helpers.py`)

Report: `local/packet-helpers.json` (exit 0, ROM unchanged).

- Both helpers bounded (`0x080428b4` 215 ins, `0x08042848` 269 ins,
  shared end `0x08042a62` — two entries, one body) and clean: zero
  SUBs, zero register-stores, zero struct `+0x34`/`+0x2e`.
- Both call **`bl 0x80421ac` — exactly the decompiled death path**
  (`FUN_080421ac`), further corroborating the 25th slice.
- Death path bounded too (`0x080421ac..0x0804276e`, 737 ins) and also
  clean of halfword idioms — but it repeatedly calls **`0x080da7ac`**
  (overlap-routine neighborhood) and, like both helpers, **`0x080415a8`**
  (6+ calls across the three bodies): the most-called undecoded shared
  primitive, hence the next static target for the HP write.
- Static elimination now covers drain body, all its callees, both
  packet helpers and the death path. What remains: `0x080415a8` /
  `0x08041864` / `0x080da7ac`, the queue-function body SUB scan, or
  register dataflow / Ghidra.

## Shared primitive + queue body: zero idioms, static wall reached (38th slice, `scripts/decode_packet_helpers.py`)

Report: `local/packet-helpers.json` (exit 0, ROM unchanged).

- `0x080415a8` / `0x08041864`: no prologue in range (shared tails or
  mid-function entries — unboundable by heuristic); forward windows
  clean. `0x080da7ac`: bounded window clean. Queue `0x0806b1fc`:
  forward window clean, calls packet helpers + `0x803f2c8`/`0x803f17c`/
  `0x803f0e4` (overlap/proc family). Final: **4/7 bounded, 0 with
  SUB/store/`+0x34`/`+0x2e` idioms**.
- Static idiom elimination is now exhaustive over every reachable body:
  drain, 5 callees, 2 helpers, death path, primitive windows, queue
  window. The HP write uses no halfword SUB/store idiom visible to a
  linear decoder — remaining possibilities, in order: (a) full-word
  `STR` (the decoder never modeled the `0x6000` family — last static
  stone, one scan), (b) register dataflow hiding the offset, (c) Ghidra
  decompilation of the queue/drain bodies.

## Word-store scan: zeros everywhere, static elimination complete (39th slice, `scripts/scan_word_stores.py`)

Report: `local/word-stores.json` (exit 0, ROM unchanged).

- Scanned six decoded ranges (drain+queue, both helpers, death path,
  `0x08000da0`, `0x08001d00`, `0x080da6b0`): **zero** word-stores at
  `0x30/0x34/0x38`, **zero** register-`STR`, **zero** word-loads of
  `+0x34`. Combined with slices 29–38: no halfword AND no word idiom
  touches victim HP anywhere statically reachable.
- The HP write is now definitively beyond linear pattern scanning.
  What remains: register dataflow (offset computed across calls),
  Ghidra decompilation, or a native RAM watchpoint (emulator support
  unknown — not attempted).
- Fixed a dropped-zero address typo mid-slice (`0x801D00` < ROM base →
  negative offset); the new bounds guard caught it, broke cleanly, and
  the corrected rerun covers the intended `0x08001D00` window.
- **Damage candidate: u16[0] = 27.** The 26th slice measured drop 18 is
  overkill clamped at zero (victim HP 18 < 27), so 27 >= 18 is consistent
  with the one-cast kill — not a contradiction. Field identity stays a
  candidate until a non-lethal +0x34 check against a tougher victim pins
  exactly 27; descriptor damage fields and match-pass internals remain open.

## What this unlocks and what stays shut

- `docs/OWNED-PROJECTILES.md` binder items 1 (spawn linkage), 2 (position /
  velocity map), and 4 (SFX call convention + spawn ID) are now evidence-backed;
  item 3 (HP/damage: +0x34 HP, 22 single-frame zombie pin; descriptor 27
  vs multiplier 45 vs DEF open; skeleton DEF-0 pin missed twice,
  harness proven) and 5–6 (lifecycle: transition clears, pause unproven)
  remain open only at the match-pass/dynamic-confirmation level.
- No write permission follows: call signatures are decompiler-recovered, the
  engine's allocation tables are unmapped, and audio sample ownership is open.
- The operator's GUI session still lacks functions at `0x08026008`/`0x08025f70`
  (manual D+F+save never stuck); the bridge can only xref what that session
  knows until then. Headless remains the working path for new addresses.
