"""Optional Pillow authoring adapter. Builds remain standard-library only."""
import argparse,json
from pathlib import Path
from PIL import Image
p=argparse.ArgumentParser(description='Convert an indexed PNG to Tactical Soul Framework tiles4/palette JSON; no quantization or ROM writes')
p.add_argument('image',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--palette-banks',type=int,default=1);a=p.parse_args()
im=Image.open(a.image);im.load()
if im.mode!='P' or im.width%8 or im.height%8 or not 8<=im.width<=1024 or not 8<=im.height<=1024:p.error('Use an indexed PNG with 8-pixel-aligned dimensions, 8..1024')
pixels=list(im.get_flattened_data() if hasattr(im,"get_flattened_data") else im.getdata())
if max(pixels)>15:p.error('4bpp images may use only indices 0..15')
if not 1<=a.palette_banks<=16:p.error('Palette banks must be 1..16')
trans=im.info.get('transparency')
if trans is not None and trans!=0:p.error('Only index 0 transparency is supported; remove partial alpha')
raw=im.getpalette();colors=[raw[i*3:i*3+3] for i in range(16)]
if any(len(c)!=3 for c in colors):p.error('PNG palette must contain 16 RGB entries')
a.out.mkdir(parents=True,exist_ok=True)
(a.out/'tiles.json').write_text(json.dumps({'width':im.width,'height':im.height,'pixels':pixels}))
(a.out/'palette.json').write_text(json.dumps(colors*a.palette_banks))
print('Wrote tiles.json and palette.json; choose checked native bindings in your manifest.')
