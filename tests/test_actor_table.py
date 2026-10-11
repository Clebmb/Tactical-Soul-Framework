"""Static host-gated facts for the v0.29 walker visual binding.

Needs the private host ROM; skipped without it. No emulator, no RAM
fixtures: table regularity, walker row values, palette hash, graphics
struct shape, LZ art-page decoding and reference counts. Live VRAM
evidence lives in docs/ENEMY-BINDING.md, not here.
"""
import hashlib
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TABLE = 0x080E13C0
ROWS = 32
WALKER_ROW = 8
WALKER_PALETTE = 0x0820B164
WALKER_PALETTE_SHA256 = '36c99a2c7a680c2c2a1501058de3a6646b19362a319465461e9d4b36f83d6ab7'
WALKER_GFX = 0x0823199C
WALKER_FRAMES = 0x0823195C
WALKER_PARTS = 0x0823189C
WALKER_ART_LZ = 0x08635990


def blob():
    return (ROOT / 'CastlevaniaAoS.gba').read_bytes()


def u32(data, address):
    return struct.unpack('<I', data[address - 0x08000000:address - 0x08000000 + 4])[0]


@unittest.skipUnless((ROOT / 'CastlevaniaAoS.gba').exists(), 'Private host unavailable')
class ActorTableTests(unittest.TestCase):
    def test_table_row_count_and_ranges(self):
        data = blob()
        rows = []
        for r in range(ROWS):
            p, g, s = struct.unpack('<3I', data[TABLE - 0x08000000 + r * 12:TABLE - 0x08000000 + r * 12 + 12])
            rows.append((p, g, s))
        for p, g, s in rows:
            self.assertTrue(0x0820B000 <= p < 0x08210000, hex(p))
            self.assertTrue(0x08230000 <= g < 0x08270000, hex(g))
            self.assertTrue(0x08080000 <= s < 0x08700000, hex(s))
        pals = [p for p, _, _ in rows]
        self.assertEqual(len(set(pals)), ROWS)
        # Contiguous strides except the single documented rows 9->10 gap.
        for r in range(ROWS - 1):
            if r == 9:
                self.assertEqual(pals[r + 1] - pals[r], 0x44)
            else:
                self.assertEqual(pals[r + 1] - pals[r], 0x24)

    def test_walker_row_values_and_palette(self):
        data = blob()
        p, g, s = struct.unpack('<3I', data[TABLE - 0x08000000 + WALKER_ROW * 12:TABLE - 0x08000000 + WALKER_ROW * 12 + 12])
        self.assertEqual((p, g, s), (WALKER_PALETTE, WALKER_GFX, 0x081D08E8))
        self.assertEqual(data[WALKER_PALETTE - 0x08000000:WALKER_PALETTE - 0x08000000 + 4], bytes.fromhex('00 04 01 00'))
        palette = data[WALKER_PALETTE + 4 - 0x08000000:WALKER_PALETTE + 4 - 0x08000000 + 32]
        self.assertEqual(hashlib.sha256(palette).hexdigest(), WALKER_PALETTE_SHA256)

    def test_walker_graphics_struct_shape(self):
        data = blob()
        a, b = struct.unpack('<2H', data[WALKER_GFX - 0x08000000:WALKER_GFX - 0x08000000 + 4])
        parts, frames, anim = struct.unpack('<3I', data[WALKER_GFX - 0x08000000 + 4:WALKER_GFX - 0x08000000 + 16])
        self.assertEqual((a, b, parts, frames), (12, 2, WALKER_PARTS, WALKER_FRAMES))
        self.assertEqual(u32(data, anim), WALKER_FRAMES)
        self.assertEqual(data[WALKER_PARTS - 0x08000000:WALKER_PARTS - 0x08000000 + 16], bytes(16))
        entries = [struct.unpack('<4I', data[WALKER_PARTS - 0x08000000 + e * 16:WALKER_PARTS - 0x08000000 + e * 16 + 16])
                   for e in range(12)]
        for zero, _flags, _top, _bottom in entries:
            self.assertEqual(zero, 0)

    def test_walker_art_page_decode_and_single_wrapper_reference(self):
        sys_path = str(ROOT)
        import sys
        sys.path.insert(0, sys_path)
        from aria.compression import decode_lz10
        data = blob()
        out, _ = decode_lz10(data[WALKER_ART_LZ - 0x08000000:WALKER_ART_LZ - 0x08000000 + 0x9000])
        self.assertEqual(len(out), 0x2004)
        word = struct.pack('<I', WALKER_ART_LZ)
        hits, off = [], 0
        while True:
            i = data.find(word, off)
            if i < 0:
                break
            hits.append(0x08000000 + i)
            off = i + 1
        self.assertEqual(hits, [0x082052DC])


if __name__ == '__main__':
    unittest.main()
