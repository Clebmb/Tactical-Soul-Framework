"""Read-only full-castle support survey; candidates are not write grants."""
import sys,json,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image
from aria.terrain_support import catalog_terrain_support
host=ROOT/'CastlevaniaAoS.gba';r=load_image(host);before=copy.deepcopy(r.__dict__);rows=[];offset=0
while True:
 p=catalog_terrain_support(r,offset=offset,limit=128);assert p['enumeration_complete'];rows.extend(p['rooms'])
 if p['next_offset'] is None:break
 offset=p['next_offset']
assert len(rows)==343 and len({v['id'] for v in rows})==343
registered=[{'sector':v['sector'],'room':v['room']} for v in rows if v['write_enabled']]
assert {(v['sector'],v['room']) for v in registered}=={(0,3),(0,5),(0,6),(0,31)}
assert r.__dict__==before and host.read_bytes()==r.original
summary={status:sum(v['status']==status for v in rows) for status in ('registered','static_candidate','blocked')}
report={'status':'static_support_survey_passed','image_sha256':p['image_sha256'],'rooms':343,'summary':summary,'registered_rooms':registered,
        'passed':['all 343 unique base slots assessed','four existing registrations unchanged','original/image/ledger/profile/allocator unchanged'],
        'limitations':['candidate is not edit authorization or native verification','main-layer and current base-state static loads only','no new registrations performed']}
(ROOT/'local').mkdir(exist_ok=True)
(ROOT/'local/terrain-support-verification.json').write_text(json.dumps(report,indent=2))
(ROOT/'local/terrain-support-catalog.json').write_text(json.dumps({'schema_version':1,'rooms':rows},indent=2))
print(json.dumps(report,indent=2))
