"""Confirm the HP store is a DNA spawn-copy via the zombie's DNA row (static).

docs/ENEMIES.md: enemy DNA is 113 x 36-byte records at 0x080E9644 with
HP/MP/EXP at +12/+14/+16. The 25th slice names the zombie update
FUN_0807a9ec; the 26th slice measured a victim with 18 HP and +1 EXP.
This probe finds the DNA row whose update pointer is the zombie's,
checks its HP/EXP against the native measurements, and closes the
reframe: the 0x0806b06a store copies DNA HP into the instance record
(spawn-init), so the true HP-=damage subtract still lives elsewhere.

Read-only: no ROM writes, no emulation. Outputs stay under local/.
Original ROM is never modified.
"""
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROM_BASE = 0x08000000
DNA_ADDR = 0x080E9644
DNA_COUNT = 113
DNA_STRIDE = 36
ZOMBIE_UPDATE = 0x0807A9EC
MEASURED_HP = 18
MEASURED_EXP = 1


def u32(data, off):
    return struct.unpack('<I', data[off:off + 4])[0]


def u16(data, off):
    return struct.unpack('<H', data[off:off + 2])[0]


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    rom = bytes(original)
    base = DNA_ADDR - ROM_BASE
    zombie = None
    for i in range(DNA_COUNT):
        off = base + i * DNA_STRIDE
        update = u32(rom, off + 4) & ~1
        if update == ZOMBIE_UPDATE:
            zombie = {'index': i,
                      'create_hex': hex(u32(rom, off)),
                      'update_hex': hex(u32(rom, off + 4)),
                      'hp': u16(rom, off + 12),
                      'mp': u16(rom, off + 14),
                      'exp': u16(rom, off + 16)}
    assert zombie is not None, 'zombie DNA row not found'
    report = {
        'dna_hex': hex(DNA_ADDR),
        'zombie_row': zombie,
        'native_measured': {'hp': MEASURED_HP, 'exp': MEASURED_EXP},
        'hp_match': zombie['hp'] == MEASURED_HP,
        'exp_match': zombie['exp'] == MEASURED_EXP,
        'verdict': ('zombie DNA[%d] HP=%d EXP=%d matches the native victim '
                    '(18 HP, +1 EXP): the 0x0806b06a store is a DNA->instance '
                    'spawn copy; the HP-subtract site is still open' % (
                        zombie['index'], zombie['hp'], zombie['exp'])
                    if zombie['hp'] == MEASURED_HP and zombie['exp'] == MEASURED_EXP
                    else 'DNA row does not match native measurements'),
        'original_unchanged': host.read_bytes() == original,
        'rom_sha256': hashlib.sha256(original).hexdigest(),
        'limits': ['static identity only; spawn moment not traced natively',
                   'instance +0x2e = DNA MP is inferred, not natively watched'],
    }
    (ROOT / 'local/spawn-copy.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    assert host.read_bytes() == original
    assert report['hp_match'] and report['exp_match'], 'DNA/native mismatch'


if __name__ == '__main__':
    main()
