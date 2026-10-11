"""Actual mGBA equipment stats, menu, combat and save regression.

Private fixtures: one Cape ownership byte; save test combines unchanged equipment
edits with room-workshop doors to reach a statue quickly. No ROM data distributed.
"""
import sys,json,ctypes as C,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest
from aria.equipment import catalog,resolve
from aria.tables import layout
from emulator import Emulator
host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes()
manifest=ROOT/'examples/equipment-workshop/mod.json'
image=load_image(host);apply_manifest(image,manifest)
rom=ROOT/'build/mods/equipment-workshop/equipment-workshop.gba';image.output(rom,host)
assert len(catalog(image))==104
assert resolve(image,'weapons','dainslef')['fields']['constitution']==-2
assert resolve(image,'armor','skull-necklace')['fields']['luck']==-1
assert resolve(image,'weapons','knife')['flags']['effects']['raw']==3
# Compare every byte of touched records, including unknown bytes and resources.
for edit in json.loads(manifest.read_text())['equipment_edits']:
 row=resolve(image,edit['table'],edit['item']);spec,address=layout(row['table'],row['index'])
 offset=image.offset(address,spec['stride']);before=original[offset:offset+spec['stride']]
 after=image.read(address,spec['stride']);allowed=set()
 for field in set(edit.get('fields',{}))|set(edit.get('flags',{})):
  f=spec['fields'][field];allowed.update(range(f['offset'],f['offset']+f['size']))
 assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(before,after)))
results=['all 104 native equipment names resolve; existing signed penalties decode','named effects written and unchanged resource fields retained']
def press(e,key,wait=40):e.run(1,[key]);e.run(wait)
def start(e):
 e.run(1000)
 for k in [3,8,8,8,3,3,8]:press(e,k,100)
 for _ in range(60):press(e,8,90)
 assert e.read(0x02000010,1)==4

def stats(e):return [e.read(0x020131EE+i*2,2) for i in range(7)]
e=Emulator(host);start(e);baseline=stats(e);e.close()
e=Emulator(rom);start(e);changed=stats(e)
assert baseline==[15,11,10,12,11,9,0],baseline
assert changed==[25,20,8,12,11,8,2],changed
results.append('native new-game ATK/DEF/STR/LCK and flame resistance reflect equipment edits')
# Ownership fixture only. Equip via actual menu/controller; no direct stat writes.
e.write(0x02013294+116,1,1)
for k in [3,5,8,5,5,8,5,8]:press(e,k)
assert e.read(0x0201326D,1)==25
assert stats(e)[1]==23 and stats(e)[4]==15,stats(e)
e.snap('equipment-workshop-equipped.png')
for k in [8,6,8]:press(e,k)
assert e.read(0x0201326D,1)==255
assert stats(e)[1]==20 and stats(e)[4]==11
for k in [8,7,8]:press(e,k)
assert e.read(0x0201326D,1)==25
assert stats(e)[1]==23 and stats(e)[4]==15
for k in [0,0,3]:press(e,k)
results.append('native equipment menu equips, removes and re-equips Cape with correct DEF/INT recomputation')
# Native attack input remains functional; measure native EXP after hallway combat.
exp_before=e.read(0x0201328C)
for _ in range(90):
 e.run(20,[7,0]);e.run(1,[7,8]);e.run(15,[7,0])
assert e.read(0x0201328C)>exp_before,(exp_before,e.read(0x0201328C))
e.snap('equipment-workshop-combat.png');e.close()
results.append('modified Knife kills native enemies through controller attacks and awards native EXP')
# Save-route fixture uses the already tested existing-room door pair.
mod=json.loads(manifest.read_text())
mod['room_edits']={'connections':json.loads((ROOT/'examples/room-workshop/mod.json').read_text())['room_edits']['connections']}
fixture=ROOT/'local/equipment-save-fixture.json';fixture.write_text(json.dumps(mod,indent=2))
image=load_image(host);apply_manifest(image,fixture)
save_rom=ROOT/'local/equipment-save-fixture.gba';image.output(save_rom,host)
e=Emulator(save_rom);start(e)
e.write(0x02013294+116,1,1)
for k in [3,5,8,5,5,8,5,8]:press(e,k)
for k in [0,0,3]:press(e,k)
for _ in range(180):
 e.run(20,[7,0]);e.run(1,[7,8]);e.run(15,[7,0])
 if e.read(0x02000088)==0x0851021C:break
assert e.read(0x02000088)==0x0851021C,(hex(e.read(0x02000088)),e.read(0x02000010,1),e.read(0x02000064,1),e.read(0x02000526,2),e.read(0x0200A09A,2))
# Stop at statue center, avoiding controller-sequence-dependent arrival X.
e.run(90)
for _ in range(150):
 x=e.read(0x02000526,2)
 if 112<=x<=124:break
 e.run(1,[7 if x<112 else 6])
e.run(10);press(e,4,30);press(e,6,1);press(e,8,240)
sram=C.string_at(e.lib.retro_get_memory_data(0),e.lib.retro_get_memory_size(0))
e.close()
e=Emulator(save_rom);C.memmove(e.lib.retro_get_memory_data(0),sram,len(sram));e.run(1000)
for k in [3,8,8,8]:press(e,k,160)
assert e.read(0x02000088)==0x0851021C
assert e.read(0x0201326D,1)==25
assert stats(e)[1]==23 and stats(e)[4]==15,stats(e)
e.snap('equipment-workshop-reload.png');e.close()
results.append('native save/continue preserves equipped Cape and recomputes modified stats (documented route/ownership fixtures)')
assert host.read_bytes()==original
report={'passed':results+['original ROM remains unchanged'],'baseline_stats':baseline,'modified_starting_stats':changed,'stat_order':['ATK','DEF','STR','CON','INT','LCK','resistances'],'output_sha256':hashlib.sha256(rom.read_bytes()).hexdigest(),'fixtures':['Cape inventory count at 0x02013308 set to one; equipped through native menu','save-route fixture adds room-workshop paired doors; equipment edits identical'],'limitations':['individual elemental/status damage and special modifiers are structurally labeled, not all gameplay certified','price/shop behavior not exercised','full campaign/hardware and custom graphics/animations not certified']}
(ROOT/'local/equipment-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
