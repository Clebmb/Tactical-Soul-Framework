"""Native dense velocity track for Winged Skeleton projectile words (private).

One fresh-core run repeats the verified opening + menu + one Up+B cast, then
samples record words 16/17 (prime position candidates) plus 10/2 every 2 frames
on slots 2–3 until both code words clear or 70 frames pass. Fits each series
with ``aria.soul_projectiles.fit_word_series``.

Read-only: no ROM writes, no authoring. A constant fit describes steady motion
at an unproven fixed-point scale, not a certified velocity. Outputs stay under
local/. Original ROM is never modified.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aria.soul_projectiles import (
    fit_word_series,
    read_slot_word,
    snapshot_actor_window,
)
from emulator import Emulator

EXPECTED_COST = 12
STEP = 2
CAP_FRAMES = 70
WORDS = (16, 17, 10, 2)


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
        e.run(1, [3])
        e.run(30)
        e.run(1, [8])
        e.run(30)
        assert e.read(0x02000064, 1) == 6
        for key in [0, 0]:
            e.run(1, [key])
            e.run(30)
        assert e.read(0x02000064, 1) == 1 and e.read(0x020004EE, 1) == 0
        mp_pre = e.read(0x0201327C, 2)
        hp_pre = e.read(0x0201327A, 2)
        e.run(1, [4, 0])
        e.run(6)
        assert mp_pre - e.read(0x0201327C, 2) == EXPECTED_COST
        assert e.read(0x0201327A, 2) == hp_pre
        e.run(1)
        series = {str(slot): {word: [] for word in WORDS} for slot in (2, 3)}
        frames, soma = [], []
        elapsed = 0
        while elapsed < CAP_FRAMES:
            e.run(STEP)
            elapsed += STEP
            snap = snapshot_actor_window(e.read)
            if 2 not in snap and 3 not in snap and frames:
                break
            frames.append(elapsed)
            soma.append(e.read(0x02000526, 2) + e.read(0x0200A09A, 2))
            for slot in (2, 3):
                for word in WORDS:
                    series[str(slot)][word].append(read_slot_word(e.read, slot, word))
        fits = {slot: {str(word): fit_word_series(series[slot][word], STEP)
                       for word in WORDS} for slot in ('2', '3')}
        report = {
            'route': 'verified opening + soul menu open/close + one Up+B cast, 2-frame word track',
            'step_frames': STEP,
            'sample_frames': frames,
            'live_samples': len(frames),
            'soma_world_x_per_sample': soma,
            'soma_still': len(set(soma)) == 1,
            'fits': fits,
            'scope': ('constant fits describe steady word motion at an unproven scale; '
                      'not a certified position/velocity semantic'),
            'original_unchanged': host.read_bytes() == original,
            'rom_sha256': hashlib.sha256(original).hexdigest(),
            'limits': [
                'one cast, one room, one direction, one run',
                'words sampled only while a slot code is present; stale post-clear words excluded',
                'no rendering/OAM/palette, damage/collision, lifecycle or SFX proof',
            ],
        }
        (ROOT / 'local/soul-projectile-velocity.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        short = {slot: {word: {k: fits[slot][word][k] for k in (
            'samples', 'first_hex', 'last_hex', 'displacement_hex', 'monotonic',
            'constant', 'mean_delta', 'min_delta', 'max_delta')} for word in ('16', '17', '10', '2')}
            for slot in ('2', '3')}
        print(json.dumps({'live_samples': len(frames), 'soma_still': report['soma_still'],
                          'fits': short}, indent=2))
    finally:
        e.close()
        assert host.read_bytes() == original


if __name__ == '__main__':
    main()
