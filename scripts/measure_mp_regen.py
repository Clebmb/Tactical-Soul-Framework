"""MP regen rate after a verified cast (private).

The 18th audio slice found net MP spend reading 11 instead of 12 over a
60-frame window, attributed to mid-window MP regen. This probe pins the
rate: opening room, controller-only, one verified Up+B cast (12 MP), then
11 samples of MP (2-byte word at 0x0201327C) every 30 idle frames.

Read-only: no ROM writes, no authoring. Outputs stay under local/. Original
ROM is never modified.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT))
from emulator import Emulator

MP_ADDR = 0x0201327C
EXPECTED_COST = 12
STEP = 30
SAMPLES = 11


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
        e.run(1, [3])
        e.run(30)
        e.run(1, [8])
        e.run(30)
        assert e.read(0x02000064, 1) == 6, 'soul menu did not open'
        for key in [0, 0]:
            e.run(1, [key])
            e.run(30)
        mp_pre = e.read(MP_ADDR, 2)
        e.run(1, [4, 0])
        e.run(6)
        spent = mp_pre - e.read(MP_ADDR, 2)
        series = []
        for _ in range(SAMPLES):
            e.run(STEP)
            series.append(e.read(MP_ADDR, 2))
        diffs = [b - a for a, b in zip(series, series[1:])]
        report = {
            'route': 'opening room; one verified cast then idle sampling',
            'mp_before_cast': mp_pre,
            'mp_spent_on_cast': spent,
            'cast_fired': spent == EXPECTED_COST,
            'sample_step_frames': STEP,
            'mp_series': series,
            'per_step_diffs': diffs,
            'verdict': ('regen ~%g MP per %d frames'
                        % (sum(diffs) / len(diffs), STEP)
                        if spent == EXPECTED_COST and all(d >= 0 for d in diffs)
                        and sum(diffs) > 0 else
                        'no measurable regen in window or cast did not fire cleanly'),
            'accounting_rule': ('subtract regen (~1 MP per 60 frames at this rate) '
                                'from gross spend before comparing to cost 12'),
            'original_unchanged': host.read_bytes() == original,
            'rom_sha256': hashlib.sha256(original).hexdigest(),
            'limits': ['opening room, full-MP start, one run; rate may vary with max MP'],
        }
    finally:
        e.close()
    (ROOT / 'local/mp-regen.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    assert host.read_bytes() == original


if __name__ == '__main__':
    main()
