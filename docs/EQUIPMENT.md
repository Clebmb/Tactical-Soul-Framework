# Weapons and equipment toolkit

This milestone adds a named semantic layer over the native weapon and armor tables. It edits existing equipment and preserves native identities, graphics, animations and unknown bytes. It does not create extra inventory slots, new art, new attack families or custom item scripts.

## Commands

Run from the Tactical Soul Framework project folder:

```powershell
.\TacticalSoul.cmd equipment --query sword
.\TacticalSoul.cmd equipment --table weapons --item knife
.\TacticalSoul.cmd equipment --table weapons --index 23
.\TacticalSoul.cmd equipment --table armor --item cape
.\TacticalSoul.cmd equipment --out local/equipment-catalog.json
.\TacticalSoul.cmd build examples/equipment-workshop/mod.json
.\TacticalSoul.cmd equipment --table weapons --item knife --mod examples/equipment-workshop/mod.json
.\TacticalSoul.cmd play examples/equipment-workshop/mod.json
```

Use `--host` or ARIA_HOST_ROM for an original elsewhere. The host must pass the existing exact-version fingerprint. `--mod` applies the supplied manifest in memory before displaying fields; a patched ROM is not a valid host. Catalog exports are local reference snapshots, not directly importable manifests. Names are read locally from the immutable original; no complete extracted name or description bank is shipped. The output ROM remains separate from the original. Existing low-level `inspect --table weapons --index 0` remains available and intentionally shows unsigned storage values.

`--query` filters names/keys by substring, case-insensitive. `--item` requires an exact displayed name or generated key, case-insensitive; fuzzy matching never selects a record silently. A key is the lowercase English name with non-alphanumeric runs replaced by hyphens. Keys derive from the supported original, not modded display text. This is a stable selector within this exact ROM profile, not an international identifier.

## JSON contract

Add `equipment_edits` to a schema-version-1 manifest. See `examples/equipment-workshop/mod.json` for a runnable complete example:

```json
{
  "schema_version": 1,
  "id": "my-knife-mod",
  "equipment_edits": [{
    "table": "weapons",
    "item": "knife",
    "expect": {"attack": 5, "strength": 0, "effects": 1},
    "fields": {"attack": 17, "strength": -2},
    "flags": {"effects": {"add": ["flame"]}}
  }]
}
```

Each edit accepts `table`, exactly one of `item` or `index`, `expect`, optional `fields`, optional `flags`. Tables are `weapons` and `armor`; body and accessory share the native armor table and are distinguished by its type. Every changed field must have an expected prior value. Expectations use signed values for signed fields, and the complete numeric flag word for flags. Hex-prefixed strings or integer numbers are accepted; booleans are rejected.

Editable ordinary fields are price, attack, defense, strength, constitution, intelligence and luck. Price is u32, attack/defense are u8. STR/CON/INT/LCK bonuses are signed i8, range -128..127. The semantic toolkit rejects a value such as 254 for STR; use -2. The lower-level `aria.tables` API retains its unsigned storage contract for backward compatibility. Two's-complement conversion occurs only at the toolkit boundary. Large but representable values are not a guarantee against gameplay caps, odd UI formatting or poor balance.

Weapon flags use `effects`; armor flags use `resistances`. An update accepts `add` and/or `remove`, each a list of names. Unknown flags, duplicated names and contradictory add/remove requests fail. All unmentioned bits, including unknown bits, are preserved. There is deliberately no destructive replace-whole-word operation in this layer. Readable views include raw numeric value and `unknown_mask` so discoveries do not silently vanish.

Known elemental/status labels, bits 0..8, are slash, flame, water, thunder, dark, holy, poison, curse, stone. Weapon modifier labels are killer_mantle (11), half_damage (12), no_interrupt_on_land (13). Armor exposes only the elemental/status labels. These labels follow the documented native format; effectiveness varies by enemy/attack and is not a promise of universal resistance or immunity. Unknown bits 9,10,14,15 in effects and 9..15 in resistances are surfaced rather than guessed. All individual modifier/status interactions are not yet gameplay-certified.

Native item_id, icon, attack_type/type, gfx_index, sprite_index, weapon_animation, palette, swing_animation, iframes, swing_sound and unexplained bytes are preserved by this API. The existing table API remains the explicit lower-level route for advanced changes, which require separate research. Arbitrarily copying a weapon's attack_type while retaining another's sprite/animation can create invalid combinations; range checking alone cannot establish resource compatibility.

