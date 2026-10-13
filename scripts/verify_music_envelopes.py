"""Private native authored envelope comparisons, no RAM/controller fixtures."""
import copy,hashlib,json,math,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image
from aria.music import install_boot_melody
from verify_boot_melody import capture

def main():
 host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes();folder=ROOT/'local/audio'
 spec=json.loads((ROOT/'examples/envelope-melody/mod.json').read_text())['boot_melody'];signals={};pcms={};paths={}
 settings={'fast':{'attack':255,'decay':255,'sustain':255,'release':128},'slow-attack':{'attack':8,'decay':255,'sustain':255,'release':128},'slow-release':{'attack':255,'decay':255,'sustain':255,'release':224},'low-sustain':{'attack':255,'decay':192,'sustain':32,'release':128},'mute':{'attack':255,'decay':255,'sustain':255,'release':128}}
 for name,envelope in settings.items():
  value=copy.deepcopy(spec);value['envelope']=envelope
  if name=='mute':value['volume']=0
  rom=load_image(host);report=install_boot_melody(rom,value);path=folder/(name+'-envelope.gba');rom.output(path,host);paths[name]=path
  pcm,header,timing,state=capture(path);assert header==report['header'] and state==1
  pcms[name]=pcm;signals[name]=struct.unpack('<'+'h'*(len(pcm)//2),pcm)[::2]
 repeat,h,t,s=capture(paths['slow-attack']);assert repeat==pcms['slow-attack'] and t==timing
 rate=timing['sample_rate']
 def rms(name,start,end):
  values=signals[name][int(start*rate):int(end*rate)];return math.sqrt(sum(v*v for v in values)/len(values))
 windows={name:{'early':rms(name,.02,.06),'plateau':rms(name,.5,.6),'release':rms(name,.9,1.0),'tail':rms(name,2.7,2.9)} for name in settings}
 assert 0<windows['slow-attack']['early']<windows['fast']['early']*.5,windows
 assert abs(windows['slow-attack']['plateau']/windows['fast']['plateau']-1)<.01,windows
 assert windows['low-sustain']['plateau']<windows['fast']['plateau']*.2,windows
 assert windows['fast']['release']==0<windows['slow-release']['release'],windows
 assert all(w['tail']==0 for w in windows.values());assert not any(pcms['mute']);assert host.read_bytes()==original
 result={'rms_windows':windows,'settings':settings,'fresh_repeat_exact':True,'mute_zero':True,'original_unchanged':True,'pcm_sha256':{k:hashlib.sha256(v).hexdigest() for k,v in pcms.items()},'scope':'selected native sampled-envelope attack/decay-sustain/release contrasts; no exact envelope-clock or arbitrary mix/lifecycle certification'}
 (folder/'music-envelopes-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
