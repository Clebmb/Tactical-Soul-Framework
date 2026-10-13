"""Synthetic direct/rhythm resolution fixtures; no commercial ROM data."""
import unittest

from aria.audio import resolve_note_voice

BASE = 0x08000000


def entry(kind=0, key=60, word=0, pan=0):
    return bytes([kind, key, 0, pan]) + word.to_bytes(4, 'little') + bytes([255, 128, 64, 128])


class VoiceResolutionTests(unittest.TestCase):
    def fixture(self, child=None):
        rom = bytearray(256)
        rom[:12] = entry(0x80, word=BASE + 32)
        rom[32 + 2 * 12:32 + 3 * 12] = child or entry(key=48, pan=0xE0)
        return rom

    def test_direct_retains_note_key(self):
        got = resolve_note_voice(entry(key=20), 0, 0, 70)
        self.assertEqual((got['offset'], got['playback_key'], got['rhythm_pan']),
                         (0, 70, None))

    def test_rhythm_uses_note_index_and_child_pitch(self):
        rom = self.fixture()
        before = bytes(rom)
        got = resolve_note_voice(rom, 0, 0, 2)
        self.assertEqual((got['offset'], got['playback_key'], got['rhythm_pan']),
                         (56, 48, 64))
        self.assertEqual(bytes(rom), before)

    def test_rhythm_without_forced_pan(self):
        got = resolve_note_voice(self.fixture(entry(pan=0x7F)), 0, 0, 2)
        self.assertIsNone(got['rhythm_pan'])

    def test_pointer_and_entry_bounds(self):
        for pointer in (BASE - 1, BASE + 256, 0):
            rom = self.fixture()
            rom[:12] = entry(0x80, word=pointer)
            with self.assertRaises(ValueError):
                resolve_note_voice(rom, 0, 0, 2)
        for rom, bank, index, key in ((b'\x00' * 11, 0, 0, 0),
                                       (self.fixture(), 0, 127, 0),
                                       (self.fixture(), 0, 0, 127)):
            with self.assertRaises(ValueError):
                resolve_note_voice(rom, bank, index, key)

    def test_nested_banks_and_unknown_child_rejected(self):
        for kind in (0x40, 0x80, 0xFF):
            with self.assertRaises(ValueError):
                resolve_note_voice(self.fixture(entry(kind)), 0, 0, 2)
        with self.assertRaises(ValueError):
            resolve_note_voice(entry(0x40), 0, 0, 2)

    def test_bad_arguments_and_child_key(self):
        for value in (-1, 128, True, 1.5):
            with self.assertRaises(ValueError):
                resolve_note_voice(self.fixture(), 0, value, 2)
            with self.assertRaises(ValueError):
                resolve_note_voice(self.fixture(), 0, 0, value)
        with self.assertRaises(ValueError):
            resolve_note_voice(self.fixture(), -1, 0, 2)
        with self.assertRaises(ValueError):
            resolve_note_voice(self.fixture(entry(key=255)), 0, 0, 2)

    def test_custom_rom_base(self):
        rom = self.fixture()
        rom[:12] = entry(0x80, word=0x1000 + 32)
        self.assertEqual(resolve_note_voice(rom, 0, 0, 2, rom_base=0x1000)['offset'], 56)
