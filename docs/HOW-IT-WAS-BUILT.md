# How the native mashup was accomplished

## 1. Establish exact targets and available tooling

The user supplied an 8 MiB Aria of Sorrow ROM and a 4 MiB Super Mario Advance 2
ROM. Header inspection read title at file 0xA0, game code at 0xAC and revision at
0xBC. Full SHA-256 verification locked every subsequent offset to these copies.
Aria is CASTLEVANIA2/A2CE, revision 0; SMA2 is SUPER MARIOB/AA2E, revision 0.
No original file was patched in place. The builder reads both into memory and
writes a third private output.

Melty search identified custom game slugs, but no dedicated GBA loader/version
configuration or matching existing mashup. The actual integration therefore
had to be built locally before a draft install recipe could be meaningful.

Source references used:
- https://github.com/LagoLunatic/DSVEdit — Aria room structures, free-space and RAM docs.
- https://github.com/KarisaAdvynia/sma2-disasm — exact SMA2 source/layout and hash.
- https://github.com/mgba-emu/mgba — emulator interfaces and native execution.

Local checkouts live under tools/, which is development-only and ignored.
The reverse-engineer-anything skill was consulted. Its REA service was not
available, so the work used source documentation, disassembly and actual emulator
observations instead. Do not describe this as a successful REA analysis session.

## 2. Inventory the host instead of drawing a replacement game

scripts/inspect_roms.py follows the area/sector/room tables and records metadata,
layer sizes and native entities in local/rom-inspection.json. This established
which rooms already contained the original save statue and which corridor
architecture could be reused. The prototype keeps native architecture and
Soma presentation; it does not invent a substitute engine or player sprite.

Sector 0 rooms 31, 29, 28 and 27 were selected as destinations. The sanctuary
keeps room 31's native content. Three crossover rooms copy the layer/graphics
configuration of native corridor 6 and replace its enemy entity list with an
empty terminator. Door records connect the four rooms leftward and back.
This isolation allows known sprite/OAM banks to be reserved without claiming
that the same reservation is safe across the entire original castle.

## 3. Add native code at a documented free-space region

A tiny armips patch replaces eight bytes at virtual address 0x08000500 with a
Thumb trampoline. Its wrapper is at 0x08651200. It preserves the original
return context, reconstructs displaced register setup and lets the original
update run. On its return, it calls custom tick at 0x08660001 (Thumb bit set).
The C code was compiled for arm7tdmi Thumb freestanding with Zig 0.15.2.
The linker fixes its origin at 0x08660000 and removes exception metadata.

This was tested incrementally: first original title/new game, then room entry,
then visible sprites, then interactions, combat, save/reload and clean install.
A plausible hook is insufficient: one early register/pointer assumption was
wrong. The corrected wrapper restores r3=-1 and r0=0x084F0B14 before branching
to 0x08000509. r0 here is a ROM pointer to the game's state-dispatch data; it
is not an arbitrary RAM address. See src/hook.asm for the actual instruction order.

## 4. Identify real companion assets through SMA2 execution

Tile identification combined source layout with real SMA2 VRAM/OAM/palette
observations. Temporary probes and extracted images were kept under local/.
A local SMA2 probe spawned a real Fire Flower using native initialization,
which helped disambiguate dynamic sprite banks. Those probes are investigation
artifacts, not distributable content or build dependencies.

A GBA 4bpp 8x8 tile is 32 bytes. A 16x16 sprite in this game's 2D mapping is
four tiles with indices [t,t+1,t+32,t+33], NOT [t,t+1,t+2,t+3]. This was a key
correction. Koopa's head comes from a separate bank. Flower graphics initially
looked like another enemy because the wrong dynamic bank was being sampled.
The verified flower is at file offsets 0x188714, 0x188734, 0x188B14, 0x188B34.
The actual 8x8 fireball is at 0x1887F4.

Block and coin graphics are original BG tiles, copied into OBJ slots for the
custom actor renderer. Their palette was reconstructed from observed native
colors mapped back to original ROM color words. An animated white was replaced
with the original ROM's white rather than distributing an extracted palette.
The builder stores offsets and extracts only on the player's machine.

## 5. Integrate with host state rather than replacing it

Soma's movement and weapon entities remain original. Enemy overlap checks
inspect host weapon/soul entity slots, and use the host attack stat as damage.
Enemy contact calls the native damage/hurt routine, instead of merely reducing
an HP counter. Coins increment native gold. Enemy deaths increment native EXP,
but the native level-up pathway has NOT been verified and remains a known gap.

Custom enemies have their own small fixed-capacity actor array. A Goomba patrols;
a Koopa patrols, temporarily enters a shell after a surviving hit, then recovers.
These are newly implemented behaviors, not full ports of the SMA2 engine.
The flower is a timer alongside existing equipment/soul slots. Up+attack creates
a straight projectile without consuming MP. Room changes retain the timer and
clear projectiles; death or leaving gameplay clears the flower. Custom actors
and pickups repopulate on room re-entry and are not written into host SRAM.

## 6. Correct the rendering pipeline

Native OBJ data is uploaded to VRAM 0x06012000. Palette colors must go into
source palette buffer 0x02011F1C and mark native palette update flags. Writing
only the transformed output buffer made colors unstable/wrong. OAM entries
110..127 are written through the native hardware-format buffer at 0x03000C58.
An earlier 0x03000058 assumption was wrong: that address is a different internal
renderer structure, not the eight-byte OAM list.

