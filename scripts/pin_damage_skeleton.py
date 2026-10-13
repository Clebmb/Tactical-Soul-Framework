"""Pin soul per-hit damage vs a DEF-0 skeleton (native, private).

42nd slice: the zombie pin (40th slice) fixed damage at 22 vs DEF 1 with
descriptor u16[0]=27 and soul-record multiplier 45. This probe reuses the
workshop-shortcut route (scripts/verify_enemies.py path: zombie room
0x0850F15C -> skeleton room 0x0850F32C) on the enemy-workshop build, where
skeleton DEF is unchanged (0) and HP is RAM-boosted 12->200, then samples
every slot's +0x34 per frame across one verified cast.

Decision table (scripts/census_damage_candidates.py):
  skeleton 22 -> DEF plays no role (45//2 or 27-5 survive);
  skeleton 23 -> DEF subtracts (23-DEF family survives);
  else all four hypotheses falsified.

RAM-only instrumentation in a throwaway session: the workshop build is a
regenerated artifact; the original ROM is never written. Outputs stay
under local/.
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
SKELETON_CODE = 0x080C34F9
SKELETON_NATIVE_HP = 12  # on the enemy-workshop build (vanilla 20)
ZOMBIE_ROOM = 0x0850F15C
SKELETON_ROOM = 0x0850F32C
BOOSTED_HP = 200
MAX_PRESSES = 6


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    from aria.cli import load_image, apply_manifest
    rom = load_image(host)
    apply_manifest(rom, ROOT / 'examples/enemy-workshop/mod.json')
    build = ROOT / 'build/mods/enemy-workshop/enemy-workshop.gba'
    build.parent.mkdir(parents=True, exist_ok=True)
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
        for _ in range(180):
            e.run(20, [7, 0])
            e.run(1, [7, 8])
            e.run(15, [7, 0])
            if e.read(0x02000088) == SKELETON_ROOM:
                break
        assert e.read(0x02000088) == SKELETON_ROOM, 'no skeleton room'
        # 43rd slice: advance into the room before boosting/casting.
        # The 42nd slice cast from the room-entry position and missed
        # twice deterministically; verify_enemies.py fights skeletons at
        # world X>=600, so walk right with combat cycles first.
        # 46th slice: MIRROR mode (argv 'mirror') replicates the zombie
        # pin exactly — walk right 70, idle 30, no combat advance — since
        # the combat advance may scatter/aggro skeletons out of the lane.
        # 48th slice: FACE mode taps Left once (face left into the
        # left-behind skeleton per the 47th-slice tracking) before the
        # press-budget cast. Usage: argv may combine, e.g. 'mirror face'
        # or 'advance face'; bare 'face' implies mirror timing.
        args = sys.argv[1:]
        face_left = 'face' in args
        mode = next((a for a in args if a in ('mirror', 'advance')), 'advance')
        if face_left and mode == 'advance' and 'mirror' not in args and len(args) == 1:
            mode = 'mirror'
        if face_left:
            e.run(1, [6])
            e.run(10)
        if mode == 'mirror':
            e.run(70, [7])
            e.run(30)
        else:
            for _ in range(90):
                e.run(20, [7, 0])
                e.run(1, [7, 8])
                e.run(15, [7, 0])
                if e.read(0x02000526, 2) + e.read(0x0200A09A, 2) >= 400:
                    break
        world_x = e.read(0x02000526, 2) + e.read(0x0200A09A, 2)

        def boost_all():
            boosted = []
            for slot in range(ACTOR_SLOTS):
                base = ACTOR_BASE + slot * ACTOR_STRIDE
                if (e.read(base, 4) == SKELETON_CODE
                        and e.read(base + HP_OFFSET, 2) == SKELETON_NATIVE_HP):
                    e.write(base + HP_OFFSET, BOOSTED_HP, 2)
                    boosted.append(slot)
            return boosted

        slots = []
        waited = 0
        while waited < 400:
            e.run(10)
            waited += 10
            for s in boost_all():
                if s not in slots:
                    slots.append(s)
            if slots:
                break
        stable = True
        seen200 = set()
        for _ in range(10):
            e.run(1)
            for s in list(slots):
                v = e.read(ACTOR_BASE + s * ACTOR_STRIDE + HP_OFFSET, 2)
                if v == BOOSTED_HP:
                    seen200.add(s)
                elif v == SKELETON_NATIVE_HP and s in seen200:
                    stable = False
            boost_all()
        exp_before = e.read(0x0201328C)
        fired, presses = False, 0
        casts = 0
        if stable and slots:
            # Up to 3 casts with short reposition walks between: more
            # chances for the projectile to meet a boosted skeleton.
            for _ in range(3):
                for _ in range(MAX_PRESSES):
                    mp_pre = e.read(0x0201327C, 2)
                    e.run(1, [4, 0])
                    e.run(6)
                    presses += 1
                    boost_all()
                    if mp_pre - e.read(0x0201327C, 2) == EXPECTED_MANA_COST:
                        fired = True
                        casts += 1
                        break
                    for _ in range(15):
                        e.run(2)
                        boost_all()
                    for s in boost_all():
                        if s not in slots:
                            slots.append(s)
                if not fired:
                    break
                for _ in range(40):
                    e.run(3)
                    boost_all()
                for s in boost_all():
                    if s not in slots:
                        slots.append(s)
                e.run(10, [7])
                e.run(10)

        def hp_all(read):
            return {s: read(ACTOR_BASE + s * ACTOR_STRIDE + HP_OFFSET, 2)
                    for s in range(ACTOR_SLOTS)}

        def codes_all(read):
            return {s: read(ACTOR_BASE + s * ACTOR_STRIDE, 4)
                    for s in range(ACTOR_SLOTS)}

        series = []
        if stable and fired:
            for _ in range(120):
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
        skel_falls = {s: f for s, f in falls.items()
                      if f['code_hex'] == hex(SKELETON_CODE)}
        drop = next(iter(skel_falls.values()))['drop'] if len(skel_falls) == 1 else None
        verdict = ('skeleton damage %d' % drop if drop is not None else
                   'no skeleton slot appeared' if not slots else
                   'boost unstable' if not stable else
                   'cast never fired' if not fired else
                   'ambiguous falls %s' % falls)
        report = {
            'route': ('workshop shortcut zombie-room -> skeleton-room, '
                      + ('mirror zombie timing (walk 70, idle 30), ' if mode == 'mirror'
                         else 'advance to X>=400, ')
                      + 'up to 3 casts; skeleton 12->200 boost; per-frame +0x34 poll'),
            'mode': mode,
            'face_left': face_left,
            'world_x_at_cast': world_x,
            'casts': casts,
            'slots': slots,
            'boost_stable': stable,
            'presses': presses,
            'cast_fired': fired,
            'hp_falls': falls,
            'skeleton_falls': skel_falls,
            'exp_delta': exp_after - exp_before,
            'verdict': verdict,
            'original_unchanged': host.read_bytes() == original,
            'rom_sha256': hashlib.sha256(original).hexdigest(),
            'limits': ['RAM instrumentation only; original ROM untouched',
                       'workshop build: skeleton DEF unchanged (0), HP boosted so HP edit moot',
                       'single cast, skeleton room only'],
        }
    finally:
        e.close()
    (ROOT / 'local/damage-pin-skeleton.json').write_text(
        json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    assert host.read_bytes() == original


if __name__ == '__main__':
    main()
