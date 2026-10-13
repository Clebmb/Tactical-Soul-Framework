"""Private native original melody acceptance with repeat and silent controls."""
import copy,hashlib,json,math,struct,sys,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest
from aria.music import install_boot_melody
from emulator import Emulator

def capture(path):
 e=Emulator(path)
 try:
  e.run(440);header=e.read(0x03005360);timing=e.start_audio_capture(300000);e.run(180)
  return e.stop_audio_capture(),header,timing,e.read(0x02000010,1)
 finally:e.close()

def main():
 host=ROOT/'CastlevaniaAoS.gba';rom=load_image(host);original=rom.original
 apply_manifest(rom,ROOT/'examples/imported-melody/mod.json')
 folder=ROOT/'local/audio';path=folder/'imported-boot-melody.gba';rom.output(path,host)
 plan=json.loads((ROOT/'examples/imported-melody/mod.json').read_text())['boot_melody'];plan['volume']=0
 silent=load_image(host);install_boot_melody(silent,plan,ROOT/'examples/imported-melody');mute=folder/'silent-imported-melody.gba';silent.output(mute,host)
 a,header,timing,state=capture(path);b,h2,t2,s2=capture(path);zero,h3,t3,s3=capture(mute)
 assert (a,header,timing,state)==(b,h2,t2,s2)
 assert header==rom.music_report['header']==h3 and timing==t3 and state==s3==1
 samples=struct.unpack('<'+'h'*(len(a)//2),a);assert any(samples) and not any(zero)
 left=samples[::2];rate=timing['sample_rate'];pitches=[]
 for key,start in ((60,.05),(64,.4),(67,.8),(72,1.2)):
  first,last=int(start*rate),int((start+.1)*rate)
  crossings=[i for i in range(first+1,last) if left[i-1]<=0<left[i]]
  assert len(crossings)>2
  measured=rate*(len(crossings)-1)/(crossings[-1]-crossings[0])
  expected=8000/40*2**((key-60)/12)
  assert abs(measured/expected-1)<.01,(key,measured,expected)
  pitches.append({'key':key,'measured_hz':measured,'expected_hz':expected})
 with wave.open(str(ROOT/'examples/imported-melody/triangle.wav'),'rb') as source:
  cycle=[v-128 for v in source.readframes(source.getnframes())]
 window=left[int(.05*rate):int(.05*rate)+2048];mean=sum(window)/len(window);centered=[v-mean for v in window];energy=sum(v*v for v in centered);scores=[]
 for phase in range(len(cycle)):
  template=[]
  for i in range(len(window)):
   position=(phase+i*pitches[0]['measured_hz']*len(cycle)/rate)%len(cycle);index=int(position)
   template.append(cycle[index]+(cycle[(index+1)%len(cycle)]-cycle[index])*(position-index))
  average=sum(template)/len(template);variance=sum((v-average)**2 for v in template)
  scores.append(sum((v-average)*w for v,w in zip(template,centered))/math.sqrt(variance*energy))
 waveform_correlation=max(scores);assert waveform_correlation>.95,waveform_correlation
 assert not any(left[-int(rate*.2):]),'one-shot tail did not settle to silence'
 plan['volume']=64;plan['sample']['loop_start']=None
 oneshot=load_image(host);install_boot_melody(oneshot,plan,ROOT/'examples/imported-melody')
 onepath=folder/'imported-one-shot-sample.gba';oneshot.output(onepath,host)
 one_pcm,one_header,one_timing,one_state=capture(onepath)
 assert any(one_pcm) and one_header==header and one_timing==timing and one_state==state
 assert not any(one_pcm[:int(rate*.2)*4]),'nonlooping sample did not exhaust before next note'
 assert not any(one_pcm[-int(rate*.2)*4:])
 assert host.read_bytes()==original
 out=folder/'imported-boot-melody.wav'
 with wave.open(str(out),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(int(timing['sample_rate']));w.writeframes(a)
 report={'deterministic_repeat':True,'silent_control_all_zero':True,'header':header,'timing':timing,'stereo_frames':len(a)//4,'peak':max(abs(v) for v in samples),'pcm_sha256':hashlib.sha256(a).hexdigest(),'patch_count':len(rom.ledger),'music':rom.music_report,'original_unchanged':True,'pitches':pitches,'tail_silent':True,'waveform_correlation':waveform_correlation,'nonlooping_sample_exhaustion':True,'scope':'native imported looped triangle instrument; no listening or broad lifecycle approval'}
 (folder/'imported-melody-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
