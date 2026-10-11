"""Immutable editor documents with bounded undo/redo (headless, no GUI).

The document holds authored changes (plain JSON-serializable dicts such as
manifests or project bundles) relative to a verified immutable original.
Undo/redo operates on authored states only: every commit deep-copies, so
later mutation of caller objects — or of a previously returned state —
can never rewrite history. Previews/builds must apply the current state
to a clean image per build, never accumulate allocator claims across
brush strokes. See docs/GUI-EDITOR-ROADMAP.md and docs/EDITOR-DOCUMENTS.md.
"""
import copy
import hashlib
import json
from pathlib import Path

from .core import PatchError

MIN_HISTORY = 1
MAX_HISTORY = 256


def fingerprint(state):
    """Stable SHA-256 over canonical JSON for a document state."""
    try:
        canonical = json.dumps(state, sort_keys=True, separators=(',', ':'))
    except (TypeError, ValueError) as exc:
        raise PatchError('Document state must be JSON-serializable: %s' % exc)
    if not isinstance(state, dict):
        raise PatchError('Document state must be an object')
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


class EditorDocument:
    """Bounded immutable history over authored document states."""

    def __init__(self, initial, max_history=64, label='untitled'):
        if not isinstance(initial, dict):
            raise PatchError('Initial document state must be an object')
        if not isinstance(max_history, int) or not MIN_HISTORY <= max_history <= MAX_HISTORY:
            raise PatchError('max_history must be %d..%d' % (MIN_HISTORY, MAX_HISTORY))
        if not isinstance(label, str) or not label:
            raise PatchError('Document label must be a nonempty string')
        self._max_history = max_history
        self._label = label
        self._past = []
        self._future = []
        self._current = copy.deepcopy(initial)
        self._saved = fingerprint(initial)
        self._saved_state = copy.deepcopy(initial)

    @property
    def label(self):
        return self._label

    @property
    def max_history(self):
        return self._max_history

    def current(self):
        return copy.deepcopy(self._current)

    def fingerprint(self):
        return fingerprint(self._current)

    def can_undo(self):
        return bool(self._past)

    def can_redo(self):
        return bool(self._future)

    def history_labels(self):
        return [label for label, _ in self._past]

    def commit(self, state, label):
        if not isinstance(state, dict):
            raise PatchError('Committed state must be an object')
        if not isinstance(label, str) or not label:
            raise PatchError('Commit label must be a nonempty string')
        snapshot = copy.deepcopy(state)
        fingerprint(snapshot)
        self._past.append((label, self._current))
        self._current = snapshot
        self._future = []
        while len(self._past) > self._max_history:
            self._past.pop(0)
        return self.fingerprint()

    def undo(self):
        if not self._past:
            raise PatchError('Nothing to undo')
        label, state = self._past.pop()
        self._future.append((label, self._current))
        self._current = state
        return label

    def redo(self):
        if not self._future:
            raise PatchError('Nothing to redo')
        label, state = self._future.pop()
        self._past.append((label, self._current))
        self._current = state
        return label

    @property
    def is_dirty(self):
        return self.fingerprint() != self._saved

    def mark_saved(self):
        self._saved = self.fingerprint()
        self._saved_state = copy.deepcopy(self._current)

    def changes_since_saved(self):
        """Authored-change records between the saved snapshot and current."""
        return diff_states(self._saved_state, self._current)

    def to_json(self):
        return {
            'label': self._label,
            'max_history': self._max_history,
            'current': copy.deepcopy(self._current),
            'past': [(label, copy.deepcopy(state)) for label, state in self._past],
            'future': [(label, copy.deepcopy(state)) for label, state in self._future],
            'saved_fingerprint': self._saved,
            'saved_state': copy.deepcopy(self._saved_state),
        }

    @classmethod
    def from_json(cls, payload):
        if not isinstance(payload, dict) or set(payload) != {
                'label', 'max_history', 'current', 'past', 'future',
                'saved_fingerprint', 'saved_state'}:
            raise PatchError('Invalid editor document payload')
        doc = cls(payload['current'], max_history=payload['max_history'], label=payload['label'])
        past = payload['past']
        future = payload['future']
        if not isinstance(past, list) or not isinstance(future, list):
            raise PatchError('Invalid editor document history')
        for label, state in past + future:
            if not isinstance(label, str) or not label or not isinstance(state, dict):
                raise PatchError('Invalid editor document history entry')
            fingerprint(state)
        if len(past) > doc.max_history:
            raise PatchError('History exceeds max_history')
        if not isinstance(payload['saved_fingerprint'], str) or len(payload['saved_fingerprint']) != 64:
            raise PatchError('Invalid saved fingerprint')
        doc._past = [(label, copy.deepcopy(state)) for label, state in past]
        doc._future = [(label, copy.deepcopy(state)) for label, state in future]
        doc._saved = payload['saved_fingerprint']
        if not isinstance(payload['saved_state'], dict):
            raise PatchError('Invalid saved state')
        fingerprint(payload['saved_state'])
        doc._saved_state = copy.deepcopy(payload['saved_state'])
        fingerprint(doc._current)
        return doc


