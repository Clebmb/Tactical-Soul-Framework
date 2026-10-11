"""Synthetic tests for checked native label renames (no ROM)."""
import hashlib
import struct
import unittest
from aria.core import PatchError, RomImage
from aria.labels import apply_label_edits, label_span, resolve_label
from aria.text import POINTERS

BASE = 0x08000000
POINTER_TABLE = POINTERS
STRINGS = 0x08700000


def build_image(entries):
    """Synthetic image with a pointer table plus headered ASCII labels."""
    data = bytearray(0x800000)

    def put(address, payload):
        data[address - BASE:address - BASE + len(payload)] = payload
    table = bytearray(4 * 1024)
    addr = STRINGS
    spans = {}
    for text_id, text in entries.items():
        raw = b'\x01\x00' + text.encode('ascii') + b'\x06'
        put(addr, raw)
        struct.pack_into('<I', table, text_id * 4, addr)
        spans[text_id] = (addr + 2, len(text))
        addr += len(raw)
    put(POINTER_TABLE, bytes(table))
    original = bytes(data)
    profile = dict(id='synthetic', rom_base=BASE, size=len(data),
                   sha256=hashlib.sha256(data).hexdigest(),
                   allocation_ranges=[dict(start=0x08680000, end=0x08800000)])
    return RomImage(original, profile), spans


class LabelTests(unittest.TestCase):
    def setUp(self):
        # text_id 0x5B reads 'Knife' (5 chars), 0x5C reads 'Cape' (4 chars).
        entries = {0x5B + i: 'Item%03d' % i for i in range(136)}
        entries.update({0x25D + i: 'Foe%03d' % i for i in range(113)})
        entries[0x5B] = 'Knife'
        entries[0x5C] = 'Cape'
        self.rom, self.spans = build_image(entries)

    def test_resolve_and_span(self):
        row = resolve_label(self.rom, 'item', name='knife')
        self.assertEqual((row['index'], row['current'], row['max_length']), (0, 'Knife', 5))
        self.assertEqual(label_span(self.rom, 0x5B)[:2], self.spans[0x5B])

    def test_same_length_and_padded_edits(self):
        report = apply_label_edits(self.rom, [
            {'kind': 'item', 'item': 'Knife', 'expect': 'Knife', 'to': 'Fangs'},
            {'kind': 'item', 'index': 1, 'to': 'Cap'},
        ])
        self.assertEqual([(r['before'], r['after']) for r in report],
                         [('Knife', 'Fangs'), ('Cape', 'Cap ')])
        self.assertEqual(len(self.rom.ledger), 2)
        # Terminator preserved; only the intended spans differ from original.
        for text_id, _ in ((0x5B, 0), (0x5C, 1)):
            start, length = self.spans[text_id]
            off = start - BASE
            self.assertEqual(self.rom.original[off + length:off + length + 1], b'\x06')
        changed = {i for i, (a, b) in
                   enumerate(zip(self.rom.original, bytes(self.rom.data))) if a != b}
        knife, cape = self.spans[0x5B], self.spans[0x5C]
        expect = set(range(knife[0] - BASE, knife[0] - BASE + knife[1]))
        expect.add(cape[0] - BASE + cape[1] - 1)
        self.assertEqual(changed, expect)

    def test_rejections(self):
        with self.assertRaises(PatchError):
            resolve_label(self.rom, 'soul', name='x')
        with self.assertRaises(PatchError):
            resolve_label(self.rom, 'item', name='no-such-label')
        with self.assertRaises(PatchError):
            resolve_label(self.rom, 'item', index=136)
        with self.assertRaisesRegex(PatchError, 'precondition'):
            apply_label_edits(self.rom, [{'kind': 'item', 'item': 'Knife',
                                          'expect': 'Dagger', 'to': 'Fangs'}])
        for bad in ('TooLongName', '', 'F\xc3\xa4ngs'):
            with self.assertRaises(PatchError):
                apply_label_edits(self.rom, [{'kind': 'item', 'item': 'Knife', 'to': bad}])
        with self.assertRaisesRegex(PatchError, 'Repeated'):
            apply_label_edits(self.rom, [{'kind': 'item', 'index': 0, 'to': 'Fangs'},
                                         {'kind': 'item', 'index': 0, 'to': 'Blades'}])
        with self.assertRaises(PatchError):
            apply_label_edits(self.rom, [{'kind': 'enemy', 'item': 'Knife', 'to': 'Fangs'}])


if __name__ == '__main__':
    unittest.main()
