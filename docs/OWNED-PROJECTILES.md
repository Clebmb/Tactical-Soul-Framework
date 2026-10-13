# Owned projectiles subsystem (proposal + budgeting model)

Target: Isaac-style tear projectiles fired from a custom soul, with matching
gameplay SFX. This document scopes the subsystem; `aria/projectiles.py`
implements the framework-side budgeting half. First decompiler evidence now
exists (see [SOUL-DECOMPILE.md](SOUL-DECOMPILE.md)): spawn linkage, the
position/velocity record map, and the SFX call convention with the soul's
spawn sound ID are proven. Damage, lifecycle, and write permission remain
open before any tear-art binding.

## What exists now (framework side, tested)

`aria/projectiles.py` is pure reservation/accounting, covered by 9 synthetic
tests (`tests/test_projectiles.py`, no ROM):

| Contract | Bound (native source) |
|---|---|
| `MANA_COST` 12 | soul record `mana_cost` |
| `MAX_AT_ONCE` 6 / ledger capacity | soul record `max_at_once` |
| `PRESS_BUDGET_PER_CAST` 3 | count-gate slices 11/13/17 |
| `REGEN_MP_PER_FRAME` 1/60 | 19th slice (`local/mp-regen.json`) |
| live window +7..+61 | slices 1–4, twin-identical |
| `mp_spend_adjusted` / `cast_fired` | 18th slice regen confound |
| `ProjectileLedger` reserve/release/live | ownership bookkeeping only |
| `SOUL_ZOMBIE_PER_HIT_DAMAGE` 22 / `total_damage` / `casts_to_kill` | 40th slice zombie pin (n=2, single-frame; other enemies untested) |
| `SOUL_DAMAGE_MULTIPLIER` 45 / `damage_vs_defense` | 44th–45th slice fit: (45−DEF)//2 (DEF1→22 n=2, DEF10→17 n=2, DEF5→20; skeleton prediction open) |
| `casts_to_kill_for(hp, def)` | 46th slice: predicted casts from the damage model (skeleton 20/0 → 1; needs a catch) |

The ledger treats slots as opaque tags: observed actor slots 2/3 are the
default expectation, but the native slot binding is unproven, so tags stay
abstract until the spawn allocator is identified.

## What a native binder must prove (all open)

1. **Spawn allocator**: LINKAGE PROVEN — soul state 0 allocates the
   companion through `FUN_08023530` via shared spawner `FUN_080256ac`
   ([SOUL-DECOMPILE.md](SOUL-DECOMPILE.md)). The slot-selection rule and
   allocation tables stay open.
2. **Record layout**: MAPPED — words 9/10 velocity, 16/17 position,
   state/counter/flag bytes at +0x10/+0x0d/+0x0f
   ([SOUL-DECOMPILE.md](SOUL-DECOMPILE.md)). HP field still absent.
3. **Damage path**: LOCATED — victim HP is the short at record+0x34;
   overlap → +0x65 hit mailbox → queued packets (`080428b4`/`08042848`)
   → `FUN_0806ae54` drain → HP falls → death path `FUN_080421ac`
   ([SOUL-DECOMPILE.md](SOUL-DECOMPILE.md)). Per-hit numbers PINNED
   (40th slice): one live cast deals exactly 22 damage in a single
   frame vs zombies (200→178, one change-point, n=2, EXP 0 non-lethal;
   supersedes the 26th slice's clamped 18→0 overkill kill). DEF
   isolation PROVEN (44th slice): a DEF-10 zombie mod takes exactly 17
   (200→183 single-frame, n=2, victim DEF read live) — DEF subtracts,
   fitting damage = (45−DEF)//2 with 45 the soul-record multiplier
   (`damage_vs_defense`; confirmed at a third DEF in the 45th slice:
   DEF 5 → 20, victim def_at_cast 5). Descriptor u16[0]=27 is out
   as raw damage (27−1=26≠22). Open: skeleton 22-prediction catch,
   match-pass internals.
4. **SFX dispatch**: MAPPED — global dispatcher `FUN_080d7910`
   (652 callers) takes one int ID; soul spawn sound `0xe4` resolves to song
   `0x08399BEC`, one C4 note, voice 92 (sampled-no-resample), sample
   `0x083AE488` at 10,512 Hz / 0.30 s
   ([SOUL-DECOMPILE.md](SOUL-DECOMPILE.md)). Audible render, native-play
   proof, and impact audio stay open; isolated capture still required.
5. **Lifecycle**: pause / room-transition / death / save-continue behavior of
   live projectiles; OAM/palette ownership (entries 0–8, palette 2) and the
   tile set (146/150/272/400/668, 912–943) as reskin targets only.
6. **Fizzle gate**: the Up+B cast path and its arming counter behind the
   first-press fizzles.

## Explicit non-goals for the proposal

New inventory slots, custom item effects, native graphics/attack-family
changes, and multiplayer hooks stay out. The Ability SDK gains no
projectile/SFX API until items 1–4 above land.

## Acceptance for tear-art binding

Twin-run native proof of: one press-budgeted cast → reserved slot goes live
in-window → hit-flag/HP reaction on the attributed victim → despawn at
window end with ledger release; plus pause/room/death/save lifecycle and an
isolated SFX capture. Until then, `aria/projectiles.py` is budgeting
scaffolding, not a capability.
