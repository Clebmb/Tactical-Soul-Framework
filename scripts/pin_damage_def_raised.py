"""Pin whether victim DEF affects soul damage (native, private).

44th slice: the zombie pin (40th) fixed damage at 22 vs DEF 1; skeleton
pins (42nd-43rd) missed on positioning. This probe isolates ONE variable
in the room that already works: a mod raises zombie DEF 1->10 (an editable
DNA field per docs/ENEMIES.md; HP/ATK/EXP untouched), then the proven
zombie route boosts an 18-HP zombie to 200 and polls +0x34 per frame
across one verified cast.

Decision: drop 22 -> DEF plays no role (45//2 or 27-5 family). Drop 13
(23-10) or any number <22 -> DEF subtracts. Anything else is reported
as-is with the same honesty as the misses.

The mod build is a regenerated throwaway under build/; the original ROM
is never written. Outputs stay under local/.
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
)
from emulator import Emulator

HP_OFFSET = 0x34
DEF_OFFSET = 0x3D
ZOMBIE_CODE = 0x0807A9ED
ZOMBIE_ROOM = 0x0850F15C
ZOMBIE_NATIVE_HP = 18
RAISED_DEF = int(sys.argv[1]) if len(sys.argv) > 1 else 10
PREDICTED = (45 - RAISED_DEF) // 2
BOOSTED_HP = 200
MAX_PRESSES = 6


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    from aria.cli import load_image, apply_manifest
    rom = load_image(host)
    manifest = {
        'schema_version': 1,
        'id': 'def-probe',
        'enemy_edits': [{
            'enemy': 'zombie',
            'expect': {'hp': 18, 'attack': 9, 'defense': 1, 'experience': 1},
            'fields': {'defense': RAISED_DEF},
        }],
    }
    build = ROOT / 'build/mods/def-probe/def-probe.gba'
    build.parent.mkdir(parents=True, exist_ok=True)
    (build.parent / 'mod.json').write_text(json.dumps(manifest, indent=2),
                                            encoding='utf-8')
    apply_manifest(rom, build.parent / 'mod.json')
    rom.output(build, host)
    e = Emulator(build)
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
        assert e.read(0x02000088) == ZOMBIE_ROOM, 'no zombie room'
        e.run(70, [7])
        e.run(30)

        def boost_all():
            boosted = []
            for slot in range(ACTOR_SLOTS):
                base = ACTOR_BASE + slot * ACTOR_STRIDE
                if (e.read(base, 4) == ZOMBIE_CODE
                        and e.read(base + HP_OFFSET, 2) == ZOMBIE_NATIVE_HP):
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
        def_native = e.read(ACTOR_BASE + slots[0] * ACTOR_STRIDE + DEF_OFFSET, 1)
        stable = True
        seen200 = set()
        for _ in range(10):
            e.run(1)
            for s in list(slots):
                v = e.read(ACTOR_BASE + s * ACTOR_STRIDE + HP_OFFSET, 2)
                if v == BOOSTED_HP:
                    seen200.add(s)
                elif v == ZOMBIE_NATIVE_HP and s in seen200:
                    stable = False
            boost_all()
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

        def hp_all(read):
            return {s: read(ACTOR_BASE + s * ACTOR_STRIDE + HP_OFFSET, 2)
                    for s in range(ACTOR_SLOTS)}

        def codes_all(read):
            return {s: read(ACTOR_BASE + s * ACTOR_STRIDE, 4)
                    for s in range(ACTOR_SLOTS)}

        series = []
        def def_all(read):
            return {s: read(ACTOR_BASE + s * ACTOR_STRIDE + DEF_OFFSET, 1)
                    for s in range(ACTOR_SLOTS)}
        def_at_cast = def_all(e.read) if (stable and fired) else {}
        if stable and fired:
            for frame in range(120):
                e.run(1)
                boost_all()
                series.append((hp_all(e.read), codes_all(e.read)))
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
        zom_falls = {s: f for s, f in falls.items()
                     if f['code_hex'] == hex(ZOMBIE_CODE)}
        for s, f in zom_falls.items():
            f['def_at_cast'] = def_at_cast.get(int(s))
        drop = next(iter(zom_falls.values()))['drop'] if len(zom_falls) == 1 else None
        if drop == PREDICTED:
            verdict = ('damage %d at DEF %d matches (45-DEF)//2=%d: formula '
                       'holds' % (drop, RAISED_DEF, PREDICTED))
        elif drop is not None:
            verdict = ('damage %d at DEF %d vs predicted %d (and 22 at DEF 1): '
                       'formula challenged' % (drop, RAISED_DEF, PREDICTED))
        else:
            verdict = ('no catch (slots %s stable %s fired %s); cast missed '
                       'boosted victims' % (slots, stable, fired))
        report = {
            'route': ('zombie room on DEF-%d mod build; 18->200 boost; '
                      'per-frame +0x34 poll' % RAISED_DEF),
            'predicted': PREDICTED,
            'raised_def': RAISED_DEF,
            'def_native_observed': def_native,
            'def_edit_live': def_native == RAISED_DEF,
            'slots': slots,
            'boost_stable': stable,
            'presses': presses,
            'cast_fired': fired,
            'hp_falls': falls,
            'zombie_falls': zom_falls,
            'exp_delta': exp_after - exp_before,
            'verdict': verdict,
            'original_unchanged': host.read_bytes() == original,
            'rom_sha256': hashlib.sha256(original).hexdigest(),
            'limits': ['RAM instrumentation only; original ROM untouched',
                       'mod build is a regenerated throwaway; only DEF edited',
                       'single cast, zombie room only'],
        }
    finally:
        e.close()
    (ROOT / ('local/damage-pin-def%d.json' % RAISED_DEF)).write_text(
        json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    assert host.read_bytes() == original


if __name__ == '__main__':
    main()
