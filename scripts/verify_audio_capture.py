"""Private controller-free boot audio capture, with fresh-core repeatability."""
import hashlib,json,math,struct,sys,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from aria.cli import load_image
from emulator import Emulator

def capture(host):
 e=Emulator(host)
 try:
  e.run(1000)
  timing=e.start_audio_capture(500000)
  e.run(300)
  pcm=e.stop_audio_capture()
  return pcm,timing,{'game_state':e.read(0x02000010,1),'substate':e.read(0x02000064,1)}
 finally:e.close()

def main():
 host=ROOT/'CastlevaniaAoS.gba';original=load_image(host).original
 a,timing,state=capture(host);b,repeat_timing,repeat_state=capture(host)
 assert a==b and timing==repeat_timing and state==repeat_state,'fresh-core capture differs'
 assert timing['sample_rate']>0 and timing['sample_rate'].is_integer()
 samples=struct.unpack('<'+'h'*(len(a)//2),a)
 assert samples and any(samples),'silent capture'
 assert len(a)//4<500000
 out=ROOT/'local/audio/native-boot.wav'
 with wave.open(str(out),'wb') as w:
  w.setnchannels(2);w.setsampwidth(2);w.setframerate(int(timing['sample_rate']));w.writeframes(a)
 assert host.read_bytes()==original
 report=dict(timing=timing,checkpoint=state,warmup_frames=1000,captured_frames=300,stereo_frames=len(a)//4,
  seconds=len(a)/4/timing['sample_rate'],peak=max(abs(v) for v in samples),rms=math.sqrt(sum(v*v for v in samples)/len(samples)),
  pcm_sha256=hashlib.sha256(a).hexdigest(),wav_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
  deterministic_repeat=True,original_unchanged=True,scope='native emulator boot capture; song identity and reconstruction alignment unproven')
 (ROOT/'local/audio/native-capture-report.json').write_text(json.dumps(report,indent=2))
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()

