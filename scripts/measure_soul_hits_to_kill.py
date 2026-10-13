"""Soul hits-to-kill vs sword baseline on the hallway zombie (private).

Vanilla ROM, controller-only: opening, walk-right into the zombie room, then
cast Up+B facing right until EXP moves or MP runs out (12 MP/cast from 80 MP:
max 6 live casts, fizzles free). Records presses, live casts (MP spend),
projectile liveness and EXP. Compares against the sword baseline (kill at
rolls 8–10 paying +1 EXP, per local/zombie-kill-codes.json and
local/enemy-hp-scan.json): equal-or-fewer live casts implies soul damage
at or above sword-per-hit levels, without needing the HP address.

Read-only: no ROM writes, no authoring. HP-guarded. Outputs stay under
local/. Original ROM is never modified.
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
MAX_PRESSES = 30


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
        e.run(60)
        exp0 = e.read(0x0201328C)
        presses = []
        live_casts = 0
        for press in range(MAX_PRESSES):
            mp = e.read(0x0201327C, 2)
            if e.read(0x0201327A, 2) < HP_FLOOR or e.read(0x0201328C) != exp0:
                break
            if mp < EXPECTED_COST:
                presses.append({'press': press, 'skipped': True, 'reason': 'mp_empty',
                                'mp': mp})
                break
            baseline = snapshot_actor_window(e.read)
            e.run(2, [7])
            e.run(1, [4, 0])
            e.run(6)
            spent = mp - e.read(0x0201327C, 2)
            live = False
            for _ in range(20):
                e.run(2)
                if novel_codes(baseline, snapshot_actor_window(e.read)):
                    live = True
                    break
            if spent == EXPECTED_COST:
                live_casts += 1
            presses.append({'press': press, 'mp_spent': spent, 'live': live,
                            'hp': e.read(0x0201327A, 2), 'exp': e.read(0x0201328C)})
            e.run(30)
        exp1 = e.read(0x0201328C)
        report = {
            'route': 'vanilla opening + walk-right + Up+B to kill or MP out',
            'presses': presses,
            'press_count': sum(1 for row in presses if 'mp_spent' in row),
            'live_casts': live_casts,
            'killed': exp1 != exp0,
            'exp_before': exp0,
            'exp_after': exp1,
            'sword_baseline': {'kill_rolls': '8-10', 'exp': 1,
                               'source': 'local/zombie-kill-codes.json'},
            'scope': ('fewer-or-equal live casts vs sword rolls implies soul damage '
                      'at/above sword levels; no HP address needed'),
            'original_unchanged': host.read_bytes() == original,
            'rom_sha256': hashlib.sha256(original).hexdigest(),
            'limits': ['one run, one room; fizzles consume presses but not MP'],
        }
        (ROOT / 'local/soul-hits-to-kill.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps({k: report[k] for k in (
            'press_count', 'live_casts', 'killed', 'exp_before', 'exp_after',
            'scope', 'limits')}, indent=2))
    finally:
        e.close()
        assert host.read_bytes() == original


if __name__ == '__main__':
    main()
