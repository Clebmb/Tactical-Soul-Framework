"""Real-ROM structural checks plus actual native mGBA execution.
Requires private host, Pillow, and local libretro core. No companion needed.
"""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest
from aria.tables import read_record
from aria.rooms import room_address,entities,replace_entities
from aria.core import PatchError
from emulator import Emulator
results=[]
host=ROOT/"CastlevaniaAoS.gba";original_hash=hashlib.sha256(host.read_bytes()).hexdigest()
for name in ("native-balance","frame-counter"):
    rom=load_image(host);apply_manifest(rom,ROOT/"examples"/name/"mod.json")
    if name=="native-balance":
        assert read_record(rom,"enemies",0)["hp"]==18
        assert read_record(rom,"weapons",1)["attack"]==8
        assert read_record(rom,"red_souls",0)["mana_cost"]==3
        results.append("native enemy/weapon/soul fields patched at expected records")
    out=ROOT/"build/mods"/name/(name+".gba");rom.output(out,host)
    e=Emulator(out);e.run(1000)
    assert e.read(0x02000010,1)==1
    if name=="frame-counter":
        first=e.read(0x0203D000);e.run(20)
        assert e.read(0x0203D000)-first==20
        results.append("host-only frame callback executes once per native frame")
    for keys in ([3],[8],[8],[8],[3],[3],[8]):e.run(1,keys);e.run(100)
    assert e.read(0x02000010,1)==4
    assert 0x08000000<=e.read(0x02000088)<0x08800000
    # The original entrance has a long Arikado/Mina dialogue; advance naturally.
    for _ in range(60):e.run(1,[8]);e.run(90)
    before=e.read(0x02000526,2)+e.read(0x0200A09A,2)
    e.run(120,[7])
    after=e.read(0x02000526,2)+e.read(0x0200A09A,2)
    assert before!=after, (name,"movement unchanged",before,after)
    e.snap(name+"-native.png");e.close()
    results.append(name+" boots original title, enters gameplay, and accepts movement")
rom=load_image(host);pointer=room_address(rom,0,0);rows=entities(rom,pointer)
replace_entities(rom,pointer,rows,"roundtrip")
reloaded=entities(rom,pointer)
assert sorted(e.pack() for e in rows)==sorted(e.pack() for e in reloaded)
results.append("native room entity relocation preserves all original records")
assert hashlib.sha256(host.read_bytes()).hexdigest()==original_hash
results.append("commercial original remains unchanged")
report={"passed":results,"limitations":["record edits verified structurally; not every edited field exercised in gameplay","native room relocation checked structurally, not a complete room graphics/transition test","full campaign, save compatibility and hardware not certified"]}
(ROOT/"local/framework-verification.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
