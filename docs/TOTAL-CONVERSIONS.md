# Toward full Aria total conversions

A total conversion is a plausible long-term engineering goal for Tactical Soul Framework, not a capability unlocked by labeling a manifest. Current tools change actual Aria records, selected encounter placements and existing door connections, compose guarded native mechanics, and replace verified icon resources. They do not yet author an arbitrary new castle, character animation system or soundtrack.

This plan tells future agents what to establish and how to prove progress. Keep each milestone independently playable. Preserve exact original input and isolated outputs, maintain agent documentation, and publish only specifically approved redistributable artifacts.

## What works now

* Named enemy/equipment balance, ordinary drops and selected flags, with original native identities/AI/resources.
* Existing-room moves, restricted same-room clones and paired existing door connections, with map/save audits.
* One native after-update dispatcher, explicit RAM claims, input edges, conservative state guards, transient lifecycle and sample healing abilities.
* Asset codecs, checked generic bindings, all three named item-icon pages/shared palette, sparse edits, lossless local export, diff and previews.
* Independent build/play commands, hook/compiler fingerprints, actual mGBA regressions and allowlist packaging.

Use these for challenge mods, item reskins, encounter remixes and small mechanical prototypes. They can contribute to a future conversion, but they do not remove the dependencies below.

## Recommended next implementation: one room's graphics and collision

This is the highest-value next step toward a new campaign. Start with a bounded existing non-event room and preserve its identity, doors and native save mapping. Establish its layer records, dimensions, resource lists, tile/metatile definitions, compression and collision representation. Keep original actors/resources stable while testing geometry.

First deliver a read-only room-resource inspector and lossless export/rebuild. Prove byte equivalence where the format is canonical, or semantic equivalence where serialization has multiple valid encodings. Do not change the room until its current geometry can be described and reproduced.

Then create an original tiny tileset and modify one walkable feature. Prove actual collision with controller movement, jumping, landing and wall checks; visual resemblance is insufficient. Test camera bounds, reentry, death and save/continue. The Mario project's historical visual prototypes are context, not a dependency or a verified general collision API.

Acceptance: exact original unchanged; no missing graphics on entry/reentry; original event/door identities intact; both routes traversable; native save reloads correct room/position; original art provenance documented; source and rebuild steps agent-readable. Keep the first new geometry scene small.

## Sprite, enemy and weapon resource graph

Before arbitrary custom actors, establish resource headers/load lists, compression, tile size/order, palette banks, OAM limits, frame parts, animation commands, collision/hitboxes and native creator/update contracts. These relationships form a resource graph; changing a graphics pointer is not enough.

Start with one existing ordinary actor reskin while preserving its animation/AI. Test idle, motion, attack, damage, death, simultaneous instances, room reentry and coexistence with existing actors. Only then add new frame layouts or animation behavior. Player graphics may stream/swap dynamically and require separate investigation; do not extrapolate the static item-icon layout to Soma.

Acceptance: stable frame indexing and palette ownership, no VRAM/OAM corruption, documented sharing/limits, deterministic rebuild, real native motion/combat evidence. Add named catalog targets only when their consumers and bounds are proven.

## Native audio integration

Current WAV import is signed PCM preparation only. Establish Aria's actual sound driver, sample/header structures, instrument/voice tables, sequences, loop/rate semantics, playback API and channel ownership. Do not assume an m4a layout or write hardware sound registers directly from the frame hook.

First make one original short effect play through a verified native path while existing music continues. Add emulator audio capture to regression infrastructure; prove nonzero expected audio, onset/duration, repeated triggering and coexistence. Then test pause, room changes, save/reload and death. Instrument and music authoring follow only after a sample binding works.

Acceptance: original audible fixture, exact driver ABI/source evidence, bounded allocation, channel/resource cleanup, documented timing and native audio regression. Imported bytes without a consumer are not playback.

## Mechanics, native grants and progression

The frame dispatcher is useful for prototypes, but EXP, level-ups, inventory/soul grants and damage effects need their native lifecycle APIs. Establish call arguments, side effects, caller states and persistence. A frame callback signature is not an enemy or item handler signature.

Start with one verified grant and native UI/stat refresh; test duplicate ownership, caps, death and save/continue. Add reusable API helpers only after real evidence. Then expose mechanics through validated config and original modules with explicit RAM/state ownership.

Acceptance: native state remains coherent, original save semantics hold, no arbitrary unverified call signatures, lifecycle tests cover entry/exit/blocked states. Persistent custom progression needs a versioned save schema and migration plan; transient counters are not a substitute.

## Castle graph, events and save compiler

A new campaign couples rooms, layers, resources, doors/spawns, map placement, visited bits, room lookup, new-game start, save/warp points, story/boss flags and progression locks. Compile and validate them together. A visually correct room with a traversable doorway can still save the wrong room identity.

First deliver a three-room mini-campaign with start, traversal and native save. Audit forward/return paths, spawn clearance, map identity and progression. Explicitly decide how original events are preserved or bypassed; do not clone bosses or script-sensitive entities to fill rooms.

Acceptance: new game, save, fresh-session continue, death, return travel and progression completion all work. Door graph tests cannot replace actual native reload tests. Full-castle expansion follows the miniature campaign.

## Authoring and release layer

Once underlying formats are proven, add editor conveniences: resource dependency reports, per-room budgets, original-art previews, stable symbols for imported content, reproducible module builds and project templates. A UI must expose implemented contracts rather than hiding unknown native behavior.

A conversion release needs original asset provenance, reproducible source, exact-host compatibility, no commercial ROMs/extracted artwork/saves in distribution, licensed runtimes, regression evidence and approved publishing. Local exports/diffs can retain original game pixels and must stay out of source release examples unless their distribution is independently authorized.

