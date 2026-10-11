"""Bounded exact-host catalog audit; private reports remain in local/."""
import sys,json,hashlib
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest
from aria.room_catalog import catalog_rooms
from aria.rooms import room_address
host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes();r=load_image(host)
folder=ROOT/'local/catalog-audit';folder.mkdir(parents=True,exist_ok=True)
offset=0;ids=[];statuses=Counter();layer_statuses=Counter();pages=0
for _ in range(96): # hard cap: 12 sectors * 256 slots / 32 per page
    c=catalog_rooms(r,offset=offset,limit=32)
    assert c['enumeration_complete'],c['diagnostics']
    for room in c['rooms']:
        ids.append(room['id']);statuses[room['status']]+=1
        # Independently exercise the public lookup at every discovered slot.
        assert room['room_address']==room_address(r,room['sector'],room['room'])
        layer_statuses.update(l['geometry_status'] for l in room['layers'])
    (folder/f'page-{offset:04d}.json').write_text(json.dumps(c,indent=2));pages+=1
    if c['next_offset'] is None:break
    assert c['next_offset']>offset;offset=c['next_offset']
else:raise AssertionError('Catalog paging exceeded bound')
assert len(ids)==len(set(ids))==c['total_known_slots']
assert bytes(r.data)==original and not r.ledger and not r.allocations
samples=[]
for index in [0,3,6,31]:
    page=catalog_rooms(r,sector=0,offset=index,limit=1,check_rendering=True)
    room=page['rooms'][0];assert all(l['render_status']=='available' for l in room['layers'])
    samples.append({'id':room['id'],'layers_rendered':len(room['layers'])})
before=catalog_rooms(r,sector=0,offset=3,limit=1)['rooms'][0]
background_samples=[]
from aria.backgrounds import render_background
for offset in range(0,len(ids),32):
    page=catalog_rooms(r,offset=offset,limit=32)
    for room in page['rooms']:
        for layer in room['layers']:
            if layer.get('geometry_format')!='background_byte_index':continue
            p=render_background(r,room['sector'],room['room'],layer['layer'])
            assert p['width']>0 and p['height']>0
            background_samples.append({'id':room['id'],'layer':layer['layer'],'rgba_sha256':p['report']['rgba_sha256']})
assert len(background_samples)==24
apply_manifest(r,ROOT/'examples/geometry-workshop/mod.json')
after=catalog_rooms(r,sector=0,offset=3,limit=1)['rooms'][0]
assert before['id']==after['id'] and before['layers'][0]['geometry']['layout_sha256']!=after['layers'][0]['geometry']['layout_sha256']
assert host.read_bytes()==original
report={'passed':['all normal sector slots paged once with unique stable IDs','public room lookup agrees at every discovered slot including final sector','12 selected layers render through catalog checks','mod changes selected geometry without changing room identity','catalog does not mutate ROM/ledger/allocations; original unchanged'],
        'room_slots':len(ids),'pages':pages,'room_status_counts':dict(statuses),'geometry_status_counts':dict(layer_statuses),'render_samples':samples,
        'background_source_rasters':background_samples,'background_viewport_pixels_verified':False,
        'host_sha256':hashlib.sha256(original).hexdigest(),
        'limitations':['decode audit is not native campaign certification','base states only; alternate/event states not enumerated','4 type-2 sample rooms and all 24 byte-index source rasters; full-room composition not certified','background viewport pixels remain unverified','diagnostic failures are data, not automatic fixes']}
(ROOT/'local/room-catalog-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
