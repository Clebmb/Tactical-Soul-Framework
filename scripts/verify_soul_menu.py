"""Private deterministic native menu-label attribution for the first red soul.

Three fresh-core runs, controller-only native opening and menu navigation.
The diagnostic changes one label's characters only; original input unchanged.
"""
import hashlib
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aria.cli import load_image
from aria.labels import label_span
from aria.text import original_label
from aria.tables import read_record
from emulator import Emulator


def capture(path, mana_cost):
    e = Emulator(path)
    try:
        e.run(1000)
        for key in [3, 8, 8, 8, 3, 3, 8]:
            e.run(1, [key]); e.run(100)
        for _ in range(60):
            e.run(1, [8]); e.run(90)
        assert e.read(0x0201331C, 1) == 1
        assert e.read(0x02013269, 1) == 1
        e.run(1, [3]); e.run(30)
        e.run(1, [8]); e.run(30)
        assert e.read(0x02000064, 1) == 6
        image = e.image.convert('RGB').copy()
        for key in [0, 0]:
            e.run(1, [key]); e.run(30)
        assert e.read(0x02000064, 1) == 1 and e.read(0x020004EE, 1) == 0
        mp, hp = e.read(0x0201327C, 2), e.read(0x0201327A, 2)
        e.run(1, [4, 0]); e.run(6)  # Native Up + configured B attack, not jump A.
        assert e.read(0x0201327C, 2) == mp - mana_cost
        assert e.read(0x0201327A, 2) == hp
        assert e.read(0x0201331C, 1) == 1 and e.read(0x02013269, 1) == 1
        return image, {'mp_before': mp, 'mp_after': e.read(0x0201327C, 2),
                       'hp_unchanged': hp, 'ownership_unchanged': True, 'equipped_id': 1}
    finally:
        e.close()


def main():
    host = ROOT / 'CastlevaniaAoS.gba'; original = host.read_bytes()
    rom = load_image(host)
    assert original_label(rom, 0xE3) == 'Winged Skeleton'
    cost = read_record(rom, 'red_souls', 1)['mana_cost']
    assert cost == 12
    address, length, terminator = label_span(rom, 0xE3)
    replacement = b'First Red Soul'.ljust(length, b' ')
    assert len(replacement) == length
    rom.write(address, replacement, 'first-red-soul-label-diagnostic', b'Winged Skeleton')
    folder = ROOT / 'local/soul-menu'; folder.mkdir(parents=True, exist_ok=True)
    diagnostic = folder / 'label-diagnostic.gba'; rom.output(diagnostic, host)
    control, use = capture(host, cost)
    repeat, repeat_use = capture(host, cost)
    changed, changed_use = capture(diagnostic, cost)
    assert use == repeat_use == changed_use
    assert control.size == repeat.size == changed.size == (240, 160)
    assert control.tobytes() == repeat.tobytes(), 'native menu control is not deterministic'
    positions = [(x, y) for y in range(160) for x in range(240)
                 if control.getpixel((x, y)) != changed.getpixel((x, y))]
    assert positions, 'diagnostic label was not rendered'
    regions = [(40, 20, 130, 40), (132, 76, 235, 92)]
    counts = [sum(left <= x < right and top <= y < bottom for x, y in positions)
              for left, top, right, bottom in regions]
    assert all(counts) and sum(counts) == len(positions), (counts, len(positions))
    for name, image in (('control', control), ('repeat', repeat), ('diagnostic', changed)):
        image.save(folder / (name + '.png'))
    assert host.read_bytes() == original
    assert rom.read(address + length, 1) == bytes([terminator])
    report = {'text_id': '0xE3', 'label': 'Winged Skeleton', 'ownership_byte': 1,
              'equipped_red_soul_id': 1, 'control_repeat_identical': True,
              'record_table': 'red_souls', 'record_index': 1, 'native_use': use,
              'native_mana_cost': cost,
              'changed_pixels': len(positions), 'label_region_changed_pixels': counts,
              'regions': regions, 'original_unchanged': True,
              'diagnostic_sha256': hashlib.sha256(diagnostic.read_bytes()).hexdigest(),
              'limits': ['one menu/slot/count only; no duplicate-count or other soul-type proof',
                         'private label diagnostic is not a production soul-label writer or grant ABI',
                         'no projectile/damage or broader combat effect certification']}
    (ROOT / 'local/soul-menu-verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
