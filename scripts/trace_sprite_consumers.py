"""Private twin-run magenta tracer for walker art page 0x08635990.

Builds a diagnostic ROM (art solid index-1, palette index 1 set to
magenta, both staged through the ledger; original host untouched), then
runs identical input scripts on original/original (control) and
original/magenta (test) pairs. Any differing pixel names a rendered
consumer of the page. Outputs stay under local/; nothing here ships as
a production writer entry.

Declared fixture: HP-zeroing observed Zombie slots for the kill scene
(same fixture class as prior harnesses). No graphics/OAM/palette RAM
writes.
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
from aria.cli import load_image
from aria.compression import read_aria, rebuild_aria
from aria.sprite_attribution import diff_scenes as library_diff_scenes
from aria.tables import read_record
from emulator import Emulator
from probe_actor_binding import boot, zombie_slots

PAGE = 0x08635990
# All three byte-identical page copies and their wrapper slots. The hallway
# loader demonstrably does not use the first slot alone (diagnostic art
# reaches VRAM yet renders nothing), so all three are repointed together.
SLOTS = ((0x082052DC, 0x08635990), (0x0826C844, 0x086457A0), (0x08277990, 0x0864CFBC))
PALETTE_DATA = 0x0820B168
MAGENTA_555 = 0x7C1F


def build_diagnostic(host):
    rom = load_image(host)
    before = bytes(rom.data)
    resource = read_aria(rom, PAGE)
    assert len(bytes.fromhex(resource['data_hex'])) == 8192
    resource['data_hex'] = (b'\x11' * 8192).hex()
    compressed = rebuild_aria(resource, preserve=False)
    address = rom.allocate('tracer:walker-page', compressed, 4)
    for slot, expected in SLOTS:
        assert rom.integer(slot) == expected, (hex(slot), hex(rom.integer(slot)))
        rom.write(slot, struct.pack('<I', address), 'tracer:walker-binding', struct.pack('<I', expected))
    pal_preimage = rom.read(PALETTE_DATA + 2, 2)
    rom.write(PALETTE_DATA + 2, struct.pack('<H', MAGENTA_555), 'tracer:walker-palette', pal_preimage)
    # Self-check on the staged image before writing it out.
    for slot, _ in SLOTS:
        check = read_aria(rom, rom.integer(slot))
        assert bytes.fromhex(check['data_hex']) == b'\x11' * 8192
        assert rom.integer(slot) == address
    assert rom.read(PALETTE_DATA + 2, 2) == struct.pack('<H', MAGENTA_555)
    out = ROOT / 'local/tracer-magenta-walker.gba'
    rom.output(out, host)
    assert host.read_bytes() == before and bytes(load_image(host).data) == before
    return out, dict(allocated_address=hex(address), compressed_bytes=len(compressed),
                     ledger_entries=len(rom.ledger), slots_repointed=len(SLOTS))


def run_script(path):
    """Identical input script returning per-scene framebuffer bytes."""
    e = Emulator(path)
    try:
        boot(e)
        assert e.read(0x02000088) == 0x0850F15C
        scenes = {}

        def snap_every(label, frames, keys=(), step=10):
            shots = []
            for _ in range(0, frames, step):
                e.run(step, keys)
                shots.append(e.image.tobytes())
            scenes[label] = shots

        snap_every('idle', 300)
        snap_every('walk_right', 600, keys=(7,))
        snap_every('fight', 600, keys=(7,))
        # Kill fixture: zero HP in observed Zombie slots, then watch deaths.
        rom = load_image(ROOT / 'CastlevaniaAoS.gba')
        update = read_record(rom, 'enemies', 1)['update_code']
        for _ in range(40):
            for s in zombie_slots(e, update):
                e.write(s + 0x34, 0, 2)
            e.run(10)
            slots = zombie_slots(e, update)
            if not slots or not any(e.read(s + 0x34, 2) > 0 for s in slots):
                break
        snap_every('kill', 120)
        e.snap('tracer-' + Path(str(path)).stem + '.png')
        return scenes
    finally:
        e.close()


def diff_scenes(left, right):
    """Snapshot diff via the reusable aria.sprite_attribution library."""
    return library_diff_scenes(left, right)


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    diag, build = build_diagnostic(host)
    control_a = run_script(host)
    control_b = run_script(host)
    control = diff_scenes(control_a, control_b)
    assert all(v['differing_frames'] == 0 for v in control.values()), ('nondeterministic harness', control)
    test = diff_scenes(control_a, run_script(diag))
    assert host.read_bytes() == original
    report = dict(status='walker_page_tracer_complete',
                  host_sha256=hashlib.sha256(original).hexdigest(),
                  diagnostic_sha256=hashlib.sha256(diag.read_bytes()).hexdigest(),
                  build=build, control_deterministic=True, scenes=test,
                  fixtures=['HP zeroed in observed Zombie slots for the kill scene; no graphics/OAM/palette/tile writes'],
                  limitations=['Only rendered consumers in visited hallway scenes are named',
                               'Sibling-page tiles, shared lists and palette-copy users outside these scenes stay unproven'])
    (ROOT / 'local/tracer-walker.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
