"""Magenta twin-run tracer for the skeleton-row resource page (0x08207300).

Private host, mGBA libretro and Pillow required. Uses the enemy-workshop mod's
paired shortcut doors to reach the skeleton room (0,6) on original and
diagnostic builds with identical inputs. The diagnostic build injects a
single_entry_consumers registry entry at runtime; nothing unproven enters the
production registry. No graphics/OAM/palette RAM is written. Evidence goes to
local/. See docs/ENEMY-BINDING.md.
"""
import copy
import hashlib
import json
import struct
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from aria.cli import load_image, apply_manifest, apply_manifest_data
from aria.core import PatchError
from emulator import Emulator

PAGE_WRAPPER = 0x08207300
PAGE_DATA = 0x08207304
PAL_WRAPPER = 0x0820C574
PAL_DATA = 0x0820C578
PAGE_SHA = '979176f91e6fdfce69573b34392ef61a760b556442a63dbb001eb19a905f4729'
PAL_SHA = 'c6a02d55643e031dcd92ae1b9a19a73c32b10f5fdbc6d7bf1cfcfc1cde355a28'
BASE_MOD = ROOT / 'examples/enemy-workshop/mod.json'
W, H = 240, 160


def skeleton_entry():
    return dict(page_sha=PAGE_SHA, palette_sha=PAL_SHA, wrapper=PAGE_WRAPPER,
                wrapper_bytes='00041008', palette_data=PAL_DATA, compressed_source=None,
                encoding='raw', width=128, height=64, scope='single_entry_consumers', literals=())


def build_diagnostic():
    from aria import sprite_assets as module
    from aria import sprite_rendering as rendering
    original_registry = dict(module.REGISTRY)
    original_resources = dict(rendering.SPRITE_RESOURCES)
    module.REGISTRY['skeleton-probe'] = skeleton_entry()
    rendering.SPRITE_RESOURCES['skeleton-probe'] = dict(
        pages=[PAGE_WRAPPER], palette=PAL_WRAPPER, bank=0)
    try:
        folder = ROOT / 'local/skeleton-probe'
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'art.json').write_text(json.dumps(dict(width=128, height=64, pixels=[1] * 8192)))
        (folder / 'palette.json').write_text(json.dumps([[0, 0, 0], [248, 0, 248]] + [[0, 0, 0]] * 14))
        base = json.loads(BASE_MOD.read_text(encoding='utf-8'))
        rom = load_image(ROOT / 'CastlevaniaAoS.gba')
        apply_manifest(rom, BASE_MOD)
        staged = copy.deepcopy(rom)
        document = dict(schema_version=1, id='skeleton-probe', sprite_assets=[dict(
            resource='skeleton-probe', scope='single_entry_consumers', source='art.json',
            palette_source='palette.json', expected_page_sha256=PAGE_SHA,
            expected_palette_sha256=PAL_SHA,
            provenance='Private diagnostic-only magenta fill; never ship.')])
        apply_manifest_data(staged, document, folder)
        rom.__dict__.clear()
        rom.__dict__.update(staged.__dict__)
        out = ROOT / 'local/skeleton-magenta.gba'
        rom.output(out, ROOT / 'CastlevaniaAoS.gba')
        return out
    finally:
        module.REGISTRY.clear()
        module.REGISTRY.update(original_registry)
        rendering.SPRITE_RESOURCES.clear()
        rendering.SPRITE_RESOURCES.update(original_resources)


def boot(e):
    e.run(1000)
    for key in [3, 8, 8, 8, 3, 3, 8]:
        e.run(1, [key])
        e.run(100)
    for _ in range(60):
        e.run(1, [8])
        e.run(90)
    assert e.read(0x02000010, 1) == 4, 'Not in gameplay state'
    for _ in range(600):
        e.run(1, [7])
        if e.read(0x02000088) == 0x0850F15C:
            break
    assert e.read(0x02000088) == 0x0850F15C, 'Never reached hallway'


