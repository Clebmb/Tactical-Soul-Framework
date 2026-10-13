"""Generate private authored-policy examples; does not enforce native events."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from aria.cli import load_image, apply_manifest
from aria.room_catalog import room_id
from aria.world_graph import audit_world_graph


def main():
    rom = load_image(ROOT / 'CastlevaniaAoS.gba')
    apply_manifest(rom, ROOT / 'examples/custom_room/mod.json')
    graph = audit_world_graph(rom)
    start, target = [room_id(graph['profile'], 0, index) for index in (31, 3)]
    edge = next(edge['id'] for edge in graph['edges']
                if edge['source'] == start and edge['targets'] == [target])
    spec = {'schema_version': 1, 'profile': graph['profile'],
            'image_sha256': graph['image_sha256'], 'start': start,
            'flags': ['key'], 'required_rooms': [target], 'itinerary': [target, start],
            'edge_requirements': {edge: ['key']}}
    folder = ROOT / 'local/progression'
    folder.mkdir(parents=True, exist_ok=True)
    for name, room in (('key-before-gate', start), ('key-behind-gate', target)):
        spec['room_grants'] = {room: ['key']}
        path = folder / (name + '.json')
        path.write_text(json.dumps(spec, indent=2) + '\n', encoding='utf-8')
        print(path)


if __name__ == '__main__':
    main()
