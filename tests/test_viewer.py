"""Viewer view-model tests: pure math always runs, native needs the host."""
import unittest
from pathlib import Path
from aria.core import PatchError
from aria.viewer import crop_rgba, markers_in_view, visible_range

ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / 'CastlevaniaAoS.gba'


class ViewMathTests(unittest.TestCase):
    def test_visible_range_clamps(self):
        self.assertEqual(visible_range(30, 0, 240),
                         {'first': 0, 'last': 7, 'count': 8})
        self.assertEqual(visible_range(30, 64, 240)['first'], 2)
        clipped = visible_range(10, 0, 9999)
        self.assertEqual((clipped['last'], clipped['count']), (9, 10))
        self.assertEqual(visible_range(10, 320, 240)['count'], 0)
        with self.assertRaises(PatchError):
            visible_range(10, -1, 240)
        with self.assertRaises(PatchError):
            visible_range(10, 0, 0)

    def test_markers_in_view(self):
        markers = [{'x': 10, 'y': 10}, {'x': 500, 'y': 10}, {'x': -5, 'y': 10}]
        kept = markers_in_view(markers, (0, 0), (240, 160))
        self.assertEqual(kept, [{'x': 10, 'y': 10}])
        kept[0]['x'] = 999
        self.assertEqual(markers[0]['x'], 10)
        with self.assertRaises(PatchError):
            markers_in_view(markers, (0, 0), (0, 160))

    def test_crop_rgba(self):
        rgba = bytes(range(4 * 3 * 4))
        cropped, w, h = crop_rgba(rgba, 4, 3, (1, 1), (2, 2))
        self.assertEqual((w, h), (2, 2))
        self.assertEqual(cropped, rgba[(1 * 4 + 1) * 4:(1 * 4 + 3) * 4] +
                        rgba[(2 * 4 + 1) * 4:(2 * 4 + 3) * 4])
        cropped, w, h = crop_rgba(rgba, 4, 3, (3, 0), (240, 160))
        self.assertEqual((w, h), (1, 3))
        cropped, w, h = crop_rgba(rgba, 4, 3, (99, 99), (50, 50))
        self.assertEqual((cropped, w, h), (b'', 0, 0))
        with self.assertRaises(PatchError):
            crop_rgba(b'too-short', 4, 3, (0, 0), (2, 2))


@unittest.skipUnless(HOST.exists(), 'Private host unavailable')
class NativeViewerTests(unittest.TestCase):
    def test_hallway_view_model(self):
        from aria.cli import load_image
        from aria.viewer import room_view
        view = room_view(load_image(HOST), 0, 3)
        self.assertGreater(view['dimensions_cells'][0], 0)
        self.assertGreaterEqual(view['entity_count_total'], 1)
        self.assertGreaterEqual(view['door_count_total'], 1)
        w, h = view['viewport_size']
        self.assertEqual(len(view['viewport_rgba']), w * h * 4)
        self.assertGreater(w, 0)
        self.assertEqual(len(view['image_sha256']), 64)
        self.assertIn('x', view['visible_cells'])

    def test_document_view_with_real_manifest(self):
        import json
        from aria.cli import apply_manifest_data, load_image
        from aria.rendering import render_layer
        from aria.viewer import document_view, room_view
        folder = ROOT / 'examples/geometry-workshop'
        state = json.loads((folder / 'mod.json').read_text(encoding='utf-8'))
        room = {'sector': 0, 'index': 3, 'layer': 0}
        view = document_view(state, room, lambda: load_image(HOST),
                             apply_manifest_data, render_layer, folder)
        self.assertGreater(view['entity_count_total'], 0)
        w, h = view['viewport_size']
        self.assertEqual(len(view['viewport_rgba']), w * h * 4)
        plain = room_view(load_image(HOST), 0, 3)
        self.assertEqual(view['dimensions_cells'], plain['dimensions_cells'])


if __name__ == '__main__':
    unittest.main()
