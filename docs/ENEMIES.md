# Enemy and encounter toolkit

Tactical Soul Framework now has a named semantic layer for native enemy balance, item drops, elemental flags, and conservative existing-room encounter authoring. It changes actual Aria records; original AI entrypoints are preserved. Arbitrary AI replacement, new enemy graphics, general resource allocation and boss/event scripting remain extension work.

## Quick start

Run from the independent Tactical Soul Framework folder:

```powershell
.\TacticalSoul.cmd enemies --query skeleton
.\TacticalSoul.cmd enemies --enemy zombie
.\TacticalSoul.cmd enemies --index 33
.\TacticalSoul.cmd enemies --out local/enemy-catalog.json
.\TacticalSoul.cmd encounters 0 3
.\TacticalSoul.cmd build examples/enemy-workshop/mod.json
.\TacticalSoul.cmd enemies --enemy zombie --mod examples/enemy-workshop/mod.json
.\TacticalSoul.cmd encounters 0 6 --mod examples/enemy-workshop/mod.json
.\TacticalSoul.cmd play examples/enemy-workshop/mod.json
```

`--host` or ARIA_HOST_ROM selects the exact verified original. `--mod` builds an in-memory view before inspection; a patched ROM is not an accepted host. Catalog export is a local reference snapshot, not an importable manifest. Both catalog and encounter audits are read-only. Unknown/fuzzy selectors never silently select an enemy: `--enemy` requires an exact native English label or lowercase hyphenated key. `--query` uses case-insensitive substring matching. `--index` is zero-based. Names come from the immutable original, so editing a record cannot change its selector. No complete extracted name bank is bundled.

## Enemy record authoring

A schema-version-1 mod can contain `enemy_edits`:

```json
{
  "schema_version": 1,
  "id": "zombie-balance",
  "enemy_edits": [{
    "enemy": "zombie",
    "expect": {"hp":18,"experience":1,"item_1":93,"item_1_rarity":20},
    "fields": {"hp":30,"experience":7},
    "drops": {"item_1":{"item":"potion","rarity":0}}
  }]
}
```

Each entry accepts exactly one of `enemy` or `index`, `expect`, and optional `fields`, `flags`, `drops`. `fields` exposes hp, mp, experience, attack, defense and soul_rarity. HP must be positive and fit u16; MP/EXP fit u16; ATK/DEF/soul rarity fit u8. Storage-valid extremes are not a promise about native signed comparisons, caps or balanced gameplay. There is no speed field in enemy DNA: speed is generally native behavior code or per-entity parameters, not an invented table property.

Every changed native field must have an expected prior value. Numeric integers and 0x-prefixed strings are accepted, booleans rejected. Expectations can additionally assert unchanged fields. Stats apply globally to all instances of that native enemy subtype, including native spawners; they are not per-placement variants. Boss stats can be edited through this table layer, but that does not certify boss progression or make bosses safe to clone.

`flags` supports weaknesses and resistances. Each update has `add` and/or `remove`, lists of known names. Both expose slash, flame, water, thunder, dark, holy, poison, curse and stone in bits 0..8. Weakness bit 11 is labeled killer_mantle; resistance bit 10 is time_stop. Unknown bits are displayed as `unknown_mask` and preserved. Duplicated/contradictory names and unknown labels fail. Expectations for flag changes use the entire numeric prior word. Labels are documented native semantics, not exhaustive gameplay proof of every elemental/status interaction.

`drops` supports item_1 and item_2, each with exactly `item` and `rarity`. Item is an exact ordinary item name/key, including consumables, weapons, body armor and accessories; null disables that slot by writing item ID zero. Rarity is a native byte, not a percentage: lower values generally mean more common. **Item rarity zero does not guarantee a drop.** The native RNG/luck/ring logic still runs. Require expectations for both the slot's item ID and its `_rarity` field, even when disabling. Item IDs stored in enemy DNA are global item ID plus one: Potion=1, Baselard=34, Cloth Tunic=93. Do not use equipment table index 1 to mean Baselard here. Null maps to zero; raw numeric item IDs are deliberately excluded from the named drop API.

