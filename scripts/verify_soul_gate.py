"""Native narrow ownership barrier: unowned walk/jump/attack, owned exit and save.

Ownership/position are never injected. Fresh-instance SRAM transport is used;
--composed additionally injects an HP deficit solely to verify healing.
The owned probe redirects the entrance door; the gated room's exit is unchanged.
"""
import ctypes as C
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aria.cli import load_image, apply_manifest_data
from aria.rooms import room_address, doors, replace_doors
from aria.input_routes import observe_native
from aria.native_events import observe_progression_flags
from aria.room_catalog import room_id
from aria.world_graph import audit_world_graph
from aria.progression_traces import compare_progression_trace
from emulator import Emulator


def boot(e, save, opening=False):
    e.run(1000)
    for key in [3, 8, 8, 8, 3, 3, 8]:
        e.run(1, [key]); e.run(100)
    for _ in range(60):
        e.run(1, [8]); e.run(90)
        if not opening and e.read(0x02000088) == save and e.read(0x02000010, 1) == 4:
            break
    e.run(120)


def save_game(e):
    e.run(1, [4]); e.run(30)
    assert e.read(0x0200042C) & 1
    before = C.string_at(e.lib.retro_get_memory_data(0), e.lib.retro_get_memory_size(0))
    e.run(1, [6]); e.run(1); e.run(1, [8]); e.run(240)
    result = C.string_at(e.lib.retro_get_memory_data(0), e.lib.retro_get_memory_size(0))
    assert result != before
    return result


def continue_game(e, sram, save):
    C.memmove(e.lib.retro_get_memory_data(0), sram, len(sram))
    e.run(1000)
    for key in [3, 8, 8, 8]:
        e.run(1, [key]); e.run(160)
    assert e.read(0x02000088) == save and e.read(0x0201327A, 2) > 0


