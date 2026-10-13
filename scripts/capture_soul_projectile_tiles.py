"""Native projectile tile provenance: OAM entries to VRAM tiles (private).

One fresh-core run repeats the verified opening + menu + one Up+B cast in the
opening room (reliable first-try casts), captures OAM mid-flight while slots
2–3 are live, decodes the cast-rewritten entries 0–8 with
``decode_oam_entry`` and hashes the referenced OBJ tiles plus the 16 OBJ
palette-2 colors. Establishes which tiles/palette the cast uses: the exact
set a future tear-art reskin must replace.

Read-only: no ROM writes, no authoring. Tile/palette identity is not
actor-to-entry proof (which entry serves which slot stays open). Raw tile
bytes and colors stay local in hashed form; no assets ship. Original ROM is
never modified.
"""
import hashlib
import json
import struct
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aria.soul_projectiles import (
    OBJ_TILE_BASE,
    decode_oam_entry,
    snapshot_actor_window,
)
from emulator import Emulator

EXPECTED_COST = 12
OAM_ADDRESS = 0x07000000
OAM_SIZE = 1024
OBJ_PALETTE_ADDRESS = 0x05000200
OBJ_PALETTE_SIZE = 512
PALETTE2_OFFSET = 64
CAST_ENTRIES = list(range(9))


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
        e.run(1, [4, 0])
        e.run(6)
        assert mp_pre - e.read(0x0201327C, 2) == EXPECTED_COST
        e.run(1)
        e.run(22)
        snap = snapshot_actor_window(e.read)
        assert 2 in snap and 3 in snap, 'projectile slots not live'
        oam = e.bytes(OAM_ADDRESS, OAM_SIZE)
        entries = {}
        tiles = {}
        for entry in CAST_ENTRIES:
            decoded = decode_oam_entry(oam[entry * 8:(entry + 1) * 8])
            tile_size = 64 if decoded['colors256'] else 32
            address = OBJ_TILE_BASE + decoded['tile'] * tile_size
            blob = e.bytes(address, tile_size)
            digest = hashlib.sha256(blob).hexdigest()
            tiles.setdefault(digest, {'tile_numbers': [], 'size': tile_size,
                                      'sha256': digest})
            tiles[digest]['tile_numbers'].append(decoded['tile'])
            entries[str(entry)] = {k: decoded[k] for k in (
                'y', 'x', 'tile', 'priority', 'palette', 'colors256',
                'size_pixels', 'disabled', 'affine')}
            entries[str(entry)]['tile_sha256'] = digest
        palette = e.bytes(OBJ_PALETTE_ADDRESS + PALETTE2_OFFSET, 32)
        colors = struct.unpack('<16H', palette)
        report = {
            'route': 'verified opening + menu + one Up+B cast, OAM captured live',
            'mp_spent': EXPECTED_COST,
            'slots_live': sorted(hex(code) for code in snap.values() if code in (snap.get(2), snap.get(3))),
            'entries': entries,
            'distinct_tiles': len(tiles),
            'tiles': sorted(tiles.values(), key=lambda row: row['tile_numbers']),
            'palette2_colors_rgb555': [hex(color) for color in colors],
            'palette2_sha256': hashlib.sha256(palette).hexdigest(),
            'scope': ('tile/palette identity for the 9 cast entries; actor-to-entry '
                      'binding stays open'),
            'original_unchanged': host.read_bytes() == original,
            'rom_sha256': hashlib.sha256(original).hexdigest(),
            'limits': [
                'one cast, one room, one direction, one run',
                '1-D OBJ mapping assumed for tile addressing',
                'no tile-art replacement permission follows',
            ],
        }
        (ROOT / 'local/soul-projectile-tiles.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))
    finally:
        e.close()
        assert host.read_bytes() == original


if __name__ == '__main__':
    main()
