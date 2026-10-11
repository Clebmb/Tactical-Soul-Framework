"""Private-host byte-index background survey; no native pixel certification."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image
from aria.rooms import sector_span,room_address,metadata
from aria.backgrounds import inspect_background,verify_background_roundtrip
r=load_image(ROOT/'CastlevaniaAoS.gba');original=bytes(r.data);rows=[]
for sector in range(12):
    _,count=sector_span(r,sector)
    for index in range(count):
        listing=metadata(r,room_address(r,sector,index))[3]
        for layer in range(3):
            address=r.integer(listing+layer*12+8)
            if not address or r.integer(address+2,2) not in (1,3):continue
            b=inspect_background(r,sector,index,layer,True);rebuilt=verify_background_roundtrip(b)
            visual=bytes.fromhex(rebuilt['visual_source_hex']);layout=bytes.fromhex(rebuilt['layout_hex'])
            assert visual==r.read(b['visual_tileset_address'],len(visual))
            assert layout==r.read(b['layout_address'],len(layout))
            rows.append({k:b[k] for k in ('sector','room','layer','tileset_type','metatiles_including_blank','visual_sha256','layout_sha256')})
assert len(rows)==24 and sum(x['tileset_type']==1 for x in rows)==11
assert bytes(r.data)==original and not r.ledger and not r.allocations
report={'passed':['11 raw type-1 and 13 compressed type-3 layers inspect','source visual/layout bytes rebuild exactly','ROM, mutation ledger and allocations unchanged'],
        'image_sha256':hashlib.sha256(original).hexdigest(),'layer_count':len(rows),'layers':rows,
        'limitations':['read-only structural evidence','no native pixels or affine viewport verification','no new write targets; collision pointer opaque']}
folder=ROOT/'local';folder.mkdir(exist_ok=True)
(folder/'background-verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='layers'},indent=2))
