"""Close-range first-cast fizzle probe (private).

Vanilla ROM, controller-only: opening, walk-right into the zombie room, then
keep walking right toward the zombie (bounded, HP-guarded) before the FIRST
Up+B cast. Records whether it fires, Soma world-x, MP spend and actor codes.
Tests the proximity hypothesis for the hit-attempt fizzles (far first casts
fizzled 3/3 at Soma x≈6): if close-range first casts fire, the gate is
positional, not attempt-count.

Read-only: no ROM writes, no authoring. One cast per run; replicate with a
second run. Outputs stay under local/. Original ROM is never modified.
"""
import argparse
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


def main():
    args = argparse.ArgumentParser(description='Close-range first-cast probe')
    args.add_argument('--advance', type=int, default=120)
    args.add_argument('--tag', type=str, default='close')
    opts = args.parse_args()
    if not 0 <= opts.advance <= 600:
        raise SystemExit('advance must be 0..600')
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
        for _ in range(opts.advance):
            if e.read(0x0201327A, 2) < HP_FLOOR:
                break
            e.run(1, [7])
        soma_x = e.read(0x02000526, 2) + e.read(0x0200A09A, 2)
        soma_hp = e.read(0x0201327A, 2)
        baseline = snapshot_actor_window(e.read)
        mp_pre = e.read(0x0201327C, 2)
        context = {'state': e.read(0x02000010, 1), 'substate': e.read(0x02000064, 1),
                   'player_state': e.read(0x020004EE, 1),
                   'vel_x': e.read(0x0200052C, 2), 'vel_y': e.read(0x02000530, 2)}
        e.run(1, [4, 0])
        e.run(6)
        spent = mp_pre - e.read(0x0201327C, 2)
        live = False
        live_codes = []
        for _ in range(20):
            e.run(2)
            novel = novel_codes(baseline, snapshot_actor_window(e.read))
            if novel:
                live = True
                live_codes = novel
                break
        report = {
            'advance_frames': opts.advance,
            'soma_world_x': soma_x,
            'soma_hp': soma_hp,
            'mp_spent': spent,
            'fired': spent == EXPECTED_COST,
            'projectile_live': live,
            'live_codes': live_codes,
            'cast_context': context,
            'actor_codes': sorted(hex(code) for code in baseline.values()),
            'original_unchanged': host.read_bytes() == original,
            'rom_sha256': hashlib.sha256(original).hexdigest(),
            'limits': ['one cast per run; replicate across runs before claiming a gate'],
        }
        out = ROOT / ('local/cast-fizzle-%s.json' % opts.tag)
        out.write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))
    finally:
        e.close()
        assert host.read_bytes() == original


if __name__ == '__main__':
    main()
