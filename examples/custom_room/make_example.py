"""Recreate original MIT pixel sources and checked bindings from private host.

No extracted character art is written. Native numeric placements/preimages are
read through the framework. Run from any directory with the framework Python.
"""
import json, math, sys
from dataclasses import asdict, replace
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from aria.cli import load_image
from aria.geometry import inspect_geometry
from aria.rooms import room_address, entities, doors


def create():
    folder = Path(__file__).resolve().parent
    def save(name, data):
        (folder/name).write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')
    # Four original 32px organic panels, two brightly lit and two in shadow.
    pixels = []
    for y in range(64):
        for x in range(64):
            u, v = x % 32, y % 32
            ridge = math.sin(u*.43 + math.sin(v*.23)*2.1) + math.cos(v*.37-u*.14)
            vein = abs((u + int(3*math.sin(v*.3)) + (v//11)*5) % 23 - 11)
            if y < 32:
                index = 2 + int((ridge+2)*1.5)
                if vein < 1: index = 1
                if ridge > 1.65: index = 9
            else:
                index = 10 + min(3, max(0, int((ridge+2)*.9)))
                if vein < 1: index = 14
            pixels.append(index)
    save('flesh-tiles.json', {'width':64, 'height':64, 'pixels':pixels})
    save('flesh-palette.json', [
        [0,0,0], [58,4,16], [98,16,32], [124,28,46], [148,40,57],
        [174,57,70], [194,77,87], [214,105,111], [230,135,133],
        [249,170,151], [24,4,13], [38,7,20], [52,11,28], [67,17,34],
        [91,12,31], [255,215,185]])
    rom = load_image(ROOT/'CastlevaniaAoS.gba')
    mod = {'schema_version':1, 'id':'custom_room',
           'description':'Flesh sanctuary: new-game save-room start, right exit and five-screen zombie corridor. Original MIT artwork.',
           'new_game_start':{'sector':0,'room':31,'position':[128,141]},
           'palette_tints':[{'target':target,'style':'blood','scope':'shared-native-palette'}
                            for target in ('save-statue','save-flame','save-particles','zombie')],
           'room_assets':[], 'geometry_edits':[], 'door_lists':[], 'entity_lists':[]}
    template = json.loads((ROOT/'examples/two-room-art/mod.json').read_text())
    for i in (31, 3):
        slot = next(a.copy() for a in template['room_assets'] if a['room']['room']==i)
        slot.update(graphics_source='flesh-tiles.json', palette_source='flesh-palette.json',
                    provenance='Original procedural flesh ridges and vessels; authored for Tactical Soul Framework under MIT. No extracted artwork.')
        mod['room_assets'].append(slot)
        bundle = inspect_geometry(rom,0,i,full=True)
        first = 1
        definitions = []
        for k, (tx,ty,solid) in enumerate(((0,0,True),(4,0,True),(0,4,False),(4,4,False))):
            definitions.append({'id':first+k,
                'minitiles':[0x8200+(ty+y)*8+tx+x for y in range(4) for x in range(4)],
                'collision':[3 if solid else 0]*16})
        cells=[]
        width=bundle['width_cells']
        for p,old in enumerate(bundle['cells']):
            x,y=p%width,p//width
            solid = y <= 1 or y >= 6
            if i == 31: solid |= x == 0
            else: solid |= x == width-1
            value=first+(x%2 if solid else 2+x%2)
            if old != value:cells.append({'x':x,'y':y,'expect':old,'value':value})
        mod['geometry_edits'].append({'room':{'sector':0,'room':i},'layer':0,
            'expected_layout_sha256':bundle['layout_sha256'],'cells':cells,'metatile_replacements':definitions})
    hall=room_address(rom,0,3); sanctuary=room_address(rom,0,31)
    # Numeric native door record serialization is an existing checked API.
    # Retain only this isolated two-room route, with floor at y192.
    save_door=replace(doors(rom,sanctuary)[0], x=1,y=0,destination=hall,
                      dest_x=0,dest_y=0,dest_x_2=0,dest_y_2=0)
    hall_door=replace(doors(rom,hall)[0], destination=sanctuary,
                      dest_x=240,dest_y=0,dest_x_2=0,dest_y_2=0)
    mod['door_lists']=[{'sector':0,'room':31,'doors':[asdict(save_door)]},
                       {'sector':0,'room':3,'doors':[asdict(hall_door)]}]
    rows=entities(rom,hall)
    spawner=next(e for e in rows if e.unique_id==3)
    rows=[replace(e,x=256) if e.unique_id==3 else e for e in rows]
    # Example-local full-list authoring, NOT a new generic spawner clone grant.
    rows.extend([replace(spawner,unique_id=8,x=640),replace(spawner,unique_id=9,x=1024)])
    mod['entity_lists']=[{'sector':0,'room':3,'entities':[asdict(e) for e in rows]}]
    save('mod.json',mod)


if __name__ == '__main__': create()

