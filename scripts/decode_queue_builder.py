"""Decode the hit-packet queue builder for descriptor loads (static, private).

25th slice: FUN_0806b1fc reads the hit packet via +0x65 and queues 4-byte
hit packets (types 1/2) through FUN_080428b4/08042848. 33rd slice: the
0x0806b06a twin store is a DNA spawn copy, not the damage path. This probe
decodes 0x0806b000-0x0806b300 with bl-pair and LDR-literal resolution and
reports every LDRH [Rn, #0x0/#0x2] (candidate descriptor damage loads),
every register-offset STRH (candidate HP subtract), and every bl target.

Read-only: no ROM writes, no emulation. Outputs stay under local/.
Original ROM is never modified.
"""
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROM_BASE = 0x08000000
START = 0x0806B000
END = 0x0806B300


def hword(data, off):
    return struct.unpack('<H', data[off:off + 2])[0]


def u32(data, off):
    return struct.unpack('<I', data[off:off + 4])[0]


def decode(data, start, end):
    out = []
    off = start - ROM_BASE
    pending_bl = None
    reg_ops = ('str', 'strh', 'strb', 'ldrsb', 'ldr', 'ldrh', 'ldrb', 'ldrsh')
    while ROM_BASE + off < end:
        ins = hword(data, off)
        addr = ROM_BASE + off
        e = {'addr_hex': hex(addr), 'ins_hex': hex(ins)}
        if (ins & 0xF800) == 0xF000:
            pending_bl = (ins & 0x7FF) << 12
            if pending_bl & 0x400000:
                pending_bl -= 0x800000
            e['text'] = 'bl-prefix'
        elif (ins & 0xF800) == 0xF800 and pending_bl is not None:
            # BL target base is the FIRST halfword + 4 = suffix addr + 2.
            e['text'] = 'bl 0x%x' % ((addr + 2 + pending_bl + ((ins & 0x7FF) << 1)) & 0xFFFFFFFF)
            pending_bl = None
        elif (ins & 0xF000) == 0x5000:
            e['text'] = '%s r%d, [r%d, r%d]' % (reg_ops[(ins >> 9) & 7],
                                                ins & 7, (ins >> 3) & 7, (ins >> 6) & 7)
        elif (ins & 0xF800) == 0x4800:
            pool = (addr + 4 & ~3) + (ins & 0xFF) * 4
            word = u32(data, pool - ROM_BASE) if 0 <= pool - ROM_BASE < len(data) - 3 else None
            e['text'] = 'ldr r%d, [pc,#0x%x]' % ((ins >> 8) & 7, (ins & 0xFF) * 4)
            e['pool_hex'] = hex(pool)
            e['pool_word_hex'] = hex(word) if word is not None else None
        elif (ins & 0xF800) == 0x8000:
            e['text'] = 'strh r%d, [r%d, #0x%x]' % (ins & 7, (ins >> 3) & 7, ((ins >> 6) & 0x1F) * 2)
        elif (ins & 0xF800) == 0x8800:
            e['text'] = 'ldrh r%d, [r%d, #0x%x]' % (ins & 7, (ins >> 3) & 7, ((ins >> 6) & 0x1F) * 2)
        elif (ins & 0xFF00) == 0xB500:
            e['text'] = 'push {..lr}'
        elif (ins & 0xFF00) == 0xBD00:
            e['text'] = 'pop {..pc} + RETURN'
        else:
            e['text'] = 'other'
        out.append(e)
        off += 2
    return out


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    rom = bytes(original)
    window = decode(rom, START, END)
    desc_loads = [w for w in window if w['text'] in ('ldrh r0, [r0, #0x0]', 'ldrh r1, [r1, #0x0]',
                                                     'ldrh r0, [r0, #0x2]', 'ldrh r1, [r1, #0x2]')]
    desc_loads = [w for w in window if w['text'].startswith('ldrh') and w['text'].endswith(('#0x0]', '#0x2]'))
                    and ', [r' in w['text']]
    reg_strh = [w for w in window if w['text'].startswith('strh r') and ', [r' in w['text']
                and '#0x' not in w['text']]
    calls = [w for w in window if w['text'].startswith('bl 0x')]
    imm34 = [w for w in window if '#0x34' in w['text']]
    report = {
        'range_hex': [hex(START), hex(END)],
        'ins_count': len(window),
        'descriptor_load_candidates': desc_loads,
        'register_strh': reg_strh,
        'bl_targets': [w['text'] for w in calls],
        'imm34_accesses': imm34,
        'full_window': window,
        'verdict': ('%d descriptor-load candidates, %d register-STRH, %d calls in range' % (
            len(desc_loads), len(reg_strh), len(calls))),
        'original_unchanged': host.read_bytes() == original,
        'rom_sha256': hashlib.sha256(original).hexdigest(),
        'limits': ['linear decode across function/pool boundaries; literal pools decode as code',
                   'register contents unknown; candidates need dataflow confirmation'],
    }
    (ROOT / 'local/queue-builder.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    slim = {k: v for k, v in report.items() if k != 'full_window'}
    print(json.dumps(slim, indent=2))
    assert host.read_bytes() == original


if __name__ == '__main__':
    main()
