# Exact-version ROM and RAM reference

ROM addresses are GBA virtual addresses unless explicitly file offsets. File
offset = virtual - 0x08000000. All records are little-endian. Addresses apply only
to aos-usa-r0's SHA-256. Never loosen the hash gate to try another region/revision.

## ROM reservations and structures

| Address | Purpose |
|---|---|
| 0x08001990 | Literal pointing to area/sector tables |
| 0x08000500 | Eight-byte native update entry hook |
| 0x08000509 | Thumb continuation after displaced instructions |
| 0x084F0B14 | Reconstructed native dispatch pointer |
| 0x08651170..0x08800000 | DSVEdit-documented free space, half-open |
| 0x08651200..0x08651230 | Original project after-update wrapper |
| 0x08660000 | Mario C origin |
| 0x08670000..0x08671000 | Locally imported Mario tiles |
| 0x08671000..0x086710A0 | Five Mario palette banks |
| 0x08672000..0x08672320 | Four 200-byte RoomDef records |
| 0x08673000..0x08673030 | Twelve u32 Mario balance values |
| 0x08680000..0x08800000 | Tactical Soul Framework allocation arena; Mario also allocates here in its separate output |
| 0x08116650 | Castle tile metadata (save lookup coupling) |
| 0x08117DD0 | Castle map line nibbles |
| 0x084F0D8C | New-game sector/room bytes |
| 0x084F0D90 | New-game camera/player coordinate halfwords |

Room metadata is 36 bytes `<HH8I`: +4 alternate pointer, +8 layers, +12 graphics,
+16 palettes, +20 entity list, +24 doors, +28 door count/effects, +32 packed map.
Preserve unexplained bits/halfwords. Entities are `<hhBBBBHH>` (12 bytes):
x,y,unique_id,type,subtype,byte_8,var_a,var_b. End marker x=32767. Types: 0 nothing,
1 enemy, 2 special object, 3 candle, 4 pickup; 5/6 conditional pickup variants.
Doors `<IBB5H>` (16 bytes): destination room pointer, source x/y screen-side
indices, dest_x_2,dest_y_2,dest_x,dest_y,unused. Left edge source x=255.
Native loading assumes entities sorted by X in horizontal rooms, Y in vertical
rooms; nothing-type entries last. Destination spawn coordinates must fit geometry.

framework/tables.json is the machine-readable native record reference: 113 enemies,
32 consumables, 59 weapons, 45 armor, 56 red souls, 25 blue, 36 yellow, 4 Julius
skills. Indices are zero-based within a table, not global inventory IDs. Unsigned
storage does not prove unsigned gameplay/stat semantics. Source facts came from
DSVEdit aos_constants.rb; field gameplay support is not exhaustively tested.

## Runtime addresses

| Address | Storage/meaning |
|---|---|
| 0x02000010 | u8 state: observed 1 title, 2 selection, 4 gameplay, 5 game-over, 7 prologue |
| 0x02000014 / 0x02000016 | u16 GBA held / newly pressed button bits |
| 0x02000064 | u8 substate: observed 1 active, 3 transition, 6 pause |
| 0x02000088 | u32 current room pointer |
| 0x0200009E / 0x0200009F | u8 save sector/room from map lookup |
| 0x020004E4 | Native entity array base, stride 0x84 |
| entity +0x40 / +0x44 | s32 16.16 screen X/Y |
| entity +0x42 / +0x46 | s16 pixel halves X/Y |
| entity +0x48 / +0x4C | s32 velocity X/Y |
| entity +0x58 | Facing byte; observed bit 0x40 left |
| 0x0200A09A / 0x0200A09E | s16 camera X/Y |
| 0x020131EE | u16 attack stat |
| 0x02013268..0x0201326B | Equipped weapon/red/blue/yellow identifiers |
| 0x0201327A / 0x0201327C | u16 HP/MP |
| 0x0201327E / 0x02013280 | u16 max HP/MP |
| 0x0201328C / 0x02013290 | u32 EXP/gold |
| 0x02013398 / 0x0201339A | Configured attack/jump button masks |
| 0x0201331C | Owned-red-soul data beginning; exact bit semantics need more work |
| 0x02011F1C | Companion palette source buffer |
| 0x020123E1 / 0x020123DC | Palette update byte / pending bank mask |
| 0x0203D000 | Custom RAM reservation, isolated-example evidence |
| 0x03000C58 | Hardware-format OAM buffer base |
| 0x06012000 | Custom OBJ tile bank |

Hardware button bits A=1,B=2,Up=64 are NOT libretro IDs. Libretro B=0,Select=2,
Start=3,Up=4,Down=5,Left=6,Right=7,A=8,L=10,R=11. Sign-extend RAM values yourself;
the Python harness reads unsigned integers.

Used native damage routine: Thumb 0x08021655. Candidate collision function
0x08001FE9 was identified but is not a validated general API. No complete native
level-up/soul-grant/item-grant/sprite-allocator ABI has been established.

## SMA2 sources (file offsets, companion exact version only)

| Asset | Original source |
|---|---|
| Shared sprite page | 0x18A454, 32 bytes per tile |
| Goomba | page IDs 0x18,0x19,0x38,0x39 |
| Koopa body | page IDs 0x10,0x11,0x30,0x31 |
| Koopa shell | page IDs 0x0A,0x0B,0x2A,0x2B |
| Koopa head | 0x13B910,0x13B930,0x13BD10,0x13BD30 |
| Flower | 0x188714,0x188734,0x188B14,0x188B34 |
| 8x8 fireball | 0x1887F4..0x188814 |
| Question block | 0x186C54 plus 0,32,64,96 |
| Used block | 0x186D54 plus 0,32,64,96 |
| Coin | 0x186DD4 plus 0,32,64,96 |
| Shared white/black | 0x1F18D6..0x1F18DA |
| Five-color slices | 0xD5B4E yellow, 0xD5B72 green, 0xD5B66 red |

Block palette source words are in data/assets.json. Intermediate builder defaults
may be overwritten by verified final lists; final writes define actual output.
Offsets/provenance are distributed, not extracted assets. New companions need
independent hash, source layout, compression, tile/palette and behavior research.

## Ability milestone D

See [ABILITIES.md](ABILITIES.md) for the implemented native SDK and precise extension contracts. `aria/abilities.py` validates config/RAM/runtime selection; `native/abilities/` owns C modules, guards, ABI, linker and dependency fingerprints; `tests/test_abilities.py` covers contracts; `scripts/verify_abilities.py` verifies native behavior. The SDK uses the existing single hook. Custom mechanics remain trusted native code, with transient RAM and no custom SRAM schema.
