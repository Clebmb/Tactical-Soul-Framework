"""Private boot-song binding via read-only scan and isolated ROM diagnostic."""
import hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image
from aria.audio_binding import match_song_headers
from emulator import Emulator
from verify_audio_capture import capture

def observe(path,catalog):
 e=Emulator(path)
 try:
  e.run(1);previous=None;changes=[]
  for frame in range(1,1001):
   value=e.read(0x03005360)
   if value!=previous:changes.append({'frame':frame,'header':value});previous=value
   if frame<1000:e.run(1)
  hits=[]
  for base,size in ((0x02000000,0x40000),(0x03000000,0x8000)):
   hits.extend(match_song_headers(e.bytes(base,size),base,catalog))
  return {'transitions':changes,'matches':hits}
 finally:e.close()

def main():
 host=ROOT/'CastlevaniaAoS.gba';rom=load_image(host);original=rom.original
 table=0x0827cd40;catalog=[('bgm:'+str(i),int.from_bytes(rom.read(table+8*i,4),'little')) for i in range(45)]
 baseline=observe(host,catalog);repeat=observe(host,catalog);assert baseline==repeat
 expected=catalog[26][1];replacement=catalog[0][1]
 assert baseline['matches']==[{'identity':'bgm:26','header':expected,'memory_address':0x03005360}]
 assert {'frame':433,'header':expected} in baseline['transitions']
 rom.write(table+26*8,replacement.to_bytes(4,'little'),'boot-song-binding-diagnostic',expected.to_bytes(4,'little'))
 out=ROOT/'local/audio/boot-song-redirect.gba';rom.output(out,host)
 changed=observe(out,catalog)
 assert {'frame':433,'header':replacement} in changed['transitions']
 a,timing,state=capture(host);b,other_timing,other_state=capture(out)
 assert timing==other_timing and state==other_state and a!=b and len(a)==len(b)
 assert hashlib.sha256(a).hexdigest()=='6a38e113249fbf87c1dc0327506335586f8573adef9b22fd5134254607d4c61e'
 assert host.read_bytes()==original
 report={'table':table,'index':26,'header':expected,'live_field':0x03005360,'header_transition_frame':433,
  'baseline':baseline,'diagnostic':changed,'replacement_index':0,'patch_count':len(rom.ledger),
  'baseline_pcm_sha256':hashlib.sha256(a).hexdigest(),'diagnostic_pcm_sha256':hashlib.sha256(b).hexdigest(),
  'capture_offset_after_header_frames':1000-433,'original_unchanged':True,
  'scope':'native emulator song-table lookup binding; exact audible onset and reconstruction fidelity unproven'}
 (ROOT/'local/audio/boot-binding-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
