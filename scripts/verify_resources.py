"""Native named-resource regression; declares an identical Potion ownership fixture."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest
from aria.resources import catalog,export_resource
from aria.content import tiles
from emulator import Emulator

def capture(path,label):
 e=Emulator(path);e.run(1000)
 for k in [3,8,8,8,3,3,8]:e.run(1,[k]);e.run(100)
 for _ in range(60):e.run(1,[8]);e.run(90)
 e.write(0x02013294,1,1)
 e.run(1,[3]);e.run(90)
 # Capture Equipment, then return to pause and choose Item Use.
 e.run(1,[5]);e.run(30);e.run(1,[8]);e.run(90)
 equip=(e.bytes(0x06000000,0x18000),e.image.tobytes());e.snap('resources-'+label+'-equipment.png')
 e.run(1,[0]);e.run(30);e.run(1,[5]);e.run(30);e.run(1,[8]);e.run(90)
 item=(e.bytes(0x06000000,0x18000),e.image.tobytes(),e.bytes(0x05000000,0x400));e.snap('resources-'+label+'-items.png');e.close()
 return equip,item

if __name__=='__main__':
 host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes()
 base_e,base_i=capture(host,'original')

 results=[]
 for name in ['named-content-workshop','sparse-content-workshop']:
  manifest=ROOT/'examples'/name/'mod.json';rom=load_image(host);apply_manifest(rom,manifest)
  out=ROOT/'build/mods'/name/(name+'.gba');rom.output(out,host)
  equip,item=capture(out,name)
  if name=='named-content-workshop':
   observed=[]
   for i in range(3):
    data=tiles(json.loads((manifest.parent/('page-'+str(i)+'.json')).read_text()))
    unique={data[j:j+32] for j in range(0,len(data),32)}
    if any((t in equip[0] or t in item[0]) and t not in base_e[0] and t not in base_i[0] for t in unique):observed.append(i)
   assert 0 in observed and len(observed)>=2,observed
   assert equip[1]!=base_e[1] and item[1]!=base_i[1]
   results.append({'mod':name,'observed_pages':observed,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
  else:
   edited=set()
   for patch in rom.ledger:edited.update(range(patch['address']-rom.base,patch['end']-rom.base))
   assert len(edited)==78
   assert all(a==b for j,(a,b) in enumerate(zip(original,rom.data)) if j not in edited)
   row=json.loads(manifest.read_text())['resource_edits'][0]['tiles'][0]
   tile=tiles({'width':8,'height':8,'pixels':row['pixels']})
   assert tile in item[0] and tile not in base_i[0]
   assert item[1]!=base_i[1]
   results.append({'mod':name,'bytes_claimed':len(edited),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
  for d in catalog(rom):
   start=rom.offset(d['header_address'],4);assert rom.read(d['header_address'],4)==original[start:start+4]
 assert host.read_bytes()==original
 report={'passed':['named icon resources load through native Equipment and Item Use menus','sparse original tile artwork appears in native Item Use VRAM and rendering','all bytes outside sparse ledger claims preserved','native resource headers and private original unchanged'],'builds':results,'fixtures':['one Potion ownership byte set identically for all captures; no graphics/palette RAM writes'],'limitations':['no automatic item-name-to-tile mapping','native evidence identifies observed pages, not all items or animations','palette banks shared; no per-item palette ownership','not a full campaign/save/hardware graphics certification']}
 (ROOT/'local/resource-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
