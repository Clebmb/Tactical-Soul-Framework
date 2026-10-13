"""Private native checks of the final custom_room ROM, controller-only route.

No graphics, palette, actor, position or collision RAM injection. SRAM is
transported to a fresh emulator only for the save/continue check.
"""
import ctypes as C
import hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest
from aria.rooms import room_address,metadata
from aria.rendering import read_graphics,read_palettes
from aria.tables import read_record
from emulator import Emulator
from probe_actor_binding import zombie_slots
from aria.palette_tints import TARGETS


def boot(e):
    e.run(1000)
    for k in [3,8,8,8,3,3,8]:
        e.run(1,[k]);e.run(100)
    for _ in range(60):
        if e.read(0x02000088)==0x0851021C and e.read(0x02000010,1)==4:
            break
        e.run(1,[8]);e.run(90)
    e.run(120)


def main():
    host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes()
    rom=load_image(host);apply_manifest(rom,ROOT/'examples/custom_room/mod.json')
    out=ROOT/'build/mods/custom_room/custom_room.gba';rom.output(out,host)
    save=room_address(rom,0,31);hall=room_address(rom,0,3)
    results=[]
    def art(e,i):
        m=metadata(rom,room_address(rom,0,i))
        chunks,_=read_graphics(rom,m[4]);banks,_=read_palettes(rom,m[5])
        assert e.bytes(0x0600C000,2048)==chunks[24]
        import struct
        assert e.bytes(0x05000100,32)==struct.pack('<16H',*banks[8])
    e=Emulator(out)
    try:
        boot(e)
        print('boot',hex(e.read(0x02000088)),e.read(0x02000010,1),e.read(0x02000526,2),e.read(0x0200052A,2),flush=True)
        assert e.read(0x02000088)==save and e.read(0x02000010,1)==4
        art(e,31);e.snap('custom-room-start.png')
        for bank,target in ((11,'save-statue'),(12,'save-flame'),(13,'save-particles')):
            assert e.bytes(0x05000200+bank*32,32)==rom.read(TARGETS[target][0],32)
        results.append('fresh new game starts in flesh save room; imported art/palette load exactly')
        # At statue center, open native prompt and select Yes.
        e.run(1,[4]);e.run(30);e.snap('custom-room-save-prompt.png')
        before_sram=C.string_at(e.lib.retro_get_memory_data(0),e.lib.retro_get_memory_size(0))
        e.run(1,[6]);e.run(1);e.run(1,[8]);e.run(240)
        sram=C.string_at(e.lib.retro_get_memory_data(0),e.lib.retro_get_memory_size(0))
        assert sram!=before_sram,'native save did not change SRAM'
        for _ in range(150):
            e.run(4,[7])
            if e.read(0x02000088)==hall:break
        assert e.read(0x02000088)==hall, 'right exit did not enter corridor'
        e.run(90);art(e,3);e.snap('custom-room-corridor.png')
        results.append('controller-only right exit enters five-screen flesh corridor with exact resource reload')
        update=read_record(rom,'enemies',1)['update_code']
        max_zombies=0;max_world_x=0
        for _ in range(240):
            e.run(8,[7,0]);e.run(1);e.run(1,[0,7])
            max_zombies=max(max_zombies,len(zombie_slots(e,update)))
            x=e.read(0x02000526,2)+e.read(0x0200A09A,2)
            max_world_x=max(max_world_x,x)
            if e.read(0x02000010,1)!=4:break
        e.snap('custom-room-zombies.png')
        print('corridor',max_zombies,max_world_x,e.read(0x0201327A,2),flush=True)
        assert max_zombies>=3, 'multiple live zombies not observed'
        results.append(f'native corridor combat observes {max_zombies} simultaneous live zombie slots')
        # Use a fresh boot to test the return without depending on combat health.
    finally:e.close()
    e=Emulator(out)
    try:
        boot(e);e.run(100,[7]);e.run(90)
        assert e.read(0x02000088)==hall
        e.run(100,[6]);e.run(90)
        assert e.read(0x02000088)==save
        art(e,31);e.snap('custom-room-return.png')
        results.append('controller-only corridor left return restores flesh save-room resources')
    finally:e.close()
    e=Emulator(out)
    try:
        C.memmove(e.lib.retro_get_memory_data(0),sram,len(sram))
        e.run(1000)
        for k in [3,8,8,8]:e.run(1,[k]);e.run(160)
        assert e.read(0x02000088)==save and e.read(0x02000010,1)==4
        art(e,31);e.snap('custom-room-continue.png')
        results.append('native statue save and fresh-instance continue restore sanctuary and exact art')
    finally:e.close()
    assert host.read_bytes()==original
    report={'passed':results,'rom_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
        'original_unchanged':True,'fixtures':['fresh SRAM for new games; native SRAM transport for continue'],
        'limitations':['no death or full campaign certification','statue texture overlay and blood tears unimplemented; native full-screen save flash retained',
                       'dark flesh backdrop is opaque non-solid main-layer art, not a native parallax background edit']}
    (ROOT/'local/custom-room-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
