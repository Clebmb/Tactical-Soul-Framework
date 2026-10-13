"""Native 33-word record scan for Winged Skeleton projectile slots (private).

One fresh-core run repeats the verified opening + menu + one Up+B cast, then
captures the full 33-word records of slots 2–3 at frames +7..+61 in 9-frame
steps, with Soma world-x as a stillness reference. Reports which words change
across the cast window with min/max/delta facts.

Read-only: no ROM writes, no authoring. A changing word is a tracking
candidate, not a proven position/velocity semantic. Outputs stay under local/.
Original ROM is never modified.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aria.soul_projectiles import (
    SLOT_WORDS,
    code_to_slots,
    diff_records,
    novel_codes,
    read_slot_record,
    snapshot_actor_window,
)
from emulator import Emulator

EXPECTED_COST = 12
SAMPLE_FRAMES = [7, 16, 25, 34, 43, 52, 61]


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
        baseline = snapshot_actor_window(e.read)
        mp_pre = e.read(0x0201327C, 2)
        e.run(1, [4, 0])
        e.run(6)
        assert mp_pre - e.read(0x0201327C, 2) == EXPECTED_COST
        e.run(1)
        samples = []
        previous = 0
        for frame in SAMPLE_FRAMES:
            e.run(frame - previous)
            previous = frame
            snap = snapshot_actor_window(e.read)
            samples.append({
                'frame': frame,
                'codes': {str(slot): hex(snap[slot]) if slot in snap else None for slot in (2, 3)},
                'novel': novel_codes(baseline, snap),
                'soma_world_x': e.read(0x02000526, 2) + e.read(0x0200A09A, 2),
                'soma_world_y': e.read(0x0200052A, 2) + e.read(0x0200A09E, 2),
                'records': {str(slot): [hex(w) for w in read_slot_record(e.read, slot)] for slot in (2, 3)},
            })
        words = {}
        for slot in (2, 3):
            series = [[int(w, 16) for w in s['records'][str(slot)]] for s in samples]
            per_word = []
            for index in range(SLOT_WORDS):
                values = [row[index] for row in series]
                per_word.append({
                    'index': index,
                    'changed': len(set(values)) > 1,
                    'first_hex': hex(values[0]),
                    'last_hex': hex(values[-1]),
                    'min_hex': hex(min(values)),
                    'max_hex': hex(max(values)),
                })
            words[str(slot)] = {
                'changed_indices': [w['index'] for w in per_word if w['changed']],
                'per_word': per_word,
                'spawn_to_end_diff': diff_records(series[0], series[-1]),
            }
        report = {
            'route': 'verified opening + soul menu open/close + one Up+B cast, 33-word scan',
            'sample_frames': SAMPLE_FRAMES,
            'samples': [{k: s[k] for k in ('frame', 'codes', 'novel', 'soma_world_x', 'soma_world_y')}
                        for s in samples],
            'slot_records_first': {s['frame']: s['records'] for s in (samples[0], samples[-1])},
            'words': words,
            'scope': ('changing words are tracking candidates; no position/velocity '
                      'semantic is proven'),
            'original_unchanged': host.read_bytes() == original,
            'rom_sha256': hashlib.sha256(original).hexdigest(),
            'limits': [
                'one cast, one room, one run; slots 2–3 only',
                'post-despawn recycling and other slots unmapped',
                'no rendering/OAM/palette, damage/collision, lifecycle or SFX proof',
            ],
        }
        (ROOT / 'local/soul-projectile-words.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps({k: report[k] for k in ('sample_frames', 'samples', 'words', 'scope', 'limits')}, indent=2))
    finally:
        e.close()
        assert host.read_bytes() == original


if __name__ == '__main__':
    main()
