"""Input-only continuous bridge crossing in a checked entry harness."""
import sys,json,hashlib,copy,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest
from aria.geometry import inspect_geometry,verify_roundtrip
from aria.rooms import doors,room_address
from aria.level import MAP
from aria.world_graph import audit_world_graph
from aria.input_routes import observe_native
from emulator import Emulator
host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes()
r=load_image(host);before=inspect_geometry(r,0,5,full=True);verify_roundtrip(before)
source=ROOT/'examples/bridge-route';apply_manifest(r,source/'mod.json');after=inspect_geometry(r,0,5,full=True)
changed=[i for i,(a,b) in enumerate(zip(before['cells'],after['cells'])) if a!=b];assert len(changed)==22
assert before['visual_resource']==after['visual_resource'] and before['collision_resource']==after['collision_resource']
assert r.read(before['layout_address'],512)==bytes.fromhex(verify_roundtrip(before)['layout_hex'])
assert r.read(MAP,6016)==original[MAP-0x08000000:MAP-0x08000000+6016]
graph=audit_world_graph(r);assert graph['enumeration_complete'] and graph['summary']['edges_without_observed_direct_return']==3 and graph['summary']['unresolved_destinations']==0
out=ROOT/'build/mods/bridge-route/bridge-route.gba';r.output(out,host)
manifest=json.loads((source/'mod.json').read_text());manifest['room_edits']['connections'][0]['b']={'room':{'sector':0,'room':5},'door':2,'spawn':[0,0]}
workspace=ROOT/'local/bridge-route-harness';workspace.mkdir(parents=True,exist_ok=True)
for asset in manifest['room_assets']:
 for key in ('graphics_source','palette_source'):shutil.copyfile(source/asset[key],workspace/asset[key])
fixture=workspace/'mod.json';fixture.write_text(json.dumps(manifest,indent=2));h=load_image(host);apply_manifest(h,fixture)
for room,index in ((5,0),(5,1),(9,1),(25,1)):assert doors(h,room_address(h,0,room))[index].pack()==doors(r,room_address(r,0,room))[index].pack()
assert inspect_geometry(h,0,5,full=True)['cells']==after['cells']
rom=workspace/'fixture.gba';h.output(rom,host);e=Emulator(rom);samples=[]
def sample(label):
 row=dict(stage=label,**observe_native(e));assert row['state']==4 and row['substate']==1 and row['hp']>0
 samples.append(row);e.snap('bridge-route-'+label+'.png');print(json.dumps(row),flush=True)
try:
 e.run(1000)
 for k in [3,8,8,8,3,3,8]:e.run(1,[k]);e.run(100)
 for _ in range(60):e.run(1,[8]);e.run(90)
 for _ in range(200):
  e.run(30,[7,8]);e.run(45,[7,0])
  if e.read(0x02000088)==room_address(r,0,5):break
 e.run(120);sample('entry');assert e.read(0x02000088)==room_address(r,0,5)
 # No gameplay RAM writes: the checked entrance lands on the upper bridge.
 for label,key,target in [('east-to-nine',7,9),('west-through-five-to-25',6,25),('east-through-five-to-nine',7,9)]:
  visited=[]
  for _ in range(300):
   e.run(3,[key,0]);row=observe_native(e);visited.append(row)
   assert row['hp']>0
   if row['room_address']==room_address(r,0,target):break
  e.run(90);sample(label);assert e.read(0x02000088)==room_address(r,0,target),label
  if 'through-five' in label:
   points=[v for v in visited if v['room_address']==room_address(r,0,5) and v['state']==4 and v['substate']==1]
   assert points and min(v['world_x'] for v in points)<64 and max(v['world_x'] for v in points)>448
 report={'status':'input_only_bridge_traversal_passed','output_sha256':hashlib.sha256(r.data).hexdigest(),'fixture_sha256':hashlib.sha256(h.data).hexdigest(),
         'changed_cells':changed,'graph_summary':graph['summary'],'samples':samples,
         'passed':['22 isolated room5 edits','shared visual/collision resources and source layout unchanged','castle map unchanged','four proposed endpoint records byte-exact','input-only complete room5 crossing in both directions','original unchanged'],
         'fixtures':['checked hallway entry redirects to room5 upper bridge using its lower-left door record and upper spawn; separate private harness','no position, velocity, ability, HP or collision RAM writes'],
         'limitations':['harness entry differs from playable campaign route','neighbor network campaign/event access and full world not certified','main-route lifecycle tested separately; no neighbor-branch save statue']}
 (ROOT/'local/bridge-route-traversal-verification.json').write_text(json.dumps(report,indent=2))
finally:e.close();assert host.read_bytes()==original
