"""Optional Pillow sheet preview. Private native exports stay under local/."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.content import tiles,palette
from PIL import Image
p=argparse.ArgumentParser(description='Preview indexed tiles JSON using one RGB palette bank')
p.add_argument('tiles',type=Path);p.add_argument('palette',type=Path);p.add_argument('--bank',type=int,default=0);p.add_argument('--scale',type=int,default=4);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
spec=json.loads(a.tiles.read_text());colors=json.loads(a.palette.read_text());tiles(spec);palette(colors)
if not 0<=a.bank<=(len(colors)-16)//16:p.error('Choose a complete 16-color bank in the supplied palette')
if not 1<=a.scale<=8:p.error('Scale must be 1..8')
if not a.out.resolve().is_relative_to((ROOT/'local').resolve()):p.error('Previews must stay under local/; native exports can contain private game artwork')
if a.out.resolve() in [a.tiles.resolve(),a.palette.resolve()]:p.error('Preview must not overwrite an input')
bank=colors[a.bank*16:(a.bank+1)*16]
im=Image.new('RGBA',(spec['width'],spec['height']));im.putdata([tuple(bank[i])+(0 if i==0 else 255,) for i in spec['pixels']]);im=im.resize((im.width*a.scale,im.height*a.scale),Image.Resampling.NEAREST)
a.out.parent.mkdir(parents=True,exist_ok=True);im.save(a.out,format='PNG');print(str(a.out.resolve()))
