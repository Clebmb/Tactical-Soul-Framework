"""Native existing-room traversal and save/reload regression. Requires private host and Pillow."""
import sys,ctypes as C
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parent))
from emulator import Emulator
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest
from aria.level import MAP
host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes()
image=load_image(host);apply_manifest(image,ROOT/'examples/room-workshop/mod.json')
assert image.read(MAP,6016)==original[MAP-0x08000000:MAP-0x08000000+6016]
assert image.read(0x08117DD0,1504)==original[0x117DD0:0x117DD0+1504]
rom=ROOT/'build/mods/room-workshop/room-workshop.gba';image.output(rom,host)
e=Emulator(rom);e.run(1000)
for k in [3,8,8,8,3,3,8]:e.run(1,[k]);e.run(100)
for _ in range(60):e.run(1,[8]);e.run(90)
for i in range(180):
 e.run(20,[7,0]);e.run(1,[7,8]);e.run(15,[7,0])
 if e.read(0x02000088)==0x0851021C:break
e.run(90);e.run(60,[7]);e.run(1,[4]);e.run(30);e.snap('save-dialog2.png')
assert e.read(0x02000088)==0x0851021C
e.snap('room-workshop-arrival.png')
e.run(1,[6]);e.run(1);e.run(1,[8]);e.run(240)
sram=C.string_at(e.lib.retro_get_memory_data(0),e.lib.retro_get_memory_size(0))
e.snap('saved-workshop2.png');e.run(110,[6]);e.run(60)
assert e.read(0x02000088)==0x0850F15C
e.snap('room-workshop-return.png');e.close()
e=Emulator(rom);C.memmove(e.lib.retro_get_memory_data(0),sram,len(sram));e.run(1000)
for k in [3,8,8,8]:e.run(1,[k]);e.run(160)
assert e.read(0x02000088)==0x0851021C and e.read(0x02000010,1)==4
e.snap('room-workshop-reload.png');e.close()
assert host.read_bytes()==original
report={'passed':['native entrance to edited hallway to save-room shortcut','native return door to hallway','native statue save and SRAM reload in destination room','both castle map banks preserved','original ROM unchanged'],'limitations':['nonadjacent shortcut; displaced neighbors not repaired','full campaign and hardware not certified','general collision-definition and graphics authoring unimplemented; narrow geometry edits tested separately']}
(ROOT/'local/room-verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
