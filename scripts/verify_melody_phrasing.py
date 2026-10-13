"""Private controller-free boot phrasing sound/silence acceptance."""
import copy,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image
from aria.music import install_boot_melody
from emulator import Emulator

def capture(path):
 e=Emulator(path)
 try:
  e.run(440);header=e.read(0x03005360);timing=e.start_audio_capture(400000);e.run(300)
  return e.stop_audio_capture(),header,timing
 finally:e.close()
def main():
 host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes();folder=ROOT/'local/audio'
 spec=json.loads((ROOT/'examples/phrased-melody/mod.json').read_text())['boot_melody']
 captures={};reports={}
 for name in ('phrased','full-gate','mute'):
  value=copy.deepcopy(spec)
  if name=='full-gate':value['notes'][0]['gate_ticks']=96
  if name=='mute':value['volume']=0
  rom=load_image(host);report=install_boot_melody(rom,value);path=folder/(name+'-phrasing.gba');rom.output(path,host)
  pcm,header,timing=capture(path);assert header==report['header']
  captures[name]=(pcm,timing);reports[name]=report
 pcm,timing=captures['phrased'];again,header,t2=capture(folder/'phrased-phrasing.gba');assert pcm==again and timing==t2
 rate=timing['sample_rate']
 def peak(name,start,end):
  data=captures[name][0];samples=struct.unpack('<'+'h'*(len(data)//2),data)[::2]
  return max(abs(v) for v in samples[int(start*rate):int(end*rate)])
 windows={'first_note':peak('phrased',.02,.07),'short_gate_gap':peak('phrased',.8,1.1),'explicit_rest':peak('phrased',2.3,2.6),'second_note':peak('phrased',3.12,3.18),'tail':peak('phrased',4.5,4.8),'full_gate_control':peak('full-gate',.8,1.1)}
 assert windows['first_note']>0 and windows['second_note']>0 and windows['full_gate_control']>0,windows
 assert windows['short_gate_gap']==windows['explicit_rest']==windows['tail']==0,windows
 assert not any(captures['mute'][0]);assert host.read_bytes()==original
 report={'windows_peak':windows,'deterministic_repeat':True,'mute_zero':True,'original_unchanged':True,'timing':timing,'music':reports['phrased'],'pcm_sha256':hashlib.sha256(pcm).hexdigest(),'scope':'selected boot sound/silence windows; release tails remain native; no listening or broad lifecycle certification'}
 (folder/'melody-phrasing-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
