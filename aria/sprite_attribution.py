"""Snapshot-anchored sprite attribution helpers (no OAM-map dependence).

Compares rendered framebuffer snapshots from deterministic twin runs.
Only rendered consumers can differ, so a zero diff names no consumer
without trusting OAM-bank tracking or live tile reads. All helpers are
pure (bytes in, report out); native capture stays in private scripts.
"""
from .core import PatchError

WIDTH = 240
HEIGHT = 160
CHANNELS = 3
CELL = 8


def _check_framebuffer(buf, width=WIDTH, height=HEIGHT, channels=CHANNELS):
    expect = width * height * channels
    if not isinstance(buf, (bytes, bytearray)) or len(buf) != expect:
        raise PatchError('Framebuffer must be %d bytes' % expect)


def diff_framebuffers(left, right, width=WIDTH, height=HEIGHT, channels=CHANNELS):
    """Return the count of differing bytes between two snapshots."""
    _check_framebuffer(left, width, height, channels)
    _check_framebuffer(right, width, height, channels)
    return sum(1 for a, b in zip(left, right) if a != b)


def heat_cells(left, right, width=WIDTH, height=HEIGHT, channels=CHANNELS, cell=CELL):
    """Return sorted ['cx,cy:frames'] single-frame heat cells (8px grid)."""
    _check_framebuffer(left, width, height, channels)
    _check_framebuffer(right, width, height, channels)
    if left == right:
        return []
    cells = []
    for cy in range(height // cell):
        for cx in range(width // cell):
            hit = False
            for py in range(cy * cell, cy * cell + cell):
                base = (py * width + cx * cell) * channels
                if left[base:base + cell * channels] != right[base:base + cell * channels]:
                    hit = True
                    break
            if hit:
                cells.append('%d,%d:1' % (cx, cy))
    return sorted(cells)


def diff_scenes(left, right, width=WIDTH, height=HEIGHT, channels=CHANNELS, cell=CELL):
    """Diff per-scene snapshot lists; report frames/differing_frames/heat_cells.

    left/right map scene label -> list of framebuffer bytes. Heat cells
    count differing frames covering each 8px cell across the scene.
    """
    if not isinstance(left, dict) or not isinstance(right, dict):
        raise PatchError('Scenes must map label to snapshot list')
    if set(left) != set(right):
        raise PatchError('Scene labels differ')
    report = {}
    for label in left:
        a_list, b_list = left[label], right[label]
        if not isinstance(a_list, list) or not isinstance(b_list, list):
            raise PatchError('Scene snapshots must be lists: ' + str(label))
        if len(a_list) != len(b_list):
            raise PatchError('Scene frame count differs: ' + str(label))
        differing = 0
        counts = {}
        for a, b in zip(a_list, b_list):
            _check_framebuffer(a, width, height, channels)
            _check_framebuffer(b, width, height, channels)
            if a != b:
                differing += 1
                for cy in range(height // cell):
                    for cx in range(width // cell):
                        found = False
                        for py in range(cy * cell, cy * cell + cell):
                            base = (py * width + cx * cell) * channels
                            if a[base:base + cell * channels] != b[base:base + cell * channels]:
                                found = True
                                break
                        if found:
                            counts[(cx, cy)] = counts.get((cx, cy), 0) + 1
        report[label] = {
            'frames': len(a_list),
            'differing_frames': differing,
            'heat_cells': sorted('%d,%d:%d' % (x, y, c) for (x, y), c in counts.items()),
        }
    return report
