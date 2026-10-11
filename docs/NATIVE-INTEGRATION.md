# Native integration and ABI

## Execution model and hook

The original GBA Aria engine executes in mGBA. Native Thumb code in ROM free
space is called after the host update. Callbacks run in title/menu/dialogue
states as well as gameplay: each feature must gate itself appropriately.

Eight bytes at 0x08000500 redirect to wrapper 0x08651201. The 48-byte wrapper
preserves return context, pushes its own after_original target, reconstructs
r3=-1/r0=0x084F0B14, then branches to 0x08000509. On native return it calls the
custom callback and restores the original return. src/hook.asm is authoritative;
this is not a generic arbitrary-prologue replacement.

Mario links tick at 0x08660000. Tactical Soul Framework links its example callback at
0x08680000, allocating it before other blobs. hooks.py reuses the project's
original wrapper/entry code and replaces its unique callback literal with
0x08680001. Low bit 1 means Thumb. Data pointers must not acquire that bit.
There is one after-update hook: combine features behind a dispatcher rather
than overwriting the same entry twice. Outputs start from the original ROM;
Tactical Soul Framework and Mario outputs must not be patched on top of each other.

## C requirements

ARM7TDMI Thumb, freestanding, no OS/libc/startup. The linker collects text/rodata;
it does not initialize BSS, mutable globals or a general C runtime. Reserve RAM
explicitly and initialize feature state. Inspect output for compiler support
calls, division/floating-point helpers or unresolved symbols. Keep stack use
bounded, preserve callee-saved registers and return normally.

Native addresses are not complete API contracts. Verify calling arguments,
return values, caller state and side effects before invoking a new host routine.
The frame callback signature is not automatically an enemy/soul update signature.

## Mario state ABI

Custom state starts at 0x0203D000. It has been exercised in isolated examples,
not certified for every cutscene/ending/hardware configuration.

| Offset | Storage | Meaning |
|---|---|---|
| +0x00 | u32 | magic 0x4D415249 |
| +0x04 | u32 | room pointer |
| +0x08 | u32 | frame counter |
| +0x0C | u16 | flower frames |
| +0x0E | u16 | contact cooldown |
| +0x10 | u16 | firing cooldown |
| +0x12 | u8 | actor count |
| +0x13 | u8 | emitted sprite count |
| +0x14 | s32 | previous world feet Y |
| +0x18 | Actor[16] | custom objects/enemies |
| +0x158 | Actor[4] | projectiles |

Actor is 20 bytes: s32 x,y,dx in 16.16; u16 hp,timer; u8 active,kind,flash,pad.
First projectile active byte is +0x168. Update memory assertions if this ABI changes.
ROM RoomDef is 200 bytes: u32 room pointer, s32 count, sixteen 12-byte ObjectDef
records. ObjectDef is six s16: kind,x,y,left,right,reward. Reward currently means
flower=1 or coin=0, not a native item identifier. Value changes within that fixed
ABI need no C recompile; layout/address/interpretation changes do.

## Coordinates and graphics ownership

Native entity pixel halves are screen-relative. Add native camera X/Y to obtain
world coordinates. Actor x/y are world top-left; Soma's y is feet. Corridor floor
is world 192, Soma's feet around 191, camera Y around 48. Damage impact coordinates
passed to the native routine are screen-relative fixed-point values.

Custom OBJ tiles use VRAM 0x06012000..0x06012FFF (tile base 256 relative to OBJ
base). A 16x16 sprite in 2D mapping uses tiles t,t+1,t+32,t+33. Palette banks
10..14 go into source buffer 0x02011F1C and native update flags are marked. Direct
writes to the transformed output buffer are not a stable palette integration.
OAM entries 110..127 use eight-byte hardware-format records at 0x03000C58+index*8.
The renderer caps at 18 sprites. This is an isolated-room reservation, not a
complete resource manager. Native enemies, weapons, scenes and menus can compete.
The sanctuary skips companion bank writes to preserve native statue graphics.

## Gameplay boundaries

Contact invokes Thumb 0x08021655 with a four-u32 argument block containing damage/
type and screen-fixed impact X/Y. Weapon overlap checks active native slots 2..16
using approximate rectangles and the host attack stat. Native elemental/defense
and exact weapon/soul geometries are not fully reconstructed. Coins add native
gold with a cap. Enemy death adds EXP but native level-up dispatch remains unverified.
Flower state coexists with equipment slots; no new soul acquisition is implemented.

## Ability milestone D

See [ABILITIES.md](ABILITIES.md) for the implemented native SDK and precise extension contracts. `aria/abilities.py` validates config/RAM/runtime selection; `native/abilities/` owns C modules, guards, ABI, linker and dependency fingerprints; `tests/test_abilities.py` covers contracts; `scripts/verify_abilities.py` verifies native behavior. The SDK uses the existing single hook. Custom mechanics remain trusted native code, with transient RAM and no custom SRAM schema.
