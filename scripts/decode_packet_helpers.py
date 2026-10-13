"""Decode the hit-packet helpers for the HP-subtract idiom (static, private).

25th slice (bridge): FUN_0806b1fc queues 4-byte hit packets (types 1/2)
through FUN_080428b4 / FUN_08042848, guarded by flag +0x72 bit 0 and
indexed by +0x73. Slices 29-36 eliminated the drain body and all its
callees as subtract hosts. This probe bounds and decodes both helpers
with the shared machinery and reports SUBs, register-offset stores,
struct +0x34/+0x2e accesses and bl targets.

Read-only: no ROM writes, no emulation. Outputs stay under local/.
Original ROM is never modified.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from decode_callees import summarize

HELPERS = [0x080428B4, 0x08042848, 0x080421AC, 0x080415A8, 0x08041864, 0x080DA7AC,
           0x0806B1FC]


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    rom = bytes(original)
    functions = [summarize(rom, a) for a in HELPERS]
    hits = [f for f in functions
            if f.get('bounded') and (f['subs'] or f['register_stores']
                                     or f['half34'] or f['half2e'])]
    report = {
        'functions': functions,
        'subtract_candidates': [h['addr_hex'] for h in hits],
        'verdict': ('%d/%d helpers bounded; %d with SUB/store/+0x34/+0x2e idioms' % (
            sum(1 for f in functions if f.get('bounded')), len(functions), len(hits))),
        'original_unchanged': host.read_bytes() == original,
        'rom_sha256': hashlib.sha256(original).hexdigest(),
        'limits': ['linear decode; register contents unknown',
                   'bounds are prologue/pop heuristic, not analysis-backed'],
    }
    (ROOT / 'local/packet-helpers.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    slim = [{k: (v if k not in ('subs', 'register_stores', 'half34', 'half2e', 'calls')
                else v if k == 'calls' else len(v)) for k, v in f.items()} for f in functions]
    print(json.dumps({'functions': slim,
                      'candidates': report['subtract_candidates'],
                      'verdict': report['verdict'],
                      'original_unchanged': report['original_unchanged']}, indent=2))
    assert host.read_bytes() == original


if __name__ == '__main__':
    main()