Soul rarity zero disables soul drops according to the documented native format. This toolkit permits changing rarity while preserving soul_type and soul index. Catalog output exposes both numeric references. Cross-type soul reassignment, ability drops, new soul code and native grant APIs are not implemented by this milestone. They need separate lifecycle and persistence evidence. Item-drop and soul-drop rarity zero have different meanings; do not conflate them.

The batch validates selectors, expected values, ranges, drops and duplicate field claims before writing. Create/update code pointers, soul references and unexplained bytes remain intact. The low-level `aria.tables` API remains available for research but is not a complete semantic validator. Shared patch-ledger rules prevent overlapping writes; any API failure requires discarding the partially modified RomImage.

## Soul drop-table mapping and spawn-scan boundary

`soul_catalog(rom)` groups all 113 enemy soul references by
`(type, index)` with holder names and rarities; `resolve_soul(rom,
'2:12')` looks one up and `TacticalSoul.cmd enemies --soul 2:12`
prints it. Indices stay numeric: soul kind names are not established
from sources. Measured on the exact host: 111 distinct souls, 110
with a single holder; soul (0,0) is shared natively by Belmont,
Graham and Chaos. Types distribute 0:58, 1:21, 2:33, 3:1. Seven
records carry soul rarity zero and all seven are bosses
(Headhunter, Death, Legion, Balore, Belmont, Graham, Chaos),
consistent with zero disabling soul drops; item rarity zero behaves
differently (the workshop Potion drops), so the two formulas must not
be conflated and neither formula is proven here. Soul type/index
reassignment stays rejected (`test_ai_and_soul_reassignment_rejected`)
until collection can be proven.

