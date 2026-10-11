"""Native mGBA enemy stats, EXP, item drop and encounter regression.

No RAM/seed/ownership fixtures: deterministic controller inputs on the example.
Item-drop check observes one real roll; it does not certify a probability formula.
"""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest
from aria.enemies import catalog,resolve
from aria.encounters import audit_encounters
from aria.tables import layout,read_record
from aria.rooms import room_address,entities
from emulator import Emulator
host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes()
rom=load_image(host);apply_manifest(rom,ROOT/'examples/enemy-workshop/mod.json')
assert len(catalog(rom))==113
assert resolve(rom,'zombie')['drops']['item_1']['pickup_id']==1
for index in [1,2]:
 spec,address=layout('enemies',index);off=rom.offset(address,36)
 assert rom.read(address,8)==original[off:off+8]
 assert rom.read(address+23,3)==original[off+23:off+26]
 assert rom.read(address+28,8)==original[off+28:off+36]
assert rom.read(0x08116650,6016)==original[0x116650:0x117dd0]
assert rom.read(0x08117DD0,1504)==original[0x117dd0:0x1183b0]
assert not audit_encounters(rom,0,6)['errors']
assert len([e for e in entities(rom,room_address(rom,0,6)) if e.type==1])==6
out=ROOT/'build/mods/enemy-workshop/enemy-workshop.gba';rom.output(out,host)
updates={read_record(rom,'enemies',i)['update_code']:i for i in [1,2]}
def observe(e):
 result=set()
 for j in range(1,224):
  a=0x020004E4+j*0x84;code=e.read(a)
  if code in updates:result.add((updates[code],e.read(a+0x34,2),e.read(a+0x3c,1),e.read(a+0x3d,1)))
 return result

e=Emulator(out);e.run(1000)
for k in [3,8,8,8,3,3,8]:e.run(1,[k]);e.run(100)
for _ in range(60):e.run(1,[8]);e.run(90)
assert e.read(0x02000010,1)==4
for _ in range(600):
 e.run(1,[7])
 if e.read(0x02000088)==0x0850F15C:break
assert e.read(0x02000088)==0x0850F15C
e.run(70,[7]);e.run(120);observed=observe(e)
assert any(row[0]==1 and row[1]==30 for row in observed),observed
exp_before=e.read(0x0201328c);potions=e.read(0x02013294,1)
for roll in range(700):
 direction=7 if (roll//10)%2==0 else 6
 e.run(1,[0,direction]);e.run(12,[direction]);e.run(1);e.run(12)
 observed|=observe(e)
 if e.read(0x02013294,1)>potions:break
assert any(row[0]==1 and row[2:]==(11,1) for row in observed),observed
assert e.read(0x02013294,1)>potions,'No native Potion collected in bounded deterministic combat sequence'
exp_after=e.read(0x0201328c)
assert exp_after>exp_before and (exp_after-exp_before)%7==0
assert e.read(0x0201327a,2)<320 and e.read(0x0201327a,2)>0
e.snap('enemy-workshop-drop.png')
for _ in range(180):
 e.run(20,[7,0]);e.run(1,[7,8]);e.run(15,[7,0])
 observed|=observe(e)
 if e.read(0x02000088)==0x0850F32C:break
assert e.read(0x02000088)==0x0850F32C
assert (2,12,12,0) in observed,observed
e.run(60);e.snap('enemy-workshop-arrival.png');skeleton_exp=e.read(0x0201328c)
for _ in range(90):
 e.run(20,[7,0]);e.run(1,[7,8]);e.run(15,[7,0])
 if e.read(0x02000526,2)+e.read(0x0200A09A,2)>=600:break
assert e.read(0x02000088)==0x0850F32C
assert e.read(0x02000526,2)+e.read(0x0200A09A,2)>=600
assert e.read(0x0201328c)>skeleton_exp and (e.read(0x0201328c)-skeleton_exp)%5==0
e.snap('enemy-workshop-clone-zone.png')
for _ in range(180):
 e.run(20,[6,0]);e.run(1,[6,8]);e.run(15,[6,0])
 if e.read(0x02000088)==0x0850F15C:break
assert e.read(0x02000088)==0x0850F15C
e.snap('enemy-workshop-return.png');e.close()
assert host.read_bytes()==original
report={'passed':['all 113 enemy names resolve; drop IDs, native AI pointers and unknown fields preserved','both map banks preserved; original-room resource evidence passes','native Zombie HP/ATK/DEF initialize to 30/11/1','native kills award modified Zombie EXP in multiples of seven','native edited Potion drop collected through controller combat; no forced RNG or inventory writes','native Skeleton HP initializes to 12; added-encounter room traversed past clone position and kills award EXP in multiples of five','paired shortcut returns to first hallway','original ROM remains unchanged'],'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'drop_controller_cycles':roll+1,'zombie_exp_before':exp_before,'zombie_exp_after':exp_after,'fixtures':[],'limitations':['single deterministic drop observation; rates/statistical formula and soul drops not certified','same-room resource reuse is not universal VRAM/OAM/collision certification','clone serialization and traversal tested; actor identity is not directly mapped from runtime slots','full campaign, hardware, arbitrary AI, boss scripting and new resource provisioning unsupported']}
(ROOT/'local/enemy-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
