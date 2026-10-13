"""Native bridge-art checks: imported room5 art/palette loads, input-only crossings.

No graphics, palette, position, ability, HP or collision RAM writes. The
checked entrance lands on the upper room5 bridge via a private harness that
redirects the first connection; gameplay inputs are controller-only.
"""
import sys,json,hashlib,struct,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest
from aria.geometry import inspect_geometry
from aria.rooms import doors,room_address,metadata
from aria.rendering import read_graphics,read_palettes
from aria.input_routes import observe_native
from emulator import Emulator
host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes()
r=load_image(host);before=inspect_geometry(r,0,5,full=True)
source=ROOT/'examples/bridge-art';apply_manifest(r,source/'mod.json');after=inspect_geometry(r,0,5,full=True)
changed=[i for i,(a,b) in enumerate(zip(before['cells'],after['cells'])) if a!=b];assert len(changed)==22
old_visual=bytes.fromhex(before['visual_resource']['data_hex']);new_visual=bytes.fromhex(after['visual_resource']['data_hex'])
old_collision=bytes.fromhex(before['collision_resource']['data_hex']);new_collision=bytes.fromhex(after['collision_resource']['data_hex'])
assert new_collision==old_collision,'room5 collision must be byte-identical after the reskin'
assert new_visual[5*32:6*32]!=old_visual[5*32:6*32] and new_visual[:5*32]==old_visual[:5*32] and new_visual[6*32:]==old_visual[6*32:]
m=metadata(r,room_address(r,0,5));chunks,_=read_graphics(r,m[4]);banks,_=read_palettes(r,m[5])
assert 24 in chunks and 8 in banks
out=ROOT/'build/mods/bridge-art/bridge-art.gba';r.output(out,host)
manifest=json.loads((source/'mod.json').read_text());manifest['room_edits']['connections'][0]['b']={'room':{'sector':0,'room':5},'door':2,'spawn':[0,0]}
workspace=ROOT/'local/bridge-art-harness';workspace.mkdir(parents=True,exist_ok=True)
for asset in manifest['room_assets']:
 for key in ('graphics_source','palette_source'):shutil.copyfile(source/asset[key],workspace/asset[key])
fixture=workspace/'mod.json';fixture.write_text(json.dumps(manifest,indent=2));h=load_image(host);apply_manifest(h,fixture)
for room,index in ((5,0),(5,1),(9,1),(25,1)):assert doors(h,room_address(h,0,room))[index].pack()==doors(r,room_address(r,0,room))[index].pack()
assert inspect_geometry(h,0,5,full=True)['cells']==after['cells']
rom=workspace/'fixture.gba';h.output(rom,host);e=Emulator(rom);samples=[]
def art(i):
    mm=metadata(r,room_address(r,0,i));cc,_=read_graphics(r,mm[4]);bb,_=read_palettes(r,mm[5])
    assert e.bytes(0x0600C000,2048)==cc[24]
    assert e.bytes(0x05000100,32)==struct.pack('<16H',*bb[8])
def sample(label):
 row=dict(stage=label,**observe_native(e));assert row['state']==4 and row['substate']==1 and row['hp']>0
 samples.append(row);e.snap('bridge-art-'+label+'.png');print(json.dumps(row),flush=True)
try:
 e.run(1000)
 for k in [3,8,8,8,3,3,8]:e.run(1,[k]);e.run(100)
 for _ in range(60):e.run(1,[8]);e.run(90)
 for _ in range(200):
  e.run(30,[7,8]);e.run(45,[7,0])
  if e.read(0x02000088)==room_address(r,0,5):break
 e.run(120);sample('entry');assert e.read(0x02000088)==room_address(r,0,5)
 art(5)
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
 for _ in range(300):
  e.run(3,[6,0])
  if e.read(0x02000088)==room_address(r,0,5):break
 e.run(90);sample('return');assert e.read(0x02000088)==room_address(r,0,5)
 art(5)
 report={'status':'bridge_art_native_passed','output_sha256':hashlib.sha256(r.data).hexdigest(),'fixture_sha256':hashlib.sha256(h.data).hexdigest(),
         'changed_cells':changed,'samples':samples,
         'passed':['22 isolated room5 cells unchanged from the bridge-route design','metatile 6 visual reskinned onto imported chunk 24 / palette bank 8; all other visual bytes preserved','room5 collision stream byte-identical','imported tiles and palette load exactly at native VRAM 0x0600C000 and 0x05000100','input-only complete room5 crossing in both directions over the reskinned deck','exact art reload on natural room5 return','original unchanged'],
         'fixtures':['checked hallway entry redirects to room5 upper bridge using its lower-left door record and upper spawn; separate private harness','no position, velocity, ability, HP, collision, graphics or palette RAM writes'],
         'limitations':['harness entry differs from playable campaign route','neighbor network campaign/event access and full world not certified','no save statue on the bridge branch; lifecycle covered by the main-route examples']}
 (ROOT/'local/bridge-art-verification.json').write_text(json.dumps(report,indent=2))
finally:e.close();assert host.read_bytes()==original
