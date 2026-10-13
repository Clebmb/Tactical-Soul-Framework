"""Private original boot-instrument lifecycle: controller-only fresh-core twins."""
import hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image
from aria.music import install_boot_melody
from emulator import Emulator

def run(path):
 e=Emulator(path);frame=0;records=[]
 def advance(count,keys=()):
  nonlocal frame
  e.run(count,keys);frame+=count
 def checkpoint(name):
  begin=frame;header=e.read(0x03005360);timing=e.start_audio_capture(100000)
  advance(30);pcm=e.stop_audio_capture()
  records.append({'name':name,'start_frame':begin,'header':header,'game_state':e.read(0x02000010,1),
   'substate':e.read(0x02000064,1),'room':e.read(0x02000088),'hp':e.read(0x0201327A,2),'mp':e.read(0x0201327C,2),
   'ownership':e.read(0x0201331C,1),'image_sha256':hashlib.sha256(e.image.convert('RGB').tobytes()).hexdigest(),
   'pcm_sha256':hashlib.sha256(pcm).hexdigest(),'nonzero_audio':any(pcm),'stereo_frames':len(pcm)//4,'timing':timing})
 try:
  advance(1000);checkpoint('boot')
  for index,key in enumerate([3,8,8,8,3,3,8]):
   advance(1,[key]);advance(100)
   checkpoint('menu-step-'+str(index))
  for _ in range(60):advance(1,[8]);advance(90)
  assert e.read(0x0201331C,1)==1 and e.read(0x02000010,1)==4
  checkpoint('gameplay')
  advance(1,[3]);advance(30);checkpoint('pause')
  advance(1,[0]);advance(30);checkpoint('resume')
  return records
 finally:e.close()

def main():
 host=ROOT/'CastlevaniaAoS.gba';rom=load_image(host);original=rom.original
 config=json.loads((ROOT/'examples/imported-melody/mod.json').read_text())['boot_melody']
 config.update(tempo=30,repeats=8)
 install_boot_melody(rom,config,ROOT/'examples/imported-melody')
 path=ROOT/'local/audio/music-lifecycle.gba';rom.output(path,host)
 baseline=run(host);changed=run(path);repeat=run(path)
 assert changed==repeat,'custom lifecycle not deterministic'
 assert baseline[0]['header']!=changed[0]['header']==rom.music_report['header']
 assert baseline[0]['pcm_sha256']!=changed[0]['pcm_sha256'] and changed[0]['nonzero_audio']
 for a,b in zip(baseline,changed):
  for field in ('name','start_frame','game_state','substate','room','hp','mp','ownership','image_sha256','stereo_frames','timing'):
   assert a[field]==b[field],(a['name'],field,a[field],b[field])
 for name in ('menu-step-1','menu-step-2','menu-step-3','menu-step-4','menu-step-5','menu-step-6','gameplay','pause','resume'):
  a=next(r for r in baseline if r['name']==name);b=next(r for r in changed if r['name']==name)
  assert a['header']==b['header']!=rom.music_report['header']
  assert a['pcm_sha256']==b['pcm_sha256'],name
 assert next(r for r in changed if r['name']=='pause')['substate']==6
 assert next(r for r in changed if r['name']=='resume')['substate']==1
 # At the same frame with no input, authored music is still active/non-silent.
 takeover=next(r for r in changed if r['name']=='menu-step-1')['start_frame']
 passive=Emulator(path)
 try:
  passive.run(takeover);passive_header=passive.read(0x03005360)
  passive.start_audio_capture(100000);passive.run(30);passive_pcm=passive.stop_audio_capture()
  assert passive_header==rom.music_report['header'] and any(passive_pcm)
 finally:passive.close()
 assert host.read_bytes()==original
 report={'baseline':baseline,'custom':changed,'fresh_repeat_equal':True,'visual_state_equal':True,
  'gameplay_pause_resume_audio_equal':True,'post_takeover_audio_equal':True,'passive_control_still_playing_at_takeover':True,'takeover_checkpoint_frame':takeover,'passive_pcm_sha256':hashlib.sha256(passive_pcm).hexdigest(),'original_unchanged':True,'music':rom.music_report,
  'scope':'boot to new game, pause/resume; no save/death/room-transition or broad channel certification'}
 (ROOT/'local/audio/music-lifecycle-report.json').write_text(json.dumps(report,indent=2))
 print(json.dumps({'checkpoints':len(changed),'header_changes':[(r['name'],hex(r['header'])) for r in changed],
  'fresh_repeat_equal':True,'visual_state_equal':True,'gameplay_pause_resume_audio_equal':True},indent=2))
if __name__=='__main__':main()
