"""Native opening red-soul acquisition and save/continue; private routed probe.

One existing entrance door is redirected to the verified save room (0,14).
No event, position, HP or inventory RAM writes; only saved SRAM transport.
This diagnostic does not certify the original campaign route or a grant ABI.
"""
import ctypes as C
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aria.cli import load_image
from aria.rooms import doors, room_address, replace_doors
from aria.input_routes import observe_native
from aria.native_events import observe_progression_flags
from aria.world_graph import audit_world_graph
from aria.room_catalog import room_id
from aria.campaign_progression import plan_progression
from aria.progression_traces import compare_progression_trace
from emulator import Emulator


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    rom = load_image(host)
    save = room_address(rom, 0, 14)
    entrance = room_address(rom, 0, 0)
    rows = doors(rom, entrance)
    assert len(rows) == 1
    rows[0].destination = save
    rows[0].dest_x_2 = rows[0].dest_y_2 = 0
    rows[0].dest_x, rows[0].dest_y = 128, 160
    replace_doors(rom, entrance, rows, 'soul-save-diagnostic')
    folder = ROOT / 'local/soul-progression'
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / 'probe.gba'
    rom.output(out, host)
    graph = audit_world_graph(rom)
    start_id, save_id = [room_id(rom.profile['id'], 0, index) for index in (0, 14)]
    edge_id = next(edge['id'] for edge in graph['edges']
                   if edge['source'] == start_id and edge['targets'] == [save_id])
    # Begin the policy after the scripted acquisition, not on room entry.
    policy = {'schema_version': 1, 'profile': graph['profile'],
              'image_sha256': graph['image_sha256'], 'start': start_id,
              'flags': ['first_red_soul_owned'], 'initial_flags': ['first_red_soul_owned'],
              'required_rooms': [save_id], 'itinerary': [save_id],
              'edge_requirements': {edge_id: ['first_red_soul_owned']}}
    planned = plan_progression(graph, policy)
    assert planned['itinerary_route']['door_path'] == [edge_id]
    observations = {}
    transitions = []
    e = Emulator(out)
    try:
        e.run(1000)
        for key in [3, 8, 8, 8, 3, 3, 8]:
            e.run(1, [key])
            e.run(100)
        before = e.read(0x0201331C, 1)
        assert before == 0, before
        observations['before_opening_grant'] = {'raw_byte': before, 'context': observe_native(e)}
        for cycle in range(60):
            for frame in range(91):
                old = e.read(0x0201331C, 1)
                e.run(1, [8] if frame == 0 else [])
                new = e.read(0x0201331C, 1)
                if new != old:
                    transitions.append({'cycle': cycle, 'frame': frame, 'before': old, 'after': new})
        assert len(transitions) == 1 and transitions[0]['before'] == 0 and transitions[0]['after'] == 1, transitions
        observations['after_opening_grant'] = observe_progression_flags(e.read)
        assert e.read(0x02000088) == entrance
        assert observations['after_opening_grant']['flags']['first_red_soul_owned']
        for _ in range(300):
            e.run(4, [7])
            if e.read(0x02000088) == save:
                break
        assert e.read(0x02000088) == save
        e.run(120)
        # Input-only movement from the observed left-edge landing to the statue.
        e.run(79, [7])
        e.run(30)
        assert abs(observe_native(e)['world_x'] - 128) <= 4
        observations['settled_destination'] = observe_progression_flags(e.read)
        e.run(1, [4])
        e.run(30)
        assert e.read(0x0200042C) & 1, 'native save prompt did not open'
        before_sram = C.string_at(e.lib.retro_get_memory_data(0), e.lib.retro_get_memory_size(0))
        e.run(1, [6])
        e.run(1)
        e.run(1, [8])
        e.run(240)
        sram = C.string_at(e.lib.retro_get_memory_data(0), e.lib.retro_get_memory_size(0))
        assert sram != before_sram
        observations['after_save'] = observe_progression_flags(e.read)
        assert observations['after_save']['first_red_soul']['count'] == 1
    finally:
        e.close()
    e = Emulator(out)
    try:
        C.memmove(e.lib.retro_get_memory_data(0), sram, len(sram))
        e.run(1000)
        for key in [3, 8, 8, 8]:
            e.run(1, [key])
            e.run(160)
        assert e.read(0x02000088) == save and e.read(0x0201327A, 2) > 0
        observations['fresh_continue'] = observe_progression_flags(e.read)
        assert observations['fresh_continue']['first_red_soul']['count'] == 1
    finally:
        e.close()
    assert host.read_bytes() == original
    trace = {'schema_version': 1, 'profile': graph['profile'],
             'image_sha256': graph['image_sha256'], 'samples': [
                 {'room': start_id, 'flags': observations['after_opening_grant']['flags'], 'via': None},
                 {'room': save_id, 'flags': observations['settled_destination']['flags'], 'via': edge_id}]}
    comparison = compare_progression_trace(graph, policy, trace)
    assert comparison['matches_policy'] and comparison['itinerary_observed']
    assert comparison['required_rooms_observed']
    assert hashlib.sha256(out.read_bytes()).hexdigest() == graph['image_sha256']
    for name, value in (('policy', policy), ('trace', trace), ('comparison', comparison)):
        (folder / (name + '.json')).write_text(json.dumps(value, indent=2), encoding='utf-8')
    report = {'observations': observations, 'acquisition_transitions': transitions,
              'route_comparison': comparison,
              'rom_sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
              'original_unchanged': True, 'native_save_changed_sram': True,
              'fixtures': ['existing entrance door redirected to room (0,14)',
                           'controller-only opening, route and save; fresh-instance SRAM transport'],
              'limits': ['first red-soul slot only; other slots and counts unverified',
                         'no native grant API, ability effect/menu proof, gate enforcement or original campaign certification']}
    (ROOT / 'local/soul-progression-verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
