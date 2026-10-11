"""Read-only live capture: bank-0 tall-actor OAM tiles + OBJ palette bank 0.

No RAM writes. Boots the hallway, records the moving bank-0 tall actor's
OAM tile numbers, and saves VRAM, the tile list, OBJ palette banks 0/10
and a screenshot to local/. v0.30 correction (see ENEMY-BINDING.md):
kinematics show the bank-0 entries track Soma, not the walker, so this
capture identifies Soma-adjacent art/palette sources, not walker ones.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from emulator import Emulator
from probe_actor_binding import boot, tall_entries, zombie_slots
from aria.cli import load_image
from aria.tables import read_record

def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    rom = load_image(host)
    zombie_update = read_record(rom, 'enemies', 1)['update_code']
    e = Emulator(host)
    try:
        boot(e)
        slots = zombie_slots(e, zombie_update)
        assert slots, 'No live Zombie at capture start'
        tiles = set()
        for _ in range(250):
            e.run(1)
            for _index, _x, bank, tile in tall_entries(e):
                if bank == 0:
                    tiles.add(tile)
        assert tiles, 'No bank-0 tall tiles observed'
        vram = e.bytes(0x06010000, 0x8000)
        pal0 = e.bytes(0x05000200, 32)
        pal10 = e.bytes(0x05000280, 32)
        oam = e.bytes(0x07000000, 1024)
        e.snap('zombie-live-capture.png')
    finally:
        e.close()
    out = ROOT / 'local/zombie-live'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'vram.bin').write_bytes(vram)
    (out / 'pal0.bin').write_bytes(pal0)
    (out / 'pal10.bin').write_bytes(pal10)
    (out / 'oam.bin').write_bytes(oam)
    tile_list = sorted(tiles)
    tile_bytes = b''.join(vram[t * 32:(t + 1) * 32] for t in tile_list)
    (out / 'walker-tiles.bin').write_bytes(tile_bytes)
    report = {
        'status': 'walker_source_captured',
        'bank0_tiles': tile_list,
        'walker_tiles_sha256': hashlib.sha256(tile_bytes).hexdigest(),
        'pal0_sha256': hashlib.sha256(pal0).hexdigest(),
        'pal10_sha256': hashlib.sha256(pal10).hexdigest(),
        'fixtures': ['read-only capture; no graphics/OAM/palette/tile RAM writes'],
    }
    (out / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    assert host.read_bytes() == original
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