def blocked_crossing(e, save, keys, frames=180, sdk=False):
    states, reasons, minimum, minimum_y = set(), set(), 9999, 9999
    for _ in range(frames):
        e.run(1, keys)
        row = observe_native(e)
        minimum = min(minimum, row['world_x'])
        minimum_y = min(minimum_y, row['world_y'])
        states.add(e.read(0x020004EE, 1))
        if sdk: reasons.add(e.read(0x0203D024))
        assert row['room_address'] == save and row['world_x'] >= 80, row
        assert e.read(0x0201331C, 1) & 15 == 0
    return {'minimum_x': minimum, 'minimum_y': minimum_y, 'player_states': sorted(states),
            'sdk_block_reasons': sorted(reasons)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--composed', action='store_true', help='Check the custom SDK runtime; includes an explicit HP-deficit fixture')
    args = parser.parse_args()
    name = 'soul-gate-abilities' if args.composed else 'soul-gate'
    host = ROOT / 'CastlevaniaAoS.gba'; original = host.read_bytes()
    folder = ROOT / 'local' / name; folder.mkdir(parents=True, exist_ok=True)
    manifest_folder = ROOT / 'examples' / name
    spec = json.loads((manifest_folder / 'mod.json').read_text())
    outcomes = {}
    for owned in (False, True):
        rom = load_image(host)
        selected = dict(spec)
        if owned:
            selected.pop('new_game_start')
        apply_manifest_data(rom, selected, manifest_folder)
        save = room_address(rom, 0, 14)
        destination = doors(rom, save)[0].destination
        if owned:
            entrance = room_address(rom, 0, 0)
            rows = doors(rom, entrance)
            rows[0].destination = save
            rows[0].dest_x_2 = rows[0].dest_y_2 = 0
            rows[0].dest_x, rows[0].dest_y = 128, 160
            replace_doors(rom, entrance, rows, 'gate-owned-route')
        out = folder / ('owned.gba' if owned else 'unowned.gba'); rom.output(out, host)
        e = Emulator(out)
        result = {}
        try:
            boot(e, save, opening=owned)
            assert bool(e.read(0x0201331C, 1) & 15) == owned
            if owned:
                for _ in range(300):
                    e.run(4, [7])
                    if e.read(0x02000088) == save: break
                assert e.read(0x02000088) == save
                e.run(120); e.run(79, [7]); e.run(30)
            else:
                if args.composed:
                    # Explicit HP-only deficit fixture for positive healing proof.
                    # Ownership, position, velocity and input RAM are never injected.
                    cap = e.read(0x0201327E, 2)
                    e.write(0x0201327A, cap - 20, 2)
                    e.run(120)
                    assert e.read(0x0201327A, 2) == cap - 19
                    assert e.read(0x0203D044) == 1
                    mp = e.read(0x0201327C, 2)
                    e.run(1, [11])
                    assert e.read(0x0201327A, 2) == cap - 14
                    assert e.read(0x0201327C, 2) == mp - 3
                    assert e.read(0x0203D054) == 1
                    e.run(1)
                    result['sdk_healing'] = 'regen +1 at120 eligible frames; focus +5/-3MP on R press'
                for action, keys in (('walk', [6]), ('jump', [6, 8]), ('attack', [6, 0])):
                    result[action] = blocked_crossing(e, save, keys, sdk=args.composed)
                    e.run(30)
                assert 1 in result['attack']['player_states'], 'attack fixture did not attack'
                if args.composed:
                    assert 6 in result['attack']['sdk_block_reasons'], 'SDK healing guard did not block attack'
                assert result['jump']['minimum_y'] < 170, 'jump fixture did not jump'
                e.run(1, [3]); e.run(30)
                assert e.read(0x02000064, 1) == 6
                paused = e.bytes(0x02000524, 4)
                cooldown = e.read(0x0203D050) if args.composed else None
                e.run(60)
                assert e.bytes(0x02000524, 4) == paused
                if args.composed: assert e.read(0x0203D050) == cooldown
                e.run(1, [0]); e.run(30)
                assert e.read(0x02000064, 1) == 1
                result['pause_resume_walk'] = blocked_crossing(e, save, [6], 30)
                e.run(30, [7]); e.run(30)
            assert abs(observe_native(e)['world_x'] - 128) <= 4
            sram = save_game(e)
        finally:
            e.close()
        e = Emulator(out)
        try:
            continue_game(e, sram, save)
            first = observe_progression_flags(e.read)
            assert first['flags']['first_red_soul_owned'] is owned
            if not owned:
                result['fresh_continue_walk'] = blocked_crossing(e, save, [6])
            else:
                for _ in range(180):
                    e.run(1, [6])
                    if e.read(0x02000088) != save: break
                assert e.read(0x02000088) == destination
                e.run(120)
                last = observe_progression_flags(e.read)
                graph = audit_world_graph(rom)
                start = room_id(rom.profile['id'], 0, 14)
                edge = next(edge for edge in graph['edges'] if edge['source'] == start)
                target = edge['targets'][0]
                policy = {'schema_version': 1, 'profile': graph['profile'],
                          'image_sha256': graph['image_sha256'], 'start': start,
                          'flags': ['first_red_soul_owned'], 'initial_flags': ['first_red_soul_owned'],
                          'required_rooms': [target], 'itinerary': [target],
                          'edge_requirements': {edge['id']: ['first_red_soul_owned']}}
                trace = {'schema_version': 1, 'profile': graph['profile'],
                         'image_sha256': graph['image_sha256'], 'samples': [
                             {'room': start, 'flags': first['flags'], 'via': None},
                             {'room': target, 'flags': last['flags'], 'via': edge['id']}]}
                result['comparison'] = compare_progression_trace(graph, policy, trace)
                assert result['comparison']['matches_policy'] and result['comparison']['itinerary_observed']
            result['continued_ownership'] = owned
        finally:
            e.close()
        result['rom_sha256'] = hashlib.sha256(out.read_bytes()).hexdigest()
        outcomes['owned' if owned else 'unowned'] = result
    assert host.read_bytes() == original
    report = {'outcomes': outcomes, 'original_unchanged': True, 'composed_sdk': args.composed,
              'fixtures': ['unowned registered room14 start', 'owned native opening plus entrance-door redirect',
                           'controller-only gameplay; saved SRAM transport to fresh cores'],
              'limits': ['empty room14 west barrier only; states0/1 tested, others skipped',
                         'not a general door-lock system or composable ability module',
                         'no hurt/transformation/scripted-transition or arbitrary-speed certification']}
    if args.composed:
        report['fixtures'].append('HP-only deficit write for positive healing tests; no ownership/position injection')
        report['limits'][1] = 'custom SDK runtime has fixed always-enabled barrier; no generic lock schema'
    report_name = 'soul-gate-abilities' if args.composed else 'soul-gate'
    (ROOT / 'local' / (report_name + '-verification.json')).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
