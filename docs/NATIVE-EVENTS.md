# Native event and progression observations

`aria/native_events.py:observe_native_events(read)` samples registered USA-r0
RAM fields through a caller-supplied `read(address, byte_count)` function.
Pause the emulator while sampling: sequential reads are not atomic against a
running core. The caller must establish the exact supported host; this function
cannot identify a ROM from a memory reader. Invalid unsigned field values fail.
It performs no writes and makes no changes to native code or save formats.

The result retains raw game state, substate, room pointer, player state and the
32-bit word at `0x0200042C`. `modal_lock_bit` reports only mask `1` of that word.
The name describes the observed behavior, not an exclusive native meaning.
The existing native ability guard in `native/abilities/dominance.h` blocks on
this same bit. Other producers and other bits remain unknown.

## Native evidence

Run `python scripts/verify_native_events.py` with local development tools and the
private exact host. It builds a separate probe under `local/native-events/`
using the existing verified room `(0,14)` new-game start. Controller input alone
produces these observations:

| Checkpoint | Bit 0 |
| --- | --- |
| Settled fresh gameplay | clear |
| Statue prompt opened with Up | set |
| Prompt cancelled with B | clear |
| Statue prompt reopened | set |
| Native Yes/save completed | clear |
| Fresh-instance continue from saved SRAM | clear |

Saving changes SRAM; fresh continue restores the same room with positive HP.
SRAM is copied to the fresh emulator for that check; no position, HP or event
RAM is injected. The verifier checks the original ROM remains byte-identical.
Private raw observations are in `local/native-events-verification.json`.
This is local mGBA evidence, not REA/decompiler evidence. The REA session check
reported no open target; the prior GBA unsupported finding remains in force.
No provider installation or host configuration changes were made.

## Limits and next binding

This is a transient UI lock, **not a persistent unlock or room-entry grant**.
Do not feed it into the monotone inventory in [progression policies](PROGRESSION-POLICIES.md).
One statue/start lifecycle does not certify other events, death, scripted
teleports or all prompt consumers. Next establish a persistent native event or
ability flag, its acquisition and save/continue behavior, before connecting a
declared progression policy to native gameplay enforcement.

## First persistent ownership observation

`observe_progression_flags(read)` now exposes `flags.first_red_soul_owned` and
the low-nibble count/raw byte at `0x0201331C`. This is deliberately one slot,
not a generic inventory decoder or a grant function. It requires state 4,
substate 1 and an aligned original-ROM-range room pointer; other contexts fail
rather than reporting a false unowned flag. Callers must establish the exact
host and pause the emulator. It reads only, with no automatic policy integration.

Local reference provenance: DSVEdit `docs/AoS RAM Map.txt` describes the owned
red-soul region `0x0201331C..0x02013337`, two counts per byte; its
`docs/asm/AoS Functions.txt` describes `GetNumOwnedSoul` at `0x080326B8` with
an index-minus-one argument. These are reference claims, not recovered ABI proof.
The native check below establishes the first low nibble only. Other soul types,
adjacent nibbles, duplicate counts, menu identity and ability effects remain
unverified by this check. No reference files or extracted assets are released.

Run `python scripts/verify_soul_progression.py` with local development tools.
It retains the native opening sequence and observes exactly one byte transition
from 0 to 1, then walks through a diagnostic entrance-door redirect into the
existing room `(0,14)`. Controller input opens the native statue prompt and
saves; SRAM changes. A fresh core continues in that room with positive HP and
the first red-soul count still 1. No position, inventory or event RAM is written;
only saved SRAM is transported into the fresh core. The exact original remains
unchanged. Probe ROM/report stay in `local/soul-progression/` and
`local/soul-progression-verification.json`.

This establishes an observed persistent ownership predicate. It does not prove
that counts can never decrease, enforce an authored gate, certify the original
campaign route, or establish a callable soul-grant ABI. The probe explicitly
changes one door; its observed left-edge landing is followed by input-only
movement to the statue. It does not expand room/start write registrations.
Earlier private relocated ability-pickup probes showed no acquisition change;
no pickup writer or binding was registered from those negative trials.

The verifier now compares this flag on its bounded native route with an authored
policy; see [progression traces](PROGRESSION-TRACES.md). Native gate enforcement
and broader soul effect evidence remain required before broader grants.

## First-slot identity and native menu/use proof

`python scripts/verify_soul_menu.py` now attributes the first owned red-soul
nibble to **Winged Skeleton**, native equipped red-soul ID 1, `red_souls` record
index 1 and text ID `0xE3`. `observe_progression_flags` includes those identity
fields in `first_red_soul`; its existing flag key and read contract are unchanged.
Record 0 is the empty record, so ownership nibble 0 does not imply record index 0.

Three fresh native runs retain the original opening and use controller input
to open Start → Soul Set. Two original controls must produce identical RGB pixels.
A private diagnostic changes only the characters of text `0xE3` from
`Winged Skeleton` to a padded `First Red Soul`, preserving length and terminator.
Exactly 314 pixels change, 157 in each of the equipped-name and selectable-name
regions: `(40,20)..(130,40)` and `(132,76)..(235,92)`, half-open coordinates.
No differences occur elsewhere. Visual inspection of the original screen shows
Winged Skeleton and quantity 1; RAM independently reports ownership byte 1 and
equipped ID 1. This ties the menu label and slot together without inventory writes.

After closing the menu with B twice, native Up+B spends exactly 12 MP, matching
`red_souls[1].mana_cost`, in all three runs. HP, ownership and equipped ID remain
unchanged. This establishes a narrow native-use/resource-cost observation, not
projectile rendering, damage, collision or all soul effects. No game RAM, SRAM,
position or input buffers are injected. The original ROM remains byte-identical.

Private screenshots, diagnostic ROM and JSON report stay under `local/soul-menu/`
and `local/soul-menu-verification.json`. Source releases include the verifier only.
This is local mGBA execution and private pixel attribution, not REA/decompiler
evidence. No production soul-label writer or callable grant ABI is introduced.
Other souls, adjacent nibbles, duplicate counts, menu rearrangement and arbitrary
soul reassignment remain pending. Next extend a verified identity/effect path
before generic inventory/grant authoring, or resume audio capture/comparison.