The sanctuary skips companion bank writes so its original statue/enemies do
not inherit Mario palettes or graphics. This reservation is specific to the
isolated corridors; adding native enemies requires a new graphics-bank audit.

## 7. Fix save data by rebuilding the map as well as doors

The first apparent save succeeded, but reloading entered a black screen with
an invalid room pointer. Native save-sector/room IDs are derived from castle
map lookup tables. Moving rooms and doors without updating those tables made
saved room IDs invalid. The builder now rebuilds the isolated slice's tile
metadata and line nibbles, including the sanctuary save marker. A native save
roundtrip with a controlled gold=123 fixture reloads room 31 and gold correctly.

This is the most important lesson for future room work: doors, world-map
coordinates, room metadata, save lookups and native geometry form one contract.
A valid transition is not proof that saving is safe.

## 8. Test actual code and package only distributable inputs

A ctypes libretro harness supplies real controller inputs to mGBA, captures
240x160 frames and exposes core memory mappings for assertions. It handles the
experimental flag on environment commands by masking to 16 bits. Keeping ctypes
callbacks and ROM buffers alive is necessary to avoid crashes.

scripts/verify.py checks startup, travel, damage, flower spawn/collection/fire,
Goomba death/EXP, Koopa shell, expiry, equipment-slot preservation, death reset,
return route and native save roundtrip. It explicitly records its RAM fixtures.
It does not claim a complete soul/equipment matrix or a full campaign test.

The allowlist packager includes original code/data, precompiled original runtime,
Python 3.14.0 embed, mGBA 0.10.5 and their notices. Commercial ROMs, private builds,
extracted graphics and saves are excluded. A clean extraction rebuilt the same
private ROM hash using the bundled Python and started bundled mGBA.

## 9. Prepare a truthful Melty draft

The actual recipe validator exposed a richer ownCopies object format than the
MCP argument summary suggested. Validation diagnostics established game, rom
extensions/as, and a managed destination folder. Each required game is declared
ownCopy=true. Melty stages base.gba for both, installs app/ under {managed}/app,
and passes the two managed paths to Launch.cmd. No file picker is needed when
those supplied paths exist and hashes match. The static check passes all 77
mapped package files. Real client execution remains untested.

The listing is an MIT/remix-enabled development draft. Uploading the ROM-free
archive was blocked by automatic approval review pending explicit user consent
to that payload/destination. No release was submitted, and nothing published.
The user's later documentation request is not permission to retry the upload.


## Existing-room milestone (2026-10-10)

See [ROOM-DESIGN.md](ROOM-DESIGN.md) for sparse entity moves, paired existing doors, map/save diagnostics, commands, test evidence and extension guidance. `aria/level.py` implements this layer; `examples/room-workshop/mod.json` is its runnable example. Geometry/collision editing, map relocation and campaign-wide graph repair remain unimplemented.

## Building the equipment semantic layer

DSVEdit item-format notes distinguish signed stat bonuses from unsigned bytes. Native Dainslef CON/INT 254 and Skull Necklace LCK 255 confirmed why unsigned-only inspection was misleading. The new layer keeps raw table compatibility and provides signed views/edits. Native item-name pointers yield exact selectors locally, avoiding a shipped extracted name bank. Catalog enumeration established all 104 identities; flag edits preserve unknown bits. New-game baseline/mod comparisons established the runtime bonuses. Cape ownership is an explicit test fixture; the native menu performs equip and stat recomputation. A save-route fixture composes the existing paired-door API to test persistence. The first traversal attempt released Right during jumping and stalled at a hallway obstacle; holding Right through jump/attack follows the working room test. No ROM patch was needed for that input-harness correction. See EQUIPMENT.md and scripts/verify_equipment.py.

## Building the enemy semantic layer

The copied DSVEdit DNA format established one-based item drop IDs and separate soul/item rarity behavior. Native names were read from the original text pointer bank rather than shipping a full extracted list; equipment now shares the bounded reader. The first hallway record proved to be a Zombie spawner (var_a=2, var_b=1), not a single actor. Movement preserves its parameters; cloning rejects it. Clone templates are restricted to original single Bat/Zombie/Skeleton actors in the same room, with a conservative two-addition limit. Encounter and room edits share staged arrays to avoid pointer-patch conflicts.

Native observation showed the spawner itself can have zero ATK/DEF while its children use the edited DNA stats. The verifier was corrected to observe both over time rather than assume immediate child initialization. Controller combat collected an actual edited Potion and EXP rewards without RAM/seed fixtures. A paired hallway shortcut reached the cloned Skeleton encounter and returned; original map banks remain intact. The original room, equipment and callback verifiers passed after the shared-module changes. See ENEMIES.md for exact limits and extension guidance.

## Ability milestone D

See [ABILITIES.md](ABILITIES.md) for the implemented native SDK and precise extension contracts. `aria/abilities.py` validates config/RAM/runtime selection; `native/abilities/` owns C modules, guards, ABI, linker and dependency fingerprints; `tests/test_abilities.py` covers contracts; `scripts/verify_abilities.py` verifies native behavior. The SDK uses the existing single hook. Custom mechanics remain trusted native code, with transient RAM and no custom SRAM schema.
