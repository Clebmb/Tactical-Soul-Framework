"""Actual native ability lifecycle tests. Declared fixtures are listed in report."""
import sys,json,hashlib,ctypes as C
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest
from emulator import Emulator
host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes();manifest=ROOT/'examples/ability-workshop/mod.json'
image=load_image(host);apply_manifest(image,manifest)
out=ROOT/'build/mods/ability-workshop/ability-workshop.gba';image.output(out,host)
S=0x0203D000;RG=0x0203D040;FC=0x0203D050;HP=0x0201327A;MP=0x0201327C
results=[]
def press(e,k,n=40):e.run(1,[k]);e.run(n)
def new_game(e):
 e.run(1000)
 for k in [3,8,8,8,3,3,8]:press(e,k,100)
def finish_intro(e):
 for _ in range(60):press(e,8,90)
 assert e.read(S+28)==1

e=Emulator(out);e.run(1000)
assert e.read(S)==0x444D4142 and e.read(S+20)==0 and e.read(S+36)==2
before=e.read(S+16);e.run(20);assert e.read(S+16)-before==20
results.append('single shared callback runs once per native frame; title blocks abilities')
for k in [3,8,8,8,3,3,8]:press(e,k,100)
assert e.read(S+36)==6 and e.read(S+20)==0
e.write(HP,300,2);mp=e.read(MP,2);e.run(120,[11])
assert e.read(HP,2)==300 and e.read(MP,2)==mp
results.append('original scripted entrance dialogue blocks healing and MP spending')
finish_intro(e);slots=e.bytes(0x02013268,6);maxhp=e.read(0x0201327E,2);maxmp=e.read(0x02013280,2)
e.write(S-4,0xDEADBEEF);e.write(S+96,0xAABBCCDD)
e.write(RG,0) # Controlled interval-start fixture, independent of intro duration.
regen_before=e.read(RG+4)
e.write(HP,maxhp-20,2);e.run(119)
assert e.read(HP,2)==maxhp-20,(e.read(HP,2),e.read(RG))
e.run(1);assert e.read(HP,2)==maxhp-19 and e.read(RG+4)==regen_before+1
results.append('stationary regeneration fires at configured 120 active frames')
e.write(HP,maxhp-20,2);e.write(MP,maxmp,2);press(e,11,0)
assert e.read(HP,2)==maxhp-15 and e.read(MP,2)==maxmp-3 and e.read(FC)==180 and e.read(FC+4)==1
e.run(60,[11]);assert e.read(FC+4)==1
e.run(1);press(e,11,0);assert e.read(FC+4)==1
e.run(200);press(e,11,0);assert e.read(FC+4)==2
results.append('R heal spends MP, respects cooldown, and uses press edges rather than held repeats')
e.run(220);e.write(HP,maxhp-20,2);e.write(MP,0,2);e.run(1);press(e,11,0)
assert e.read(FC+4)==2
results.append('insufficient MP blocks active ability')
e.run(220);e.write(HP,maxhp-2,2);e.write(MP,10,2);e.run(1);press(e,11,0)
assert e.read(HP,2)==maxhp and e.read(MP,2)==7
results.append('healing caps at native maximum HP')
e.run(220);events=e.read(FC+4);mp=e.read(MP,2);press(e,11,0)
assert e.read(FC+4)==events and e.read(MP,2)==mp
results.append('full HP does not consume MP')
e.run(1);e.write(HP,maxhp-20,2);press(e,11,0);events=e.read(FC+4)
press(e,3,40);assert e.read(0x02000064,1)==6
cooldown=e.read(FC);hp=e.read(HP,2);mp=e.read(MP,2);active=e.read(S+20)
e.run(240,[11]);assert (e.read(FC),e.read(HP,2),e.read(MP,2),e.read(S+20))==(cooldown,hp,mp,active)
e.run(1,[3,11]);e.run(30,[11]);assert e.read(FC+4)==events
results.append('pause freezes abilities; holding R through resume does not create an activation edge')
e.run(120,[7]);assert e.read(RG)==0
assert e.bytes(0x02013268,6)==slots
assert e.read(S-4)==0xDEADBEEF and e.read(S+96)==0xAABBCCDD
results.append('movement interrupts passive timer; equipment and RAM boundary canaries preserved')
room=e.read(0x02000088);resets=e.read(S+24)
for _ in range(180):
 e.run(20,[7,0]);e.run(1,[7,8]);e.run(15,[7,0])
 if e.read(0x02000088)!=room:break
