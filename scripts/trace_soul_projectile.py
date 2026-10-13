"""Bounded native Winged Skeleton cast/projectile trace (private, read-only).

Reuses the verified ``scripts/verify_soul_menu.py`` opening + menu route so
the first red soul is owned and equipped, then snapshots the established
224-slot actor window around one Up+B cast. Reports cast-correlated novel
actor codes, MP spend, screenshots and a bounded idle-vs-cast audio
comparison. Original ROM is never modified; probe outputs stay under local/.

This is an observation harness, not a projectile/SFX authoring API. Absence
of a novel code in this window does not prove absence of a projectile; a
mixed-audio difference does not attribute SFX. See docs/SOUL-PROJECTILE-TRACE.md.
"""
import hashlib
import json
import struct
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aria.cli import load_image
from aria.soul_projectiles import (
    ACTOR_BASE,
    ACTOR_STRIDE,
    code_to_slots,
    compare_audio_windows,
    count_pointer_occurrences,
    describe_winged_skeleton,
    novel_codes,
    snapshot_actor_window,
)
from emulator import Emulator


def boot_to_owned_soul(e):
    e.run(1000)
    for key in [3, 8, 8, 8, 3, 3, 8]:
        e.run(1, [key])
        e.run(100)
    for _ in range(60):
        e.run(1, [8])
        e.run(90)
    assert e.read(0x0201331C, 1) == 1, 'first red soul not owned after opening'
    assert e.read(0x02013269, 1) == 1, 'winged skeleton not equipped after opening'


def open_and_close_soul_menu(e):
    e.run(1, [3])
    e.run(30)
    e.run(1, [8])
    e.run(30)
    assert e.read(0x02000064, 1) == 6, 'soul menu did not open'
    menu_image = e.image.convert('RGB').copy()
    for key in [0, 0]:
        e.run(1, [key])
        e.run(30)
    assert e.read(0x02000064, 1) == 1 and e.read(0x020004EE, 1) == 0
    return menu_image


def world_pos(e):
    return {
        'world_x': e.read(0x02000526, 2) + e.read(0x0200A09A, 2),
        'world_y': e.read(0x0200052A, 2) + e.read(0x0200A09E, 2),
    }


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    rom = load_image(host)
    descriptor = describe_winged_skeleton(rom)
    pointer_hits = count_pointer_occurrences(bytes(rom.original), descriptor['code'])
    folder = ROOT / 'local/soul-projectile'
    folder.mkdir(parents=True, exist_ok=True)

    e = Emulator(host)
    try:
        boot_to_owned_soul(e)
        menu_image = open_and_close_soul_menu(e)
        menu_image.save(folder / 'menu.png')
        mp_before = e.read(0x0201327C, 2)
        hp_before = e.read(0x0201327A, 2)
        baseline_pos = world_pos(e)
        baseline = snapshot_actor_window(e.read)
        e.run(1)
        baseline_image = e.image.convert('RGB').copy()
        baseline_image.save(folder / 'baseline.png')

        # Bounded idle audio window (no input) as a control.
        idle_timing = e.start_audio_capture(120000)
        e.run(60)
        idle_pcm = e.stop_audio_capture()

        # One verified cast with audio capture running.
        cast_timing = e.start_audio_capture(120000)
        mp_pre = e.read(0x0201327C, 2)
        e.run(1, [4, 0])
        e.run(6)
        cast_pcm = e.stop_audio_capture()
        mp_post = e.read(0x0201327C, 2)
        hp_post = e.read(0x0201327A, 2)
        assert mp_pre - mp_post == descriptor['mana_cost'], (mp_pre, mp_post)
        assert hp_post == hp_before
        e.run(1)
        cast_image = e.image.convert('RGB').copy()
        cast_image.save(folder / 'cast-plus7.png')

        # Post-cast actor tracking: every 2 frames for 120 frames.
        samples = []
        first_seen = {}
        last_seen = {}
        slot_history = {}
        for frame in range(0, 120, 2):
            if frame:
                e.run(2)
            snap = snapshot_actor_window(e.read)
            pos = world_pos(e)
            samples.append({
                'frame': frame + 7,
                'codes': code_to_slots(snap),
                'world': pos,
                'state': e.read(0x02000010, 1),
                'substate': e.read(0x02000064, 1),
                'player_state': e.read(0x020004EE, 1),
            })
            for code_hex in novel_codes(baseline, snap):
                first_seen.setdefault(code_hex, frame + 7)
                last_seen[code_hex] = frame + 7
                slot_history.setdefault(code_hex, []).append(
                    code_to_slots(snap)[code_hex])
            if frame == 30:
                e.image.convert('RGB').copy().save(folder / 'cast-plus37.png')
        e.image.convert('RGB').copy().save(folder / 'cast-plus127.png')

        # Calm-phase novelty check: 30 more idle frames, same sampling.
        calm_novel = set()
        for _ in range(15):
            e.run(2)
            for code_hex in novel_codes(baseline, snapshot_actor_window(e.read)):
                calm_novel.add(code_hex)

        audio = compare_audio_windows(idle_pcm, cast_pcm)
        report = {
            'descriptor': descriptor,
            'pointer_occurrences': {
                'count': len(pointer_hits),
                'file_offsets_hex': [hex(0x08000000 + off) for off in pointer_hits[:32]],
                'truncated': len(pointer_hits) > 32,
                'scope': 'static byte hits; not proven consumers',
            },
            'cast': {
                'mp_before': mp_pre,
                'mp_after': mp_post,
                'mp_spent': mp_pre - mp_post,
                'hp_unchanged': hp_post == hp_before,
                'ownership_byte': e.read(0x0201331C, 1),
                'equipped_id': e.read(0x02013269, 1),
                'baseline_world': baseline_pos,
            },
            'actor_window': {
                'base_hex': hex(ACTOR_BASE),
                'stride': ACTOR_STRIDE,
                'baseline_codes': code_to_slots(baseline),
                'novel_first_seen_frame': first_seen,
                'novel_last_seen_frame': last_seen,
                'novel_slot_history': slot_history,
                'calm_phase_novel_codes': sorted(calm_novel),
            },
            'audio_windows': {
                'idle_frames': 60,
                'cast_frames': 7,
                'idle_sample_rate': idle_timing['sample_rate'],
                'cast_sample_rate': cast_timing['sample_rate'],
                'comparison': audio,
                'scope': ('bounded mixed-output capture; equality/difference '
                          'is not firing/impact SFX proof'),
            },
            'images': ['menu.png', 'baseline.png', 'cast-plus7.png',
                       'cast-plus37.png', 'cast-plus127.png'],
            'original_unchanged': host.read_bytes() == original,
            'rom_sha256': hashlib.sha256(original).hexdigest(),
            'limits': [
                'one Up+B cast in the vanilla opening room; no enemy-hit or terrain-collision proof',
                'actor observation limited to the 224-slot window at 0x020004E4 stride 0x84',
                'no rendering/OAM, palette, damage, cooldown, pause/room/death/save lifecycle proof',
                'audio windows are mixed output; no isolated SFX or BGM-coexistence certification',
                'static pointer hits are byte matches, not consumer attribution',
            ],
        }
        (ROOT / 'local/soul-projectile-trace.json').write_text(
            json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))
    finally:
        e.close()
        assert host.read_bytes() == original


if __name__ == '__main__':
    main()
