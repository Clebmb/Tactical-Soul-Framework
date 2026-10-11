# Data contracts and executable behavior

## Tactical Soul Framework manifest version 1

Top-level keys: schema_version=1; id (lowercase alphanumeric/underscore/hyphen,
1..64 characters); optional description; table_edits,frame_hook,blobs,entity_lists,
door_lists,patches,room_edits,equipment_edits,enemy_edits,enemy_encounters,abilities,content,resource_edits. Unknown top-level keys fail. Addresses are virtual ROM integers
or 0x-prefixed strings. Byte strings use bytes.fromhex syntax.

```json
{"schema_version":1,"id":"my-mod","table_edits":[
 {"table":"enemies","index":0,"fields":{"hp":18}},
 {"table":"red_souls","index":0,"fields":{"mana_cost":3}}
],"blobs":[{"id":"custom-data","hex":"01020304","alignment":4}],"patches":[]}
```

Table fields/counts are in framework/tables.json. Unknown fields, out-of-range
indices and values too wide for storage fail. Semantic validation is separate:
soul IDs, code-pointer ABI, flags, palette/sprite references and stat meanings
still require research/tests. Fields are unsigned storage, not a signedness claim.

A blob has id, exactly one of hex/file, optional power-of-two alignment. File
paths must stay inside the manifest directory. A raw patch has address,expected,
exactly one of hex/pointer_to, optional label. A pointer patch targets a blob,
with optional addend and thumb=true. Expected/replacement lengths must match.
Whole-host hash verification protects typed writes; raw patches additionally
require byte preimages. Duplicate or overlapping writes fail, even if identical.

frame_hook accepts file or hex; linked_address must be 0x08680000. Optional source,
linker,fingerprint enable drift detection and --compile. The callback is allocated
first; there is one supported after-update hook, not arbitrary detour generation.
Declared dependencies are fingerprinted by the compiler; declare every included header before extending
when adding them. Native entrypoints must return normally using the proper ABI.

entity_lists entries: sector,room,entities. Entity fields x,y,unique_id,type,subtype;
optional byte_8,var_a,var_b. IDs must be unique, x=32767 is reserved. Arrays are
allocated, terminated and sorted by the native loading axis, nothing-type last.
Graphics/palettes are not provisioned automatically. door_lists entries:
sector,room,doors, with fields from aria/rooms.py. Door edits do not update maps,
save lookup, collision or destination geometry. Normal sectors 0..11 only.

Deterministic order: ability/frame callback, content, sparse resource edits, blobs, table edits, enemy edits, equipment edits, entity
arrays, door arrays, room edits, raw patches. Reports contain mutation addresses, lengths and pre/post hashes.
CLI errors prevent normal output; API callers must discard a partially mutated
RomImage after exceptions. In-memory writes are not transactional/rolled back.

## Mario sheets are an example-specific ABI

| Sheet | Executable | Descriptive or fixed in C |
|---|---|---|
| design.json | none | Design/title/version |
| rooms.json | room/source indices, object types/coordinates/patrol/reward | Names/IDs; sector fixed to 0; list order defines topology |
| enemies.json | hp,contact_damage,speed_fixed,experience, Goomba then Koopa | behavior/death/source/soul/stomp/weapon/fire descriptions |
| powerups.json | duration_frames,projectile_damage,cooldown_frames,max_projectiles | Activation/MP/equipment/save strings describe C behavior |
| assets.json | Block/coin tile and palette offsets | source_game/evidence provenance |

Custom kinds: question=1,coin=2,goomba=3,koopa=4,flower=5. New names need new builder
mapping and C update/render/collision logic. Reward is flower=1 or coin=0, not a
general native item ID. Speed uses 16.16 units (65536=1 pixel/frame). Native actor
HP/timers are u16. At most 15 initial objects per room reserves a flower slot;
exactly four destination rooms and at most four projectiles are supported.
Object bounds 768x256 do not prove actual geometric reachability. Multiple flower
blocks in one room need a real spawn-slot policy, beyond the current reserved slot.

Balance order: Goomba hp/contact/speed/EXP; Koopa hp/contact/speed/EXP; flower
duration/damage/cooldown/max. ABI/address/order changes require C compilation.
Values alone do not. Unused helper-generated strings/provisional palette values
in the legacy builder are superseded by its final packed ROM banks/generated.h.
Do not confuse those helpers with runtime source of truth.


## Existing-room milestone (2026-10-10)

See [ROOM-DESIGN.md](ROOM-DESIGN.md) for sparse entity moves, paired existing doors, map/save diagnostics, commands, test evidence and extension guidance. `aria/level.py` implements this layer; `examples/room-workshop/mod.json` is its runnable example. General geometry/collision authoring, map relocation and campaign-wide graph repair remain unimplemented; the narrow terrain milestone below is available.

## Equipment semantic edits

`equipment_edits` is documented completely in [EQUIPMENT.md](EQUIPMENT.md). It accepts exact item names/keys or table-local indices, mandatory expected values for each changed field, signed i8 primary stat bonuses, u8 ATK/DEF, u32 price and named add/remove flag operations. Identity/resources remain intact; the underlying table API retains unsigned storage values. Build reports include an equipment before/after summary.

## Enemy and encounter semantic edits

[ENEMIES.md](ENEMIES.md) defines `enemy_edits` and `enemy_encounters` completely. Enemy balance fields, named flags and named ordinary item drops require expected prior native values. Soul reference reassignment and AI-pointer changes are excluded. Encounters stage moves/clones into the existing room-edit pass, sharing each room entity array with room moves and preserving loading order. Enemy encounters reject combination with raw patches or full entity/door lists. Same-room original subtype evidence is a prerequisite, not a complete resource-capacity certificate. Reports contain `enemy_edits` plus encounter operations/audits nested in `room_audits`.

Content codecs, preimage hashes and allocation/pointer contracts are specified in CUSTOM-CONTENT.md. Ability dispatcher config/RAM and native lifecycle are specified in ABILITIES.md.

Named content target bindings and sparse resource_edits schemas are specified in RESOURCE-AUTHORING.md. content-catalog reports original/current hashes; export-content emits importable codec JSON; diff-content emits a runnable sparse manifest against immutable original. Private exports and diffs are restricted to local/.


## Room geometry foundation and project rename (2026-10-10)

The project is now **Tactical Soul Framework**, in its independent folder of the same name. Use `TacticalSoul.cmd`; `Dominance.cmd` and `Framework.cmd` remain aliases. See [rename compatibility](RENAMING.md) for environment variables and retained native ABI identifiers.

Read [ROOM-GEOMETRY.md](ROOM-GEOMETRY.md) before terrain work. `aria/compression.py` implements bounded LZ10/Aria resource reconstruction; `aria/geometry.py` inspects type-2 layers and applies checked, isolated existing-metatile edits. `inspect-geometry` and private `export-geometry` expose the source-backed format. `examples/geometry-workshop/mod.json` adds one stone step in the first hallway and composes the paired save-room route. Writes currently support only this registered main layer, unchanged dimensions and existing metatiles. New graphics, collision definitions, room resizing and full campaign compilation remain unimplemented.

Validation: 101 unit tests pass. `scripts/verify_geometry.py` passes eight structural/native checks: original walking reaches world X329, the edited step stops Soma at X311, native A jumping reaches X458, and fresh save/continue plus natural return stops at X360 on the other face. Initial comparisons declare a camera-relative X/zero-velocity fixture and retain settled Y; terrain is never injected into RAM. Private evidence stays in `local/geometry-verification.json`. See the geometry guide for format provenance, contracts, file responsibilities and next extensions.
