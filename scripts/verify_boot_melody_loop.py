"""Private native finite melody repeat/stop acceptance, no RAM fixtures."""
import hashlib,json,struct,sys,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest
from aria.music import install_boot_melody
from emulator import Emulator

def capture(path):
 e=Emulator(path)
 try:
  e.run(440);header=e.read(0x03005360);timing=e.start_audio_capture(600000);e.run(420)
  return e.stop_audio_capture(),header,timing,e.read(0x02000010,1)
 finally:e.close()

def main():
 host=ROOT/'CastlevaniaAoS.gba';rom=load_image(host);original=rom.original
 manifest=ROOT/'examples/boot-melody-loop/mod.json';apply_manifest(rom,manifest)
 folder=ROOT/'local/audio';out=folder/'looped-boot-melody.gba';rom.output(out,host)
 config=json.loads(manifest.read_text())['boot_melody'];config['volume']=0
 mute=load_image(host);install_boot_melody(mute,config);muted=folder/'looped-boot-melody-silent.gba';mute.output(muted,host)
 a,header,timing,state=capture(out);b,h2,t2,s2=capture(out);zero,h3,t3,s3=capture(muted)
 assert (a,header,timing,state)==(b,h2,t2,s2)
 assert header==h3==rom.music_report['header'] and timing==t3 and state==s3==1 and not any(zero)
 left=struct.unpack('<'+'h'*(len(a)//2),a)[::2];rate=timing['sample_rate'];period=96/timing['fps'];pitches=[]
 for iteration in range(3):
  for key,start in ((60,.05),(64,.4),(67,.8),(72,1.2)):
   first=int((start+iteration*period)*rate);last=first+int(.1*rate)
   crossings=[i for i in range(first+1,last) if left[i-1]<=0<left[i]];assert len(crossings)>2
   measured=rate*(len(crossings)-1)/(crossings[-1]-crossings[0]);expected=262.8*2**((key-60)/12)
   assert abs(measured/expected-1)<.01,(iteration,key,measured)
   pitches.append({'pass':iteration+1,'key':key,'measured_hz':measured})
 assert not any(left[-int(rate):]),'finite repeated sequence did not stop'
 assert host.read_bytes()==original
 path=folder/'looped-boot-melody.wav'
 with wave.open(str(path),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(int(rate));w.writeframes(a)
 report={'passes':3,'notes_checked':12,'pitches':pitches,'deterministic_repeat':True,'silent_control':True,'last_second_silent':True,'timing':timing,'stereo_frames':len(a)//4,'pcm_sha256':hashlib.sha256(a).hexdigest(),'music':rom.music_report,'original_unchanged':True,'scope':'finite repeat/stop native proof; no infinite-loop or gameplay lifecycle approval'}
 (folder/'melody-loop-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
