"""Native sword-kill code attribution for the hallway zombie (private).

Vanilla ROM, controller-only: opening, walk-right into the zombie room, a calm
code sample, sword kill-loops (B attacks, pattern from
scripts/scan_soul_spawn.py) until EXP moves, then a post-kill sample.
Classifies codes with ``aria.soul_projectiles.classify_transition`` and checks
whether the hit-attempt unknowns (0x807a9ed/0x807b311/0x807b3c9) fall in the
victim/transient classes.

Read-only: no ROM writes, no authoring, no RNG/inventory forcing. Classes
describe timing, not proven death/burst semantics. Outputs stay under local/.
Original ROM is never modified.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aria.soul_projectiles import (
    classify_transition,
    code_to_slots,
    snapshot_actor_window,
)
from emulator import Emulator

ZOMBIE_ROOM = 0x0850F15C
ZOMBIE_EXP = 7
MAX_ROLLS = 150
HP_FLOOR = 20
HIT_ATTEMPT_UNKNOWN = ['0x807a9ed', '0x807b311', '0x807b3c9']


def codes(e):
    return {hex(code) for code in snapshot_actor_window(e.read).values()}


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
        calm = set()
        for _ in range(10):
            e.run(6)
            calm |= codes(e)
        exp_before = e.read(0x0201328C)
        kill_roll = None
        during = set()
        for roll in range(MAX_ROLLS):
            if e.read(0x0201327A, 2) < HP_FLOOR:
                break
            direction = 7 if (roll // 10) % 2 == 0 else 6
            e.run(1, [0, direction])
            e.run(12, [direction])
            e.run(1)
            e.run(12)
            during |= codes(e)
            if e.read(0x0201328C) != exp_before:
                kill_roll = roll
                break
        exp_after = e.read(0x0201328C)
        after = set()
        for _ in range(10):
            e.run(6)
            after |= codes(e)
        classification = classify_transition(calm, during, after)
        report = {
            'route': 'vanilla opening + walk-right + calm sample + sword kill-loop',
            'exp_before': exp_before,
            'exp_after': exp_after,
            'exp_delta': exp_after - exp_before,
            'expected_zombie_exp': ZOMBIE_EXP,
            'kill_roll': kill_roll,
            'killed': kill_roll is not None,
            'calm_codes': sorted(calm),
            'classification': classification,
            'hit_attempt_unknowns': {code: {
                'in_calm': code in calm,
                'in_victim': code in classification['victim'],
                'in_transient': code in classification['transient'],
                'in_new_persistent': code in classification['new_persistent'],
            } for code in HIT_ATTEMPT_UNKNOWN},
            'code_slots_at_kill': code_to_slots(snapshot_actor_window(e.read)),
            'original_unchanged': host.read_bytes() == original,
            'rom_sha256': hashlib.sha256(original).hexdigest(),
            'limits': [
                'vanilla zombie room only; one run',
                'timing classes, not proven death/burst/pickup semantics',
                'post-kill respawns beyond the 60-frame window unmapped',
            ],
        }
        (ROOT / 'local/zombie-kill-codes.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))
    finally:
        e.close()
        assert host.read_bytes() == original


if __name__ == '__main__':
    main()
