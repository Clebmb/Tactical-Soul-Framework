# Native ability framework

Tactical Soul Framework's ability SDK composes registered native features behind the existing single after-update Thumb hook. It provides input edges, a conservative playable-state gate, explicit per-feature RAM, native HP/MP helpers, lifecycle reset handling, JSON configuration and header-aware binary fingerprints. It is a working foundation for custom mechanics, not a generic native call/signature discovery system or a finished soul/item scripting language.

## Play and configure

From the independent Tactical Soul Framework folder:

```powershell
.\TacticalSoul.cmd play examples/ability-workshop/mod.json
.\TacticalSoul.cmd inspect --mod examples/ability-workshop/mod.json
.\TacticalSoul.cmd play examples/still-regen/mod.json
.\TacticalSoul.cmd play examples/focus-heal/mod.json
```

The combined workshop includes both examples. Still regeneration heals 1 HP after 120 eligible stationary frames. Focus healing uses an R **press**, heals 5 HP, spends 3 MP, and starts a 180-eligible-frame cooldown. HP is capped at the native maximum; full HP or insufficient MP prevents MP spending. Native stats/equipment/souls are not replaced. There is no custom visual effect or item/soul unlock requirement. Single-feature examples demonstrate independent enablement of the same runtime modules.

The current active binding is the native R button, not a configurable keybinding API. The callback runs after the host has already processed input: it does not consume R. If a guardian soul is equipped, native R behavior can also run and spend MP. Test desired guardian combinations or implement an independently verified input arbitration hook before promising exclusive bindings. Default new-game tests use the original empty guardian slot. Button remapping and a generic input interception layer are extension work.

A version-1 manifest can contain:

```json
{
  "schema_version":1,
  "id":"my-abilities",
  "abilities": {
    "features": [
      {"id":"still_regen","interval":120,"amount":1},
      {"id":"focus_heal","amount":5,"mana_cost":3,"cooldown":180}
    ]
  }
}
```

Parameters are integer values or 0x-prefixed strings; booleans fail. Amounts and mana_cost range 1..999. Interval/cooldown range 1..36000. Omitted parameters use the shown defaults. The feature list must be nonempty; unknown/duplicate IDs or parameters fail. List order does not control execution order: the SDK registry runs focus first, then passive regeneration, refreshing the native HP/MP snapshot between modules to avoid lost writes. A disabled feature never ticks, but both compiled feature state blocks remain reserved and reset by the dispatcher.

JSON-only changes need no compilation. Native runtime code, headers, linker or build descriptor edits require:

```powershell
.\TacticalSoul.cmd build examples/ability-workshop/mod.json --compile
```

Player builds use bundled Python and fingerprint-verified precompiled runtime.bin, with no compiler requirement. Zig 0.15.2 is the documented development compiler. The local sandbox may prevent Zig resolving its own executable path; the development session compiled successfully through the authorized tool escalation. That is an environment limitation, not a reason to weaken fingerprints or ROM version verification.

## One hook and deterministic dispatch

`abilities` owns the existing frame hook and is mutually exclusive with `frame_hook`. Install it before other allocations so its binary occupies 0x08680000. The original wrapper/entry trampoline remains authoritative; abilities do not add another detour or stack patched ROMs. Table, equipment, enemy and room edits can compose in the same manifest under their existing rules. Reports include the ability ABI, enabled features, configuration tag/address, RAM claims and runtime SHA-256.

`native/abilities/runtime.c` defines a const Feature registry: mask, RAM pointer, word count, tick callback. Registration order is execution order. All callbacks run only after the shared guard passes and receive a stack-local Context. The dispatcher samples native held buttons each hook and computes pressed/released edges from its own previous sample. Inactive frames still update the previous sample; room entry/resume suppresses a synthetic edge for an already-held button. The SDK does not rewrite native input buffers.

Mutable state lives only in declared RAM. C has no startup, allocator, libc or initialized global runtime. The linker rejects .data/.bss, preventing accidental mutable globals from landing in ROM or silently lacking initialization. Const registry/configuration data is permitted in ROM. ARM7TDMI Thumb ABI, return discipline and bounded stack usage still apply. Do not call native item/soul/EXP routines without independently established ABI evidence.

## State checks and lifecycle

Before feature dispatch, the SDK requires config magic/version, native game state 4, substate 1, Soma mode byte 0, HP above zero, native player state byte 0, a plausible ROM room pointer, nonzero max HP, HP not above max, MP not above max, and global flag bit 0 at 0x0200042C clear. Native player state zero was observed during ordinary idle/movement/jump; attack state 1 and original scripted entrance state 17 are deliberately blocked. This conservative whitelist skips hurt, attacks, transformations and events it has not certified, even if some would be safe. Do not expand it by guessing numeric states. The native save prompt was observed setting global flag bit 0 while gameplay/player states stayed unchanged; reason 9 blocks this flag. Broader semantics of this bit remain unproven. Room ownership resets even on blocked transition frames.

