"""Bound and decode the HP-drain function FUN_0806ae54 (static, private).

25th slice (bridge): FUN_0806ae54 drains queued hit packets into victim HP
(short at record+0x34). Slices 29-34 eliminated the neighboring code (the
only nearby +0x34 store is a DNA spawn copy). This probe bounds 0x0806ae54
by prologue/pop scan, decodes it with the shared decoder from
scripts/decode_queue_builder.py, and reports SUBs, register-offset stores,
LDR-literal pools and bl targets — the HP-subtract signature.

Read-only: no ROM writes, no emulation. Outputs stay under local/.
Original ROM is never modified.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from decode_queue_builder import decode, hword

ROM_BASE = 0x08000000
DRAIN_ADDR = 0x0806AE54
DEATH_PATH = 0x080421AC


def find_prologue(data, addr):
    off = addr - ROM_BASE
    for i in range(0, 0x100):
        if off - 2 * i < 0:
            return None
        if (hword(data, off - 2 * i) & 0xFF00) == 0xB500:
            return ROM_BASE + off - 2 * i
    return None


def find_end(data, start):
    off = start - ROM_BASE
    for i in range(0x400):
        ins = hword(data, off + 2 * i)
        if (ins & 0xFF00) == 0xBD00 or ins == 0x4770:
            return ROM_BASE + off + 2 * i + 2
    return None


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    rom = bytes(original)
    start = find_prologue(rom, DRAIN_ADDR)
    assert start is not None, 'no prologue found'
    end = find_end(rom, start)
    window = decode(rom, start, end or DRAIN_ADDR + 0x200)
    full = []
    off = start - ROM_BASE
    while ROM_BASE + off < (end or DRAIN_ADDR + 0x200):
        ins = hword(rom, off)
        a = ROM_BASE + off
        if (ins & 0xF800) == 0x1E00:
            t = 'sub r%d, r%d, #%d' % (ins & 7, (ins >> 3) & 7, (ins >> 6) & 7)
        elif (ins & 0xF800) == 0x1800 and (ins & 0x0200):
            t = 'sub r%d, r%d, r%d' % (ins & 7, (ins >> 3) & 7, (ins >> 6) & 7)
        elif (ins & 0xF800) == 0x1C00 and not (ins & 0x0200):
            t = 'add r%d, r%d, #%d' % (ins & 7, (ins >> 3) & 7, (ins >> 6) & 7)
        elif (ins & 0xF800) == 0x3000:
            t = 'add r%d, #0x%x' % ((ins >> 8) & 7, ins & 0xFF)
        elif (ins & 0xF800) == 0x3800:
            t = 'sub r%d, #0x%x' % ((ins >> 8) & 7, ins & 0xFF)
        elif (ins & 0xF800) == 0x2800:
            t = 'cmp r%d, #%d' % ((ins >> 8) & 7, ins & 0xFF)
        else:
            t = None
        if t:
            full.append({'addr_hex': hex(a), 'ins_hex': hex(ins), 'text': t})
        off += 2
    arith = full
    calls = [{'addr_hex': w['addr_hex'], 'target': w['text']} for w in window
             if w['text'].startswith('bl 0x')]
    in_body = [c for c in calls if int(c['addr_hex'], 16) < (end or DRAIN_ADDR + 0x200)]
    pools = [w for w in window if 'pool_word_hex' in w]
    stores = [w for w in window if w['text'].startswith(('strh', 'str ', 'strb', 'ldrsh', 'ldrh', 'ldr '))]
    death_calls = [c for c in in_body if abs(int(c['target'][3:], 16) - DEATH_PATH) < 0x100]
    report = {
        'bounds_hex': [hex(start), hex(end) if end else None],
        'ins_count': len(window),
        'arith': arith,
        'mem_access': stores,
        'bl_targets': [c['target'] for c in calls],
        'in_body_calls': in_body,
        'literal_pools': pools,
        'death_path_calls': death_calls,
        'verdict': ('drain bounded %s..%s: %d arith, %d mem, %d calls%s' % (
            hex(start), hex(end) if end else '?', len(arith), len(stores),
            len(calls), '; death-path call present' if death_calls else '; no death-path call')),
        'original_unchanged': host.read_bytes() == original,
        'rom_sha256': hashlib.sha256(original).hexdigest(),
        'limits': ['linear decode; register contents unknown',
                   'bounds are prologue/pop heuristic, not analysis-backed'],
    }
    (ROOT / 'local/drain.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    slim = {k: v for k, v in report.items()}
    print(json.dumps(slim, indent=2))
    assert host.read_bytes() == original


if __name__ == '__main__':
    main()