## Agent handoff contract

For every new subsystem, document:

1. Concrete user-visible behavior and smallest working example.
2. Supported exact profile and address/format provenance.
3. Input schema, sizes, units, alignment, compression and resource ownership.
4. Native caller/loader assumptions and lifecycle restrictions.
5. Important files and dependencies, build/play/test commands.
6. Actual emulator evidence, declared fixtures and untested scenes.
7. Failure modes and remaining extension points.
8. How to extend without modifying another mod's private runtime/assets.

Keep capability claims in framework/capabilities.json consistent with implementation. Update FILE-GUIDE, START-HERE, relevant format guides and project inventory when adding APIs. A working example is necessary; a roadmap entry is not implementation.

## Suggested next agent prompt

"Continue Tactical Soul Framework toward total conversions. Read AGENTS.md, TOTAL-CONVERSIONS.md, ROOM-DESIGN.md, RESOURCE-AUTHORING.md and ROM-AND-RAM.md. Implement a read-only resource/geometry inspector for one existing ordinary room, with exact format provenance and a lossless export/rebuild test. Preserve room identity, doors, entities, events and native saves. Only after the roundtrip is proven, implement one original visual/collision edit and verify it through native movement, reentry and save/continue. Document all files, schemas, fixtures and remaining limits. Do not claim a complete campaign editor or bypass original hash/resource checks."


## Room geometry foundation and project rename (2026-10-10)

The project is now **Tactical Soul Framework**, in its independent folder of the same name. Use `TacticalSoul.cmd`; `Dominance.cmd` and `Framework.cmd` remain aliases. See [rename compatibility](RENAMING.md) for environment variables and retained native ABI identifiers.

Read [ROOM-GEOMETRY.md](ROOM-GEOMETRY.md) before terrain work. `aria/compression.py` implements bounded LZ10/Aria resource reconstruction; `aria/geometry.py` inspects type-2 layers and applies checked, isolated existing-metatile edits. `inspect-geometry` and private `export-geometry` expose the source-backed format. `examples/geometry-workshop/mod.json` adds one stone step in the first hallway and composes the paired save-room route. Writes currently support only this registered main layer, unchanged dimensions and existing metatiles. New graphics, collision definitions, room resizing and full campaign compilation remain unimplemented.

Validation: 101 unit tests pass. `scripts/verify_geometry.py` passes eight structural/native checks: original walking reaches world X329, the edited step stops Soma at X311, native A jumping reaches X458, and fresh save/continue plus natural return stops at X360 on the other face. Initial comparisons declare a camera-relative X/zero-velocity fixture and retain settled Y; terrain is never injected into RAM. Private evidence stays in `local/geometry-verification.json`. See the geometry guide for format provenance, contracts, file responsibilities and next extensions.


## Static room previews and GUI editor goal

Read [ROOM-PREVIEWS.md](ROOM-PREVIEWS.md) for the implemented renderer, private PNG/atlas/report command, resource formats, API contracts and native evidence. `TacticalSoul.cmd preview-room 0 3 --out local/previews/hallway.png` works with bundled Python. Add `--mod examples/geometry-workshop/mod.json` to preview checked terrain edits. `aria/rendering.py` returns GUI-independent RGBA buffers; it does not modify ROM data. The atlas currently includes referenced metatiles only. Native checks match all eight graphics chunks, eight palette banks and 7,217 opaque wall pixels for baseline and edited rooms. The suite now has 111 tests.

[GUI-EDITOR-ROADMAP.md](GUI-EDITOR-ROADMAP.md) makes a graphical level editor an explicit goal and describes frontend/model boundaries, document/undo semantics, milestones and acceptance. No GUI, room catalog, layer compositor, complete brush catalog, inherited resources or 8bpp preview is implemented yet. Current source package: `release/Tactical-Soul-Framework-0.3.0.zip`. Update the inventory with `python scripts/update_inventory.py` before packaging. Native verification requires local development tools; normal previews do not.


## Custom terrain and tracked completion (v0.5)

Read [CUSTOM-TERRAIN.md](CUSTOM-TERRAIN.md) for newly authored type-2 metatiles, explicit empty/solid collision, loaded-resource validation and isolated visual/collision streams. `examples/custom-terrain-workshop/mod.json` is runnable; `python scripts/verify_geometry.py --custom-terrain` verifies native pixels, walking, jumping, save/continue and return. All 127 unit tests pass. Original character/palette imports, VRAM allocation, other collision families and broader room writes remain unfinished.

[COMPLETION-ROADMAP.md](COMPLETION-ROADMAP.md) and `framework/roadmap.json` track the total-conversion scope and weighted maturity estimate (currently about 21%). A GUI application is deferred; work belongs in reusable framework APIs. At the end of every development turn, report progress/validation, next milestone and estimated framework completion. Next: original room graphics/palette imports with isolated load lists and explicit resource budgets. Current package: `release/Tactical-Soul-Framework-0.5.0.zip`.


## Original room artwork (v0.6)

[ROOM-ASSETS.md](ROOM-ASSETS.md) documents the registered original 4bpp/palette importer, isolated load lists, source/preimage guards, static VRAM/tilemap budgets and native evidence. `examples/original-room-art/mod.json` imports original neon-brick artwork and composes custom solid terrain with the save route. All 134 tests pass; native checks cover pixel identity, collision, jumping, fresh continue and exact resource reload on return. General VRAM ownership, other rooms, animation and death/pause/event coverage remain unfinished. Current package: `release/Tactical-Soul-Framework-0.6.0.zip`; tracked completion estimate is about 23%. Next: resource dependency/budget audits and broader native lifecycle support.
