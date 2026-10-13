"""Final-example palette/render twin checks; private screenshots and report.

Two untinted runs must match every snapshot before tint differences count.
No native RAM injection. Source palette recolors are shared globally.
"""
import json,sys,hashlib
from pathlib import Path
from PIL import ImageChops
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest_data
from aria.palette_tints import TARGETS
from emulator import Emulator
from verify_custom_room import boot

def capture(path):
 e=Emulator(path)
 try:
  boot(e)
  images={'idle':[e.image.copy()]}
  e.run(1,[4]);e.run(30);e.run(1,[6]);e.run(1);e.run(1,[8])
  images['saving']=[]
  for _ in range(15):e.run(15);images['saving'].append(e.image.copy())
  e.run(100,[7]);e.run(120);e.run(150,[7]);e.run(120)
  images['zombies']=[e.image.copy()]
  assert e.bytes(0x05000380,32)==load_rom_palette(path,'zombie')
  return images
 finally:e.close()

def load_rom_palette(path,target):
 data=path.read_bytes();address=TARGETS[target][0]-0x08000000
 return data[address:address+32]

def main():
 host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes()
 folder=ROOT/'examples/custom_room';mod=json.loads((folder/'mod.json').read_text())
 plain=dict(mod);plain.pop('palette_tints')
 paths=[]
 for name,manifest in [('untinted',plain),('tinted',mod)]:
  r=load_image(host);apply_manifest_data(r,manifest,folder)
  path=ROOT/f'local/custom-room-{name}.gba';r.output(path,host);paths.append(path)
 a=capture(paths[0]);b=capture(paths[0]);t=capture(paths[1])
 evidence={}
 for scene in a:
  assert all(ImageChops.difference(x,y).getbbox() is None for x,y in zip(a[scene],b[scene]))
  rows=[]
  for frame,(base,tinted) in enumerate(zip(a[scene],t[scene])):
   bbox=ImageChops.difference(base,tinted).getbbox()
   count=sum(x!=y for x,y in zip(base.get_flattened_data(),tinted.get_flattened_data()))
   rows.append({'frame':frame,'pixels':count,'bounds':bbox})
  assert any(row['pixels']>0 for row in rows),scene
  evidence[scene]=rows
  t[scene][min(2,len(t[scene])-1)].save(ROOT/f'local/custom-room-tinted-{scene}.png')
 # Idle differences are confined to the statue/flame; Soma stays unchanged.
 assert ImageChops.difference(a['idle'][0],t['idle'][0]).getbbox()==(105,64,131,136)
 assert ImageChops.difference(a['idle'][0].crop((132,112,140,144)),
                              t['idle'][0].crop((132,112,140,144))).getbbox() is None
 assert host.read_bytes()==original
 report={'controls_deterministic':True,'scenes':evidence,
         'final_rom_sha256':hashlib.sha256(paths[1].read_bytes()).hexdigest(),
         'original_unchanged':True,'no_ram_writes':True,
         'limits':['palette sources shared globally; other consumers not exhaustively surveyed',
                   'save white fade still native; no texture overlay or blood-tear animation',
                   'no claims about sprite art pages or OAM-map attribution']}
 (ROOT/'local/custom-room-palette-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report,indent=2))

if __name__=='__main__':main()
