"""Track soul projectile vs skeleton positions through flight (native, private).

47th slice: four skeleton pins missed with the same signature (boosted
skeleton never touched). Instead of a fifth blind cast, this probe WATCHES
the miss: on the enemy-workshop build it takes the mirror route to the
skeleton room, finds a live skeleton slot, fires one verified cast, then
samples record words 16/17 (position X/Y per docs/SOUL-DECOMPILE.md record
map: +0x40/+0x44) of the soul slot and the skeleton slot every 2 frames
for 70 frames, plus Soma world X/Y.

Verdict reads the minimum |dx|/|dy| in raw position-word units (same
layout both slots, so deltas are comparable): small dx + large dy =
wrong-lane (vertical miss, e.g. projectile flies overhead); large dx that
never closes = wrong-range (despawn first / too far); both small with no
HP fall = overlap without damage (match-pass surprise).

Read-only apart from held inputs: no RAM writes, ROM never modified.
Outputs stay under local/.
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
    read_slot_word,
)
from emulator import Emulator

SKELETON_CODE = 0x080C34F9
SOUL_CODES = (0x08026009, 0x08025F71)
ZOMBIE_ROOM = 0x0850F15C
SKELETON_ROOM = 0x0850F32C
MAX_PRESSES = 6


def words16_17(read, slot):
    return (read_slot_word(read, slot, 16), read_slot_word(read, slot, 17))


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    from aria.cli import load_image, apply_manifest
    rom = load_image(host)
    build = ROOT / 'build/mods/enemy-workshop/enemy-workshop.gba'
    if not build.exists():
        apply_manifest(rom, ROOT / 'examples/enemy-workshop/mod.json')
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
        e.run(70, [7])
        e.run(30)
        # 48th slice: FACE argv taps Left once before the cast, mirroring
        # the pin script, and logs Soma facing before/after.
        face_left = 'face' in sys.argv[1:]
        facing_before = e.read(0x0200052E, 1)
        if face_left:
            e.run(1, [6])
            e.run(10)
        facing_after = e.read(0x0200052E, 1)
        skel = None
        for slot in range(ACTOR_SLOTS):
            if e.read(ACTOR_BASE + slot * ACTOR_STRIDE, 4) == SKELETON_CODE:
                skel = slot
                break
        fired, presses = False, 0
        if skel is not None:
            for _ in range(MAX_PRESSES):
                mp_pre = e.read(0x0201327C, 2)
                e.run(1, [4, 0])
                e.run(6)
                presses += 1
                if mp_pre - e.read(0x0201327C, 2) == EXPECTED_MANA_COST:
                    fired = True
                    break
                e.run(30)
        track = []
        soul_slot = None
        if fired:
            for frame in range(0, 70, 2):
                if frame:
                    e.run(2)
                row = {'frame': frame}
                for slot in range(ACTOR_SLOTS):
                    code = e.read(ACTOR_BASE + slot * ACTOR_STRIDE, 4)
                    if code in SOUL_CODES and soul_slot is None:
                        soul_slot = slot
                if soul_slot is not None:
                    sx, sy = words16_17(e.read, soul_slot)
                    row['soul_slot'] = soul_slot
                    row['soul_x_hex'] = hex(sx)
                    row['soul_y_hex'] = hex(sy)
                if e.read(ACTOR_BASE + skel * ACTOR_STRIDE, 4) == SKELETON_CODE:
                    kx, ky = words16_17(e.read, skel)
                    row['skel_x_hex'] = hex(kx)
                    row['skel_y_hex'] = hex(ky)
                    if 'soul_x_hex' in row:
                        row['dx'] = (sx - kx) - (1 << 32) if sx - kx >= 1 << 31 else sx - kx
                        row['dy'] = (sy - ky) - (1 << 32) if sy - ky >= 1 << 31 else sy - ky
                row['soma_x'] = e.read(0x02000526, 2) + e.read(0x0200A09A, 2)
                row['soma_y'] = e.read(0x0200052A, 2) + e.read(0x0200A09E, 2)
                track.append(row)
        pairs = [r for r in track if 'dx' in r]
        if pairs:
            closest = min(pairs, key=lambda r: abs(r['dx']) + abs(r['dy']))
            verdict = ('closest approach frame %(frame)d: dx=%(dx)d dy=%(dy)d '
                       '(raw word units); ' % closest)
            verdict += ('wrong-lane (vertical miss)' if abs(closest['dx']) < abs(closest['dy']) // 4
                        else 'wrong-range (never closes in x)' if abs(closest['dx']) > 0x80000
                        else 'overlap without damage (match-pass surprise)')
        else:
            verdict = ('no shared frames (soul slot %s, skeleton slot %s%s); '
                       'soul skewness or skeleton despawn' % (
                           soul_slot, skel, '' if fired else ', cast never fired'))
        report = {
            'route': 'workshop shortcut, mirror timing; words 16/17 per 2 frames x70',
            'face_left': face_left,
            'facing_before': facing_before,
            'facing_after': facing_after,
            'skeleton_slot': skel,
            'soul_slot': soul_slot,
            'presses': presses,
            'cast_fired': fired,
            'frames': track,
            'verdict': verdict,
            'original_unchanged': host.read_bytes() == original,
            'rom_sha256': hashlib.sha256(original).hexdigest(),
            'limits': ['raw word units, scale unproven; +0x40/+0x44 layout shared so deltas comparable',
                       'single flight, skeleton room only; ROM untouched'],
        }
    finally:
        e.close()
    (ROOT / 'local/soul-vs-skeleton.json').write_text(
        json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'frames'}, indent=2))
    assert host.read_bytes() == original


if __name__ == '__main__':
    main()
