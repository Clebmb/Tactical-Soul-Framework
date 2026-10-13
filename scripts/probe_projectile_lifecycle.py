"""Projectile lifecycle: pause-freeze and room transition (private).

Opening room, controller-only. Part A (pause): verified cast, mid-flight
Start menu, 30 paused frames of slot sampling, close with B twice, then
check whether flight resumes (words 16/17 advance) or the engine despawns.
Part B (room transition): fresh core, walk to just before the east door,
cast, walk through the transition while the projectile is live, then check
whether slots 2/3 survive the room change. Death mid-flight is out of scope
(requires HP manipulation; noted as a limit).

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
    ACTOR_STRIDE,
    EXPECTED_MANA_COST,
    novel_codes,
    read_slot_word,
    snapshot_actor_window,
)
from emulator import Emulator

SLOT2 = 2
W16 = 16


def opening(e):
    e.run(1000)
    for key in [3, 8, 8, 8, 3, 3, 8]:
        e.run(1, [key])
        e.run(100)
    for _ in range(60):
        e.run(1, [8])
        e.run(90)
    assert e.read(0x0201331C, 1) == 1 and e.read(0x02013269, 1) == 1
    e.run(1, [3])
    e.run(30)
    e.run(1, [8])
    e.run(30)
    assert e.read(0x02000064, 1) == 6, 'soul menu did not open'
    for key in [0, 0]:
        e.run(1, [key])
        e.run(30)


def verified_cast(e):
    mp_pre = e.read(0x0201327C, 2)
    e.run(1, [4, 0])
    e.run(6)
    return mp_pre - e.read(0x0201327C, 2) == EXPECTED_MANA_COST


def slot2_w16(read):
    return read_slot_word(read, SLOT2, W16)


def part_pause():
    host = ROOT / 'CastlevaniaAoS.gba'
    e = Emulator(host)
    try:
        opening(e)
        pre_cast = snapshot_actor_window(e.read)
        assert verified_cast(e), 'opening cast did not fire'
        e.run(20)
        post_cast = snapshot_actor_window(e.read)
        live = bool(novel_codes(pre_cast, post_cast))
        w_pre = slot2_w16(e.read)
        e.run(1, [3])
        e.run(10)
        menu_state = e.read(0x02000064, 1)
        paused_snaps = []
        for _ in range(6):
            paused_snaps.append(snapshot_actor_window(e.read))
            e.run(5)
        still = all(s == paused_snaps[0] for s in paused_snaps)
        w_paused = slot2_w16(e.read)
        for key in [0, 0]:
            e.run(1, [key])
            e.run(30)
        e.run(20)
        w_post = slot2_w16(e.read)
        return {
            'cast_live_pre_pause': live,
            'menu_state': menu_state,
            'slots_frozen_while_paused': still,
            'word16_unchanged_while_paused': w_paused == w_pre,
            'word16_pre': hex(w_pre),
            'word16_post': hex(w_post),
            'flight_resumed': live and w_post != w_pre,
        }
    finally:
        e.close()


def part_transition():
    host = ROOT / 'CastlevaniaAoS.gba'
    e = Emulator(host)
    try:
        opening(e)
        room0 = e.read(0x02000088)
        frames_to_door = None
        for frame in range(900):
            e.run(1, [7])
            if e.read(0x02000088) != room0:
                frames_to_door = frame + 1
                break
        assert frames_to_door is not None, 'never reached the east door'
        e.close()
        e2 = Emulator(host)
        try:
            opening(e2)
            for _ in range(max(0, frames_to_door - 45)):
                e2.run(1, [7])
            assert e2.read(0x02000088) == room0, 'overshot the door approach'
            assert verified_cast(e2), 'pre-door cast did not fire'
            for _ in range(70):
                e2.run(1, [7])
                if e2.read(0x02000088) != room0:
                    break
            crossed = e2.read(0x02000088) != room0
            snap = snapshot_actor_window(e2.read)
            carried = SLOT2 in snap
            return {
                'frames_to_door': frames_to_door,
                'crossed_with_live_cast': crossed,
                'slot2_carried_across': carried,
                'post_codes': sorted(hex(c) for c in snap.values())[:12],
            }
        finally:
            e2.close()
    finally:
        try:
            e.close()
        except Exception:
            pass


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    pause = part_pause()
    transition = part_transition()
    report = {
        'route': 'opening room; pause-freeze then east-door transition with live cast',
        'pause': pause,
        'transition': transition,
        'verdict': ('pause freezes + room change clears'
                    if pause['slots_frozen_while_paused'] and not transition['slot2_carried_across']
                    else 'mixed lifecycle; see parts'),
        'original_unchanged': host.read_bytes() == original,
        'rom_sha256': hashlib.sha256(original).hexdigest(),
        'limits': ['death mid-flight out of scope; opening/east-door only'],
    }
    (ROOT / 'local/projectile-lifecycle.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    assert host.read_bytes() == original


if __name__ == '__main__':
    main()
