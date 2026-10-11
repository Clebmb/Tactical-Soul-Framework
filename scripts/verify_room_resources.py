"""Static all-base-room resource survey; no runtime ownership certification."""
import sys,json
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest
from aria.rooms import sector_span
from aria.room_resources import audit_room_resources
host=ROOT/'CastlevaniaAoS.gba';r=load_image(host);original=bytes(r.data);rows=[];states=Counter()
for sector in range(12):
    _,count=sector_span(r,sector)
    for index in range(count):
        a=audit_room_resources(r,sector,index)
        states.update(l['status'] for l in a['layers'])
        rows.append({'sector':sector,'room':index,'diagnostics':a['diagnostics'],
                     'overlaps':a['budget']['character_tilemap_overlaps'],
                     'unavailable_referenced':sum(len(l.get('unavailable_referenced_ids',[])) for l in a['layers'])})
assert len(rows)==343 and bytes(r.data)==original and not r.ledger and not r.allocations
apply_manifest(r,ROOT/'examples/original-room-art/mod.json');a=audit_room_resources(r,0,3,True)
assert a['layers'][0]['metatiles'][144]['available']
assert a['layers'][0]['metatiles'][144]['character_chunks']==[24]
assert not a['budget']['character_tilemap_overlaps']
assert host.read_bytes()==original
report={'passed':['all 343 base-state room static resource audits terminate','audit does not mutate original/ledger/allocations','imported-art dependency points to new graphics/palette loads','shared-list consumer scan completes'],
        'room_count':len(rows),'layer_status_counts':dict(states),'rooms_with_load_diagnostics':sum(bool(x['diagnostics']) for x in rows),
        'rooms_with_static_overlaps':sum(bool(x['overlaps']) for x in rows),'rooms_with_unavailable_referenced_metatiles':sum(bool(x['unavailable_referenced']) for x in rows),
        'rooms':rows,'limitations':['static dependency observations only; no dynamic/global ownership','unsupported layer formats not assigned brush availability','no new write registrations']}
folder=ROOT/'local';folder.mkdir(exist_ok=True);(folder/'room-resource-verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='rooms'},indent=2))
