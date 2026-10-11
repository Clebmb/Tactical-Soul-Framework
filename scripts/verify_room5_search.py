"""Bounded native input sweep. A missed goal is evidence, not a softlock proof."""
import sys,json,hashlib,dataclasses
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from emulator import Emulator
from aria.input_routes import replay_input_route,observe_native
host=ROOT/'CastlevaniaAoS.gba';original=hashlib.sha256(host.read_bytes()).hexdigest()
rom=ROOT/'local/connection-traversal-fixture.gba'
evidence=json.loads((ROOT/'local/connection-traversal-verification.json').read_text())
assert evidence['status']=='controlled_native_traversal_passed'
assert hashlib.sha256(rom.read_bytes()).hexdigest()==evidence['fixture_sha256']
e=Emulator(rom)
def route(walk):
 return {'schema_version':1,'id':'room5-walk-'+str(walk),'segments':[
  {'label':'approach','frames':walk,'keys':[7]},
  {'label':'jump','frames':30,'keys':[7,8]},
  {'label':'coast','frames':40,'keys':[7],'expect':{'room_address':0x0850F294,'state':4,'substate':1,'hp':[1,9999]}}]}
try:
 e.run(1000)
 for k in [3,8,8,8,3,3,8]:e.run(1,[k]);e.run(100)
 for _ in range(60):e.run(1,[8]);e.run(90)
 for _ in range(200):
  e.run(30,[7,8]);e.run(45,[7,0])
  if e.read(0x02000088)==0x0850F294:break
 e.run(240);assert e.read(0x02000088)==0x0850F294
 # Declared bootstrap only: one left-endpoint fixture, no changes in any branch.
 e.write(0x02000524,((32-e.read(0x0200A09A,2))<<16)&0xFFFFFFFF)
 e.write(0x02000528,((180-e.read(0x0200A09E,2))<<16)&0xFFFFFFFF)
 e.write(0x0200052C,0);e.write(0x02000530,0);e.run(60)
 start=observe_native(e);assert start['world_x']==32 and start['world_y']==159
 checkpoint=e.capture_state()
 a=replay_input_route(e,route(48));ram_a=e.bytes(0x02000000,0x40000);pixels_a=e.image.tobytes()
 e.restore_state(checkpoint);assert e.image is None
 b=replay_input_route(e,route(48));assert a==b and e.bytes(0x02000000,0x40000)==ram_a and e.image.tobytes()==pixels_a
 for invalid in [dataclasses.replace(checkpoint,owner=object()),dataclasses.replace(checkpoint,rom_sha256='0'*64),dataclasses.replace(checkpoint,payload=checkpoint.payload[:-1])]:
  before=e.bytes(0x02000000,0x40000)
  try:e.restore_state(invalid)
  except RuntimeError:pass
  else:raise AssertionError('Invalid checkpoint accepted')
  assert e.bytes(0x02000000,0x40000)==before
 trials=[]
 for walk in range(20,75,2):
  e.restore_state(checkpoint);result=replay_input_route(e,route(walk));assert result['status']=='passed'
  result['goal_reached']=result['samples'][-1]['observation']['world_x']>=480 and result['samples'][-1]['observation']['world_y']<=170
  trials.append(result)
 best=max(trials,key=lambda t:t['samples'][-1]['observation']['world_x'])
 e.restore_state(checkpoint);replay_input_route(e,route(int(best['id'].rsplit('-',1)[1])));e.snap('room5-search-best.png')
 report={'status':'bounded_search_completed','fixture_sha256':e.rom_sha256,'start':start,'trials':trials,
         'goal_reached':any(t['goal_reached'] for t in trials),'best_trial':best['id'],
         'best_endpoint':best['samples'][-1]['observation'],
         'checkpoint_checks':['repeat trace, complete EWRAM and framebuffer identical','foreign owner, wrong ROM and truncated payload rejected without EWRAM change'],
         'fixtures':['separate hallway entry harness','one room5 left-endpoint position and zero velocity bootstrap','no RAM edits inside search branches; no ability grants'],
         'limitations':['28 single-jump timings only, not all possible inputs','goal checks final segment only, not continuous room traversal','no proof of impossibility or softlock','no repaired campaign lifecycle certification']}
 (ROOT/'local/room5-search-verification.json').write_text(json.dumps(report,indent=2))
 print(json.dumps({k:v for k,v in report.items() if k!='trials'},indent=2))
finally:e.close();assert hashlib.sha256(host.read_bytes()).hexdigest()==original
try:e.restore_state(checkpoint)
except RuntimeError:pass
else:raise AssertionError('Closed emulator accepted checkpoint')
