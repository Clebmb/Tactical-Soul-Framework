"""Private native mixed-track acceptance with isolated and silent controls."""
import copy,hashlib,json,math,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image
from aria.music import install_boot_melody
from verify_boot_melody import capture

def main():
 host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes();folder=ROOT/'local/audio'
 spec=json.loads((ROOT/'examples/polyphonic-melody/mod.json').read_text())['boot_melody']
 results=[]
 for count,keys in ((2,(60,67)),(4,(60,64,67,72))):
  value=copy.deepcopy(spec);value['volume']=16
  value['tracks']=[{'notes':[{'key':key,'velocity':80,'ticks':96,'gate_ticks':48}]} for key in keys]
  signals={};paths={}
  for selected in ('mix','mute',*range(count)):
   plan=copy.deepcopy(value)
   for index,track in enumerate(plan['tracks']):track['volume']=16 if selected=='mix' or selected==index else 0
   rom=load_image(host);report=install_boot_melody(rom,plan);path=folder/('tracks-'+str(count)+'-'+str(selected)+'.gba');rom.output(path,host);paths[selected]=path
   pcm,header,timing,state=capture(path);assert header==report['header'] and state==1
   signals[selected]=struct.unpack('<'+'h'*(len(pcm)//2),pcm)[::2]
   if selected=='mix':mixed_pcm=pcm
  repeat,header,t2,state=capture(paths['mix']);assert repeat==mixed_pcm and t2==timing
  assert not any(signals['mute']);rate=timing['sample_rate'];first,last=int(.05*rate),int(.25*rate)
  mix=signals['mix'][first:last];summed=[sum(signals[i][j] for i in range(count)) for j in range(first,last)]
  residual=max(abs(a-b) for a,b in zip(mix,summed));rms=lambda a:math.sqrt(sum(v*v for v in a)/len(a))
  error=rms([a-b for a,b in zip(mix,summed)])/rms(mix)
  assert list(mix)==summed,(count,error,residual)
  pitches=[]
  for index,key in enumerate(keys):
   isolated=signals[index][first:last];crossings=[i for i in range(1,len(isolated)) if isolated[i-1]<=0<isolated[i]]
   measured=rate*(len(crossings)-1)/(crossings[-1]-crossings[0]);expected=10512/40*2**((key-60)/12)
   assert abs(measured/expected-1)<.01,(key,measured)
   # The expected tone is present in the simultaneous mix as well.
   strength=abs(sum(v*complex(math.cos(2*math.pi*measured*i/rate),math.sin(2*math.pi*measured*i/rate)) for i,v in enumerate(mix)))/len(mix)
   assert strength>20,(key,strength)
   pitches.append({'key':key,'isolated_hz':measured,'mixed_projection':strength})
  assert not any(signals['mix'][-int(.2*rate):])
  results.append({'tracks':count,'pitches':pitches,'sum_relative_rms_error':error,'sum_peak_residual':residual,'repeat_exact':True,'mute_zero':True,'tail_silent':True,'pcm_sha256':hashlib.sha256(mixed_pcm).hexdigest()})
 assert host.read_bytes()==original
 report={'cases':results,'original_unchanged':True,'scope':'selected2/4-track sine chord windows; fixed envelopes; no general mixer or SFX coexistence/lifecycle certification'}
 (folder/'music-tracks-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()

