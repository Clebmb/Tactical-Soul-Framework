"""Absolute-value track of the 0x807A9ED holder slots to the kill (private).

Vanilla ROM, controller-only: walk into the zombie room, snapshot the slots
holding calm-resident 0x807A9ED (the attributed live zombie from the
sword-kill control), then snapshot those slots after every kill-loop roll
until EXP pays. Reports per-word trajectories and monotonic falls.

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
from aria.soul_projectiles import (
    ACTOR_SLOTS,
    ACTOR_STRIDE,
    read_slot_record,
    snapshot_actor_window,
)
from emulator import Emulator

ZOMBIE_ROOM = 0x0850F15C
ZOMBIE_CODE = 0x807A9ED
MAX_ROLLS = 40
HP_FLOOR = 50
TRACK_WORDS = (4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15)
HIGH_WORDS = tuple(range(16, 32))


def holders(e):
    return sorted(slot for slot, code in snapshot_actor_window(e.read).items()
                  if code == ZOMBIE_CODE)


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
        start_slots = holders(e)
        assert start_slots, 'no 0x807A9ED holders found'
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
            row = {'roll': roll, 'hp': e.read(0x0201327A, 2), 'exp': e.read(0x0201328C),
                   'holders': holders(e), 'slots': {}}
            for slot in sorted(set(start_slots) | set(row['holders'])):
                record = read_slot_record(e.read, slot)
                row['slots'][str(slot)] = {str(index): hex(record[index])
                                           for index in TRACK_WORDS + HIGH_WORDS}
            series.append(row)
        exp1 = e.read(0x0201328C)
        trajectories = {}
        for slot in sorted({slot for row in series for slot in row['slots']}, key=int):
            trajectories[str(slot)] = {}
            for index in TRACK_WORDS + HIGH_WORDS:
                values = [int(row['slots'][str(slot)][str(index)], 16)
                          for row in series if str(slot) in row['slots']]
                trajectories[str(slot)][str(index)] = {
                    'first_hex': hex(values[0]), 'last_hex': hex(values[-1]),
                    'distinct': len(set(values)),
                    'monotonic_down': all(a >= b for a, b in zip(values, values[1:]))
                    and values[0] > values[-1] if len(values) > 1 else False,
                }
        report = {
            'route': 'vanilla opening + walk-right + sword rolls with holder snapshots',
            'start_slots': start_slots,
            'rolls': len(series),
            'kill_roll': kill_roll,
            'killed': exp1 != exp0,
            'exp_before': exp0,
            'exp_after': exp1,
            'series': series,
            'trajectories': trajectories,
            'scope': 'monotonic fall to ~0 at the kill roll names an HP candidate only',
            'original_unchanged': host.read_bytes() == original,
            'rom_sha256': hashlib.sha256(original).hexdigest(),
            'limits': ['one run, one room; holder identity from the kill-control code set'],
        }
        (ROOT / 'local/zombie-hp-track.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        short = {slot: {index: facts for index, facts in words.items() if facts['distinct'] > 1}
                 for slot, words in trajectories.items()}
        print(json.dumps({'start_slots': start_slots, 'rolls': len(series),
                          'kill_roll': kill_roll, 'exp': [exp0, exp1],
                          'changing': short}, indent=2))
    finally:
        e.close()
        assert host.read_bytes() == original


if __name__ == '__main__':
    main()
