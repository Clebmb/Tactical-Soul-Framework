"""Pin soul per-hit damage with a RAM-boosted 200-HP zombie (native, private).

28th slice: descriptor u16[0] = 27 is the damage candidate; the 26th
slice's 18-drop was overkill clamped at zero. This probe reuses the
26th-slice zombie-room route, finds the zombie slot by update code
(0x0807A9ED) + HP 18, uses the harness RAM write() to raise its +0x34
to 200 (verifying stability first: a snap-back to 18 would prove a
periodic DNA copy), budgets presses for one verified cast, then samples
the victim +0x34 every frame. A non-lethal 200->173 fall pins damage 27
exactly; any other exact number is reported as-is.

RAM-only instrumentation in a throwaway session: the ROM is never
written. Outputs stay under local/.
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
    snapshot_actor_window,
)
from emulator import Emulator

HP_OFFSET = 0x34
ZOMBIE_CODE = 0x0807A9ED
ZOMBIE_ROOM = 0x0850F15C
BOOSTED_HP = 200
MAX_PRESSES = 6


def find_zombies(read):
    found = []
    for slot in range(ACTOR_SLOTS):
        base = ACTOR_BASE + slot * ACTOR_STRIDE
        if read(base, 4) == ZOMBIE_CODE and read(base + HP_OFFSET, 2) == 18:
            found.append(slot)
    return found


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
        def boost_all():
            boosted = []
            for slot in range(ACTOR_SLOTS):
                base = ACTOR_BASE + slot * ACTOR_STRIDE
                if e.read(base, 4) == ZOMBIE_CODE and e.read(base + HP_OFFSET, 2) == 18:
                    e.write(base + HP_OFFSET, BOOSTED_HP, 2)
                    boosted.append(slot)
            return boosted

        slots = []
        waited = 0
        while waited < 300:
            e.run(10)
            waited += 10
            for s in boost_all():
                if s not in slots:
                    slots.append(s)
            if slots:
                break
        assert slots, 'no 18-HP zombie slot appeared'
        stable = True
        seen200 = set()
        for _ in range(10):
            e.run(1)
            for s in list(slots):
                v = e.read(ACTOR_BASE + s * ACTOR_STRIDE + HP_OFFSET, 2)
                if v == BOOSTED_HP:
                    seen200.add(s)
                elif v == 18 and s in seen200:
                    stable = False  # snap-back: periodic DNA copy
            boost_all()
        addrs = [ACTOR_BASE + s * ACTOR_STRIDE + HP_OFFSET for s in slots]
        exp_before = e.read(0x0201328C)
        fired, presses = False, 0
        if stable:
            for _ in range(MAX_PRESSES):
                mp_pre = e.read(0x0201327C, 2)
                e.run(1, [4, 0])
                e.run(6)
                presses += 1
                boost_all()
                if mp_pre - e.read(0x0201327C, 2) == EXPECTED_MANA_COST:
                    fired = True
                    break
                for _ in range(15):
                    e.run(2)
                    boost_all()
                for s in boost_all():
                    if s not in slots:
                        slots.append(s)
            addrs = [ACTOR_BASE + s * ACTOR_STRIDE + HP_OFFSET for s in slots]
        def hp_all(read):
            return {s: read(ACTOR_BASE + s * ACTOR_STRIDE + HP_OFFSET, 2)
                    for s in range(ACTOR_SLOTS)}

        def codes_all(read):
            return {s: read(ACTOR_BASE + s * ACTOR_STRIDE, 4)
                    for s in range(ACTOR_SLOTS)}

        series = []
        if stable and fired:
            prev = {}
            for frame in range(120):
                e.run(1)
                boost_all()
                snap = (hp_all(e.read), codes_all(e.read))
                series.append(snap)
        exp_after = e.read(0x0201328C)
        falls = {}
        for s in range(ACTOR_SLOTS):
            values = [hp[s] for hp, _ in series]
            changes = [[f, values[f]] for f in range(1, len(values))
                       if values[f] != values[f - 1]]
            if values and values[0] > values[-1]:
                falls[str(s)] = {'first': values[0], 'last': values[-1],
                                 'drop': values[0] - values[-1],
                                 'code_hex': hex(series[0][1][s]),
                                 'change_points': changes}
        drop27 = [s for s, f in falls.items() if f['drop'] == 27]
        report = {
            'route': 'zombie room; ALL 18-HP zombies RAM-boosted; per-frame +0x34 poll',
            'slots': slots,
            'boost_stable': stable,
            'presses': presses,
            'cast_fired': fired,
            'hp_falls': falls,
            'exp_delta': exp_after - exp_before,
            'verdict': ('damage pinned exactly 27 on slot(s) %s (descriptor u16[0])' % drop27
                        if drop27 else
                        'periodic DNA copy resets HP (spawn-copy is per-frame)'
                        if stable is False else
                        'falls %s with +1 EXP kill elsewhere; cast missed boosted victims' % falls
                        if not falls and exp_after - exp_before else
                        'exact falls %s; see hp_falls' % falls),
            'original_unchanged': host.read_bytes() == original,
            'rom_sha256': hashlib.sha256(original).hexdigest(),
            'limits': ['RAM instrumentation only; ROM untouched',
                       'single cast, single victim, zombie room only'],
        }
    finally:
        e.close()
    (ROOT / 'local/damage-pin.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    assert host.read_bytes() == original


if __name__ == '__main__':
    main()
