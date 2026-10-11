"""Synthetic tests for snapshot-anchored attribution helpers (no ROM)."""
import unittest
from aria.core import PatchError
from aria.sprite_attribution import diff_framebuffers, diff_scenes, heat_cells

W, H, C = 240, 160, 3
N = W * H * C


def frame(fill=0):
    return bytes([fill]) * N


def with_pixel(fill, x, y, rgb=(1, 2, 3)):
    buf = bytearray(bytes([fill]) * N)
    base = (y * W + x) * C
    buf[base:base + C] = bytes(rgb)
    return bytes(buf)


class AttributionTests(unittest.TestCase):
    def test_identical_frames_zero(self):
        self.assertEqual(diff_framebuffers(frame(), frame()), 0)
        self.assertEqual(heat_cells(frame(), frame()), [])

    def test_single_pixel_diff_and_cell(self):
        a, b = frame(), with_pixel(0, 10, 20)
        self.assertEqual(diff_framebuffers(a, b), 3)
        cells = heat_cells(a, b)
        self.assertEqual(cells, ['1,2:1'])

    def test_scene_report_counts_and_cells(self):
        a = frame()
        b = with_pixel(0, 10, 20)
        report = diff_scenes({'idle': [a, a], 'kill': [a, b]}, {'idle': [a, a], 'kill': [a, a]})
        self.assertEqual(report['idle'], {'frames': 2, 'differing_frames': 0, 'heat_cells': []})
        self.assertEqual(report['kill']['frames'], 2)
        self.assertEqual(report['kill']['differing_frames'], 1)
        self.assertEqual(report['kill']['heat_cells'], ['1,2:1'])

    def test_label_and_length_mismatch_rejected(self):
        a = frame()
        with self.assertRaises(PatchError):
            diff_scenes({'x': [a]}, {'y': [a]})
        with self.assertRaises(PatchError):
            diff_scenes({'x': [a]}, {'x': [a, a]})
        with self.assertRaises(PatchError):
            diff_framebuffers(b'\x00', a)


if __name__ == '__main__':
    unittest.main()
