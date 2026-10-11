# Tactical Soul Framework verification after folder split

Eight synthetic safety-contract tests passed using this folder. Both examples
rebuilt using this folder's bundled Python; frame-counter recompiled with its
own copied Zig and preserved output SHA-256. Actual mGBA emulation passed:

- native enemy/weapon/soul fields patched at expected records
- native-balance boots original title, enters gameplay, and accepts movement
- host-only frame callback executes once per native frame
- frame-counter boots original title, enters gameplay, and accepts movement
- native room entity relocation preserves all original records
- commercial original remains unchanged

Native-balance ROM SHA-256: `0b5d72804608fddfdaffc801e1493e0f8c38a9ab319722f434b7935b1944d7b9`.
Frame-counter ROM SHA-256: `dbbc9cf5f9d71cabdad8ace071de325b30ce058903080f1ffac6c43e86a72ee0`.

Its copied mGBA executable started successfully with the local output ROM in a
hidden launch smoke check, then the test closed only its own process. This is
not exhaustive GUI/hardware certification.

Limits: record edits verified structurally; not every edited field exercised in gameplay; native room relocation checked structurally, not a complete room graphics/transition test; full campaign, save compatibility and hardware not certified.

## Ability milestone D

See [ABILITIES.md](ABILITIES.md) for the implemented native SDK and precise extension contracts. `aria/abilities.py` validates config/RAM/runtime selection; `native/abilities/` owns C modules, guards, ABI, linker and dependency fingerprints; `tests/test_abilities.py` covers contracts; `scripts/verify_abilities.py` verifies native behavior. The SDK uses the existing single hook. Custom mechanics remain trusted native code, with transient RAM and no custom SRAM schema.