def diff_states(old, new, _path=()):
    """Recursive authored-change records between two JSON values.

    Returns a deterministically ordered list of records:
    {'path': [...], 'kind': 'added'|'removed'|'changed', 'old': ..., 'new': ...}.
    Dict keys sort; list entries compare by index. Values are deep copies.
    """
    if isinstance(old, dict) and isinstance(new, dict):
        records = []
        for key in sorted(set(old) | set(new)):
            if key not in old:
                records.append({'path': list(_path) + [key], 'kind': 'added',
                                'old': None, 'new': copy.deepcopy(new[key])})
            elif key not in new:
                records.append({'path': list(_path) + [key], 'kind': 'removed',
                                'old': copy.deepcopy(old[key]), 'new': None})
            else:
                records.extend(diff_states(old[key], new[key], _path + (key,)))
        return records
    if isinstance(old, list) and isinstance(new, list):
        records = []
        for index in range(max(len(old), len(new))):
            if index >= len(old):
                records.append({'path': list(_path) + [index], 'kind': 'added',
                                'old': None, 'new': copy.deepcopy(new[index])})
            elif index >= len(new):
                records.append({'path': list(_path) + [index], 'kind': 'removed',
                                'old': copy.deepcopy(old[index]), 'new': None})
            else:
                records.extend(diff_states(old[index], new[index], _path + (index,)))
        return records
    if old != new:
        return [{'path': list(_path), 'kind': 'changed',
                 'old': copy.deepcopy(old), 'new': copy.deepcopy(new)}]
    return []


def build_from_document(state_or_doc, fresh_image, applier, folder=None):
    """Apply a document's manifest state to two clean images; require identical rebuilds.

    fresh_image() must return a clean image each call; applier(image,
    manifest, folder) applies the authored state. Previews/builds must use
    this pattern — never accumulate allocator claims across strokes on one
    image. Returns {'sha256', 'image_bytes', 'ledger_entries'}.
    """
    state = state_or_doc.current() if isinstance(state_or_doc, EditorDocument) else state_or_doc
    fingerprint(state)
    if not callable(fresh_image) or not callable(applier):
        raise PatchError('build_from_document needs fresh_image and applier callables')
    snapshots = []
    for _ in range(2):
        try:
            image = fresh_image()
        except Exception as exc:
            raise PatchError('Clean image factory failed: %s' % exc)
        applier(image, copy.deepcopy(state), folder)
        try:
            payload = bytes(image.data)
            ledger = list(image.ledger)
        except AttributeError:
            raise PatchError('Image must expose data and ledger')
        snapshots.append((payload, ledger))
    if snapshots[0] != snapshots[1]:
        raise PatchError('Document rebuild is not deterministic from a clean image')
    payload, ledger = snapshots[0]
    return {'sha256': hashlib.sha256(payload).hexdigest(),
            'image_bytes': len(payload), 'ledger_entries': len(ledger)}


def preview_document(state_or_doc, room, fresh_image, manifest_applier, renderer, folder=None):
    """Render a room preview from a document's manifest state via clean builds.

    Applies the current state to two clean images, renders the requested
    room layer from each, and requires identical pixels — the headless
    equivalent of `preview-room --mod`, driven by a document instead of a
    manifest file. room is {'sector','index','layer'} (ints); renderer(image,
    sector, index, layer) returns {'width','height','rgba','report'} with a
    width*height*4-byte RGBA buffer. Returns the first render plus
    {'image_sha256'} of its built image.
    """
    state = state_or_doc.current() if isinstance(state_or_doc, EditorDocument) else state_or_doc
    fingerprint(state)
    if not isinstance(room, dict) or set(room) != {'sector', 'index', 'layer'}:
        raise PatchError('room must be {sector,index,layer}')
    sector, index, layer = room['sector'], room['index'], room['layer']
    if any(not isinstance(v, int) or v < 0 for v in (sector, index, layer)):
        raise PatchError('room sector/index/layer must be nonnegative ints')
    if not callable(fresh_image) or not callable(manifest_applier) or not callable(renderer):
        raise PatchError('preview_document needs fresh_image, manifest_applier and renderer callables')
    renders = []
    for _ in range(2):
        try:
            image = fresh_image()
        except Exception as exc:
            raise PatchError('Clean image factory failed: %s' % exc)
        manifest_applier(image, copy.deepcopy(state), folder)
        try:
            payload = bytes(image.data)
        except AttributeError:
            raise PatchError('Image must expose data')
        result = renderer(image, sector, index, layer)
        if (not isinstance(result, dict) or set(result) < {'width', 'height', 'rgba'} or
                not isinstance(result['width'], int) or not isinstance(result['height'], int) or
                not isinstance(result['rgba'], (bytes, bytearray)) or
                len(result['rgba']) != result['width'] * result['height'] * 4):
            raise PatchError('Renderer must return width/height/rgba (W*H*4 bytes)')
        renders.append((payload, result))
    if renders[0][1]['rgba'] != renders[1][1]['rgba']:
        raise PatchError('Document preview is not deterministic from a clean image')
    first, result = renders[0]
    return {'width': result['width'], 'height': result['height'],
            'rgba': bytes(result['rgba']), 'report': copy.deepcopy(result.get('report')),
            'image_sha256': hashlib.sha256(first).hexdigest()}


def save_manifest(state_or_doc, path):
    """Write an authored manifest state as canonical JSON (.json only)."""
    state = state_or_doc.current() if isinstance(state_or_doc, EditorDocument) else state_or_doc
    fingerprint(state)
    target = Path(path)
    if target.suffix.lower() != '.json':
        raise PatchError('Manifest output must be a .json path')
    if not target.parent.exists():
        raise PatchError('Manifest parent directory does not exist')
    target.write_text(json.dumps(state, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return str(target)


def load_manifest_state(path):
    """Read a manifest JSON object back into an authored state."""
    try:
        payload = json.loads(Path(path).read_text(encoding='utf-8'))
    except OSError as exc:
        raise PatchError('Cannot read manifest: %s' % exc)
    except ValueError as exc:
        raise PatchError('Manifest is not valid JSON: %s' % exc)
    if not isinstance(payload, dict):
        raise PatchError('Manifest state must be an object')
    fingerprint(payload)
    return copy.deepcopy(payload)