Stationary regeneration additionally requires zero native X/Y velocity, no directional input, and HP below maximum. Movement, jumping, full HP and blocked scenes reset its progress; time spent paused does not accumulate a deferred heal. Focus cooldown advances only during eligible frames, so pausing or excluded player states freezes it.

Room changes reset both modules' timers and diagnostic event counters. Death/non-gameplay resets transient feature state and room ownership. Title frames continue the dispatcher counter without enabling gameplay. Pause blocks writes to HP/MP and freezes cooldown, while discarding passive progress. Native save dialogs are tested as blocked. On continue in a fresh emulator, the runtime reinitializes from its magic/version/config tag rather than restoring custom timers from SRAM.

HP/MP changes themselves are ordinary native character state and follow native saves. Only custom timers/counters are transient; this is not a claim that healing effects disappear when saved. There is no new save schema, custom SRAM allocation or migration. Full campaign/ending/alternate-character/transformation coverage is not certified. The RAM reservation has passed the listed scenes, not a complete global engine audit.

## ROM configuration ABI

The exact profile defines the runtime origin and fixed config at 0x0867F000, inside the documented original free-space region and before the allocation arena. The builder checks expected original bytes and logs the config write. Version 1 is ten little-endian u32 words (40 bytes):

| Offset | Meaning |
|---:|---|
| 0 | magic 0x444D4346 |
| 4 | ABI version 1 |
| 8 | feature mask: regen=1, focus=2 |
| 12 | deterministic configuration tag |
| 16 | regeneration interval |
| 20 | regeneration amount |
| 24 | focus input mask 0x100 (hardware R) |
| 28 | focus healing amount |
| 32 | focus MP cost |
| 36 | focus cooldown |

The tag is the first four SHA-256 bytes interpreted little-endian over the packed config with its tag word zero. It detects changed settings in owned RAM; it is not a signature or code-authenticity check. Code ABI/layout changes require a coordinated version bump in Python, profile and C. The builder rejects a profile ABI/address layout different from the compiled SDK contract. Native binary/source integrity is tracked separately by fingerprints.

## RAM ownership ABI

Declared arena is 0x0203D000..0x0203D400 (half-open). This output cannot be stacked with the old frame-counter or Mario callback; those use overlapping concepts/RAM and the same frame entry. Three fixed claims are always reserved:

| Range | Owner |
|---|---|
| 0x0203D000..0x0203D040 | dispatcher header, 64 bytes |
| 0x0203D040..0x0203D050 | still_regen, 16 bytes |
| 0x0203D050..0x0203D060 | focus_heal, 16 bytes |

All header fields are u32: +0 magic 0x444D4142; +4 ABI; +8 config tag; +12 room pointer; +16 hook ticks; +20 eligible frame count; +24 feature reset count; +28 active flag; +32 previous held buttons; +36 block reason; +40..63 reserved. Regen block: +0 timer, +4 event count, +8..15 reserved. Focus block: +0 cooldown, +4 event count, +8..15 reserved. Initialization clears these three claims explicitly. Diagnostic counters are transient and can reset; do not use them as a persistent progression system.

Block reasons: 0 eligible, 1 config mismatch, 2 non-gameplay, 3 native substate/menu, 4 non-Soma mode, 5 zero HP, 6 excluded player state, 7 invalid room pointer, 8 invalid stats. Reasons are checked in that order, so a game-over screen may report non-gameplay rather than zero HP.

`abilities.ram_claims` can declare additional aligned four-byte ranges for custom native modules, with exact `id`, `start`, `size`. Claims must be positive, inside the arena, nonoverlapping and uniquely named. For example:

```json
"ram_claims":[{"id":"my-dash-state","start":"0x0203D060","size":16}]
```

A claim does not implement a feature, allocate native engine memory, initialize arbitrary extension state or sandbox C. Custom modules must initialize/clear their own claimed bytes and update reset ownership appropriately. Build validation catches declared overlaps; trusted native code can still write outside its claims if implemented incorrectly. Do not treat boundary canary tests as universal memory safety.

## Native addresses and input helpers

`dominance.h` centralizes these observed addresses: native held buttons 0x02000014; state 0x02000010; menu/transition substate 0x02000064; room pointer 0x02000088; player state 0x020004EE; fixed-point velocities 0x0200052C/0x02000530; Soma/Julius mode 0x02013266; HP/MP/max HP/max MP 0x0201327A/7C/7E/80. Reads are volatile. Context carries held/pressed/released, room, signed velocities and current native stats. Helpers clamp healing to max HP and clear explicit state words. This is an observed exact-version SDK, not a cross-region address resolver.

Hardware R=0x100 differs from libretro R ID 11. Do not copy controller IDs into C button masks. Native player state is distinct from the top-level state and from room substate; state=4 alone did not prove control during the original entrance dialogue.

