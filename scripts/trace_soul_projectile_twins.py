"""Twin determinism + slot position trace for the Winged Skeleton cast (private).

Two fresh-core runs repeat the verified opening + menu + one Up+B cast from
``scripts/trace_soul_projectile.py``. Compares cast-correlated novel codes,
slots and timing with ``aria.soul_projectiles.compare_cast_twins`` and records
calibrated world-x trajectories (record word 8 low halfword / 256, per
docs/ENEMY-BINDING.md v0.44) for slots 2–3 across the cast window.

Read-only: no ROM writes, no authoring. Twin equality names repeatable spawn
timing, not rendering, damage, collision or SFX proof. Outputs stay under
local/. Original ROM is never modified.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aria.soul_projectiles import (
    code_to_slots,
    compare_cast_twins,
    novel_codes,
    slot_world_x,
    snapshot_actor_window,
)
from emulator import Emulator

EXPECTED_COST = 12


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
    menu_pixels = e.image.convert('RGB').copy().tobytes()
    for key in [0, 0]:
        e.run(1, [key])
        e.run(30)
    assert e.read(0x02000064, 1) == 1 and e.read(0x020004EE, 1) == 0
    return menu_pixels


def run_once(save_images):
    e = Emulator(ROOT / 'CastlevaniaAoS.gba')
    try:
        boot_to_owned_soul(e)
        menu_pixels = open_and_close_soul_menu(e)
        if save_images:
            e.image.convert('RGB').copy().save(ROOT / 'local/soul-projectile-twins-menu.png')
        mp_pre = e.read(0x0201327C, 2)
        hp_pre = e.read(0x0201327A, 2)
        baseline = snapshot_actor_window(e.read)
        e.run(1)
        baseline_pixels = e.image.convert('RGB').copy().tobytes()
        if save_images:
            e.image.convert('RGB').copy().save(ROOT / 'local/soul-projectile-twins-baseline.png')
        e.run(1, [4, 0])
        e.run(6)
        mp_post = e.read(0x0201327C, 2)
        assert mp_pre - mp_post == EXPECTED_COST, (mp_pre, mp_post)
        assert e.read(0x0201327A, 2) == hp_pre
        assert e.read(0x0201331C, 1) == 1 and e.read(0x02013269, 1) == 1
        e.run(1)
        if save_images:
            e.image.convert('RGB').copy().save(ROOT / 'local/soul-projectile-twins-cast.png')
        first_seen, last_seen, slot_sets = {}, {}, {}
        trajectories = {2: [], 3: []}
        for frame in range(0, 120, 2):
            if frame:
                e.run(2)
            snap = snapshot_actor_window(e.read)
            codes = code_to_slots(snap)
            for code_hex in novel_codes(baseline, snap):
                first_seen.setdefault(code_hex, frame + 7)
                last_seen[code_hex] = frame + 7
                slot_sets.setdefault(code_hex, set()).update(codes[code_hex])
            for slot in trajectories:
                trajectories[slot].append({
                    'frame': frame + 7,
                    'code_hex': hex(snap[slot]) if slot in snap else None,
                    'world_x': round(slot_world_x(e.read, slot), 4),
                })
        summary = {code: {'first': first_seen[code], 'last': last_seen[code],
                          'slots': sorted(slot_sets[code])} for code in first_seen}
        return {
            'menu_pixels_sha256': hashlib.sha256(menu_pixels).hexdigest(),
            'baseline_pixels_sha256': hashlib.sha256(baseline_pixels).hexdigest(),
            'mp_spent': mp_pre - mp_post,
            'baseline_codes': code_to_slots(baseline),
            'summary': summary,
            'trajectories': trajectories,
        }
    finally:
        e.close()


def summarize_trajectory(points):
    present = [p for p in points if p['code_hex'] is not None]
    if not present:
        return {'present_samples': 0}
    xs = [p['world_x'] for p in present]
    return {
        'present_samples': len(present),
        'first_frame': present[0]['frame'],
        'last_frame': present[-1]['frame'],
        'first_world_x': present[0]['world_x'],
        'last_world_x': present[-1]['world_x'],
        'displacement': round(present[-1]['world_x'] - present[0]['world_x'], 4),
        'min_world_x': min(xs),
        'max_world_x': max(xs),
    }


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    folder = ROOT / 'local'
    first = run_once(save_images=True)
    second = run_once(save_images=False)
    comparison = compare_cast_twins(first['summary'], second['summary'])
    twin_pixels = {
        'menu_identical': first['menu_pixels_sha256'] == second['menu_pixels_sha256'],
        'baseline_identical': first['baseline_pixels_sha256'] == second['baseline_pixels_sha256'],
    }
    trajectories = {}
    for label, run in (('first', first), ('second', second)):
        trajectories[label] = {
            str(slot): summarize_trajectory(run['trajectories'][slot]) for slot in (2, 3)
        }
    report = {
        'route': 'verified opening + soul menu open/close + one Up+B cast per fresh core',
        'mp_spent_both_runs': [first['mp_spent'], second['mp_spent']],
        'twin_pixels': twin_pixels,
        'first_summary': first['summary'],
        'second_summary': second['summary'],
        'twin_comparison': comparison,
        'trajectories': trajectories,
        'position_scope': ('actor world-x reads as record word 8 low halfword / 256, '
                           'calibrated on a zombie approach (v0.44); projectile-slot '
                           'mapping is assumed, world-y is unmapped'),
        'images': ['soul-projectile-twins-menu.png', 'soul-projectile-twins-baseline.png',
                   'soul-projectile-twins-cast.png'],
        'original_unchanged': host.read_bytes() == original,
        'rom_sha256': hashlib.sha256(original).hexdigest(),
        'limits': [
            'two fresh-core runs in the vanilla opening room; spawn timing repeatability only',
            'world-x uses the zombie-calibrated word-8 mapping on projectile slots; not re-calibrated here',
            'no rendering/OAM/palette, damage/collision, facing/speed model, lifecycle or SFX proof',
        ],
    }
    (folder / 'soul-projectile-twins.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    assert host.read_bytes() == original


if __name__ == '__main__':
    main()