assert e.read(0x02000088)!=room
e.run(90);assert e.read(S+24)>resets and e.read(FC)==0 and e.read(FC+4)==0
results.append('natural room transition clears transient feature timers and counters')
e.snap('ability-workshop-active.png');e.write(HP,0,2);e.run(180,[11])
assert e.read(HP,2)==0 and e.read(FC)==0 and e.read(FC+4)==0
results.append('native death clears ability state and cannot heal a dead player');e.close()
# Existing native save-room route fixture, same ability config/runtime.
mod=json.loads(manifest.read_text());mod['room_edits']={'connections':json.loads((ROOT/'examples/room-workshop/mod.json').read_text())['room_edits']['connections']}
fixture=ROOT/'local/ability-save-fixture.json';fixture.write_text(json.dumps(mod))
image=load_image(host);apply_manifest(image,fixture);save_rom=ROOT/'local/ability-save-fixture.gba';image.output(save_rom,host)
e=Emulator(save_rom);new_game(e);finish_intro(e)
for _ in range(180):
 e.run(20,[7,0]);e.run(1,[7,8]);e.run(15,[7,0])
 if e.read(0x02000088)==0x0851021C:break
assert e.read(0x02000088)==0x0851021C
e.run(90)
for _ in range(150):
 x=e.read(0x02000526,2)
 if 112<=x<=124:break
 e.run(1,[7 if x<112 else 6])
e.run(10);e.write(HP,e.read(0x0201327E,2)-20,2);e.write(MP,e.read(0x02013280,2),2);press(e,11,0)
assert e.read(FC+4)>0
press(e,4,30)
active=e.read(S+20);e.run(120,[11]);assert e.read(S+20)==active
press(e,6,1);press(e,8,240)
assert e.read(FC+4)>0
sram=C.string_at(e.lib.retro_get_memory_data(0),e.lib.retro_get_memory_size(0));gold=e.read(0x02013290);saved_slots=e.bytes(0x02013268,6);e.close()
e=Emulator(save_rom);C.memmove(e.lib.retro_get_memory_data(0),sram,len(sram));e.run(1000)
for k in [3,8,8,8]:press(e,k,160)
assert e.read(0x02000088)==0x0851021C and e.read(0x02000010,1)==4
assert e.read(0x02013290)==gold and e.bytes(0x02013268,6)==saved_slots
assert e.read(FC)==0 and e.read(FC+4)==0
assert e.read(S+28)==1
e.snap('ability-workshop-continue.png');e.close()
results.append('native save dialog blocks abilities; save/continue retains native state and restarts transient ability state')
assert host.read_bytes()==original
report={'passed':results+['original ROM unchanged'],'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'runtime_bytes':(ROOT/'native/abilities/runtime.bin').stat().st_size,'fixtures':['HP/MP set to controlled values for interval, mana, cap and death checks','passive timer reset to establish exact interval start; two private-RAM boundary canaries','save-route fixture composes existing paired-door example; identical ability config'],'limitations':['conservative state whitelist tested in entrance, gameplay, pause, transition, death and save; not every event/character scene','R input is not consumed and can also activate an equipped native guardian soul','RAM arena exercised in tested scenes, not globally certified','custom native code is trusted; declared RAM claims do not sandbox arbitrary C writes','no custom SRAM schema or native item/soul/EXP grant ABI']}
(ROOT/'local/ability-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
