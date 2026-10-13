"""Native second registered new-game start: fresh landing in room (0,14),
statue save at spawn, and fresh-instance continue.

No position, HP, graphics or palette RAM writes. SRAM is transported to a
fresh emulator only for the continue check. Original ROM unchanged.
"""
import ctypes as C
import hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aria.cli import load_image, apply_manifest_data
from aria.rooms import room_address
from aria.input_routes import observe_native
from emulator import Emulator

ROOM = (0, 14)
SPAWN = [128, 160]


def boot(e):
    e.run(1000)
    for k in [3, 8, 8, 8, 3, 3, 8]:
        e.run(1, [k])
        e.run(100)
    for _ in range(60):
        e.run(1, [8])
        e.run(90)
        if e.read(0x02000088) == ROOM_ADDRESS and e.read(0x02000010, 1) == 4:
            break
    e.run(120)


ROOM_ADDRESS = None


def main():
    global ROOM_ADDRESS
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    workspace = ROOT / 'local/second-start'
    workspace.mkdir(parents=True, exist_ok=True)
    rom = load_image(host)
    apply_manifest_data(rom, {'schema_version': 1, 'id': 'second-start',
        'new_game_start': {'sector': ROOM[0], 'room': ROOM[1],
                           'position': list(SPAWN)}}, workspace)
    out = workspace / 'probe.gba'
    rom.output(out, host)
    ROOM_ADDRESS = room_address(load_image(host), *ROOM)
    results = []
    e = Emulator(out)
    try:
        boot(e)
        row = observe_native(e)
        assert row['room_address'] == ROOM_ADDRESS and row['state'] == 4, row
        assert row['hp'] > 0 and abs(row['world_x'] - SPAWN[0]) < 12, row
        assert row['world_y'] > 150, row
        e.snap('second-start-landing.png')
        results.append('fresh new game lands in room (0,14) near (128,160) and settles on the native floor')
        e.run(1, [4])
        e.run(30)
        e.snap('second-start-save-prompt.png')
        before = C.string_at(e.lib.retro_get_memory_data(0),
                             e.lib.retro_get_memory_size(0))
        e.run(1, [6])
        e.run(1)
        e.run(1, [8])
        e.run(240)
        sram = C.string_at(e.lib.retro_get_memory_data(0),
                           e.lib.retro_get_memory_size(0))
        assert sram != before, 'native save did not change SRAM'
        results.append('native statue save at spawn changes SRAM')
    finally:
        e.close()
    e = Emulator(out)
    try:
        C.memmove(e.lib.retro_get_memory_data(0), sram, len(sram))
        e.run(1000)
        for k in [3, 8, 8, 8]:
            e.run(1, [k])
            e.run(160)
        row = observe_native(e)
        assert row['room_address'] == ROOM_ADDRESS and row['state'] == 4, row
        assert row['hp'] > 0
        e.snap('second-start-continue.png')
        results.append('fresh-instance continue restores room (0,14) gameplay')
    finally:
        e.close()
    assert host.read_bytes() == original
    report = {'passed': results,
              'rom_sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
              'original_unchanged': True,
              'fixtures': ['fresh SRAM for the new game; native SRAM transport for continue'],
              'limitations': ['single registered landing; other rooms/positions unverified',
                              'no death, event, map or campaign certification']}
    (ROOT / 'local/second-start-verification.json').write_text(
        json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