The batch validates selectors, identity, ranges, expectations and duplicate field claims before writing. Shared mutation-ledger rules still reject overlap with earlier table/raw edits. Writes are not a global transaction; discard a RomImage after any failure. Table edits run before equipment edits; room edits and raw patches run afterward. Expected values therefore refer to the current in-memory state after earlier table edits. Do not edit the same native field in multiple layers. Build reports contain a human-readable before/after equipment summary in addition to the binary mutation ledger; this summary records this phase's edits, not arbitrary later raw-patch semantics.

## IDs and native formats

Weapons: 59 records, 28 bytes each, base 0x08505D3C. Armor: 45 records, 20 bytes each, base 0x085063B0. Body armor has type 0; accessory type 1. Unknown fields remain byte-identical. Native table offsets live in `framework/tables.json`; high-level meaning and flag labels live in `framework/equipment.json`.

Do not interchange these identities:

| Identity | Knife | Cape | Meaning |
|---|---:|---:|---|
| table index | 0 | 25 | Within weapons or armor |
| global_id | 32 | 116 | Zero-based inventory byte and English item-name index |
| pickup_id | 33 | 117 | One-based ID used by contexts such as native global pickup/shop references; verify each consumer |
| equipped_id | 0 | 25 | Table-local equipped byte; accessory 255 means none |

Weapons' global base is 32; armor's is 91. `item_id` in each original record matches that global ID; the high-level editor refuses a changed identity. An item name is obtained from text ID 0x5B + global ID, through the u32 pointer list at 0x08506B38. Strings have a 01 00 header, ASCII label, 06 label-end command and 0A terminator. The decoder is intentionally bounded to short English item labels; it rejects unsupported control bytes rather than pretending to implement dialogue/localization. It does not rename in-game labels or descriptions.

Observed runtime equipment bytes: 0x02013268 weapon, 0x0201326C body, 0x0201326D accessory. Inventory counts begin 0x02013294, one byte per global ID. These observations support the local test fixtures, not a completed native item-grant API. Current stats begin 0x020131EE: ATK, DEF, STR, CON, INT, LCK and resistance word, each u16. Bonus interpretation is signed in ROM; current aggregate stats are native runtime results and may clamp differently.

## Example and evidence

The example changes starting Knife ATK 5 to 17, adds STR -2 and flame; Casual Clothes DEF 5 to 14, LCK -1 and flame resistance; Cape DEF 1 to 3 and INT +4. It preserves original displayed names, descriptions, behavior families and resources. Knife and clothes are available in a normal new game. Cape remains obtained through normal game availability; the verifier uses an explicit inventory fixture to test it immediately.

Run `python -m unittest discover -s tests -v`, then `python scripts/verify_equipment.py`. The first includes synthetic and optional private-host contracts; native tests skip if the private original is unavailable. The second requires a Python with Pillow, the private original, and the local libretro DLL. It boots real mGBA, compares original and edited new-game stats, equips Cape through native menus, exercises controller combat, and tests save/continue with declared fixtures. Run-specific results and actual frames live under `local/`, excluded from packaging.

Baseline starting stats measured ATK 15, DEF 11, STR 10, CON 12, INT 11, LCK 9, resistance 0. Modified starting stats measured 25,20,8,12,11,8,2. Cape menu equip adds 3 DEF and 4 INT. Native combat and save evidence, fixture details, ROM SHA-256 and exact limitations are in `local/equipment-verification.json`; do not claim a successful run if that verifier failed or its report is stale. Elemental/status damage ratios, every special modifier, shops and all weapons are not exhaustively tested.

## How another agent should extend this

`aria/equipment.py` owns equipment name resolution, signed views, narrow semantic validation and edit reports; `aria/text.py` now supplies the shared bounded original-label reader. `aria/tables.py` owns raw record layouts/writes; do not silently change its unsigned API. `aria/cli.py` exposes catalog and build integration. `framework/equipment.json` stores established semantics without commercial text. `tests/test_equipment.py` covers contracts; `scripts/verify_equipment.py` covers native evidence. The example is a reproducible starting point, not a new gameplay engine.

For more fields, document storage, signedness, dependent resources and native consumers before exposing edits. Attack/graphics templates need complete compatible resource bundles and real menu/combat checks. Custom names/descriptions need an independently bounded text encoder/allocator and UI tests. New slots/IDs require inventory, equip validation, pickup/shop/drop references, and save format work together. New special effects require native dispatch/ABI evidence and state/lifecycle tests. Do not equate a changed table flag or added JSON property with an implemented new mechanic.
