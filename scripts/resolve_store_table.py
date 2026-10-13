"""Resolve the literal pool and table behind the HP-store stanza (static).

29th slice (`scripts/scan_hp_drain.py`): the native HP store is
`strh r0,[r1,#0x34]` at 0x0806b06a, fed by `ldrh r0,[r0,#0xc]` after a
x36 index build, with `ldr r2,[pc,#0x4c]` just above. This probe decodes
the full 0x0806af98 function with bl-pair resolution, dumps every
LDR-literal pool word, and follows pool words that point into ROM data:
it reads the pointed-to table's +0xc halfwords at x36 stride and checks
whether the soul's damage candidate (27, 28th slice) appears.

Read-only: no ROM writes, no emulation. Outputs stay under local/.
Original ROM is never modified.
"""
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROM_BASE = 0x08000000
FN_ADDR = 0x0806AF98
STORE_ADDR = 0x0806B06A
DAMAGE_CANDIDATE = 27
STRIDE = 36
FIELD = 0x0C


def hword(data, off):
    return struct.unpack('<H', data[off:off + 2])[0]


def u32(data, off):
    return struct.unpack('<I', data[off:off + 4])[0]


def decode_function(data, start, max_ins=400):
    """Decode until pop {pc}; resolve bl pairs and LDR-literal pools."""
    out = []
    off = start - ROM_BASE
    pending_bl = None
    for _ in range(max_ins):
        ins = hword(data, off)
        addr = ROM_BASE + off
        entry = {'addr_hex': hex(addr), 'ins_hex': hex(ins)}
        if (ins & 0xF800) == 0xF000:
            pending_bl = (ins & 0x7FF) << 12
            if pending_bl & 0x400000:
                pending_bl -= 0x800000
            entry['text'] = 'bl-prefix'
        elif (ins & 0xF800) == 0xF800 and pending_bl is not None:
            target = addr + 2 + pending_bl + ((ins & 0x7FF) << 1)
            entry['text'] = 'bl 0x%x' % (target & 0xFFFFFFFF)
            pending_bl = None
        elif (ins & 0xF800) == 0x4800:
            pool = (addr + 4 & ~3) + (ins & 0xFF) * 4
            word = u32(data, pool - ROM_BASE) if 0 <= pool - ROM_BASE < len(data) - 3 else None
            entry['text'] = 'ldr r%d, [pc, #0x%x]' % ((ins >> 8) & 7, (ins & 0xFF) * 4)
            entry['pool_hex'] = hex(pool)
            entry['pool_word_hex'] = hex(word) if word is not None else None
        elif (ins & 0xFF00) == 0xBD00:
            entry['text'] = 'pop {..pc} + RETURN'
            out.append(entry)
            break
        elif (ins & 0xFFC0) == (0x8000 | (0x1A << 6)):
            entry['text'] = 'strh r%d, [r%d, #0x34] <-- HP STORE?' % (ins & 7, (ins >> 3) & 7)
        else:
            entry['text'] = 'other 0x%x' % ins
        out.append(entry)
        off += 2
    return out


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    rom = bytes(original)
    window = decode_function(rom, FN_ADDR)
    pools = [w for w in window if 'pool_word_hex' in w]
    tables = []
    for p in pools:
        word = int(p['pool_word_hex'], 16) if p['pool_word_hex'] else None
        info = {'ins': p, 'follows': None}
        if word is not None and ROM_BASE <= word < ROM_BASE + len(rom):
            base = word - ROM_BASE
            entries = []
            for i in range(64):
                doff = base + i * STRIDE + FIELD
                if doff + 1 < len(rom):
                    entries.append(hword(rom, doff))
            info['follows'] = {
                'table_hex': hex(word),
                'stride_0x24_plus0xc_first8': entries,
                'candidate_27_present': DAMAGE_CANDIDATE in entries,
            }
        tables.append(info)
    store_seen = any('HP STORE' in w['text'] for w in window)
    report = {
        'function_hex': hex(FN_ADDR),
        'ins_count': len(window),
        'store_in_function': store_seen,
        'literal_pools': tables,
        'verdict': ('HP store %s in 0x0806af98 window; %d literal pool(s), %d table(s) followed' % (
            'SEEN' if store_seen else 'NOT SEEN', len(pools),
            sum(1 for t in tables if t['follows']))),
        'original_unchanged': host.read_bytes() == original,
        'rom_sha256': hashlib.sha256(original).hexdigest(),
        'limits': ['linear decode, pool words may be code pointers not tables',
                   'x36/+0xc table shape is assumed from the stanza, not proven'],
    }
    (ROOT / 'local/store-table.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    assert host.read_bytes() == original
    assert store_seen, 'HP store not inside decoded window'


if __name__ == '__main__':
    main()
