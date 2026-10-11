"""Verify custom icons through real native VRAM and menu rendering."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest
from emulator import Emulator
from aria.content import tiles,palette
host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes();manifest=ROOT/'examples/content-workshop/mod.json'
rom=load_image(host);apply_manifest(rom,manifest);out=ROOT/'build/mods/content-workshop/content-workshop.gba';rom.output(out,host)
def capture(path,label):
 e=Emulator(path);e.run(1000)
 for k in [3,8,8,8,3,3,8]:e.run(1,[k]);e.run(100)
 for _ in range(60):e.run(1,[8]);e.run(90)
 e.write(0x02013294,1,1) # Declared Potion ownership fixture, identical in both captures.
 e.run(1,[3]);e.run(90)
 # Native pause menu -> equipment page.
 e.run(1,[5]);e.run(30);e.run(1,[5]);e.run(30);e.run(1,[8]);e.run(90)
 e.snap('content-'+label+'.png')
 v=e.bytes(0x06000000,0x18000);p=e.bytes(0x05000000,0x400);im=e.image.copy();e.close();return v,p,im
base_v,base_p,base_im=capture(host,'original');v,p,im=capture(out,'custom')
expected=tiles(json.loads((manifest.parent/'diamonds.json').read_text()));matches=[(v.find(expected[i:i+32]),expected[i:i+32]) for i in range(0,len(expected),32) if any(expected[i:i+32]) and expected[i:i+32] not in base_v]
matches=[(o,t) for o,t in matches if o>=0]
assert matches,'No unique custom icon tile found in native VRAM'
offset,tile=matches[0]
assert base_v[offset:offset+32]!=tile
assert im.tobytes()!=base_im.tobytes(),'Native rendered menu unchanged'
assert host.read_bytes()==original
report={'passed':['custom 4bpp icon tiles loaded by native item menu into VRAM','native menu renders differently with original custom artwork','ability SDK composes with imported assets','original ROM unchanged'],'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'vram_address':hex(0x06000000+offset),'content':rom.content_report,'fixtures':['Potion ownership count set to one identically in baseline/custom; no graphics or palette RAM writes'],'limitations':['PCM chirp imported and hashed, not connected to native sound playback','same-size icon-page replacement only; no sprite animation/resource allocator','no hardware or full campaign asset coverage','render comparison proves visible difference, not per-icon identity semantics']}
(ROOT/'local/content-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
