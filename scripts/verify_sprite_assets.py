"""Native registered bats/clouds reskin: engine-loaded OBJ bytes and OAM pixels.

Private host, mGBA libretro and Pillow required. No graphics/OAM/palette RAM
writes. Final example and separate composed save-route harness are distinguished.
"""
import ctypes as C
import json
import hashlib
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest,apply_manifest_data
from aria.sprite_rendering import resolve_sprite_resources,render_sprite_frame
from aria.sprites import inspect_sprite,SPRITES
from emulator import Emulator

def press(e,key,wait=100):e.run(1,[key]);e.run(wait)

def boot(e):
    e.run(1000)
    for key in [3,8,8,8,3,3,8]:press(e,key)
    for _ in range(60):press(e,8,90)
    for _ in range(150):
        e.run(5,[7])
        if e.read(0x02000088)==0x0850F15C:break
    assert e.read(0x02000088)==0x0850F15C
    e.run(240)
    for _ in range(1200):
        if not e.read(0x0200042C)&1:break
        e.run(1)
    assert not e.read(0x0200042C)&1,'Native entry event still owns input'

def page_binding(e,resources):
    # Engine copies a 16-tile-wide source into its 32-tile-wide OBJ canvas.
    assert not e.read(0x04000000,2)&64,'Unexpected native OBJ mapping mode'
    data=resources['pages'][0];vram=e.bytes(0x06000000,0x18000)
    bases=[base for base in range(0x10000,0x18000-3*1024-512+1,32)
           if all(vram[base+row*1024:base+row*1024+512]==data[row*512:(row+1)*512] for row in range(4))]
    assert bases,'Native OBJ VRAM lacks complete registered sprite page'
    palette=b''.join(c.to_bytes(2,'little') for c in resources['palette'])
    native=e.bytes(0x05000000,0x400)
    banks=[bank for bank in range(16) if native[0x200+bank*32:0x220+bank*32]==palette]
    assert banks,'Native OBJ palette differs from registered source'
    return bases[0],banks

def pixel_matches(e,resources,base,banks,parts):
    import struct
    shapes=(((8,8),(16,16),(32,32),(64,64)),((16,8),(32,8),(32,16),(64,32)),((8,16),(8,32),(16,32),(32,64)))
    oam=e.bytes(0x07000000,1024);matches=[]
    for index in range(128):
        a,b,c,_=struct.unpack_from('<4H',oam,index*8)
        # Ordinary non-affine/non-blended 4bpp parts only; blended clouds are
        # covered by bytes/palette, not incorrectly compared as opaque pixels.
        if a&0x3F00 or (a>>14)==3 or (c>>12) not in banks:continue
        delta=(c&1023)-(base-0x10000)//32
        if delta<0:continue
        col,row=delta%32,delta//32
        if col>=16 or row>=4:continue
        w,h=shapes[a>>14][b>>14]
        key=(col*8,row*8,w,h)
        if key not in parts:continue
        flips=(2 if b&0x1000 else 0)|(1 if b&0x2000 else 0)
        part=dict(x=0,y=0,gfx_x=col*8,gfx_y=row*8,width=w,height=h,
                  object_dimensions=[w,h],gfx_page=0,flip_bits=flips)
        image=render_sprite_frame({'parts':[part]},resources)
        x=b&511;y=a&255
        if x>=256:x-=512
        if y>=160:y-=256
        compared=0;failed=False
        for py in range(h):
            for px in range(w):
                offset=(py*w+px)*4;color=image['pixels'][offset:offset+4]
                if not color[3] or not (0<=x+px<240 and 0<=y+py<160):continue
                compared+=1
                if any(native>>3!=source>>3 for native,source in zip(e.image.getpixel((x+px,y+py)),color[:3])):
                    failed=True
        if compared>=3 and not failed:matches.append(dict(oam_index=index,source_part=list(key),opaque_pixels=compared))
    return matches

def check(e,resources,parts,label):
    best=[];base=0;banks=[]
    for _ in range(120):
        base,banks=page_binding(e,resources)
        matches=pixel_matches(e,resources,base,banks,parts)
        if sum(m['opaque_pixels'] for m in matches)>sum(m['opaque_pixels'] for m in best):best=matches
        if sum(m['opaque_pixels'] for m in best)>=12:break
        e.run(3)
    assert sum(m['opaque_pixels'] for m in best)>=12,'No sufficiently visible ordinary sprite part matched static pixels'
    e.snap('sprite-assets-'+label+'.png')
    return dict(stage=label,vram_base=hex(0x06000000+base),obj_palette_banks=banks,
                matching_opaque_pixels=sum(m['opaque_pixels'] for m in best),matched_parts=best,
                tiles_verified=64)

def return_to_window(e):
    e.run(110,[6]);e.run(60)
    assert e.read(0x02000088)==0x0850F15C
    for _ in range(160):
        if e.read(0x02000526,2)+e.read(0x0200A09A,2)<140:break
        e.run(10,[6,0])
    assert e.read(0x02000088)==0x0850F15C
    e.run(60)

