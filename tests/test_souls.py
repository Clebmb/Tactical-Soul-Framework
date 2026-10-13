import unittest
from pathlib import Path
from aria.core import PatchError
from aria.souls import plan_soul_edits, apply_soul_edits


def edit(value=6, expected=12):
    return [{'soul': 'winged-skeleton', 'expect': {'mana_cost': expected}, 'fields': {'mana_cost': value}}]


class SoulContractTests(unittest.TestCase):
    def test_cost_bounds_and_hex(self):
        for value in (1, 999, '0x6'):
            self.assertGreater(plan_soul_edits(edit(value))['mana_cost'], 0)
        for value in (0, 1000, True, -1):
            with self.assertRaises(PatchError): plan_soul_edits(edit(value))

    def test_unsupported_fields_identity_and_duplicates(self):
        invalid = [[], edit() * 2, [{'soul': 'other', 'expect': {'mana_cost': 12}, 'fields': {'mana_cost': 6}}],
                   [{'soul': 'winged-skeleton', 'expect': {}, 'fields': {'mana_cost': 6}}],
                   [{'soul': 'winged-skeleton', 'expect': {'mana_cost': 12}, 'fields': {'code': 1}}]]
        for edits in invalid:
            with self.assertRaises(PatchError): plan_soul_edits(edits)

    def test_private_host_preservation_preconditions_and_conflicts(self):
        from aria.cli import load_image
        from aria.tables import layout
        root = Path(__file__).resolve().parents[1]
        if not (root/'CastlevaniaAoS.gba').exists(): self.skipTest('Private host absent')
        rom = load_image(root/'CastlevaniaAoS.gba')
        before = bytes(rom.data)
        with self.assertRaises(PatchError): apply_soul_edits(rom, edit(expected=13))
        self.assertEqual(bytes(rom.data), before)
        apply_soul_edits(rom, edit())
        _, address = layout('red_souls', 1); offset = rom.offset(address + 6, 2)
        self.assertEqual(bytes(rom.data[:offset]), before[:offset])
        self.assertEqual(bytes(rom.data[offset+2:]), before[offset+2:])
        self.assertEqual(len(rom.ledger), 1)
        with self.assertRaises(PatchError): apply_soul_edits(rom, edit(3, 6))
        fresh = load_image(root/'CastlevaniaAoS.gba')
        fresh.write(address + 10, b'\0\0', 'prior-other-soul-field')
        changed = bytes(fresh.data)
        with self.assertRaises(PatchError): apply_soul_edits(fresh, edit())
        self.assertEqual(bytes(fresh.data), changed)
        self.assertEqual(len(fresh.ledger), 1)
