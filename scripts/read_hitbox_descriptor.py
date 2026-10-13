"""Read the soul's hitbox descriptor chain (static, private).

Decompiler fact (docs/SOUL-DECOMPILE.md): soul state 0 passes word 2 of the
static struct at *PTR_080260a0 as the hitbox descriptor to FUN_0803b924.
This probe walks that chain from the exact ROM and dumps the descriptor,
checking the damage-field candidate (u16[0] = 27) against the natively
measured 18-HP one-cast kill (overkill clamped at zero explains 18 < 27).

Read-only: no ROM writes, no authoring, no emulation. Outputs stay under
local/. Original ROM is never modified.
"""
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROM_BASE = 0x08000000
PTR_SLOT = 0x260A0
EXPECTED_DESCRIPTOR = 0x082308E8
EXPECTED_U16_0 = 27
MEASURED_KILL_HP = 18


def u32(data, offset):
    return struct.unpack('<I', data[offset:offset + 4])[0]


def u16(data, offset):
    return struct.unpack('<H', data[offset:offset + 2])[0]


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    rom = bytes(original)
    struct_ptr = u32(rom, PTR_SLOT)
    struct_off = struct_ptr - ROM_BASE
    words = [u32(rom, struct_off + 4 * i) for i in range(3)]
    descriptor = words[2]
    desc_off = descriptor - ROM_BASE
    raw = rom[desc_off:desc_off + 32]
    halves = [u16(rom, desc_off + i) for i in range(0, 32, 2)]
    report = {
        'chain': 'PTR_080260a0 -> struct -> word2 = descriptor (FUN_0803b924 param_2)',
        'struct_ptr_hex': hex(struct_ptr),
        'struct_words_hex': [hex(w) for w in words],
        'descriptor_ptr_hex': hex(descriptor),
        'descriptor_u16': halves,
        'descriptor_hex': raw.hex(),
        'damage_candidate': halves[0],
        'chain_intact': descriptor == EXPECTED_DESCRIPTOR and halves[0] == EXPECTED_U16_0,
        'consistent_with_kill': halves[0] >= MEASURED_KILL_HP,
        'verdict': ('descriptor base damage 27 one-shots the 18-HP zombie; '
                    'measured drop 18 is overkill clamped at zero'
                    if descriptor == EXPECTED_DESCRIPTOR and halves[0] >= MEASURED_KILL_HP
                    else 'descriptor chain differs from decompile-time read'),
        'original_unchanged': host.read_bytes() == original,
        'rom_sha256': hashlib.sha256(original).hexdigest(),
        'limits': ['damage field is a candidate (u16[0]); non-lethal +0x34 check vs tougher victim still open'],
    }
    (ROOT / 'local/hitbox-descriptor.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    assert host.read_bytes() == original
    assert report['chain_intact'], 'descriptor chain changed: ' + json.dumps(report['struct_words_hex'])


if __name__ == '__main__':
    main()
