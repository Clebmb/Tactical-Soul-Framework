"""Private authored multitrack/envelope scene and menu-sound controls."""
import copy,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image
from aria.music import install_boot_melody
from emulator import Emulator
from verify_music_lifecycle import run

def menu_capture(path,press):
 e=Emulator(path)
 try:
  e.run(1030);before=e.read(0x03005360);timing=e.start_audio_capture(200000)
  e.run(1,[3] if press else ());e.run(100)
  pcm=e.stop_audio_capture();after=e.read(0x03005360)
  return pcm,before,after,timing
 finally:e.close()

def main():
 host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes();folder=ROOT/'local/audio'
 config={'tempo':30,'volume':24,'repeats':8,'envelope':{'attack':16,'decay':240,'sustain':180,'release':160},'tracks':[{'notes':[{'key':key,'velocity':80,'ticks':96}]} for key in (60,67)]}
 rom=load_image(host);install_boot_melody(rom,config);path=folder/'arrangement-lifecycle.gba';rom.output(path,host)
 muted=load_image(host);mute_config=copy.deepcopy(config);mute_config['volume']=0;install_boot_melody(muted,mute_config);mute=folder/'arrangement-lifecycle-mute.gba';muted.output(mute,host)
 baseline=run(host);changed=run(path);repeat=run(path);assert changed==repeat
 for a,b in zip(baseline,changed):
  for field in ('name','start_frame','game_state','substate','room','hp','mp','ownership','image_sha256','stereo_frames','timing'):
   assert a[field]==b[field],(a['name'],field)
 assert changed[0]['header']==rom.music_report['header'] and changed[0]['nonzero_audio']
 takeover=[]
 for a,b in zip(baseline,changed):
  if b['name'] in ('boot','menu-step-0'):continue
  assert a['header']==b['header']!=rom.music_report['header']
  assert a['pcm_sha256']==b['pcm_sha256'],b['name'];takeover.append(b['name'])
 assert changed[-2]['substate']==6 and changed[-1]['substate']==1
 captures={}
 for name,source,press in (('music-input',path,True),('music-passive',path,False),('mute-input',mute,True),('mute-passive',mute,False)):
  pcm,before,after,timing=menu_capture(source,press)
  assert before==after==rom.music_report['header']
  captures[name]=struct.unpack('<'+'h'*(len(pcm)//2),pcm)
 sound=[a-b for a,b in zip(captures['mute-input'],captures['mute-passive'])]
 mixed_delta=[a-b for a,b in zip(captures['music-input'],captures['music-passive'])]
 native_sound_observed=any(sound)
 residual=max(abs(a-b) for a,b in zip(sound,mixed_delta))
 # Retain the measured residual; absence of an isolated sound cannot certify coexistence.
 assert any(captures['music-passive']) and not any(captures['mute-passive'])
 assert host.read_bytes()==original
 result={'checkpoints':changed,'fresh_repeat_exact':True,'visual_state_equal':True,'post_takeover_equal':takeover,'menu_sound_control':{'frame':1030,'frames':101,'background_header_unchanged':True,'mute_passive_zero':True,'music_passive_nonzero':True,'native_sound_observed':native_sound_observed,'isolated_sound_peak':max(abs(v) for v in sound),'mixed_minus_passive_equals_isolated_delta':residual==0,'peak_residual':residual},'music':rom.music_report,'original_unchanged':True,'scope':'selected two-track envelope arrangement, Start-button sound probe negative, boot/new-game/pause/resume; no SFX coexistence certification or custom gameplay SFX dispatch, arbitrary mixes or room/save/death certification'}
 (folder/'arrangement-lifecycle-report.json').write_text(json.dumps(result,indent=2));print(json.dumps({'checkpoints':len(changed),'post_takeover_equal':takeover,'menu_sound_control':result['menu_sound_control']},indent=2))
if __name__=='__main__':main()
