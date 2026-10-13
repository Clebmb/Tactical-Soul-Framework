# Boot melody scene-transition evidence

`python scripts/verify_music_lifecycle.py` verifies the registered imported
boot instrument through controller-only title/menu/new-game and pause/resume.
It authors an8000Hz triangle melody with tempo30 and8 finite passes, long
enough to remain active through the initial menu inputs. The diagnostic ROM
stays in `local/audio/music-lifecycle.gba`; no new playback slot is registered.

Three fresh-core runs compare the exact original, the authored build, and
an authored repeat. All11 checkpoints match on image SHA256, game/substate,
room pointer (`0x02000088`), HP/MP, ownership, sample count and core timing.
Each checkpoint records30 native frames of audio. The two authored runs
match completely. At frame1000 and1131 the authored header is selected and
audio differs from the original, as intended. At menu checkpoint1/frame1262,
the native header changes from allocated `0x086800D0` to `0x083F7EDC`.
A separate passive no-input authored core at that same frame still selects
the authored header and emits nonzero audio. This distinguishes scene-driven
takeover from natural melody completion; it is not an exact transition-frame
trace or a callable stop ABI.

From menu checkpoint1 onward, every captured audio window is byte-identical
to the original, including later menus, native opening/gameplay, pause and
resume. Gameplay selects `0x0848392C`; pause substate6 and resume substate1
are explicitly checked. Gameplay checkpoint is frame7407, pause7468 and
resume7529. Native acquisition leaves first-red ownership1, as in the baseline.
The test uses the previously verified native opening menu/input sequence,
including60 A-button/wait cycles. No game RAM, SRAM or position fixtures.
The original ROM remains unchanged.

Private evidence: `local/audio/music-lifecycle-report.json`. Full suite426
tests pass (`local/music-lifecycle-tests.log`). REA unsupported-GBA boundary
remains; these are mGBA observations. No new C/native code or authoring ABI.
Broad simultaneous SFX/channel stress, room changes, death, save/continue,
other assets and physical hardware/human listening remain unverified. Equal
sample windows are narrow regression evidence, not all-frame audio equality
or universal lifecycle safety. Source-project melody composition now has singleton ownership and asset
fingerprints; expand playback slots only with their own native evidence.

## Two-track authored-envelope follow-up (2026-10-12)

`python scripts/verify_arrangement_lifecycle.py` now repeats the controller-only
route with two generated-sine tracks, tempo30,8 passes, volume24 and authored
attack16/decay240/sustain180/release160. Original/custom/custom-repeat runs
match all11 checkpoint state/image/timing fields; custom repeats match fully.
Nine post-takeover audio/header checkpoints equal the original, including
gameplay, pause and resume. This extends the selected route to this arrangement,
not every multitrack/instrument/envelope combination.

A separate101-frame Start-button input/passive comparison begins at frame1030
with music and volume0 controls. The boot header remains unchanged. Muted input
and muted passive are both silent: no isolated native sound was observed.
Music input-minus-passive has peak384 relative to that zero isolated delta.
The verifier retains this measured residual instead of asserting SFX linearity.
Cause remains unresolved; no menu-SFX or gameplay-SFX coexistence certification.
Do not present successful lifecycle assertions as a successful sound probe.

Private evidence: local/audio/arrangement-lifecycle-report.json and
local/arrangement-lifecycle-final.log. No game RAM/input/SRAM fixtures or native
code changes. Full suite462 tests. Next prioritize the requested tear-style
soul's actual projectile/SFX bindings; see CUSTOM-PROJECTILE-ABILITIES.md.
