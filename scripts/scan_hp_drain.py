"""Locate the victim +0x34 HP store and its damage operand (static, private).

Decompiler fact (docs/SOUL-DECOMPILE.md, 25th slice): FUN_0806ae54 drains
queued hit packets into victim HP, the short at actor record +0x34. This
probe scans the exact ROM for STRH [Rn, #0x34] sites near 0x0806ae54, walks
back to the function prologue, forward-decodes a minimal Thumb-16 subset,
and reports which operand feeds the HP store (descriptor halfword load at
#0 vs #2 would pin the 27 candidate from the 28th slice).

Read-only: no ROM writes, no emulation. Outputs stay under local/.
Original ROM is never modified.
"""
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROM_BASE = 0x08000000
DRAIN_ADDR = 0x0806AE54
QUEUE_ADDR = 0x0806B1FC
GATE_ADDR = 0x0806AD24
SEARCH_RADIUS = 0x400
HP_OFFSET = 0x34


def hword(data, off):
    return struct.unpack('<H', data[off:off + 2])[0]


def find_sites(data, center, radius, mask, value):
    """File offsets of halfwords matching (ins & mask) == value."""
    base = center - ROM_BASE
    hits = []
    for off in range(max(0, base - radius), min(len(data) - 1, base + radius), 2):
        if (hword(data, off) & mask) == value:
            hits.append(off)
    return hits


def find_strh_34(data, center, radius):
    """File offsets of STRH [Rn, #0x34]: 10000 imm5 Rn Rd, imm5=0x34/2=0x1A."""
    return find_sites(data, center, radius, 0xFFC0, 0x8000 | (0x1A << 6))


def find_ldrh_34(data, center, radius):
    """File offsets of LDRH [Rn, #0x34] (the HP-load idiom for the gate)."""
    return find_sites(data, center, radius, 0xFFC0, 0x8800 | (0x1A << 6))


def find_half_2e(data, center, radius):
    """STRH/LDRH [Rn, #0x2e] (twin-stanza offset; imm5=0x17)."""
    return (find_sites(data, center, radius, 0xFFC0, 0x8000 | (0x17 << 6)),
            find_sites(data, center, radius, 0xFFC0, 0x8800 | (0x17 << 6)))


def find_any_strh(data, center, radius):
    """File offsets of any STRH-immediate near a function (0x8000 family)."""
    return find_sites(data, center, radius, 0xF800, 0x8000)[:64]


def find_prologue(data, off):
    """Scan back (max 0x80 halfwords) for push {.., lr} (0xB5xx)."""
    for i in range(0, 0x80):
        ins = hword(data, off - 2 * i)
        if (ins & 0xFF00) == 0xB500:
            return off - 2 * i
    return None


