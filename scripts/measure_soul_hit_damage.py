"""Per-hit soul damage via the victim HP halfword (private).

Decompiler result (docs/SOUL-DECOMPILE.md, 25th slice): victim HP is the
short at actor-record +0x34. This probe walks vanilla Soma into the zombie
room, budgets presses for the count-gate until one Up+B cast fires
(MP-spend verified), and samples every slot's +0x34 halfword each 2 frames
through the live window. A slot whose +0x34 falls across the window names
the victim and the per-hit damage number.

Read-only: no ROM writes, no authoring. Outputs stay under local/. Original
ROM is never modified.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from aria.soul_projectiles import (
    ACTOR_BASE,
    ACTOR_SLOTS,
    ACTOR_STRIDE,
    EXPECTED_MANA_COST,
    novel_codes,
    snapshot_actor_window,
)
from emulator import Emulator

HP_OFFSET = 0x34
ZOMBIE_ROOM = 0x0850F15C
MAX_PRESSES = 6


def hp_halfwords(read):
    out = {}
    for slot in range(ACTOR_SLOTS):
        out[slot] = read(ACTOR_BASE + slot * ACTOR_STRIDE + HP_OFFSET, 2)
    return out


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
        baseline = snapshot_actor_window(e.read)
        hp_before = hp_halfwords(e.read)
        exp_before = e.read(0x0201328C)
        fired = False
        presses = 0
        for _ in range(MAX_PRESSES):
            mp_pre = e.read(0x0201327C, 2)
            e.run(1, [4, 0])
            e.run(6)
            presses += 1
            if mp_pre - e.read(0x0201327C, 2) == EXPECTED_MANA_COST:
                fired = True
                break
            e.run(30)
        series = []
        live_seen = False
        if fired:
            for frame in range(0, 70, 2):
                if frame:
                    e.run(2)
                snap = snapshot_actor_window(e.read)
                if novel_codes(baseline, snap):
                    live_seen = True
                series.append({'frame': frame, 'hp': hp_halfwords(e.read)})
        hp_after = hp_halfwords(e.read)
        exp_after = e.read(0x0201328C)
        falls = {}
        for slot in range(ACTOR_SLOTS):
            values = [s['hp'][slot] for s in series]
            if values and values[0] > values[-1]:
                falls[slot] = {'first': values[0], 'last': values[-1],
                               'drop': values[0] - values[-1]}
        report = {
            'route': 'zombie room; press-budgeted cast, +0x34 sampled every 2 frames',
            'presses': presses,
            'cast_fired': fired,
            'projectile_live': live_seen,
            'exp_delta': exp_after - exp_before,
            'hp_falls': falls,
            'verdict': ('per-hit damage measured'
                        if fired and len(falls) == 1 else
                        'ambiguous or no isolated HP fall; see hp_falls'),
            'original_unchanged': host.read_bytes() == original,
            'rom_sha256': hashlib.sha256(original).hexdigest(),
            'limits': ['zombie room only; one cast; holder identity from falls, not slots'],
        }
    finally:
        e.close()
    (ROOT / 'local/soul-hit-damage.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    assert host.read_bytes() == original


if __name__ == '__main__':
    main()
