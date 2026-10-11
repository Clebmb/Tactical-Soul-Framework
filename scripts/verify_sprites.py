"""Static exact-host sprite coverage and private contact sheets; no native claims."""
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from aria.cli import load_image
from aria.sprites import SPRITES, inspect_sprite
from aria.sprite_rendering import resolve_sprite_resources, render_sprite_frame
from aria.rendering import png_rgba

def main():
    host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes();rom=load_image(host)
    output=ROOT/'local/sprite-previews';output.mkdir(parents=True,exist_ok=True)
    reports=[]
    for name,pointer in SPRITES.items():
        sprite=inspect_sprite(rom,pointer);resources=resolve_sprite_resources(rom,name)
        images=[render_sprite_frame(frame,resources) for frame in sprite['frames']]
        # Contact sheets center each tight frame in its own cell. They do not
        # establish a stable actor pivot or imply animation playback order.
        cell_w=max(i['width'] for i in images)+4;cell_h=max(i['height'] for i in images)+4
        columns=12;rows=(len(images)+columns-1)//columns
        width=columns*cell_w;height=rows*cell_h
        if width*height>4*1024*1024:raise ValueError('Contact sheet exceeds pixel budget')
        sheet=bytearray(width*height*4);frames=[]
        for index,image in enumerate(images):
            x=(index%columns)*cell_w+(cell_w-image['width'])//2
            y=(index//columns)*cell_h+(cell_h-image['height'])//2
            for row in range(image['height']):
                start=((y+row)*width+x)*4;source=row*image['width']*4
                sheet[start:start+image['width']*4]=image['pixels'][source:source+image['width']*4]
            frames.append(dict(index=index,width=image['width'],height=image['height'],origin=image['origin'],
                               opaque_pixels=sum(a!=0 for a in image['pixels'][3::4]),
                               rgba_sha256=hashlib.sha256(image['pixels']).hexdigest()))
        (output/(name+'-contact-sheet.png')).write_bytes(png_rgba(width,height,sheet))
        reports.append(dict(sprite=name,frame_count=len(images),animation_count=sprite['animation_count'],
                            resources=resources['provenance'],frames=frames,
                            contact_sheet=dict(columns=columns,cell_width=cell_w,cell_height=cell_h)))
    assert sum(r['frame_count'] for r in reports)==272
    assert reports[1]['frames'][0]['rgba_sha256']=='169b79e78d8ead425f5a0370f265e8e88d88fc99e6407b1bca667fd2fceb85cc'
    assert bytes(rom.data)==original and not rom.ledger and host.read_bytes()==original
    report=dict(status='static_sprite_preview_verified',host_sha256=hashlib.sha256(original).hexdigest(),
                frame_count=272,sprites=reports,
                passed=['All registered source frames render within actual page payloads','Raw and Aria-LZ pages resolved',
                        'Deterministic Julius frame0 RGBA regression','Original image and ledger unchanged'],
                limitations=['Static source rendering only; no native OAM/pixel/lifecycle proof','No writes or dynamic Soma resource binding'])
    (ROOT/'local/sprite-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='sprites'},indent=2))

if __name__=='__main__':main()
