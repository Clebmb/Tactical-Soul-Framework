"""Static damage-candidate census (42nd slice, read-only).

Reads enemy DNA (113 x 36B at 0x080E9644) from the exact host and lists
HP/ATK/DEF for the zombie/skeleton pair plus all high-HP candidates.
Computes what each open formula hypothesis predicts for a second victim
so the native skeleton pin has a fixed decision table before it runs.

Hypotheses for observed zombie damage 22 (descriptor u16[0]=27,
soul-record multiplier 45, zombie DEF=1):
  H-def-ignored: damage = 45//2 = 22 regardless of DEF -> skeleton takes 22.
  H-minus-def:   damage = 23 - DEF (23 = 22 + zombie DEF 1) -> skeleton takes 23.
  H-desc-minus5: damage = 27 - 5 fixed -> skeleton takes 22 (no DEF role).
  H-desc-minus-def: damage = 27 - DEF - 4 -> zombie 22, skeleton 23.
Any skeleton number outside {22, 23} falsifies all four and forces new theory.

Outputs local/damage-candidates.json; ROM never modified.
"""
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM_BASE = 0x08000000
DNA_ADDR = 0x080E9644
DNA_COUNT = 113
DNA_STRIDE = 36


def u32(data, off):
    return struct.unpack('<I', data[off:off + 4])[0]


def u16(data, off):
    return struct.unpack('<H', data[off:off + 2])[0]


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    rom = bytes(original)
    base = DNA_ADDR - ROM_BASE
    rows = []
    for i in range(DNA_COUNT):
        off = base + i * DNA_STRIDE
        rows.append({
            'index': i,
            'update_hex': hex(u32(rom, off + 4)),
            'hp': u16(rom, off + 12),
            'attack': rom[off + 19],
            'defense': rom[off + 20],
        })
    zombie = next(r for r in rows if r['update_hex'] == '0x807a9ed')
    skeleton = next(r for r in rows if r['update_hex'] == '0x80c34f9')
    assert zombie['hp'] == 18 and zombie['defense'] == 1, zombie
    assert skeleton['hp'] == 20 and skeleton['defense'] == 0, skeleton
    predictions = {
        'H-def-ignored (45//2)': 22,
        'H-minus-def (23-DEF)': 23 - skeleton['defense'],
        'H-desc-minus5 (27-5)': 22,
        'H-desc-minus-def (27-DEF-4)': 27 - skeleton['defense'] - 4,
    }
    bulky = sorted([r for r in rows if r['hp'] >= 30],
                   key=lambda r: -r['hp'])[:12]
    report = {
        'zombie': zombie,
        'skeleton': skeleton,
        'skeleton_room_hex': '0x0850F32C',
        'skeleton_route': ('vanilla zombie-room route then workshop-shortcut '
                           'path per scripts/verify_enemies.py; native pin '
                           'runs on the enemy-workshop build where skeleton '
                           'DEF is unchanged (0) and HP is RAM-boosted to 200'),
        'predictions_skeleton': predictions,
        'decision': ('skeleton 22 -> DEF plays no role (H-def-ignored / '
                     'H-desc-minus5 survive); skeleton 23 -> DEF subtracts '
                     '(H-minus-def / H-desc-minus-def survive); else all four '
                     'falsified'),
        'bulky_candidates': bulky,
        'observed_zombie_damage': 22,
        'descriptor_u16_0': 27,
        'soul_multiplier': 45,
        'original_unchanged': host.read_bytes() == original,
        'rom_sha256': hashlib.sha256(original).hexdigest(),
        'limits': ['static DNA only; damage formula needs the native skeleton pin'],
    }
    (ROOT / 'local/damage-candidates.json').write_text(
        json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    assert host.read_bytes() == original


if __name__ == '__main__':
    main()
