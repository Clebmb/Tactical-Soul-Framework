"""Isolated original room character/palette imports into registered free slots.

Initial contract: one raw 2KB 4bpp load and one RGB555 bank for first hallway.
No general VRAM allocator, inherited resources, sprite or animation support.
"""
import hashlib,json,struct
from .core import PatchError
from .content import integer,local,tiles,palette
from .rooms import room_address,metadata
from .rendering import read_graphics,read_palettes
from .room_resources import bg_tilemap_ranges


def plan_room_assets(rom, entries, folder):
    if not isinstance(entries,list) or not entries:raise PatchError('room_assets must be nonempty')
    plans=[];seen=set()
    for row in entries:
        required={'room','target_chunk','palette_bank','graphics_source','palette_source','provenance','expected_graphics_list_sha256','expected_palette_list_sha256'}
        if not isinstance(row,dict) or set(row)!=required:raise PatchError('Invalid room_assets schema')
        ref=row['room']
        if not isinstance(ref,dict) or set(ref)!={'sector','room'}:raise PatchError('Invalid room asset room reference')
        s=integer(ref['sector'],0,11);i=integer(ref['room'],0,255)
        chunk=integer(row['target_chunk'],0,31);bank=integer(row['palette_bank'],0,15)
        slot={'sector':s,'room':i,'target_chunk':chunk,'palette_bank':bank}
        if slot not in rom.profile.get('room_asset_slots',[]):raise PatchError('Room asset slot is not registered')
        if (s,i) in seen:raise PatchError('Duplicate room asset batch')
        seen.add((s,i))
        if not isinstance(row['provenance'],str) or not row['provenance'].strip():raise PatchError('Room assets require provenance')
        for key in ['graphics_source','palette_source']:
            if not isinstance(row[key],str):raise PatchError('Room asset sources must be relative paths')
        pointer=room_address(rom,s,i);m=metadata(rom,pointer)
        chunks,gfx=read_graphics(rom,m[4]);banks,pals=read_palettes(rom,m[5])
        if chunk in chunks or bank in banks:raise PatchError('Room asset import overlaps existing graphics/palette loads')
        tilemaps=bg_tilemap_ranges(rom,m[3])
        if any(chunk*2048<t['end'] and (chunk+1)*2048>t['start'] for t in tilemaps):
            raise PatchError('Room asset graphics overlap a layer tilemap')
        gfxlist=rom.read(m[4],len(gfx)*8+4);pallist=rom.read(m[5],len(pals)*8+4)
        for payload,key in [(gfxlist,'expected_graphics_list_sha256'),(pallist,'expected_palette_list_sha256')]:
            if hashlib.sha256(payload).hexdigest()!=row[key]:raise PatchError('Room asset load-list preimage mismatch')
        gp=local(folder,row['graphics_source']);pp=local(folder,row['palette_source'])
        graphics=tiles(json.loads(gp.read_text()));colors=palette(json.loads(pp.read_text()))
        if len(graphics)!=2048 or len(colors)!=32:raise PatchError('Room assets require exactly 64 4bpp tiles and sixteen colors')
        if len(gfx)>=64 or len(pals)>=64:raise PatchError('No room for appended load-list entry')
        plans.append({'row':row,'room_address':pointer,'metadata':m,'graphics':graphics,'colors':colors,
                      'gfxlist':gfxlist,'pallist':pallist,'tilemaps':tilemaps,
                      'source_hashes':{'graphics':hashlib.sha256(gp.read_bytes()).hexdigest(),'palette':hashlib.sha256(pp.read_bytes()).hexdigest()}})
    return plans


def install_room_assets(rom, entries, folder):
    plans=plan_room_assets(rom,entries,folder);reports=[]
    for p in plans:
        row=p['row'];chunk=row['target_chunk'];bank=row['palette_bank'];ref=row['room']
        label=f"room-assets-{ref['sector']}-{ref['room']}"
        wrapper=rom.allocate(label+'-characters',bytes([0,4,0,4])+p['graphics'])
        colors=rom.allocate(label+'-palette',bytes([0,0,1,0])+p['colors'])
        gfxlist=rom.allocate(label+'-graphics-list',p['gfxlist'][:-4]+struct.pack('<IBBBB',wrapper,chunk,0,1,0)+bytes(8))
        pallist=rom.allocate(label+'-palette-list',p['pallist'][:-4]+struct.pack('<IBBBB',colors,bank,0,1,0)+bytes(8))
        rom.write_integer(p['room_address']+12,gfxlist,4,label+'-graphics-pointer',p['metadata'][4].to_bytes(4,'little'))
        rom.write_integer(p['room_address']+16,pallist,4,label+'-palette-pointer',p['metadata'][5].to_bytes(4,'little'))
        reports.append({'room':ref,'graphics_wrapper_address':wrapper,'palette_address':colors,
                        'graphics_list_address':gfxlist,'palette_list_address':pallist,
                        'graphics_sha256':hashlib.sha256(p['graphics']).hexdigest(),'palette_sha256':hashlib.sha256(p['colors']).hexdigest(),
                        'source_sha256':p['source_hashes'],'provenance':row['provenance'],
                        'budget':{'new_character_bytes':2048,'new_palette_bytes':32,'character_range':[chunk*2048,(chunk+1)*2048],
                                  'palette_bank':bank,'excluded_tilemaps':p['tilemaps'],
                                  'rom_payload_bytes':2052+36+len(p['gfxlist'])+12+len(p['pallist'])+12},
                        'shared_original_resources_preserved':True,'scope':'registered static room load; not global VRAM ownership'})
    return reports
