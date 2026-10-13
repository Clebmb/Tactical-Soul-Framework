# Ownership barrier composed with the ability SDK

```powershell
TacticalSoul.cmd play examples/soul-gate-abilities/mod.json
TacticalSoul.cmd build examples/soul-gate-abilities/mod.json --compile
python scripts/verify_soul_gate.py --composed
```

This separate example uses the existing `abilities.runtime` extension contract
to combine the [room14 barrier](../soul-gate/README.md) with standard stationary
regeneration and R focus healing behind **one** frame hook. It starts unowned
at the statue and supplies no unlock route. The invisible west barrier is a
blocking demonstration, not a finished mini-campaign. Healing uses the SDK's
usual HP/MP/interval/cooldown settings; native R input is not consumed.

The custom `runtime/` contains original SDK source/header copies plus `gate.h`.
The barrier runs before the SDK healing guard and follows its own tested state
whitelist (0/1). Thus attacks still meet the barrier while SDK reason 6 blocks
healing. The barrier also rejects camera X outside -256..256 before fixed-point
multiplication. Built-in ABI 1, the 40-byte config and the dispatcher/regen/focus
RAM claims remain unchanged. No additional custom RAM or save data is used.

Selecting this **custom runtime always installs the fixed barrier**, independent
of which healing features are enabled. It is not a registered configurable SDK
feature or a general gate manifest API. The built-in runtime and standalone
gate example are unchanged. If extending this copy, synchronize/review SDK
upgrades explicitly; it does not automatically inherit later built-in changes.
The compiler fingerprints runtime source, linker, SDK headers, build descriptor,
gate header and binary. Source/header edits require `--compile`; player builds
use the precompiled original binary.

Native acceptance covers unowned walking, actual jump/attack, pause/resume with
frozen focus cooldown, statue save and fresh continue with continued blocking;
owned opening acquisition, redirected entrance, save/continue and the original
west exit with matching authored policy. A separately disclosed **HP-only deficit
write** verifies regeneration +1 after 120 eligible frames and R healing +5 HP
for 3 MP. Ownership, position, velocity and input RAM are not injected. Saved
SRAM is transported to fresh cores. Evidence remains in
`local/soul-gate-abilities-verification.json`; original ROM stays unchanged.

The barrier's prior limitations still apply: empty room14 only, no visible art,
states outside0/1 skipped, no hurt/transform/scripted-transition or arbitrary-speed
certification. This composition does not solve after-update transition bypasses
or add new write/start registrations, native grants or a save schema.
