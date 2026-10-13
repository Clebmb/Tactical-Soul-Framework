"""Input-hold cast variants for the fizzle gate (private).

Vanilla ROM, controller-only: opening, walk-right into the zombie room, then
one first-cast attempt per hold length (1, 5, 15 frames of Up+B held), each on
a FRESH core so every attempt is a true first cast. Records MP spend and
liveness per hold length. Tests whether the count-gate is really about
presses or about input-held frames.

Read-only: no ROM writes, no authoring. Outputs stay under local/. Original
ROM is never modified.
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
HOLDS = (1, 5, 15)


def attempt(hold):
    host = ROOT / 'CastlevaniaAoS.gba'
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
        baseline = snapshot_actor_window(e.read)
        mp_pre = e.read(0x0201327C, 2)
        e.run(hold, [4, 0])
        e.run(6)
        spent = mp_pre - e.read(0x0201327C, 2)
        live = False
        for _ in range(20):
            e.run(2)
            if novel_codes(baseline, snapshot_actor_window(e.read)):
                live = True
                break
        return {'hold_frames': hold, 'mp_spent': spent,
                'fired': spent == EXPECTED_COST, 'live': live}
    finally:
        e.close()


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    rows = [attempt(hold) for hold in HOLDS]
    report = {
        'route': 'fresh core per hold length; first Up+B cast held N frames',
        'attempts': rows,
        'verdict': ('hold-gated' if any(r['fired'] for r in rows if r['hold_frames'] > 1)
                    and not rows[0]['fired'] else
                    'press-gated (all first casts fizzle regardless of hold)'
                    if not any(r['fired'] for r in rows) else
                    'tap fires: gate is not about first casts here'),
        'original_unchanged': host.read_bytes() == original,
        'rom_sha256': hashlib.sha256(original).hexdigest(),
        'limits': ['one attempt per hold length; zombie-room only'],
    }
    (ROOT / 'local/cast-hold-variants.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    assert host.read_bytes() == original


if __name__ == '__main__':
    main()
