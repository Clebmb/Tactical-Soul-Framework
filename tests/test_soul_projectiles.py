"""Synthetic contracts for read-only soul projectile observers; one host-gated pin."""
import unittest
from pathlib import Path

from aria.core import PatchError
from aria.soul_projectiles import (
    ACTOR_BASE,
    ACTOR_SLOTS,
    ACTOR_STRIDE,
    EXPECTED_MANA_COST,
    SLOT_WORD8_OFFSET,
    code_to_slots,
    compare_audio_windows,
    compare_cast_twins,
    count_pointer_occurrences,
    describe_winged_skeleton,
    novel_codes,
    classify_transition,
    diff_bytes,
    diff_records,
    fit_word_series,
    decode_oam_entry,
    read_slot_record,
    read_slot_word,
    scan_decreases,
    slot_base,
    slot_world_x,
    snapshot_actor_window,
)

ROOT = Path(__file__).resolve().parents[1]


def reader(mapping):
    def read(address, size=4):
        if size != 4:
            raise AssertionError(hex(address))
        return mapping.get(address, 0)
    return read


class SoulProjectileObserverTests(unittest.TestCase):
    def test_snapshotfilters_zero_and_validates(self):
        mapping = {
            ACTOR_BASE: 0,
            ACTOR_BASE + ACTOR_STRIDE: 0x080221CD,
            ACTOR_BASE + 2 * ACTOR_STRIDE: 0,
        }
        snapshot = snapshot_actor_window(reader(mapping))
        self.assertEqual(snapshot, {1: 0x080221CD})
        with self.assertRaises(PatchError):
            snapshot_actor_window(lambda address, size: -1)
        with self.assertRaises(PatchError):
            snapshot_actor_window(lambda address, size: 1 << 32)

    def test_code_to_slots_and_novel_codes(self):
        baseline = {1: 0x080221CD, 5: 0x08012345}
        current = {1: 0x080221CD, 5: 0x08012345, 9: 0x08099999}
        inverted = code_to_slots(current)
        self.assertEqual(inverted[hex(0x08099999)], [9])
        self.assertEqual(novel_codes(baseline, current), [hex(0x08099999)])
        self.assertEqual(novel_codes(baseline, dict(baseline)), [])

    def test_pointer_search_bounds_and_hits(self):
        data = (0x08026009).to_bytes(4, 'little') + b'\x00' + (0x08026009).to_bytes(4, 'little')
        hits = count_pointer_occurrences(data, 0x08026009)
        self.assertEqual(hits, [0, 5])
        with self.assertRaises(PatchError):
            count_pointer_occurrences(b'', 0x08026009)
        with self.assertRaises(PatchError):
            count_pointer_occurrences(data, -1)
        with self.assertRaises(PatchError):
            count_pointer_occurrences(data, 0x08026009, limit=0)

    def test_slot_words_position_and_twin_comparison(self):
        self.assertEqual(SLOT_WORD8_OFFSET, 32)
        self.assertEqual(slot_base(0), ACTOR_BASE)
        with self.assertRaises(PatchError):
            slot_base(ACTOR_SLOTS)
        with self.assertRaises(PatchError):
            read_slot_word(reader({}), 0, 33)
        # Word 8 value 0x00123456 -> low halfword 0x3456 / 256 = 52.3359375.
        mapping = {ACTOR_BASE + 2 * ACTOR_STRIDE + 32: 0x00123456}
        self.assertAlmostEqual(slot_world_x(reader(mapping), 2), 0x3456 / 256.0)
        with self.assertRaises(PatchError):
            slot_world_x(lambda address, size: -1, 2)
        summary = lambda: {'0x8026009': {'first': 7, 'last': 61, 'slots': [2]}}
        report = compare_cast_twins(summary(), summary())
        self.assertTrue(report['identical'])
        other = {'0x8026009': {'first': 7, 'last': 63, 'slots': [2]}}
        report = compare_cast_twins(summary(), other)
        self.assertFalse(report['identical'])
        self.assertFalse(report['timing_equal'])
        self.assertTrue(report['novel_equal'] and report['slots_equal'])
        with self.assertRaises(PatchError):
            compare_cast_twins([], {})

    def test_record_read_and_diff(self):
        from aria.soul_projectiles import SLOT_WORDS
        mapping = {ACTOR_BASE + 2 * ACTOR_STRIDE + 4 * i: 0x1000 + i for i in range(SLOT_WORDS)}
        record = read_slot_record(reader(mapping), 2)
        self.assertEqual(len(record), SLOT_WORDS)
        self.assertEqual(record[0], 0x1000 + 0)
        self.assertEqual(record[SLOT_WORDS - 1], 0x1000 + SLOT_WORDS - 1)
        with self.assertRaises(PatchError):
            read_slot_record(lambda address, size: -1, 2)
        moved = list(record)
        moved[5] += 0x120
        moved[8] = 0
        changes = diff_records(record, moved)
        self.assertEqual([c['index'] for c in changes], [5, 8])
        self.assertEqual(changes[0]['delta'], 0x120)
        self.assertEqual(changes[1]['delta'], -record[8])
        self.assertEqual(diff_records(record, list(record)), [])
        with self.assertRaises(PatchError):
            diff_records(record, record[:3])
        with self.assertRaises(PatchError):
            diff_records(record, ['x'] * SLOT_WORDS)

    def test_word_series_fit(self):
        fit = fit_word_series([0x100, 0x140, 0x180, 0x1C0])
        self.assertTrue(fit['monotonic'] and fit['constant'])
        self.assertEqual(fit['deltas'], [0x40] * 3)
        self.assertEqual(fit['displacement'], 0xC0)
        self.assertEqual(fit['mean_delta'], 0x40)
        uneven = fit_word_series([10, 20, 25, 40], step_frames=2)
        self.assertTrue(uneven['monotonic'])
        self.assertFalse(uneven['constant'])
        self.assertEqual(uneven['step_frames'], 2)
        flat = fit_word_series([7, 7, 7])
        self.assertFalse(flat['monotonic'] or flat['constant'])
        wrapping = fit_word_series([0xFFFFFFF0, 0x10])
        self.assertEqual(wrapping['deltas'], [0x20])
        with self.assertRaises(PatchError):
            fit_word_series([1])
        with self.assertRaises(PatchError):
            fit_word_series([1, -1])
        with self.assertRaises(PatchError):
            fit_word_series([1, 2], step_frames=0)

    def test_byte_diff_ranges(self):
        report = diff_bytes(b'\x00\x01\x02\x03', b'\x00\x09\x02\x08')
        self.assertEqual(report['count'], 2)
        self.assertEqual(report['changed'], [1, 3])
        self.assertEqual(report['ranges'], [{'start': 1, 'length': 1}, {'start': 3, 'length': 1}])
        adjacent = diff_bytes(b'\x00\x00\x00', b'\x01\x02\x00')
        self.assertEqual(adjacent['ranges'], [{'start': 0, 'length': 2}])
        self.assertEqual(diff_bytes(b'ab', b'ab')['count'], 0)
        with self.assertRaises(PatchError):
            diff_bytes(b'', b'')
        with self.assertRaises(PatchError):
            diff_bytes(b'ab', b'abc')

    def test_transition_classification(self):
        report = classify_transition({'a', 'b'}, {'b', 'c', 'd'}, {'b', 'd', 'e'})
        self.assertEqual(report['victim'], ['a'])
        self.assertEqual(report['transient'], ['c'])
        self.assertEqual(report['new_persistent'], ['d'])
        self.assertEqual(classify_transition([], [], [])['victim'], [])
        with self.assertRaises(PatchError):
            classify_transition([1], [], [])
        with self.assertRaises(PatchError):
            classify_transition('ab', [], [])

    def test_hp_scan_leads(self):
        from aria.soul_projectiles import SLOT_WORDS, scan_decreases
        blank = [0] * SLOT_WORDS
        before = {5: list(blank), 9: list(blank)}
        after = {5: list(blank), 9: list(blank)}
        after[5][12] = 0
        before[5][12] = 30
        after[5][12] = 22
        before[9][3] = 1000
        after[9][3] = 10
        report = scan_decreases(before, after, 1, 50)
        self.assertEqual([(lead['slot'], lead['index'], lead['drop']) for lead in report['leads']],
                         [(5, 12, 8)])
        self.assertEqual(scan_decreases(before, after, 1, 5)['leads'], [])
        with self.assertRaises(PatchError):
            scan_decreases({}, after)
        with self.assertRaises(PatchError):
            scan_decreases(before, after, 0, 5)

    def test_oam_entry_decode(self):
        import struct
        # y=80, square 16x16, tile 66, palette 2, priority 1, 16 colors.
        block = struct.pack('<4H', 80 | (0 << 14), 100 | (1 << 14), 66 | (1 << 10) | (2 << 12), 0)
        entry = decode_oam_entry(block)
        self.assertEqual((entry['y'], entry['x']), (80, 100))
        self.assertEqual(entry['tile'], 66)
        self.assertEqual(entry['palette'], 2)
        self.assertEqual(entry['size_pixels'], [16, 16])
        self.assertFalse(entry['colors256'] or entry['disabled'] or entry['affine'])
        wide = decode_oam_entry(struct.pack('<4H', 0 | (1 << 14), 0 | (2 << 14), 0, 0))
        self.assertEqual(wide['size_pixels'], [32, 16])
        hidden = decode_oam_entry(struct.pack('<4H', 0x0200, 0, 0, 0))
        self.assertTrue(hidden['disabled'])
        with self.assertRaises(PatchError):
            decode_oam_entry(b'\x00' * 7)
        with self.assertRaises(PatchError):
            decode_oam_entry(struct.pack('<4H', 0xC000, 0, 0, 0))

    def test_audio_comparison_facts(self):
        import struct
        first = struct.pack('<4h', 0, 100, -100, 0)
        second = struct.pack('<4h', 0, 200, -200, 0)
        report = compare_audio_windows(first, second)
        self.assertFalse(report['equal'])
        self.assertGreater(report['second_peak'], report['first_peak'])
        self.assertGreater(report['second_rms'], report['first_rms'])
        self.assertTrue(compare_audio_windows(first, bytes(first))['equal'])
        with self.assertRaises(PatchError):
            compare_audio_windows(b'', second)

    @unittest.skipUnless((ROOT / 'CastlevaniaAoS.gba').exists(), 'Private host absent')
    def test_host_winged_skeleton_descriptor_pin(self):
        import sys
        sys.path.insert(0, str(ROOT))
        from aria.cli import load_image
        rom = load_image(ROOT / 'CastlevaniaAoS.gba')
        descriptor = describe_winged_skeleton(rom)
        self.assertEqual(descriptor['mana_cost'], EXPECTED_MANA_COST)
        self.assertEqual(descriptor['code'], 0x08026009)
        self.assertTrue(descriptor['code_is_thumb'])
        self.assertEqual(descriptor['max_at_once'], 6)
        self.assertEqual(descriptor['damage_multiplier'], 45)
        self.assertEqual(descriptor['effects'], 1)


if __name__ == '__main__':
    unittest.main()
