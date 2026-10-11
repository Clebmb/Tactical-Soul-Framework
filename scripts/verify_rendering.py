"""Check source-backed static previews against native loaded resource memory.

Uses only controller input. Does not write VRAM, palettes, camera or player RAM.
Pixel comparisons are explicitly restricted to opaque, actor-free wall pixels.
"""
import sys, json, hashlib, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest
from aria.rooms import room_address,metadata
from aria.rendering import render_layer,read_graphics,read_palettes,png_rgba
from emulator import Emulator

def boot(e):
    e.run(1000)
    for k in [3,8,8,8,3,3,8]: e.run(1,[k]);e.run(100)
    for _ in range(60): e.run(1,[8]);e.run(90)
    for _ in range(150):
        e.run(5,[7])
        if e.read(0x02000088)==0x0850F15C: break
    assert e.read(0x02000088)==0x0850F15C
    e.run(240)
    for _ in range(1200):
        if not e.read(0x0200042C)&1: break
        e.run(1)
    assert not e.read(0x0200042C)&1

host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes();results=[]
for modified in [False,True]:
    r=load_image(host)
    if modified: apply_manifest(r,ROOT/'examples/geometry-workshop/mod.json')
    preview=render_layer(r,0,3);m=metadata(r,room_address(r,0,3))
    chunks,_=read_graphics(r,m[4]);palettes,_=read_palettes(r,m[5])
    output=ROOT/'local/rendering-native-fixture.gba'
    if modified: r.output(output,host)
    e=Emulator(output if modified else host)
    try:
        boot(e)
        exact_chunks=[n for n,data in chunks.items() if e.bytes(0x06000000+n*2048,2048)==data]
        exact_banks=[n for n,colors in palettes.items() if e.bytes(0x05000000+n*32,32)==struct.pack('<16H',*colors)]
        print('RESOURCES',modified,exact_chunks,exact_banks,flush=True)
        assert len(exact_chunks)==len(chunks),'Native character load differs from static preview'
        assert len(exact_banks)==len(palettes),'Native palette load differs from static preview'
        cx=e.read(0x0200A09A,2);cy=e.read(0x0200A09E,2)
        # Wall rectangle above actors. Mask transparent pixels; backdrop and
        # other layers are deliberately outside selected-layer rendering.
        total=matches=0;rgba=preview['rgba'];w=preview['width']
        for y in range(24,88):
            for x in range(48,208):
                wx=x+cx;wy=y+cy
                if wx>=w or wy>=preview['height']: continue
                pos=(wy*w+wx)*4
                if rgba[pos+3]!=255: continue
                total+=1;actual=e.image.getpixel((x,y));expected=tuple(rgba[pos:pos+3])
                # mGBA's framebuffer uses 5-bit channels shifted left three;
                # PNG preview expands to full 8-bit. Compare at native depth.
                same=all((a>>3)==(b>>3) for a,b in zip(actual,expected));matches+=same
        print('PIXELS',modified,cx,cy,matches,total,flush=True)
        assert total>1000 and matches==total,'Static wall pixels do not match native viewport'
        tag='step' if modified else 'baseline'
        (ROOT/'local'/f'rendering-{tag}.png').write_bytes(png_rgba(w,preview['height'],rgba))
        e.snap(f'rendering-native-{tag}.png')
        results.append({'modded':modified,'exact_chunks':exact_chunks,'exact_palette_banks':exact_banks,
                        'opaque_wall_pixels_compared':total,'matching_pixels':matches,'camera':[cx,cy],
                        'rgba_sha256':preview['report']['rgba_sha256']})
    finally: e.close()
assert host.read_bytes()==original
report={'passed':['native graphics chunk loads match preview resource mapping','native RGB555 palette banks match preview mapping','opaque actor-free wall pixels match native viewport at 5-bit color depth','baseline and geometry-edited previews verified','original unchanged'],
        'results':results,'fixtures':['controller-only entrance traversal; no RAM writes'],
        'limitations':['static selected-layer preview only','opaque wall sample only; no whole-screen actor/effect equivalence','no inherited resources, 8bpp, animation or layer composition']}
(ROOT/'local/rendering-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
