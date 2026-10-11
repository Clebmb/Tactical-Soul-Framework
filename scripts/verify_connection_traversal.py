"""Private native experiment. Controlled entrance fixture, not campaign certification."""
import sys,json,hashlib,copy,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest
from aria.level import apply_level_edits
from aria.connection_plans import plan_connections
from aria.rooms import room_address,doors,dimensions
from emulator import Emulator
host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes()
r=load_image(host);apply_manifest(r,ROOT/'examples/three-room-art/mod.json')
spec=json.loads((ROOT/'examples/three-room-art/neighbor-repair-plan.json').read_text())
proposal=plan_connections(r,spec);apply_level_edits(r,{'connections':spec['connections']})
assert hashlib.sha256(r.data).hexdigest()==proposal['proposed_image_sha256']
# Separate harness manifest combines all connections in one checked write.
# Existing hallway shortcut instead enters room5's lower-left door; the four
# proposal endpoints remain exact. This entry is not a playable campaign route.
manifest=json.loads((ROOT/'examples/three-room-art/mod.json').read_text())
manifest['room_edits']['connections'][0]['b']={'room':{'sector':0,'room':5},'door':2,'spawn':[0,256]}
manifest['room_edits']['connections'].extend(copy.deepcopy(spec['connections']))
h=load_image(host)
# Copy only original authored JSON assets into a private fixture workspace.
# All generated manifests/ROMs/screenshots stay under local/.
workspace=ROOT/'local/connection-traversal';workspace.mkdir(parents=True,exist_ok=True)
for asset in manifest['room_assets']:
 for key in ('graphics_source','palette_source'):
  name=asset[key];shutil.copyfile(ROOT/'examples/three-room-art'/name,workspace/name)
fixture=workspace/'mod.json';fixture.write_text(json.dumps(manifest,indent=2))
apply_manifest(h,fixture)
for index in (0,1):assert doors(h,room_address(h,0,5))[index].pack()==doors(r,room_address(r,0,5))[index].pack()
for room,index in ((9,1),(25,1)):assert doors(h,room_address(h,0,room))[index].pack()==doors(r,room_address(r,0,room))[index].pack()
out=ROOT/'local/connection-traversal-fixture.gba';h.output(out,host)
e=Emulator(out);samples=[]
def sample(label):
 row={'stage':label,'room':hex(e.read(0x02000088)), 'state':e.read(0x02000010,1),'substate':e.read(0x02000064,1),
      'world_x':e.read(0x02000526,2)+e.read(0x0200A09A,2),'world_y':e.read(0x0200052A,2)+e.read(0x0200A09E,2),'hp':e.read(0x0201327A,2)}
 assert row['state']==4 and row['substate']==1 and row['hp']>0, 'inactive/dead gameplay: '+label
 samples.append(row);print(json.dumps(row),flush=True);e.snap('connection-traversal-'+label+'.png');return row
try:
 e.run(1000)
 for k in [3,8,8,8,3,3,8]:e.run(1,[k]);e.run(100)
 for _ in range(60):e.run(1,[8]);e.run(90)
 for _ in range(200):
  e.run(30,[7,8]);e.run(45,[7,0])
  if e.read(0x02000088)==room_address(r,0,5):break
 e.run(240);sample('entry')
 assert e.read(0x02000088)==room_address(r,0,5),'fixture entrance failed'
 # Controlled upper-platform start, after native loading. Preserve collision data.
 e.write(0x02000524,((480-e.read(0x0200A09A,2))<<16)&0xFFFFFFFF)
 e.write(0x02000528,((180-e.read(0x0200A09E,2))<<16)&0xFFFFFFFF)
 e.write(0x0200052C,0);e.write(0x02000530,0);e.run(60);sample('upper-platform-fixture')
 for label,key,target in [('five-to-nine',7,9),('nine-to-five',6,5),('five-to-25',6,25),('25-to-five',7,5)]:
  if label=='five-to-25':
   # Independent endpoint fixture: room5's internal stairs are not under test.
   e.write(0x02000524,((32-e.read(0x0200A09A,2))<<16)&0xFFFFFFFF)
   e.write(0x02000528,((180-e.read(0x0200A09E,2))<<16)&0xFFFFFFFF)
   e.write(0x0200052C,0);e.write(0x02000530,0);e.run(60);sample('left-endpoint-fixture')
  for _ in range(160):
   e.run(3,[key])
   if e.read(0x02000088)==room_address(r,0,target):break
  e.run(90);sample(label)
  assert e.read(0x02000088)==room_address(r,0,target),label+' did not arrive'
  # A room pointer alone is insufficient: require settled gameplay and movement
  # away from the entry without a room change. No position writes at destination.
  width,height=dimensions(r,room_address(r,0,target))
  x=e.read(0x02000526,2)+e.read(0x0200A09A,2)
  y=e.read(0x0200052A,2)+e.read(0x0200A09E,2)
  assert 0<=x<width*256 and 0<=y<height*256
  e.run(30)
  assert e.read(0x0200052A,2)+e.read(0x0200A09E,2)==y,'landing did not settle'
  away=key;e.run(8,[away])
  nx=e.read(0x02000526,2)+e.read(0x0200A09A,2)
  assert e.read(0x02000088)==room_address(r,0,target)
  assert (nx<x if away==6 else nx>x),f'landing cannot move away: {x} -> {nx}, state {e.read(0x020004EE,2)}'
  sample(label+'-move-away')
 report={'status':'controlled_native_traversal_passed','proposal_sha256':proposal['proposed_image_sha256'],'fixture_sha256':hashlib.sha256(h.data).hexdigest(),'samples':samples,'passed':['four native endpoint crossings','settled in-bounds landings','movement away from every destination','exact proposed endpoint bytes','original host unchanged']}
except Exception as error:
 report={'status':'native_experiment_failed','error':str(error),'samples':samples};raise
finally:
 e.close();assert host.read_bytes()==original
 report['fixtures']=['checked harness hallway exit enters room5 lower door; independent room5 left/right endpoint positions with zero velocity after native loading; no collision RAM writes']
 report['limitations']=['room5 internal stairs not traversed end-to-end; independent endpoint fixtures','not full campaign reachability, progression or save lifecycle certification','fixture changes hallway and room5 lower-left entry pair; four proposed endpoints checked byte-exact']
 (ROOT/'local/connection-traversal-verification.json').write_text(json.dumps(report,indent=2))
