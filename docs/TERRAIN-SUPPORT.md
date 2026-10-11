# Terrain support discovery — v0.21.0

The headless `terrain-support` command/API reports current main-layer terrain support, loaded existing metatile brushes and reasons that prevent a narrow static assessment. It does not widen the geometry write allowlist. This is a reusable selection tool for agents and future GUI clients; the GUI remains deferred.

```powershell
.\TacticalSoul.cmd terrain-support --limit 32 --out local/terrain-support.json
.\TacticalSoul.cmd terrain-support --sector 0 --offset 3 --limit 3
.\TacticalSoul.cmd terrain-support --mod examples/bridge-route/mod.json --limit 32
```

`--host` selects an exact supported private original. `--mod` applies the manifest in memory before assessing its current resource/layout graph. Output is stdout or private JSON under `local/`, preserving host and manifest. The optional sector limits enumeration before offset/limit pagination. Limits are 1–128; continue with `next_offset` until null. `enumeration_complete` describes sector-table enumeration, not whether every room supports edits. A blocked room remains a row and does not prevent neighboring results.

## Python contracts and status meanings

`aria.terrain_support.assess_terrain_support(rom, sector, index)` validates bounded integer references and returns an independently diagnosed room. `catalog_terrain_support(rom, sector=None, offset=0, limit=32)` returns schema 1 with profile/image hash, pagination, enumeration diagnostics, rows and a page summary. Neither changes image bytes, ledger, allocation records/cursors, profile registration or host files.

Each row carries a stable base-slot ID, sector/room, registration flag, status, `write_enabled`, diagnostics and available existing metatile IDs. Successful geometry inspection includes cell dimensions, source layout/visual/collision hashes, metatile count and lossless roundtrip result. Main-layer dependencies use current loaded character chunks and palette banks. The budget check exposes character/tilemap overlaps. Nonzero alternate pointers require separate investigation and block this narrow assessment.

- `registered`: the room is already explicitly registered, main layer is type 2, metadata/resources roundtrip, current referenced dependencies are available, no static overlap/global-load diagnostics exist and no alternate state is requested. `write_enabled` is true within this narrow assessment.
- `static_candidate`: the same static checks pass, but the room is not registered. `write_enabled` stays false. This is an investigation lead, never authorization to modify the profile or proof of native gameplay safety.
- `blocked`: empty/non-type2/invalid geometry, resource-loading failures, missing referenced dependencies, overlap or alternate-state concerns prevent the narrow assessment. Registration can still be true while write_enabled is false; report both rather than silently deregistering anything.

`available_metatile_ids` describes definitions whose static character/palette dependencies are loaded, including implicit blank 0. It is not a collision semantic palette: an available brush may be a slope, hazard or an unverified collision family. The result emits no commercial character/collision asset bytes. It does not establish full dynamic VRAM ownership, event/actor loads, alternate-state inheritance or viewport effects. Other layers have independent read support; this assessment certifies neither those layers nor their editability.

The existing writer still enforces its own checks and narrow registration. This diagnostic does not replace writer preimages, conflict checks, native testing or resource authoring contracts. `write_enabled` is a static discovery result, not a runtime safety guarantee, and is not currently an additional enforcement gate inside the geometry writer.

## Current survey evidence

`scripts/verify_terrain_support.py` paginates all 343 exact-original base slots and records:

| Status | Rooms |
|---|---:|
| Registered | 4 |
| Static candidates requiring investigation | 311 |
| Blocked by narrow assessment | 28 |

The four registrations are 0:3, 0:5, 0:6, 0:31. No new room was registered by the survey. Original bytes, live image, ledger, allocation state and profile remain unchanged. Full private results are in `local/terrain-support-catalog.json`; bounded verification summary is in `local/terrain-support-verification.json`. Patched mods may produce different results. These counts are static observations for the supported host, not a claim that 315 rooms are production-ready mod targets.

Six new regression tests cover read-only success, candidates remaining unauthorized, failure blocking even registered rooms, alternate-state caution, pagination/bounds and isolation of a malformed room row. The survey can be rerun using Python with standard-library support; it does not need Pillow or execute mGBA.

## Next-agent acceptance sequence

Pick a candidate with uncomplicated dependencies, inspect room identity/map/events, verify original roundtrip and shared pointers, stage a small isolated edit in a separate experimental configuration, then prove native loading, intended collision, entry/return and relevant lifecycle behavior. Only after that evidence should a new production registration be added. Do not silently promote all 311 candidates. Prefer a reusable registration/support contract that captures evidence over a growing list with no provenance. Original sprites/animation, audio playback, new rooms, map compilation and save schemas remain larger gaps.
