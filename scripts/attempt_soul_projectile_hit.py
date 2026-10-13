"""Native Winged Skeleton hit attempt on the hallway zombie (private).

Vanilla ROM, controller-only: opening grants and equips the soul, Soma walks
right into the zombie room (0x0850F15C, route from scripts/scan_soul_spawn.py),
then casts Up+B facing right up to eight times while MP allows. Each attempt
records MP/HP/EXP, whether the known projectile actors went live, and any EXP
gain (vanilla zombie: 30 HP, 7 EXP per kill, per scripts/verify_enemies.py).

Read-only: no ROM writes, no authoring, no RNG/inventory forcing. A kill
attributes damage through EXP; a miss (no EXP change with live projectiles)
bounds the damage claim honestly. Outputs stay under local/. Original ROM is
never modified.
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
ZOMBIE_EXP = 7
MAX_ATTEMPTS = 8
HP_FLOOR = 20


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
        attempts = []
        killed = False
        for attempt in range(MAX_ATTEMPTS):
            mp = e.read(0x0201327C, 2)
            hp = e.read(0x0201327A, 2)
            exp = e.read(0x0201328C)
            if mp < EXPECTED_COST or hp < HP_FLOOR or killed:
                attempts.append({'attempt': attempt, 'skipped': True, 'reason': 'mp_hp_or_killed',
                                 'mp': mp, 'hp': hp, 'exp': exp})
                break
            baseline = snapshot_actor_window(e.read)
            pre_codes = sorted(hex(code) for code in baseline.values())
            pre_pos = e.read(0x02000526, 2) + e.read(0x0200A09A, 2)
            e.run(2, [7])
            context = {'state': e.read(0x02000010, 1), 'substate': e.read(0x02000064, 1),
                       'player_state': e.read(0x020004EE, 1),
                       'vel_x': e.read(0x0200052C, 2), 'vel_y': e.read(0x02000530, 2)}
            e.run(1, [4, 0])
            e.run(6)
            spent = mp - e.read(0x0201327C, 2)
            live, gained = False, False
            for _ in range(20):
                e.run(2)
                if novel_codes(baseline, snapshot_actor_window(e.read)):
                    live = True
                if e.read(0x0201328C) != exp:
                    gained = True
                    break
            exp_after = e.read(0x0201328C)
            killed = gained
            attempts.append({'attempt': attempt, 'mp_spent': spent, 'hp': e.read(0x0201327A, 2),
                             'exp_before': exp, 'exp_after': exp_after,
                             'exp_delta': exp_after - exp, 'projectile_live': live,
                             'kill': gained, 'cast_context': context,
                             'soma_world_x': pre_pos, 'actor_codes': pre_codes})
            e.run(30)
        exp_deltas = [row.get('exp_delta', 0) for row in attempts if 'exp_delta' in row]
        report = {
            'route': 'vanilla opening + walk-right to zombie room + Up+B facing right',
            'attempts': attempts,
            'casts': sum(1 for row in attempts if 'exp_delta' in row),
            'projectile_live_casts': sum(1 for row in attempts if row.get('projectile_live')),
            'total_exp_delta': sum(exp_deltas),
            'killed': killed,
            'kill_scope': ('EXP gain with live projectiles and no other damage source '
                           'attributes the kill; compare the payout against the sword-kill '
                           'control in scripts/attribute_zombie_kill_codes.py before naming '
                           'the victim')
            'original_unchanged': host.read_bytes() == original,
            'rom_sha256': hashlib.sha256(original).hexdigest(),
            'limits': [
                'vanilla zombie stats only (30 HP, 7 EXP); facing/direction unmapped',
                'hit reactions below a kill are not instrumented',
                'one room, one run, MP-bounded attempts',
            ],
        }
        (ROOT / 'local/soul-projectile-hit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))
    finally:
        e.close()
        assert host.read_bytes() == original


if __name__ == '__main__':
    main()