`scripts/scan_soul_spawn.py --enemy zombie|skeleton --rarity N
--rolls N --out local/x.json` builds a throwaway probe ROM (that
enemy's soul rarity set, both item slots disabled), walks to its room
with controller input only, records a no-attack calm baseline, then
kill-loops while logging kill-aligned novel EWRAM actor codes
(0x020004E4, stride 0x84, 224 slots). Victim update/create pages
flag likely death-state codes. Results across zombie rarities 0, 1,
255 and skeleton rarity 1, with fully deterministic kill rolls:

| Code | Behavior | Reading |
|---|---|---|
| 0x80221cd | attack-correlated only; absent in 60 no-attack samples | Soma slash effect, not a drop |
| 0x8042de9 | appears on non-kill hit rolls | hit transient, not a drop |
| 0x807b3e5 | strictly kill-adjacent, same page as zombie update 0x807a9ed | likely zombie death-state |
| 0x806e525 | strictly kill-adjacent at zombie kills only | kill-burst remnant (see verdict below), not a collectible crystal |
| 0x806c5ad, 0x8045c9d | strictly kill-adjacent at skeleton kills only | same verdict class, per-victim codes |

No persistent crystal actor appears at any tested rarity, so
soul-crystal spawns are not observable in this enemy actor window:
either pickups use another actor system, collection at melee range is
faster than the ~26-frame sample grain, or the drop formula needs
more kills than the bounded loop. Collection/grant, soul-inventory
RAM, menu proof and the rarity formula remain the blockers for
reassignment and grant APIs; REA MCP rejects GBA targets, so no
decompiler evidence exists. Reports record calm codes, kill rolls,
sightings, page flags and these limits under `local/`.

Fine-grained follow-ups (v0.44, private probes under `local/`, not
shipped) settled the two kill-locked codes further. A 2-frame
post-kill trace shows `0x807b3e5` living ~15 frames (death/decay
family) while `0x806e525` plays a ~16-frame animation then freezes
permanently: its animation word locks, its slot persists for 282+
frames, and walking Soma onto its position changes nothing. A
magnetizing collectible with Soma camping its corpse for 300 frames
must vanish; this one does not, so it is incompatible with a soul
crystal and most consistent with a leaked kill-burst particle (about
four spawn per kill, evicted only when slots recycle). Per-victim
codes and frozen-anim signatures therefore mark kill FX, not drops.
A reusable position method fell out along the way: actor world-x
reads as the low halfword of record word 8 divided by 256,
calibrated on a zombie walking 254→93 toward Soma; it placed the
burst cluster at the corpse line and the 254.4 reading at the spawn
edge. Corpse-anchored collection tests (walking the corpse line)
clear nothing, and retreating exits the small room, so room-crossing
collection timing stays untested.

## Encounter placements

`enemy_encounters` stages enemy operations with `room_edits` so a touched entity array is relocated only once. Moves and clones therefore retain native loading-order sorting and stable entity IDs. They can compose with paired door connections. Combining these high-level operations with raw patches or full entity/door lists is rejected, so lower-level room mutations cannot invalidate the audit.

Move an original enemy:

```json
{"op":"move","room":{"sector":0,"room":3},"entity_id":3,
 "enemy":"zombie","from":[128,176],"to":[192,176]}
```

The ID and named subtype must match one original type-1 enemy in that room. `from` must match its current staged position. Only x/y change; unique identity, byte_8, var_a and var_b remain intact. Positions must fit the existing main-layer screen dimensions (256 pixels per screen). Moving the first hallway Zombie placement moves its **spawner**, preserving var_a=2 and var_b=1. Do not describe that record as a single Zombie or reset its parameters accidentally.

Clone a supported original single actor in the same room:

```json
{"op":"clone","room":{"sector":0,"room":6},"source_id":2,
 "entity_id":9,"enemy":"skeleton","to":[560,176]}
```

The source must be present in the immutable original room, with matching subtype. The new ID must be unused and byte-sized. Cloning newly cloned records is rejected. Initial supported templates are Bat, Zombie and Skeleton **only when byte_8, var_a and var_b are all zero**. Original spawners, conditional records and parameterized variants are not clone templates. At most two added actors per room are allowed by this conservative policy, and total serialized entries must remain below 256. This limit is an engineering guard, not a measured universal engine capacity. No removals, subtype swaps, arbitrary parameters or new species insertion are exposed.

Boss and known script-sensitive subtypes from the reference boss mapping are excluded from encounter operations. Native create/update pointers must match the original for each affected subtype. The source-existing-in-original constraint provides same-subtype resource evidence; it does not allocate palettes/VRAM, prove every position reachable, or guarantee simultaneous actors fit OAM. Moving an enemy can still place it inside walls or interfere with events. Test every encounter in native gameplay.

`encounters SECTOR ROOM` reports existing type-1 identities, names, coordinates, parameters, protected status and whether each subtype appeared in the original room. Missing original subtype evidence or changed AI pointers are audit errors. The audit is intentionally narrow: its successful result does not certify arbitrary low-level list edits, spawner budgets, global resource sharing or collision. Build reports include encounter operations and audits under `room_audits`, alongside before/after enemy table summaries under `enemy_edits`.

## Example design

The runnable enemy-workshop makes Zombie HP 30, ATK 11, EXP 7, adds flame weakness, disables its soul rarity and changes item slot 1 to Potion with item rarity 0. Skeleton HP becomes 12 and EXP 5. The original Zombie spawner moves from x128 to x192. One ordinary Skeleton is cloned at (560,176) in sector 0/room 6, where that same subtype already exists. All AI pointers remain native.

For a compact playable demonstration, the example pairs the first hallway's right door with the Skeleton room's left door, using the existing room/door API. This is a nonadjacent minimap shortcut, not a coherent campaign redesign. Displaced neighbors retain their old exits and full progression is not certified. The example preserves room geometry, original map locations, both map banks and save markers. The lower HP Skeletons give the player a useful combat test after the more durable Zombies. Original displayed names/descriptions remain unchanged.

## Native format and evidence

Enemy DNA has 113 records of 36 bytes at 0x080E9644. Important offsets: create/update pointers +0/+4, one-based item slots +8/+10, HP/MP/EXP +12/+14/+16, soul rarity +18, ATK/DEF +19/+20, item rarities +21/+22, soul type/index +23/+24, weakness/resistance words +26/+28. Bytes +25 and +30..35 are preserved. See framework/tables.json for raw layout and framework/enemies.json for semantic policy.

English enemy names use text ID 0x25D + enemy table index through the pointer bank at 0x08506B38. `aria/text.py` reads bounded ASCII labels from the immutable original, with 01 00 header and 06/0A terminators. This is not a dialogue encoder or localization system. It is shared with equipment to avoid divergent name decoding.

The native entity array begins 0x020004E4, stride 0x84. In the tested actors, +0 is the native update pointer, +0x34 observes current HP storage, +0x3C ATK, +0x3D DEF. A Zombie spawner and its spawned actors do not initialize all these fields identically; do not reject a working spawner because its own ATK/DEF are zero. Runtime slot identity is not the room's stable serialized ID. Do not assume slot 9 proves clone entity ID 9.

Run:

```powershell
python -m unittest discover -s tests -v
python scripts/verify_enemies.py
python scripts/verify_rooms.py
python scripts/verify_equipment.py
python scripts/verify_framework.py
```

Unit tests include optional private-host contracts and skip those cases if the original is absent. Native verifiers require a Python with Pillow and the local libretro DLL. Enemy verification uses controller input only, with no inventory, RNG, position or enemy-HP fixtures. It checks catalog/ID/unknown-byte invariants, modified native actor stats, EXP rewards, one actual Potion drop and collection, traversal through the added encounter, native Skeleton combat and return travel. Its bounded drop observation is deterministic for the tested build/core, not statistical validation of drop probabilities. The actor creation test proves serialization and playable traversal; it does not map a runtime actor slot directly to the clone's stable ID. Full campaign, every clone template, hardware, shops/soul grants and all flag interactions remain untested. Current run evidence and real frames are in local/enemy-verification.json and local/enemy-workshop-*.png, excluded from packages.

## Extension plan for another agent

`aria/enemies.py` owns catalog, native drop name resolution, safe balance/flag/drop edits and summaries. `framework/enemies.json` records policy and format provenance. `aria/encounters.py` owns original-room resource evidence, clone templates and staged move/clone plans. `aria/level.py` owns shared entity arrays and door writes; maintain that single-owner design when adding placement operations. `aria/cli.py` exposes commands and build ordering. Tests and the example demonstrate intended contracts rather than making arbitrary native AI safe.

For custom AI, first identify native create/update calling conventions, entity allocation, child actor ownership, death/drop callbacks, update ordering and cleanup. Document signatures and disassembly/runtime evidence; pointer swapping alone is not a behavior plugin. A native actor can allocate other entities or depend on room events, graphics, or parameters beyond the exposed DNA fields. Keep custom behavior behind separately verified dispatch wrappers and owned RAM, with pause/transition/death/save tests.

For new species placement, build a real graphics/palette/resource inventory and allocation model before widening the same-room constraint. Expand clone templates only after checking parameter semantics, dynamic actor count and rendering under overlap. For per-instance stats, establish where native initialization copies DNA and how variants can avoid globally changing every enemy. For loot extensions, verify RNG semantics, luck/ring modifiers, item pickup and save persistence; soul grants need their own ABI evidence. Every new capability should have a minimal native example, regression tests, explicit limitations and agent-facing docs.

## Recorded milestone result

The 2026-10-10 run passed all 50 unit tests and all eight enemy native checks. Workshop ROM SHA-256: `9227988af2b7e8475951d0e69d217582875fa28874cb7a71a94dc29311ad2512`. The controller-only drop sequence collected a Potion after 96 combat cycles; Zombie EXP rose from 0 to 42 (six rewards of 7). These are observations of this exact build/core/input sequence, not guarantees for later mods. Room, equipment and original callback/table native regressions also passed. Originals remain unchanged.
