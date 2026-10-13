"""Native selected instrument switching with original waveform controls."""
import copy,hashlib,json,math,struct,sys,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image
from aria.music import install_boot_melody
from verify_melody_phrasing import capture

def correlation(window,cycle,rate):
 mean=sum(window)/len(window);center=[v-mean for v in window];energy=sum(v*v for v in center);scores=[]
 for phase in range(len(cycle)):
  template=[]
  for i in range(len(window)):
   position=(phase+i*8000/rate)%len(cycle);index=int(position)
   template.append(cycle[index]+(cycle[(index+1)%len(cycle)]-cycle[index])*(position-index))
  average=sum(template)/len(template);variance=sum((v-average)**2 for v in template)
  scores.append(sum((v-average)*w for v,w in zip(template,center))/math.sqrt(variance*energy))
 return max(scores)
def main():
 host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes();folder=ROOT/'examples/instrument-melody';out=ROOT/'local/audio'
 spec=json.loads((folder/'mod.json').read_text())['boot_melody'];captures={}
 for name in ('switch','triangle-control','mute'):
  value=copy.deepcopy(spec)
  if name=='triangle-control':
   for note in value['notes']:note['instrument']=0
  if name=='mute':value['volume']=0
  rom=load_image(host);report=install_boot_melody(rom,value,folder);path=out/(name+'-instruments.gba');rom.output(path,host)
  pcm,header,timing=capture(path);assert header==report['header'];captures[name]=pcm
 pcm,header,t2=capture(out/'switch-instruments.gba');assert pcm==captures['switch'] and t2==timing
 rate=timing['sample_rate'];left=struct.unpack('<'+'h'*(len(pcm)//2),pcm)[::2]
 control=struct.unpack('<'+'h'*(len(captures['triangle-control'])//2),captures['triangle-control'])[::2]
 scores=[]
 for index,instrument in enumerate((0,1,0,0,1,0)):
  start=int((index*48/timing['fps']-.117+.16)*rate);window=left[start:start+2048]
  name=('triangle','square')[instrument]
  with wave.open(str(folder/(name+'.wav')),'rb') as w:cycle=[v-128 for v in w.readframes(w.getnframes())]
  score=correlation(window,cycle,rate);assert score>.9,(index,score)
  scores.append({'note':index,'instrument':name,'correlation':score})
  if index==0:assert window==control[start:start+2048]
  if index in (1,4):assert window!=control[start:start+2048]
 assert not any(captures['mute']);assert not any(left[-int(.2*rate):]);assert host.read_bytes()==original
 result={'waveform_scores':scores,'first_note_control_identical':True,'square_windows_differ_from_triangle_control':True,'fresh_repeat_identical':True,'mute_zero':True,'tail_silent':True,'original_unchanged':True,'pcm_sha256':hashlib.sha256(pcm).hexdigest(),'scope':'one sequential native track; no simultaneous-channel or broad lifecycle certification'}
 (out/'music-instruments-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