def reach_skeleton_room(e):
    e.run(70, [7])
    e.run(120)
    for _ in range(180):
        e.run(20, [7, 0])
        e.run(1, [7, 8])
        e.run(15, [7, 0])
        if e.read(0x02000088) == 0x0850F32C:
            break
    assert e.read(0x02000088) == 0x0850F32C, 'Never reached skeleton room'
    e.run(60)


def capture(path, combat_rounds=60):
    e = Emulator(path)
    try:
        boot(e)
        reach_skeleton_room(e)
        frames = []
        for _ in range(combat_rounds):
            e.run(20, [7, 0])
            e.run(1, [7, 8])
            e.run(15, [7, 0])
            frames.append(e.image.tobytes())
        return frames, e.read(0x0201327A, 2), e.read(0x0201328c)
    finally:
        e.close()


def magenta_count(frame):
    return sum(1 for o in range(0, W * H * 3, 3)
               if frame[o] > 200 and frame[o + 1] < 80 and frame[o + 2] > 200)


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    rom = load_image(host)
    assert rom.read(PAGE_WRAPPER, 4) == bytes.fromhex('00041008')
    assert rom.read(PAL_WRAPPER, 4) == bytes.fromhex('00040100')
    assert hashlib.sha256(rom.read(PAGE_DATA, 4096)).hexdigest() == PAGE_SHA
    assert hashlib.sha256(rom.read(PAL_DATA, 32)).hexdigest() == PAL_SHA
    blob = original
    for address, want in ((PAGE_WRAPPER, None), (0x082587BC, None), (PAL_WRAPPER, None)):
        word = struct.pack('<I', address)
        hits, off = [], 0
        while True:
            i = blob.find(word, off)
            if i < 0:
                break
            hits.append(hex(0x08000000 + i))
            off = i + 1
        assert len(hits) == 1 and hits[0] in ('0x8118708', '0x8118704', '0x8118700'), (hex(address), hits)
    base_rom = load_image(host)
    apply_manifest(base_rom, BASE_MOD)
    base_path = ROOT / 'local/skeleton-base-check.gba'
    base_rom.output(base_path, host)
    run_a, _, _ = capture(base_path)
    run_b, _, _ = capture(base_path)
    baseline_diffs = sum(1 for a, b in zip(run_a, run_b) if a != b)
    diag_path = build_diagnostic()
    mod_frames, mod_hp, mod_exp = capture(diag_path)
    diff_frames, heat = 0, {}
    peak_magenta, peak_frame = 0, 0
    for n, (a, b) in enumerate(zip(run_a, mod_frames)):
        m = magenta_count(b)
        if m > peak_magenta:
            peak_magenta, peak_frame = m, n
        if a == b:
            continue
        diff_frames += 1
        for y in range(H):
            for x in range(W):
                o = (y * W + x) * 3
                if a[o:o + 3] != b[o:o + 3]:
                    heat[(x // 8, y // 8)] = heat.get((x // 8, y // 8), 0) + 1
    hot = sorted(heat.items(), key=lambda kv: -kv[1])[:25]
    base_magenta = max(magenta_count(f) for f in run_a)
    report = {
        'status': 'skeleton_tracer_probed',
        'page_sha256': PAGE_SHA,
        'palette_sha256': PAL_SHA,
        'baseline_self_diffs': baseline_diffs,
        'base_magenta_max': base_magenta,
        'diff_frames': diff_frames,
        'peak_magenta': peak_magenta,
        'peak_frame': peak_frame,
        'hot_cells': [[list(k), v] for k, v in hot],
        'mod_soma_hp': mod_hp,
        'mod_exp': mod_exp,
        'fixtures': [],
        'limitations': ['Twin determinism judged by the baseline self-run comparison',
                        'Skeleton combat uses controller inputs only; kills are not forced'],
    }
    assert host.read_bytes() == original
    (ROOT / 'local').mkdir(exist_ok=True)
    (ROOT / 'local/skeleton-binding.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