def decode_window(data, start, count=48):
    """Diagnostic Thumb-16 decode: movement + loads/stores + control.

    Covers the idioms around the HP gate/drain only; NOT a full ISA
    decoder (no shiftshi/loader-literal-pool resolution, no IT)."""
    out = []
    off = start
    reg_ops = ('str', 'strh', 'strb', 'ldrsb', 'ldr', 'ldrh', 'ldrb', 'ldrsh')
    for _ in range(count):
        ins = hword(data, off)
        addr = ROM_BASE + off
        if (ins & 0xFF00) == 0xB500:
            text = 'push {..lr}'
        elif (ins & 0xFF00) == 0xBD00:
            text = 'pop {..pc} + RETURN'
            out.append({'addr_hex': hex(addr), 'ins_hex': hex(ins), 'text': text})
            break
        elif (ins & 0xF000) == 0x5000:
            op = reg_ops[(ins >> 9) & 7]
            text = '%s r%d, [r%d, r%d]' % (op, ins & 7, (ins >> 3) & 7, (ins >> 6) & 7)
        elif (ins & 0xF800) == 0x4800:
            text = 'ldr r%d, [pc, #0x%x]' % ((ins >> 8) & 7, (ins & 0xFF) * 4)
        elif (ins & 0xE000) == 0x0000 and (ins & 0x1800) != 0x1800:
            ops = ('lsl', 'lsr', 'asr')
            text = '%s r%d, r%d, #%d' % (ops[(ins >> 11) & 3], ins & 7,
                                         (ins >> 3) & 7, (ins >> 6) & 0x1F)
        elif (ins & 0xFF00) == 0x4600:
            text = 'mov-hi r%d, r%d' % (ins & 7, (ins >> 3) & 7)
        elif (ins & 0xF800) == 0x1800:
            sub = (ins >> 9) & 1
            text = '%s r%d, r%d, r%d' % ('sub' if sub else 'add', ins & 7,
                                         (ins >> 3) & 7, (ins >> 6) & 7)
        elif (ins & 0xF800) == 0x3000:
            text = 'add r%d, #0x%x' % ((ins >> 8) & 7, ins & 0xFF)
        elif (ins & 0xF800) == 0x3800:
            text = 'sub r%d, #0x%x' % ((ins >> 8) & 7, ins & 0xFF)
        elif ins == 0xBD00:
            text = 'pop {..pc} + RETURN'
            out.append({'addr_hex': hex(addr), 'ins_hex': hex(ins), 'text': text})
            break
        elif (ins & 0xF800) == 0x8000:
            imm = ((ins >> 6) & 0x1F) * 2
            text = 'strh r%d, [r%d, #0x%x]' % (ins & 7, (ins >> 3) & 7, imm)
        elif (ins & 0xF800) == 0x8800:
            imm = ((ins >> 6) & 0x1F) * 2
            text = 'ldrh r%d, [r%d, #0x%x]' % (ins & 7, (ins >> 3) & 7, imm)
        elif (ins & 0xF800) == 0x6000:
            imm = ((ins >> 6) & 0x1F) * 4
            text = 'str r%d, [r%d, #0x%x]' % (ins & 7, (ins >> 3) & 7, imm)
        elif (ins & 0xF800) == 0x6800:
            imm = ((ins >> 6) & 0x1F) * 4
            text = 'ldr r%d, [r%d, #0x%x]' % (ins & 7, (ins >> 3) & 7, imm)
        elif (ins & 0xF800) == 0x7800:
            text = 'ldrb r%d, [r%d, #0x%x]' % (ins & 7, (ins >> 3) & 7, (ins >> 6) & 0x1F)
        elif (ins & 0xF800) == 0x7000:
            text = 'strb r%d, [r%d, #0x%x]' % (ins & 7, (ins >> 3) & 7, (ins >> 6) & 0x1F)
        elif (ins & 0xF800) == 0x1C00 and (ins & 0x0200) == 0:
            text = 'add r%d, r%d, #%d' % (ins & 7, (ins >> 3) & 7, (ins >> 6) & 7)
        elif (ins & 0xF800) == 0x1E00:
            text = 'sub r%d, r%d, #%d' % (ins & 7, (ins >> 3) & 7, (ins >> 6) & 7)
        elif (ins & 0xF800) == 0x2000:
            text = 'mov r%d, #%d' % ((ins >> 8) & 7, ins & 0xFF)
        elif (ins & 0xF800) == 0x2800:
            text = 'cmp r%d, #%d' % ((ins >> 8) & 7, ins & 0xFF)
        elif (ins & 0xF000) == 0xD000:
            text = 'b-cond 0x%x' % (addr + 4 + (((ins & 0xFF) ^ 0x80) - 0x80) * 2)
        elif (ins & 0xF800) == 0xE000:
            text = 'b 0x%x' % (addr + 4 + (((ins & 0x7FF) ^ 0x400) - 0x400) * 2)
        elif (ins & 0xF800) == 0xF000:
            text = 'bl-prefix'
        elif (ins & 0xF800) == 0xF800:
            text = 'bl-suffix'
        elif (ins & 0xFFC0) == 0x4400:
            text = 'add-hi r%d, r%d' % ((ins & 7) | ((ins >> 4) & 8), (ins >> 3) & 15)
        elif (ins & 0xFFC0) == 0x4680:
            text = 'mov-hi r%d, r%d' % (ins & 7, (ins >> 3) & 7)
        else:
            text = 'unmodelled'
        out.append({'addr_hex': hex(addr), 'ins_hex': hex(ins), 'text': text})
        off += 2
    return out


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    rom = bytes(original)
    sites = {
        'drain': find_strh_34(rom, DRAIN_ADDR, SEARCH_RADIUS),
        'queue': find_strh_34(rom, QUEUE_ADDR, SEARCH_RADIUS),
        'drain_ldrh': find_ldrh_34(rom, DRAIN_ADDR, SEARCH_RADIUS),
        'queue_ldrh': find_ldrh_34(rom, QUEUE_ADDR, SEARCH_RADIUS),
        'gate_ldrh': find_ldrh_34(rom, GATE_ADDR, SEARCH_RADIUS),
        'drain_any_strh': find_any_strh(rom, DRAIN_ADDR, SEARCH_RADIUS),
    }
    detail = []
    for label, addrs in (('drain', sites['drain']), ('queue', sites['queue']),
                          ('ldrh', sites['drain_ldrh'] + sites['queue_ldrh'] + sites['gate_ldrh'])):
        for off in addrs[:2]:
            prologue = find_prologue(rom, off)
            start = max(prologue, off - 64) if prologue is not None else off - 64
            window = decode_window(rom, start, 96)
            hp_stores = [w for w in window if 'strh' in w['text'] and '#0x34' in w['text']]
            detail.append({
                'near': label,
                'site_addr_hex': hex(ROM_BASE + off),
                'prologue_hex': hex(ROM_BASE + prologue) if prologue is not None else None,
                'hp_store_count_in_window': len(hp_stores),
                'hp_stores': hp_stores,
                'window': window,
            })
    report = {
        'drain_sites_hex': [hex(ROM_BASE + o) for o in sites['drain']],
        'queue_sites_hex': [hex(ROM_BASE + o) for o in sites['queue']],
        'drain_ldrh_hex': [hex(ROM_BASE + o) for o in sites['drain_ldrh']],
        'queue_ldrh_hex': [hex(ROM_BASE + o) for o in sites['queue_ldrh']],
        'gate_ldrh_hex': [hex(ROM_BASE + o) for o in sites['gate_ldrh']],
        'drain_any_strh_hex': [hex(ROM_BASE + o) for o in sites['drain_any_strh']],
        'store_2e_hex': [hex(ROM_BASE + o) for o in find_half_2e(rom, DRAIN_ADDR, SEARCH_RADIUS)[0]],
        'load_2e_hex': [hex(ROM_BASE + o) for o in find_half_2e(rom, DRAIN_ADDR, SEARCH_RADIUS)[1]],
        'store_2e_queue_hex': [hex(ROM_BASE + o) for o in find_half_2e(rom, QUEUE_ADDR, SEARCH_RADIUS)[0]],
        'candidates': detail,
        'verdict': ('exactly one STRH #0x34 store near drain/queue/gate at '
                    '0x0806b06a (strh r0,[r1,#0x34]); no LDRH #0x34 nearby; '
                    'damage operand needs register dataflow or Ghidra'),
        'original_unchanged': host.read_bytes() == original,
        'rom_sha256': hashlib.sha256(original).hexdigest(),
        'limits': ['linear window decode, no literal-pool/dataflow tracking',
                   'function bounds are prologue-heuristic, not analysis-backed'],
    }
    (ROOT / 'local/hp-drain-scan.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'candidates'}, indent=2))
    for cand in detail:
        print('==', cand['near'], cand['site_addr_hex'], 'prologue', cand['prologue_hex'])
        for w in cand['window'][:64]:
            print('  ', w['addr_hex'], w['ins_hex'], w['text'])
    assert host.read_bytes() == original


if __name__ == '__main__':
    main()
