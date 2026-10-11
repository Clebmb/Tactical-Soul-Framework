GUI application implementation is deferred at the user's request. Prioritize the total-conversion backend in COMPLETION-ROADMAP.md; the architecture below remains future context.

# GUI level editor: engineering roadmap and agent handoff

A GUI-based AoS level editor is now an explicit framework goal alongside deeper custom content and eventual total conversions. The current deliverable is a reusable static terrain-rendering backend and command-line previews. A graphical application has not been implemented yet.

## Intended architecture

Keep four boundaries clear:

| Layer | Responsibility | Current foundation |
|---|---|---|
| ROM model | Exact original, bounds, immutable preimages, supported profile, allocations and patch conflicts | `core`, `rooms`, `geometry`, table/ability/content APIs |
| Resource/render services | Resolve resources, decode assets, render buffers, expose diagnostics | `compression`, `resources`, new `rendering` |
| Editor document | User changes, selection, undo/redo, dirty state, editable capabilities and manifest generation | Planned |
| Frontend | Room browser, canvas, tools, property panels and build/play controls | Planned |

The frontend should call model/services directly or through a deliberately versioned local API. Choose desktop or local-web technology when implementing the UI, based on deployment requirements. Do not impose a GUI toolkit dependency on normal builds or asset decoding. The existing command line remains useful for agents, automation and reproducible builds.

The editor document should hold authored changes relative to a verified immutable original. Undo/redo operates on authored changes, then regenerates an in-memory patched image for preview/build. It must not repeatedly allocate into or destructively patch the same `RomImage` on every brush stroke. Otherwise previews could consume free space, conflict with earlier claims, and diverge from clean builds. A read cache must be keyed by ROM content and resource addresses/hashes, not just room coordinates.

## Milestone 1: room viewer

Working prerequisite: selected type-2 layer RGBA buffers, referenced-metatile atlas and diagnostic report via `aria.rendering`. Bounded room catalog enumeration and per-layer diagnostics are now implemented in ROOM-CATALOG.md. Next add layer visibility, zoom/pan, coordinates and frontend resource diagnostics. Multi-layer composition must respect z/priority, canvas sizes and native scrolling/effects; it cannot be inferred from layer number alone. A viewer should label unsupported/inherited resources and continue showing other valid rooms rather than hiding errors.

Acceptance: no ROM modifications; camera/zoom do not alter model data; native-size previews match documented native samples; selecting another room does not leak cached resources; malformed/unsupported rooms explain their limitations; private previews are excluded from releases. Entity/door outlines can precede sprite rendering, provided they clearly identify actual native coordinates and record IDs.

## Milestone 2: existing-terrain editing

Build an editor-document abstraction before painting. Reuse `geometry_edits` expected-layout hashes and per-cell `expect` values; keep original preimages stable when the same cell is painted repeatedly. A canceled edit should disappear from the authored patch. A no-op edit should not be emitted. Enable paint tools only for registered writable layers and validated available metatiles. The current atlas covers referenced metatiles only, so it is not a complete brush palette.

Acceptance: paint/erase/pick, selection, undo/redo, clean dirty-state behavior, save/reopen authored manifests, identical preview/build output from a clean original, and preservation of shared resources. Native tests must exercise collision, return routes and saving. Expand the room allowlist through evidence, not by removing it. Room resizing remains a separate feature.

## Milestone 3: entities, doors and properties

Expose supported entity, encounter, door, item and enemy APIs through typed property panels. Preserve unknown fields and native IDs, loading order, resource restrictions and expected values. Add paired-door editing with destination preview and explicit diagnostics for displaced neighbors or broken routes. Actor rectangles and spawn markers are useful before full sprite/animation decoding.

Acceptance: edited values map to the right records; selections survive sorting; unsupported entity kinds remain inspectable but cannot be casually spawned; full encounter resources are checked; native transitions, returns, saves and relevant gameplay changes pass. Do not equate serialized record IDs with runtime actor slots.

## Milestone 4: original assets and larger rooms

Add complete metatile availability analysis, graphics/palette load visualization, original tileset imports, collision definitions, allocation budgets and isolated resource-list writing. Extend sprite/animation support and native sound bindings independently. A useful GUI can expose available tools as each backend contract becomes verified.

Acceptance: authored graphics appear natively with correct transparency/flips/palettes; collision matches new terrain; ROM/VRAM/palette budgets fit; other rooms sharing original resources remain unchanged; save/reentry works. Resizing requires entity/door bounds, layer dimensions, map occupancy and reachability checks, rather than simply changing width/height bytes.

## Milestone 5: campaign and total conversions

Integrate castle-map compilation, progression/event editing, save identity/schema migration, native AI/ability extension and asset provenance. Provide project validation and reproducible source-only release packaging. See TOTAL-CONVERSIONS.md for full acceptance. Successful previews or a single playable room are insufficient evidence for a complete campaign.

## Suggested next task prompt

> Work inside Tactical Soul Framework. Read AGENTS.md, ROOM-PREVIEWS.md, ROOM-GEOMETRY.md and GUI-EDITOR-ROADMAP.md. Implement a bounded read-only room catalog API with per-layer diagnostics and stable room identifiers for a future GUI. Reuse the exact-ROM gate and resource renderer. Do not implement a full GUI or broaden terrain-writing permissions in this task. Unsupported/inherited/empty layers should yield structured diagnostics without aborting the whole catalog. Add synthetic boundary tests and a bounded private-host audit, document every new file/API and capability, and keep commercial extracted data under local/. Preserve all existing build behavior and update the source-only release package.

After this, implement the editor document and undo/redo model, then choose/build the first viewer frontend. Each task should leave a usable backend, concrete evidence and a handoff guide; avoid declaring an entire editor finished from a canvas mockup.

## Catalog milestone completed

The bounded read-only catalog API described in the earlier suggested prompt is implemented; see ROOM-CATALOG.md. Use it as the browser data source. The next agent should implement the editor-document/undo model described above before adding paint tools, while keeping write permissions and immutable original preimages intact.