## Extending with a custom runtime

To customize these modules without affecting other mods, copy the entire `native/abilities` folder into your mod folder as `runtime`, and add `"runtime":"runtime"` to the `abilities` object. Its paths must remain within that manifest folder. Keep build.json, source, headers, linker, binary and fingerprint together. Run that mod with --compile after source changes. The shipped examples use the shared default SDK; editing it affects every future default-SDK build and requires compilation.

`build.json` must declare source, linker, file, fingerprint, linked_address and dependencies. The SDK requires dominance.h, features.h and build.json to be fingerprinted. Add every additional local header/source fragment included by runtime.c to dependencies. The compiler checks declared dependency hashes before reusing a binary. It does not automatically crawl all transitive includes or hash the entire toolchain; undeclared includes remain the author's responsibility. Existing frame_hook manifests without dependencies keep their prior source/linker/binary fingerprint behavior.

To add a new built-in ID, define its validated settings and config ABI in aria/abilities.py, register its native tick module and RAM claim/reset policy, update the profile/version when layout changes, and add both contract and native tests. There is intentionally no arbitrary C-expression or dynamic code loader in JSON. A custom runtime can adapt the current two modules under this ABI; unrelated new feature IDs require explicit planner/config/registry work rather than pretending a JSON name implements code.

Future work includes richer lifecycle callbacks, independently packaged module registration, verified input interception/remapping, native sprite/resource services, item/soul/EXP grants and custom persistence. Each needs concrete native evidence. Preserve one dispatcher, disjoint state ownership, conservative gates and repeatable examples while expanding it.

## Verification and file map

Run `python -m unittest discover -s tests`, then `python scripts/verify_abilities.py`. Native verification needs the private exact original, a Python with Pillow, and the local mGBA libretro DLL. It checks title/dialogue gating, one callback per frame, regeneration timing, R edge/cooldown/MP/cap behavior, pause/resume, movement, equipment preservation, boundary canaries, natural transition, death, native save dialog and continue. Controlled HP/MP, passive timer start, death and boundary fixtures plus an existing paired-door save-route fixture are explicitly listed in the result report. They are not a natural campaign playthrough.

Current evidence is local/ability-verification.json and actual emulator frames. These private artifacts and generated ROMs are excluded from the source archive. The shared compiler/CLI changes also require original frame-counter/table, room, equipment and enemy regressions. Exact output hashes belong to measured builds, not hardcoded success claims for future changes.

| File | Responsibility |
|---|---|
| aria/abilities.py | feature config validation, fixed ABI, RAM claims, runtime selection/install and report |
| aria/compiler.py | optional Zig compile; source/linker/binary/declared dependency fingerprints |
| native/abilities/build.json | shared SDK build descriptor and dependency list |
| native/abilities/dominance.h | native addresses, Context, guards, fixed ROM/RAM ABI and helpers |
| native/abilities/features.h | two reusable native tick modules |
| native/abilities/runtime.c | const feature registry, initialization, input edges, lifecycle and dispatch |
| native/abilities/link.ld | fixed origin, text/rodata, .data/.bss rejection |
| native/abilities/runtime.bin / runtime.build.json | original precompiled callback and fingerprints |
| examples/ability-workshop | combined-feature JSON example |
| examples/still-regen / focus-heal | independent feature-mask examples |
| tests/test_abilities.py | no-ROM config/RAM/ABI and dependency contracts |
| scripts/verify_abilities.py | native scene/lifecycle evidence with declared fixtures |

## Verified build evidence

2026-10-10: 63 unit tests passed; 13 native ability checks passed. The existing equipment (7), enemy (8), room (5), and hook/framework (6) native checks also passed after the shared compiler/CLI changes. Callback: 772 bytes. Ability workshop ROM SHA-256: `84bf29b19d7838101edfff83fe2f3f887db50d49395c09aae5abe5b760ffe2ff`. Native evidence is local/ability-verification.json; frames are local/ability-workshop-active.png and local/ability-workshop-continue.png. Private native-test DLL and Zig are local tools, excluded from distribution; precompiled JSON builds and bundled mGBA launching require neither.

## Fixed ownership-barrier composition example

[Gate plus healing](../examples/soul-gate-abilities/README.md) demonstrates the existing custom runtime contract with the room14 barrier before the healing guard. Built-in ABI/config/RAM claims are unchanged; the fixed custom barrier is always enabled by this runtime and is not a general registered gate feature. Native tests disclose an HP-deficit fixture for healing; gate ownership/position are never injected.

## Tear-style projectile soul request

The existing SDK does not implement tear projectiles or gameplay SFX dispatch.
See [custom projectile ability boundary](CUSTOM-PROJECTILE-ABILITIES.md) for
current foundations, missing APIs and native acceptance criteria.
