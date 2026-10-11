# Editor documents and undo/redo (v0.33)

Headless foundation for the future graphical editor. No GUI is implemented;
this is the reusable document/undo backend that a viewer frontend would be
built on. See [GUI editor roadmap](GUI-EDITOR-ROADMAP.md) for the frontend
boundaries and [room catalog](ROOM-CATALOG.md) for the browser data source.

## Contracts

- `aria/editor_docs.py` holds **authored states only** (plain JSON objects
  such as manifests or project bundles) relative to the verified immutable
  original. It never touches a `RomImage`.
- Every commit and every returned state is a deep copy: mutating caller
  objects, or a previously returned view, can never rewrite history.
- History is bounded (`max_history` 1..256, default 64); the oldest entry
  drops when the bound is exceeded. A new commit clears the redo stack.
- `fingerprint()` is the stable SHA-256 over canonical JSON; equal content
  fingerprints equally, so identical authored states rebuild identically
  from a clean original.
- Dirty state compares the current fingerprint against the last
  `mark_saved()` fingerprint. `to_json()`/`from_json()` round-trips the
  full history with validation; corrupt payloads raise `PatchError`.

## Usage

```python
from aria.editor_docs import EditorDocument
doc = EditorDocument({'cells': []}, label='room5-draft')
doc.commit({'cells': [1]}, 'paint step')
doc.undo()
doc.redo()
doc.mark_saved()
clone = EditorDocument.from_json(doc.to_json())
```

## Rules for future frontends

Build previews by applying `doc.current()` to a **clean** image per build;
do not accumulate allocator claims across strokes. Keep snapshot hashes
distinct from room/selection IDs. Never cache by pointer or slot alone,
treat a missing atlas tile as a valid brush, or broaden terrain
permissions to enable GUI controls. Write permissions and immutable
original preimages are unchanged by this milestone.

## Authored changes and manifest IO (v0.34)

- `doc.changes_since_saved()` returns deterministic change records
  (`{path, kind, old, new}`; kinds `added`/`removed`/`changed`) between
  the saved snapshot and the current state via `diff_states`, which also
  works standalone on any two JSON values. Dict keys sort; list entries
  compare by index; record values are deep copies.
- `save_manifest(doc_or_state, path)` writes canonical sorted JSON
  (`.json` only, existing parent required); `load_manifest_state(path)`
  reads it back with `PatchError` on missing files, invalid JSON or
  non-object payloads. Round-tripping a manifest through save/load
  preserves content exactly.
- Review flow: author states, inspect `changes_since_saved()` for the
  reviewable delta, `save_manifest` the current state when it is ready.

## Clean rebuilds (v0.35)

- `build_from_document(doc_or_state, fresh_image, applier, folder)`
  applies the current manifest state to **two** clean images from
  `fresh_image()` and requires byte- and ledger-identical results,
  returning `{sha256, image_bytes, ledger_entries}`. Nondeterministic
  appliers raise `PatchError`. This is the acceptance contract from the
  GUI roadmap: identical preview/build output from a clean original.
- The covered path applies a `sprite_assets` manifest through
  `install_sprite_assets` on synthetic images (2 ledger entries,
  identical SHA). Real-manifest preview wiring for other sections stays
  future work.

## Document previews (v0.36)

- `preview_document(doc_or_state, room, fresh_image, manifest_applier,
  renderer, folder)` renders `{sector, index, layer}` from the document's
  manifest state: it applies the state to two clean images, renders the
  room layer from each, and requires identical pixels. This is the headless
  equivalent of `preview-room --mod`, driven by a document instead of a
  manifest file. Returns `{width, height, rgba, report, image_sha256}`.
- The renderer contract mirrors the room renderer (`width`/`height` plus a
  `W*H*4`-byte RGBA buffer); malformed results and nondeterministic
  previews raise `PatchError`.

## Tests

`tests/test_editor_docs.py` covers commit/undo/redo chains, immutability,
redo clearing, history bounds, fingerprint stability, dirty/save
round-trips, change records, manifest save/load, clean rebuilds, preview
wiring and rejection paths. No ROM or native host is required.
