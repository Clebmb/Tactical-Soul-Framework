import unittest
from aria.core import PatchError
from aria.native_events import FIELDS, observe_native_events, observe_progression_flags


class NativeEventTests(unittest.TestCase):
    def test_reads_and_masks(self):
        calls = []
        def read(address, size):
            calls.append((address, size))
            return 0x81 if address == 0x0200042C else 0
        row = observe_native_events(read)
        self.assertEqual(calls, list(FIELDS.values()))
        self.assertTrue(row['modal_lock_bit'])
        self.assertFalse(row['persistent_progression_binding'])
        self.assertEqual(row['context']['global_flags'], 0x81)

    def test_other_bits_are_not_modal(self):
        self.assertFalse(observe_native_events(lambda a, n: 128)['modal_lock_bit'])

    def test_invalid_reads(self):
        for value in (-1, 256, True, None):
            with self.subTest(value=value), self.assertRaises(PatchError):
                observe_native_events(lambda a, n: value)

    def test_progression_nibble_and_context(self):
        values = {0x02000010: 4, 0x02000064: 1, 0x02000088: 0x08500000}
        for raw, count in ((0, 0), (0x10, 0), (0xA1, 1), (0xFF, 15)):
            values[0x0201331C] = raw
            row = observe_progression_flags(lambda a, n: values.get(a, 0))
            self.assertEqual(row['first_red_soul']['count'], count)
            self.assertEqual(row['first_red_soul']['name'], 'Winged Skeleton')
            self.assertEqual(row['first_red_soul']['record_index'], 1)
            self.assertEqual(row['flags']['first_red_soul_owned'], bool(count))

    def test_progression_rejects_unsettled_or_invalid_reads(self):
        base = {0x02000010: 4, 0x02000064: 1, 0x02000088: 0x08500000}
        for address, value in ((0x02000010, 2), (0x02000064, 3),
                               (0x02000088, 0), (0x02000088, 0x08500001),
                               (0x0201331C, True), (0x0201331C, 256)):
            values = {**base, address: value}
            with self.subTest(address=address, value=value), self.assertRaises(PatchError):
                observe_progression_flags(lambda a, n: values.get(a, 0))
