"""Native type-3 load/map evidence; deliberately no viewport pixel certification."""
import sys,json,struct,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image
from aria.rooms import room_address,metadata
from aria.backgrounds import inspect_background,expand_background_map,render_background
from aria.rendering import read_graphics,read_palettes,png_rgba
from aria.room_resources import bg_tilemap_ranges
from emulator import Emulator
host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes();r=load_image(host)
# Source-backed new-game start constants; diagnostic ROM only, not a new API.
for address,value,size,expected in [(0x084F0D8C,4,1,b'\0'),(0x084F0D8D,0,1,b'\0'),
                                    (0x084F0D92,128,2,b'\x78\0'),(0x084F0D94,128,2,b'\x8d\0')]:
    r.write_integer(address,value,size,'background-fixture-start',expected)
fixture=ROOT/'local/background-rendering-fixture.gba';r.output(fixture,host)
b=inspect_background(r,4,0,1,True);width,height,tilemap=expand_background_map(b)
assert (width,height)==(32,32)
m=metadata(r,room_address(r,4,0));chunks,_=read_graphics(r,m[4]);banks,_=read_palettes(r,m[5])
e=Emulator(fixture)
try:
    e.run(1000)
    for attempt in range(120):
        e.run(1,[3 if attempt==0 else 8]);e.run(30)
        if e.read(0x02000088)==room_address(r,4,0):break
    else:raise AssertionError('Native fixture never reached target room')
    e.run(20);assert e.read(0x02000088)==room_address(r,4,0)
    for chunk,data in chunks.items():assert e.bytes(0x06000000+chunk*2048,2048)==data
    for bank,colors in banks.items():assert e.bytes(0x05000000+bank*32,32)==struct.pack('<16H',*colors)
    start=((b['bg_control']>>8)&31)*2048
    allocation=next(t for t in bg_tilemap_ranges(r,m[3]) if t['layer']==1)
    assert allocation=={'layer':1,'start':start,'end':start+len(tilemap)}
    assert e.bytes(0x06000000+start,len(tilemap))==tilemap
    # BG2 is assigned to this layer in this exact-room fixture.
    assert e.read(0x0400000C,2)&0xFFFC==b['bg_control']&0xFFFC
    affine=e.bytes(0x04000020,16).hex()
    e.snap('background-rendering-native.png')
finally:e.close()
p=render_background(r,4,0,1)
(ROOT/'local/background-rendering-source.png').write_bytes(png_rgba(p['width'],p['height'],p['rgba']))
assert host.read_bytes()==original
report={'passed':['20 character chunks match native VRAM','5 declared palette banks match native palette memory',
                  '1024 expanded byte tilemap entries match native BG2','original unchanged'],
        'fixture':{'sector':4,'room':0,'layer':1,'patched_new_game_start':True,'controller_boot':True,'runtime_memory_writes':False},
        'native_affine_registers_hex':affine,'source_rgba_sha256':p['report']['rgba_sha256'],
        'viewport_pixels_verified':False,
        'limitations':['static source raster only','captured affine registers do not reproduce native viewport; possible scanline effect remains unverified',
                       'one type-3 room only; no type-1 native fixture','no editing or lifecycle certification']}
(ROOT/'local/background-rendering-verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