def fresh_continue(path,sram):
    e=Emulator(path)
    C.memmove(e.lib.retro_get_memory_data(0),sram,len(sram))
    e.run(1000)
    for key in [3,8,8,8]:press(e,key,160)
    assert e.read(0x02000088)==0x0851021C and e.read(0x0201327A,2)>0,('continue',hex(e.read(0x02000088)),e.read(0x02000010,1))
    return e

def lifecycle(manifest,host,parts):
    document=json.loads(manifest.read_text());document['id']='sky-invaders-lifecycle'
    document['room_edits']=json.loads((ROOT/'examples/room-workshop/mod.json').read_text())['room_edits']
    rom=load_image(host);apply_manifest_data(rom,document,manifest.parent)
    path=ROOT/'local/sky-invaders-lifecycle.gba';rom.output(path,host)
    resources=resolve_sprite_resources(rom,'background-bats');checks=[]
    e=Emulator(path)
    try:
        boot(e)
        for _ in range(180):
            e.run(20,[7,0]);e.run(1,[7,8]);e.run(15,[7,0])
            if e.read(0x02000088)==0x0851021C:break
        assert e.read(0x02000088)==0x0851021C
        e.run(90)
        for _ in range(150):
            x=e.read(0x02000526,2)
            if 112<=x<=124:break
            e.run(1,[7 if x<112 else 6])
        assert 112<=e.read(0x02000526,2)<=124
        e.run(10);press(e,4,30)
        e.run(1,[6]);e.run(1);press(e,8,240)
        e.snap('sprite-assets-composed-save.png')
        sram=C.string_at(e.lib.retro_get_memory_data(0),e.lib.retro_get_memory_size(0))
        return_to_window(e);checks.append(check(e,resources,parts,'composed-save-return'))
    finally:e.close()
    e=fresh_continue(path,sram)
    try:
        return_to_window(e);checks.append(check(e,resources,parts,'composed-fresh-continue-return'))
        e.write(0x0201327A,0,2);e.run(180)
        assert e.read(0x020004EE,1)==16
        e.run(900);assert e.read(0x02000010,1)==5
        death_sram=C.string_at(e.lib.retro_get_memory_data(0),e.lib.retro_get_memory_size(0))
    finally:e.close()
    e=fresh_continue(path,death_sram)
    try:
        return_to_window(e);checks.append(check(e,resources,parts,'composed-post-death-continue-return'))
    finally:e.close()
    return dict(output_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),checks=checks,
                scope='Separate composed room-workshop save shortcut, not the unchanged final-example campaign',
                fixtures=['SRAM copied between fresh emulator instances','HP set to zero to trigger native death; no graphics/OAM/palette writes'])

def main():
    host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes();rom=load_image(host)
    manifest=ROOT/'examples/sky-invaders/mod.json';apply_manifest(rom,manifest)
    output=ROOT/'build/mods/sky-invaders/sky-invaders.gba';rom.output(output,host)
    parts={(p['gfx_x']//8*8,p['gfx_y']//8*8,p['width'],p['height'])
           for frame in inspect_sprite(rom,SPRITES['background-bats'])['frames'] for p in frame['parts']}
    checks=[]
    for path,image,label in [(host,load_image(host),'baseline'),(output,rom,'custom')]:
        resources=resolve_sprite_resources(image,'background-bats');e=Emulator(path)
        try:
            boot(e);checks.append(check(e,resources,parts,label+'-entry'))
            if label=='custom':
                press(e,3,40);assert e.read(0x02000064,1)==6,('pause',e.read(0x02000064,1))
                e.run(200);press(e,0,90);assert e.read(0x02000064,1)==1
                checks.append(check(e,resources,parts,'custom-pause-resume'))
                for _ in range(150):
                    e.run(5,[6])
                    if e.read(0x02000088)==0x0850EF9C:break
                assert e.read(0x02000088)==0x0850EF9C
                e.run(90)
                for _ in range(150):
                    e.run(5,[7])
                    if e.read(0x02000088)==0x0850F15C:break
                assert e.read(0x02000088)==0x0850F15C
                e.run(240);checks.append(check(e,resources,parts,'custom-room-reentry'))
        finally:e.close()
    lifecycle_report=lifecycle(manifest,host,parts) if '--lifecycle' in sys.argv else None
    assert host.read_bytes()==original
    report=dict(status='native_sprite_assets_verified',output_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                checks=checks,passed=['Input-only natural entry loads original artwork and palette through the native engine',
                'All 64 source tiles match native OBJ VRAM at each checked stage',
                'Ordinary OAM sprite parts match visible static source pixels',
                'Final example pause/resume and room exit/reentry preserve imported artwork','Original ROM unchanged'],
                fixtures=[],limitations=['Shared bats/clouds page/palette replacement, not a per-room actor import',
                'Blended cloud pixels excluded from opaque comparisons','Save/death lifecycle and other consumers not yet verified','No new frames, AI, player streaming or VRAM ownership'])
    if lifecycle_report:
        report['composed_lifecycle']=lifecycle_report
        report['passed'].append('Separate composed save-route harness preserves native art on save return, fresh continue and forced-HP death/fresh continue')
        report['limitations'][2]='Save/death checked in separate composed shortcut harness; other consumers, full campaign and hardware remain unverified'
    (ROOT/'local/sprite-assets-verification.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
