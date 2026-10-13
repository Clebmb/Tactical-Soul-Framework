"""Decode the drain's callees for the HP-subtract idiom (static, private).

35th slice: FUN_0806ae54 (0x0806ae54..0x0806b0a2) holds no subtract idiom
itself; its in-body calls are 0x08000a90, 0x080daa00, 0x0800da0,
0x080dc264, 0x0801d94. This probe bounds each callee by prologue/pop scan,
decodes it with the shared decoder, and reports per function: bounds,
SUB (imm/reg), STRH/LDRH #0x34/#0x2e, register-offset stores, and bl
targets. The HP subtract (HP-=damage with a +0x34 store) must show up as
a SUB feeding a store in one of these — or elimination continues.

Read-only: no ROM writes, no emulation. Outputs stay under local/.
Original ROM is never modified.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from decode_queue_builder import decode
from decode_drain import find_prologue, find_end

ROM_BASE = 0x08000000
CALLEES = [0x08000A90, 0x080DAA00, 0x0800DA0, 0x080DC264, 0x0801D94]


def summarize(data, addr):
    start = find_prologue(data, addr)
    if start is None:
        return {'addr_hex': hex(addr), 'bounded': False}
    end = find_end(data, start)
    window = decode(data, start, end or addr + 0x200)
    texts = [w['text'] for w in window]
    joined = ' '.join(texts)
    subs = [w for w in window if w['text'].startswith('sub ')]
    reg_stores = [w for w in window if w['text'].startswith(('str ', 'strh r', 'strb '))
                  and '#0x' not in w['text'] and ', [r' in w['text']]
    half34 = [w for w in window if '#0x34' in w['text']
              and w['text'].startswith(('ldrh', 'strh'))]
    half2e = [w for w in window if '#0x2e' in w['text']
              and w['text'].startswith(('ldrh', 'strh'))]
    calls = [w['text'] for w in window if w['text'].startswith('bl 0x')]
    return {'addr_hex': hex(addr), 'bounded': end is not None,
            'bounds_hex': [hex(start), hex(end) if end else None],
            'ins_count': len(window),
            'subs': subs, 'register_stores': reg_stores,
            'half34': half34, 'half2e': half2e, 'calls': calls}


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    rom = bytes(original)
    functions = [summarize(rom, a) for a in CALLEES]
    hits = [f for f in functions
            if f.get('bounded') and (f['subs'] or f['register_stores']
                                     or f['half34'] or f['half2e'])]
    report = {
        'functions': functions,
        'subtract_candidates': hits,
        'verdict': ('%d/%d callees bounded; %d with SUB/store/+0x34/+0x2e idioms' % (
            sum(1 for f in functions if f.get('bounded')), len(functions), len(hits))),
        'original_unchanged': host.read_bytes() == original,
        'rom_sha256': hashlib.sha256(original).hexdigest(),
        'limits': ['linear decode; register contents unknown',
                   'bounds are prologue/pop heuristic, not analysis-backed'],
    }
    (ROOT / 'local/callees.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    slim = [{k: (v if k not in ('subs', 'register_stores', 'half34', 'half2e')
                else len(v)) for k, v in f.items()} for f in functions]
    print(json.dumps({'functions': slim,
                      'candidates': [h['addr_hex'] for h in hits],
                      'verdict': report['verdict'],
                      'original_unchanged': report['original_unchanged']}, indent=2))
    assert host.read_bytes() == original


if __name__ == '__main__':
    main()
