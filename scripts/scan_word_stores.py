"""Scan decoded bodies for full-word stores covering +0x34 (static, private).

Slices 29-38 eliminated every halfword SUB/store idiom across the drain
body, its callees, the packet helpers, the death path, the shared
primitive windows and the queue window. The decoder never modeled the
full-word STR family (0x6000 imm / 0x5000 reg), so a word store covering
victim +0x34 (offsets 0x30-0x38, or register-offset) is the last static
stone. This probe scans the union of decoded ranges for STR-word-imm at
0x30/0x34/0x38, any STR-reg, and LDR-word #0x34.

Read-only: no ROM writes, no emulation. Outputs stay under local/.
Original ROM is never modified.
"""
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROM_BASE = 0x08000000
RANGES = [(0x0806AE54, 0x0806B300), (0x08042848, 0x08042A62),
          (0x080421AC, 0x0804276E), (0x08000DA0, 0x08000E00),
          (0x08001D00, 0x08001E00), (0x080DA6B0, 0x080DA800)]


def hword(data, off):
    return struct.unpack('<H', data[off:off + 2])[0]


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    rom = bytes(original)
    word34, word_regs, word_loads = [], [], []
    for start, end in RANGES:
        off = start - ROM_BASE
        while ROM_BASE + off < end:
            if not (0 <= off <= len(rom) - 2):
                print('OUT-OF-BOUNDS off=%r len=%d range=%s' % (off, len(rom), hex(start)))
                break
            ins = hword(rom, off)
            addr = ROM_BASE + off
            if (ins & 0xF800) == 0x6000:
                byte_off = ((ins >> 6) & 0x1F) * 4
                if byte_off in (0x30, 0x34, 0x38):
                    word34.append({'addr_hex': hex(addr), 'ins_hex': hex(ins),
                                   'text': 'str r%d, [r%d, #0x%x]' % (
                                       ins & 7, (ins >> 3) & 7, byte_off)})
            elif (ins & 0xF000) == 0x5000 and ((ins >> 9) & 7) == 0:
                word_regs.append({'addr_hex': hex(addr), 'ins_hex': hex(ins),
                                  'text': 'str r%d, [r%d, r%d]' % (
                                      ins & 7, (ins >> 3) & 7, (ins >> 6) & 7)})
            elif (ins & 0xF800) == 0x6800 and ((ins >> 6) & 0x1F) * 4 == 0x34:
                word_loads.append({'addr_hex': hex(addr), 'ins_hex': hex(ins),
                                   'text': 'ldr r%d, [r%d, #0x34]' % (
                                       ins & 7, (ins >> 3) & 7)})
            off += 2
    report = {
        'ranges_hex': [[hex(a), hex(b)] for a, b in RANGES],
        'word_stores_30_38': word34,
        'word_stores_register': word_regs,
        'word_loads_34': word_loads,
        'verdict': ('%d word-store(s) at 0x30/0x34/0x38, %d register-STR, %d LDR-word #0x34' % (
            len(word34), len(word_regs), len(word_loads))),
        'original_unchanged': host.read_bytes() == original,
        'rom_sha256': hashlib.sha256(original).hexdigest(),
        'limits': ['raw pattern scan, no function bounds; register contents unknown'],
    }
    (ROOT / 'local/word-stores.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    assert host.read_bytes() == original


if __name__ == '__main__':
    main()
