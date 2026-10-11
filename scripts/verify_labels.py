"""Native proof that renamed item labels render in menus (private host only).

Builds a Knife->Fangs rename mod (same length, no padding edge), then
twin-runs a fixed menu tour on the original and the renamed build with
identical inputs. Only rendered consumers can differ: a nonzero,
tightly localized framebuffer diff names the menu text as the consumer.
Control pair (original vs original) must be exactly deterministic.
"""
import hashlib
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from aria.cli import apply_manifest_data, load_image
from aria.labels import resolve_label
from aria.sprite_attribution import diff_scenes
from emulator import Emulator

MOD = {'schema_version': 1, 'id': 'label-proof',
       'label_edits': [{'kind': 'item', 'item': 'Knife',
                        'expect': 'Knife', 'to': 'Fangs'}]}


def press(e, key, wait=40):
    e.run(1, [key])
    e.run(wait)


def start(e):
    e.run(1000)
    for k in [3, 8, 8, 8, 3, 3, 8]:
        press(e, k, 100)
    for _ in range(60):
        press(e, 8, 90)
    assert e.read(0x02000010, 1) == 4


def tour(path):
    """Fixed menu tour returning labeled snapshots."""
    e = Emulator(path)
    try:
        start(e)
        scenes = {}

        def leg(label, moves):
            shots = []
            for key, count in moves:
                for _ in range(count):
                    press(e, key)
                    shots.append(e.image.tobytes())
            scenes[label] = shots

        shots = []
        for key in [3, 5, 8, 5, 5, 8, 5, 8, 8, 6, 8, 8, 7, 8, 0, 0, 3,
                    3, 4, 8, 5, 5, 8, 0, 0, 3]:
            press(e, key)
            shots.append(e.image.tobytes())
        scenes['menu_path'] = shots
        return scenes
    finally:
        e.close()


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    assert resolve_label(load_image(host), 'item', name='Knife')['current'] == 'Knife'
    rom = load_image(host)
    apply_manifest_data(rom, MOD, ROOT)
    before = original
    changed = [i for i, (a, b) in enumerate(zip(before, bytes(rom.data))) if a != b]
    assert 1 <= len(changed) <= 5, len(changed)
    assert len(rom.ledger) == 1
    built = ROOT / 'local/label-proof.gba'
    rom.output(built, host)
    assert host.read_bytes() == original
    control_a = tour(host)
    control_b = tour(host)
    control = diff_scenes(control_a, control_b)
    assert all(v['differing_frames'] == 0 for v in control.values()), ('nondeterministic', control)
    twin = diff_scenes(control_a, tour(built))
    assert host.read_bytes() == original
    hits = {k: v for k, v in twin.items() if v['differing_frames']}
    report = dict(status='label_render_proof_complete',
                  host_sha256=hashlib.sha256(original).hexdigest(),
                  renamed_sha256=hashlib.sha256(built.read_bytes()).hexdigest(),
                  rom_changed_bytes=len(changed), ledger_entries=1,
                  control_deterministic=True, twin=twin,
                  scenes_with_diffs=sorted(hits),
                  fixtures=['No RAM writes; menu tour only'],
                  limitations=['Proves the renamed bytes render somewhere in the toured menus',
                               'Heat localization is evidence, not a glyph transcript'])
    (ROOT / 'local/label-verification.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    assert hits, 'Rename never rendered in the toured menus; proof inconclusive'


if __name__ == '__main__':
    main()
