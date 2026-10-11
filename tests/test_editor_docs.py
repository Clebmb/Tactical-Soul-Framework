"""Synthetic tests for immutable editor documents (no ROM)."""
import tempfile
import unittest
from pathlib import Path
from aria.core import PatchError
from aria.editor_docs import EditorDocument, diff_states, load_manifest_state, save_manifest

ROOT = Path(__file__).resolve().parents[1]


class EditorDocTests(unittest.TestCase):
    def test_commit_undo_redo_chain(self):
        doc = EditorDocument({'cells': []})
        doc.commit({'cells': [1]}, 'paint')
        doc.commit({'cells': [1, 2]}, 'paint-more')
        self.assertEqual(doc.current(), {'cells': [1, 2]})
        self.assertEqual(doc.undo(), 'paint-more')
        self.assertEqual(doc.current(), {'cells': [1]})
        self.assertEqual(doc.redo(), 'paint-more')
        self.assertEqual(doc.current(), {'cells': [1, 2]})

    def test_history_is_immutable(self):
        first = {'cells': [1]}
        doc = EditorDocument({'cells': []})
        doc.commit(first, 'paint')
        first['cells'].append(999)
        view = doc.current()
        view['cells'].append(999)
        self.assertEqual(doc.current(), {'cells': [1]})
        doc.undo()
        self.assertEqual(doc.current(), {'cells': []})

    def test_new_commit_clears_redo_and_bounds_history(self):
        doc = EditorDocument({'n': 0}, max_history=2)
        doc.commit({'n': 1}, 'a')
        doc.commit({'n': 2}, 'b')
        doc.commit({'n': 3}, 'c')
        self.assertEqual(doc.history_labels(), ['b', 'c'])
        doc.undo()
        doc.commit({'n': 4}, 'd')
        self.assertFalse(doc.can_redo())

    def test_fingerprints_stable_and_distinct(self):
        doc = EditorDocument({'n': 1})
        before = doc.fingerprint()
        doc.commit({'n': 1}, 'noop-content')
        self.assertEqual(doc.fingerprint(), before)
        doc.commit({'n': 2}, 'change')
        self.assertNotEqual(doc.fingerprint(), before)

    def test_dirty_and_save_roundtrip(self):
        doc = EditorDocument({'n': 0})
        self.assertFalse(doc.is_dirty)
        doc.commit({'n': 1}, 'edit')
        self.assertTrue(doc.is_dirty)
        doc.mark_saved()
        self.assertFalse(doc.is_dirty)
        clone = EditorDocument.from_json(doc.to_json())
        self.assertEqual(clone.current(), {'n': 1})
        self.assertFalse(clone.is_dirty)
        self.assertEqual(clone.undo(), 'edit')
        self.assertEqual(clone.current(), {'n': 0})

    def test_changes_since_saved_and_manifest_roundtrip(self):
        folder = ROOT / 'local/editor-doc-tests'
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=folder) as temp:
            target = Path(temp) / 'draft.mod.json'
            doc = EditorDocument({'schema_version': 1, 'rooms': []})
            doc.mark_saved()
            self.assertEqual(doc.changes_since_saved(), [])
            doc.commit({'schema_version': 1, 'rooms': [{'id': 'a'}]}, 'add room a')
            changes = doc.changes_since_saved()
            self.assertEqual(len(changes), 1)
            self.assertEqual(changes[0]['kind'], 'added')
            self.assertEqual(changes[0]['path'], ['rooms', 0])
            save_manifest(doc, target)
            restored = load_manifest_state(target)
            self.assertEqual(restored['rooms'], [{'id': 'a'}])
            clone = EditorDocument.from_json(doc.to_json())
            self.assertEqual(clone.changes_since_saved(), changes)
            clone.mark_saved()
            self.assertEqual(clone.changes_since_saved(), [])

    def test_diff_states_deterministic_and_typed(self):
        old = {'b': 1, 'a': {'x': [1, 2]}}
        new = {'a': {'x': [1, 3, 4]}}
        records = diff_states(old, new)
        self.assertEqual([r['path'] for r in records], [['a', 'x', 1], ['a', 'x', 2], ['b']])
        self.assertEqual([r['kind'] for r in records], ['changed', 'added', 'removed'])
        self.assertEqual(diff_states({'n': 1}, {'n': 1}), [])
        with self.assertRaises(PatchError):
            save_manifest({'a': 1}, str(ROOT / 'local/editor-doc-tests/bad.txt'))

    def test_clean_rebuild_is_deterministic(self):
        import hashlib
        import json
        import struct
        from unittest.mock import patch
        from aria.content import lz77
        from aria.core import RomImage
        from aria.editor_docs import build_from_document
        from aria import sprite_assets as sprite_assets_module
        from aria.sprite_assets import SOURCE, WRAPPER, install_sprite_assets
        data = bytearray(0x800000)

        def put(address, payload):
            data[address - 0x08000000:address - 0x08000000 + len(payload)] = payload
        put(WRAPPER, bytes.fromhex('0104100420bf5f08'))
        put(0x08209EE8, bytes([0, 4, 1, 0]))
        for address, value in ((0x0804F1A0, WRAPPER), (0x0804F540, WRAPPER),
                               (0x0804F1A4, 0x08209EE8), (0x0804F544, 0x08209EE8),
                               (0x0804F1A8, 0x0820FE44), (0x0804F5B4, 0x0820FE44)):
            put(address, struct.pack('<I', value))
        put(SOURCE, lz77(((2048 + 4) << 8).to_bytes(4, 'little') + bytes(2048)))
        original = bytes(data)
        profile = dict(id='synthetic', rom_base=0x08000000, size=len(data),
                       sha256=hashlib.sha256(data).hexdigest(),
                       allocation_ranges=[dict(start=0x08680000, end=0x08800000)])
        folder = ROOT / 'local/editor-doc-tests'
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=folder) as temp:
            home = Path(temp)
            (home / 'art.json').write_text(json.dumps(
                dict(width=128, height=32, pixels=[1] * 4096)), encoding='utf-8')
            entry = dict(resource='background-bats', scope='all_registered_consumers',
                         source='art.json',
                         expected_page_sha256=hashlib.sha256(bytes(2048)).hexdigest(),
                         provenance='Original synthetic pixels')
            manifest = dict(schema_version=1, id='doc-test', sprite_assets=[entry])
            doc = EditorDocument(manifest, label='rebuild-check')
            registry = dict(sprite_assets_module.REGISTRY['background-bats'])
            registry.update(page_sha=hashlib.sha256(bytes(2048)).hexdigest(),
                            palette_sha=hashlib.sha256(bytes(32)).hexdigest())
            with patch.dict(sprite_assets_module.REGISTRY, {'background-bats': registry}):
                report = build_from_document(
                    doc, lambda: RomImage(original, profile),
                    lambda rom, mod, where: install_sprite_assets(rom, mod['sprite_assets'], where),
                    home)
            self.assertEqual(report['image_bytes'], 0x800000)
            self.assertEqual(report['ledger_entries'], 2)
            self.assertEqual(len(report['sha256']), 64)
            self.assertEqual(doc.current(), manifest)
            self.assertEqual(hashlib.sha256(original).hexdigest(), profile['sha256'])

    def test_nondeterministic_build_rejected(self):
        from aria.editor_docs import build_from_document

        class FakeImage:
            def __init__(self):
                self.data = bytearray(b'\x00' * 16)
                self.ledger = []
        calls = []

        def wobbly(image, manifest, folder):
            calls.append(1)
            image.data[0] = len(calls)
        with self.assertRaisesRegex(PatchError, 'not deterministic'):
            build_from_document({'n': 1}, FakeImage, wobbly)
        with self.assertRaises(PatchError):
            build_from_document(['not-a-dict'], FakeImage, wobbly)
        with self.assertRaises(PatchError):
            build_from_document({'n': 1}, FakeImage, 'not-callable')

    def test_preview_wiring_renders_from_clean_builds(self):
        from aria.editor_docs import preview_document
        seen = []

        class FakeImage:
            def __init__(self, tag):
                self.data = bytearray(b'\x00' * 8)
                self.ledger = []
                self.tag = tag
        images = []

        def fresh():
            image = FakeImage(len(images))
            images.append(image)
            return image

        def applier(image, manifest, folder):
            seen.append((image.tag, dict(manifest), folder))
            image.data[0] = 0xAB
            image.ledger.append('edit')

        def renderer(image, sector, index, layer):
            seen.append(('render', image.tag, sector, index, layer))
            return {'width': 2, 'height': 1, 'rgba': bytes(image.data[:8] * 1)[:8],
                    'report': {'room': [sector, index, layer]}}
        doc = EditorDocument({'edits': [1]}, label='preview-check')
        out = preview_document(doc, {'sector': 0, 'index': 3, 'layer': 0},
                               fresh, applier, renderer, folder='work')
        self.assertEqual(out['width'], 2)
        self.assertEqual(out['report'], {'room': [0, 3, 0]})
        self.assertEqual(len(out['image_sha256']), 64)
        self.assertEqual(len(images), 2)
        self.assertNotEqual(images[0], images[1])
        self.assertEqual(doc.current(), {'edits': [1]})
        builds = [s for s in seen if s[0] != 'render']
        self.assertEqual([(tag, man, folder) for tag, man, folder in builds],
                         [(0, {'edits': [1]}, 'work'), (1, {'edits': [1]}, 'work')])

    def test_preview_rejects_nondeterminism_and_bad_shapes(self):
        from aria.editor_docs import preview_document

        class FakeImage:
            def __init__(self):
                self.data = bytearray(b'\x00' * 8)
                self.ledger = []
        calls = []

        def wobbly(image, manifest, folder):
            calls.append(1)
            image.data[0] = len(calls)

        def flat(image, sector, index, layer):
            return {'width': 2, 'height': 1, 'rgba': bytes(image.data[:8]), 'report': {}}
        with self.assertRaisesRegex(PatchError, 'not deterministic'):
            preview_document({'n': 1}, {'sector': 0, 'index': 3, 'layer': 0},
                             FakeImage, wobbly, flat)
        with self.assertRaises(PatchError):
            preview_document({'n': 1}, {'sector': 0, 'index': 3}, FakeImage, wobbly, flat)
        with self.assertRaises(PatchError):
            preview_document({'n': 1}, {'sector': 0, 'index': 3, 'layer': 0},
                             FakeImage, wobbly, lambda *a: {'width': 2})

    def test_rejections(self):
        with self.assertRaises(PatchError):
            EditorDocument([])
        with self.assertRaises(PatchError):
            EditorDocument({}, max_history=0)
        doc = EditorDocument({})
        with self.assertRaises(PatchError):
            doc.commit([], 'bad')
        with self.assertRaises(PatchError):
            doc.commit({}, '')
        with self.assertRaises(PatchError):
            doc.undo()
        with self.assertRaises(PatchError):
            doc.redo()
        with self.assertRaises(PatchError):
            EditorDocument.from_json({'bad': True})


if __name__ == '__main__':
    unittest.main()
