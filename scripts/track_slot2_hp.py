"""Absolute-value track of zombie-candidate slot 2 from full HP to kill (private).

Vanilla ROM, controller-only: walk into the zombie room, capture slot 2's
full 33-word record after every kill-loop roll until EXP pays. Reports which
words fall monotonically from plausible HP-scale values and which zero early
(despawn/overwrite, not damage).

Read-only: no ROM writes, no authoring. A monotonic fall to ~0 at the kill
roll names an HP candidate, not a certified semantic. Outputs stay under
local/. Original ROM is never modified.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aria.soul_projectiles import read_slot_record
from emulator import Emulator

ZOMBIE_ROOM = 0x0850F15C
MAX_ROLLS = 40
HP_FLOOR = 50


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
        for _ in range(600):
            e.run(1, [7])
            if e.read(0x02000088) == ZOMBIE_ROOM:
                break
        assert e.read(0x02000088) == ZOMBIE_ROOM, 'did not reach zombie room'
        e.run(70, [7])
        e.run(60)
        exp0 = e.read(0x0201328C)
        series = []
        kill_roll = None
        for roll in range(MAX_ROLLS):
            if e.read(0x0201327A, 2) < HP_FLOOR or e.read(0x0201328C) != exp0:
                kill_roll = roll
                break
            direction = 7 if (roll // 10) % 2 == 0 else 6
            e.run(1, [0, direction])
            e.run(12, [direction])
            e.run(1)
            e.run(12)
            series.append({'roll': roll, 'code_hex': hex(e.read(0x020004E4 + 2 * 0x84)),
                           'words': [hex(w) for w in read_slot_record(e.read, 2)],
                           'hp': e.read(0x0201327A, 2), 'exp': e.read(0x0201328C)})
        exp1 = e.read(0x0201328C)
        words = {}
        for index in range(33):
            values = [int(row['words'][index], 16) for row in series]
            words[str(index)] = {
                'first_hex': hex(values[0]) if values else None,
                'last_hex': hex(values[-1]) if values else None,
                'distinct': len(set(values)),
                'monotonic_down': all(a >= b for a, b in zip(values, values[1:])) and values[0] > values[-1]
                if len(values) > 1 else False,
            }
        report = {
            'route': 'vanilla opening + walk-right + sword rolls with slot-2 snapshots',
            'rolls': len(series),
            'kill_roll': kill_roll,
            'killed': exp1 != exp0,
            'exp_before': exp0,
            'exp_after': exp1,
            'series': series,
            'word_summary': words,
            'scope': 'monotonic fall to ~0 at the kill roll names an HP candidate only',
            'original_unchanged': host.read_bytes() == original,
            'rom_sha256': hashlib.sha256(original).hexdigest(),
            'limits': ['one run, one room; slot 2 assumed the victim by position'],
        }
        (ROOT / 'local/slot2-hp-track.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        short = {index: facts for index, facts in words.items() if facts['distinct'] > 1}
        print(json.dumps({'rolls': len(series), 'kill_roll': kill_roll,
                          'exp': [exp0, exp1], 'changing_words': short}, indent=2))
    finally:
        e.close()
        assert host.read_bytes() == original


if __name__ == '__main__':
    main()
