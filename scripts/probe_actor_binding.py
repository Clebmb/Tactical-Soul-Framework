"""Native actor visual-binding discovery: track hallway OAM actors and probe resources.

Private host, mGBA libretro and Pillow required. Reads VRAM/OAM/EWRAM, plus one
declared fixture: zeroing Zombie actor slots' observed HP words to trigger
native deaths (same fixture class as prior save/death harnesses). No
graphics/OAM/palette/tile RAM is written. Evidence goes to local/.

Established stable facts (asserted): HP-zero clears every live Zombie slot;
the candidate resource entry at 0x081186F0 holds single-referenced raw 4KB page, 1-bank palette and 21-frame/9-animation struct whose consumer is unknown. Corrected in v0.30 (see ENEMY-BINDING.md): bank-0 tall OAM parts track Soma by kinematics and persist across rooms, so OAM-bank tracking does not identify the walker; the walker source question stays open.
"""
import hashlib
import struct
import sys
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from aria.cli import load_image
from aria.sprites import SPRITES, inspect_sprite
from aria.sprite_rendering import resolve_sprite_resources
from aria.tables import read_record
from emulator import Emulator

SHAPES = (((8, 8), (16, 16), (32, 32), (64, 64)),
          ((16, 8), (32, 8), (32, 16), (64, 32)),
          ((8, 16), (8, 32), (16, 32), (32, 64)))
ZOMBIE_INDEX = 1
ENTRY = 0x081186F0
PAGE_WRAPPER = 0x082052F8
PAGE_DATA = 0x082052FC
PALETTE_WRAPPER = 0x0820C550


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
    e.run(70, [7])
    e.run(120)


def zombie_slots(e, update_code):
    return [0x020004E4 + j * 0x84 for j in range(1, 224) if e.read(0x020004E4 + j * 0x84) == update_code]


def tall_entries(e):
    oam = e.bytes(0x07000000, 1024)
    out = []
    for index in range(128):
        a, b, c, _ = struct.unpack_from('<4H', oam, index * 8)
        if a & 0x3F00 or (a >> 14) == 3:
            continue
        w, h = SHAPES[a >> 14][b >> 14]
        if h < 16:
            continue
        x = b & 511
        if x >= 256:
            x -= 512
        out.append((index, x, (c >> 12) & 15, c & 1023))
    return out


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    rom = load_image(host)
    blob = original
    zombie_update = read_record(rom, 'enemies', ZOMBIE_INDEX)['update_code']
    # Static registration integrity: wrapper bytes, current hashes, single references.
    assert rom.read(PAGE_WRAPPER, 4) == bytes.fromhex('00 04 10 08')
    assert rom.read(PALETTE_WRAPPER, 4) == bytes.fromhex('00 04 01 00')
    page = rom.read(PAGE_DATA, 4096)
    palette = rom.read(PALETTE_WRAPPER + 4, 32)
    assert hashlib.sha256(page).hexdigest() == 'a9ac039760480118897915b64e8e429eeae626e9cf8124eaac18763bcef4c139'
    assert hashlib.sha256(palette).hexdigest() == 'b9ea4f9fe0aae061460895c0ee675da10e55deb76a67bdedcd13361078173e78'
    sprite = inspect_sprite(rom, SPRITES['unknown-actor'])
    assert (sprite['frame_count'], sprite['animation_count'], sprite['diagnostics']) == (21, 9, [])
    for address in (PAGE_WRAPPER, PALETTE_WRAPPER, SPRITES['unknown-actor']):
        word = struct.pack('<I', address)
        hits, off = [], 0
        while True:
            i = blob.find(word, off)
            if i < 0:
                break
            hits.append(hex(0x08000000 + i))
            off = i + 1
        assert len(hits) == 1 and hits[0] == hex(ENTRY + (address == PALETTE_WRAPPER) * 4 +
                                                 (address == SPRITES['unknown-actor']) * 8), (hex(address), hits)
    resources = resolve_sprite_resources(rom, 'unknown-actor')
    assert len(resources['pages'][0]) == 4096 and len(resources['palette']) == 16
    e = Emulator(host)
    try:
        boot(e)
        slots = zombie_slots(e, zombie_update)
        assert slots and all(e.read(s + 0x34, 2) > 0 for s in slots), 'No live Zombie at probe start'
        xs = {}
        for _ in range(250):
            e.run(1)
            for index, x, bank, _tile in tall_entries(e):
                xs.setdefault((index, bank), set()).add(x)
        moving_bank0 = [k for k, v in xs.items() if k[1] == 0 and max(v) - min(v) >= 3]
        static_bank10 = [k for k, v in xs.items() if k[1] == 10 and max(v) - min(v) == 0]
        assert moving_bank0, 'No moving bank-0 tall actor tracked (zombie)'
        assert static_bank10, 'No static bank-10 tall actor tracked (Soma)'
        for _ in range(40):
            for s in zombie_slots(e, zombie_update):
                e.write(s + 0x34, 0, 2)
            e.run(10)
            if not zombie_slots(e, zombie_update) or not any(
                    e.read(s + 0x34, 2) > 0 for s in zombie_slots(e, zombie_update)):
                break
        assert not any(e.read(s + 0x34, 2) > 0 for s in zombie_slots(e, zombie_update)), \
            'HP-zero fixture did not clear Zombie slots'
        e.run(200)
        vram = e.bytes(0x06010000, 0x8000)
        alive_note = 'page0-row residency is phase-dependent; see ENEMY-BINDING.md'
        soma_hp = e.read(0x0201327A, 2)
        e.snap('actor-binding.png')
    finally:
        e.close()
    report = {
        'status': 'native_actor_binding_probed',
        'resource_entry': hex(ENTRY),
        'page_sha256': hashlib.sha256(page).hexdigest(),
        'palette_sha256': hashlib.sha256(palette).hexdigest(),
        'sprite_struct': {'frames': 21, 'animations': 9},
        'tracked': {'moving_bank0_entries': [list(k) for k in moving_bank0],
                    'static_bank10_entries': [list(k) for k in static_bank10]},
        'kill_fixture': 'HP zeroed in observed Zombie actor slots; all slots cleared',
        'residency_note': alive_note,
        'soma_hp_after': soma_hp,
        'fixtures': ['HP zeroed in observed Zombie actor slots to trigger native deaths; no graphics/OAM/palette/tile writes'],
        'limitations': ['Walking-zombie graphics source unresolved: not the registered raw page, common pool, or five LZ table pages in hallway combat',
                        'Single static references are uninterpreted occurrence counts, not loader proof',
                        'One hallway session; spawner/respawn timing may shift disappearance sets'],
    }
    assert host.read_bytes() == original
    (ROOT / 'local').mkdir(exist_ok=True)
    (ROOT / 'local/actor-binding.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
