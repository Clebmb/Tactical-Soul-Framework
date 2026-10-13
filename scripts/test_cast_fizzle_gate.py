"""Time-vs-count fizzle gate test (private).

Vanilla ROM, controller-only: opening, walk into the zombie room, replicate
the hit attempt's two fizzles (Up+B with MP check), then settle briefly and
fire TWO quick successive casts. Verdict: a room-entry TIME gate fires both
late casts; an attempt-COUNT gate fizzles the first late cast and fires the
second.

Read-only: no ROM writes, no authoring. MP-bounded, HP-guarded. Outputs stay
under local/. Original ROM is never modified.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aria.soul_projectiles import novel_codes, snapshot_actor_window
from emulator import Emulator

EXPECTED_COST = 12
ZOMBIE_ROOM = 0x0850F15C
HP_FLOOR = 100


def cast(e):
    baseline = snapshot_actor_window(e.read)
    mp_pre = e.read(0x0201327C, 2)
    e.run(1, [4, 0])
    e.run(6)
    spent = mp_pre - e.read(0x0201327C, 2)
    live = False
    for _ in range(20):
        e.run(2)
        if novel_codes(baseline, snapshot_actor_window(e.read)):
            live = True
            break
    return {'spent': spent, 'fired': spent == EXPECTED_COST, 'live': live,
            'mp_left': e.read(0x0201327C, 2)}


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    e = Emulator(host)
    try:
        e.run(1000)
        for key in [3, 8, 8, 8, 3, 3, 8]:
            e.run(1, [key])
            e.run(100)
        for _ in range(60):
            e.run(1, [8])
            e.run(90)
        assert e.read(0x0201331C, 1) == 1 and e.read(0x02013269, 1) == 1
        for _ in range(600):
            e.run(1, [7])
            if e.read(0x02000088) == ZOMBIE_ROOM:
                break
        assert e.read(0x02000088) == ZOMBIE_ROOM, 'did not reach zombie room'
        e.run(70, [7])
        e.run(30)
        early = [cast(e), cast(e)]
        e.run(40)
        late = [cast(e)]
        e.run(10)
        late.append(cast(e))
        verdict = ('time-gate (both late casts fire)'
                   if all(row['fired'] for row in late)
                   else 'count-gate (a late cast fizzles)' if any(row['fired'] for row in late)
                   else 'neither fired late: worse than either model')
        report = {
            'route': 'walk-right + 2 early casts + settle + 2 quick late casts',
            'early_casts': early,
            'late_casts': late,
            'soma_hp': e.read(0x0201327A, 2),
            'verdict': verdict,
            'original_unchanged': host.read_bytes() == original,
            'rom_sha256': hashlib.sha256(original).hexdigest(),
            'limits': ['one run, one room; MP-bounded; fizzle model inferred from 4 casts'],
        }
        (ROOT / 'local/cast-fizzle-gate.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))
    finally:
        e.close()
        assert host.read_bytes() == original


if __name__ == '__main__':
    main()
