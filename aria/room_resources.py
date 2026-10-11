"""Read-only static BG dependencies, metatile availability and memory audit.

Unloaded slots are observations, never import authorization or runtime ownership.
"""
import hashlib,struct
from .core import PatchError
from .rooms import room_address,metadata,sector_span
from .geometry import inspect_geometry
from .rendering import read_graphics,read_palettes,graphics_chunk_modes
from .backgrounds import inspect_background


def bg_tilemap_ranges(rom, listing):
    result=[]
    for layer in range(3):
        record=rom.read(listing+layer*12,12)
        meta=int.from_bytes(record[8:12],'little')
        if not meta:continue
        raw_kind=rom.read(meta+2,2)
        if len(raw_kind)!=2:raise PatchError('Truncated tilemap layer metadata')
        kind=int.from_bytes(raw_kind,'little')
        if kind not in (1,2,3):raise PatchError('Unknown tilemap layer format')
        control=int.from_bytes(record[2:4],'little');start=((control>>8)&31)*2048
        # Text screenblocks are 16-bit maps; byte-index affine maps are
        # square 16/32/64/128-character maps. Keep physical ranges exact.
        size=control>>14
        length=(256,1024,4096,16384)[size] if kind in (1,3) else (2048,4096,4096,8192)[size]
        end=start+length
        if end>65536:raise PatchError('Unsupported wrapped background tilemap')
        result.append({'layer':layer,'start':start,'end':end})
    return result


def metatile_dependencies(descriptors, base, chunks, banks, chunk_modes=None):
    required_chunks=sorted({base*8+(v&1023)//64 for v in descriptors})
    required_banks=sorted({v>>12 for v in descriptors})
    missing_chunks=sorted(set(required_chunks)-set(chunks));missing_banks=sorted(set(required_banks)-set(banks))
    incompatible=sorted(c for c in required_chunks if c in chunks and chunk_modes is not None and chunk_modes.get(c)!=4)
    return {'available':not missing_chunks and not missing_banks and not incompatible,'incompatible_character_chunks':incompatible,'character_chunks':required_chunks,
            'palette_banks':required_banks,'missing_character_chunks':missing_chunks,'missing_palette_banks':missing_banks}


def background_dependencies(indices,base,chunks,banks,modes):
    """Byte-index dependencies; palette requirements come from actual texels."""
    required=sorted({base*8+index//32 for index in indices})
    missing=sorted(set(required)-set(chunks))
    incompatible=sorted(c for c in required if c in chunks and modes.get(c)!=8)
    palette=set();truncated=set()
    for index in set(indices):
        chunk=base*8+index//32
        if chunk not in chunks or chunk in incompatible:continue
        data=chunks[chunk][(index%32)*64:(index%32+1)*64]
        if len(data)!=64:truncated.add(chunk);continue
        palette.update(color//16 for color in data if color)
    missing_banks=sorted(palette-set(banks));complete=not missing and not incompatible and not truncated
    return {'available':complete and not missing_banks,'character_chunks':required,'palette_banks':sorted(palette),
            'missing_character_chunks':missing,'incompatible_character_chunks':incompatible,
            'truncated_character_chunks':sorted(truncated),'missing_palette_banks':missing_banks,
            'palette_dependencies_complete':complete}


def audit_room_resources(rom, sector, index, include_consumers=False):
    if not isinstance(include_consumers,bool):raise PatchError('include_consumers must be boolean')
    pointer=room_address(rom,sector,index);m=metadata(rom,pointer)
    result={'schema_version':2,'room_address':pointer,'sector':sector,'room':index,
            'image_sha256':hashlib.sha256(rom.data).hexdigest(),'diagnostics':[],'layers':[],
            'scope':'static BG loads and selected base-state definitions; no dynamic ownership/import authorization'}
    chunks={};banks={};gfx=[];pals=[];tilemaps=[]
    for code,reader,address in [('graphics',read_graphics,m[4]),('palettes',read_palettes,m[5])]:
        try:
            loaded,records=reader(rom,address)
            if code=='graphics':chunks,gfx=loaded,records
            else:banks,pals=loaded,records
        except PatchError as e:result['diagnostics'].append({'code':code+'_unavailable','message':str(e)})
    try:tilemaps=bg_tilemap_ranges(rom,m[3])
    except PatchError as e:result['diagnostics'].append({'code':'tilemaps_unavailable','message':str(e)})
    result.update({'graphics':gfx,'palettes':pals,'tilemaps':tilemaps,'character_chunk_bpp':graphics_chunk_modes(gfx)})
    overlaps=[{'chunk':c,'layer':t['layer']} for c in chunks for t in tilemaps if c*2048<t['end'] and (c+1)*2048>t['start']]
    reserved={c for t in tilemaps for c in range(t['start']//2048,(t['end']+2047)//2048)}
    result['budget']={'loaded_character_bytes':len(chunks)*2048,'loaded_palette_bytes':len(banks)*32,
                      'loaded_chunks':sorted(chunks),'loaded_palette_banks':sorted(banks),
                      'character_tilemap_overlaps':overlaps,
                      'static_unloaded_non_tilemap_chunks':sorted(set(range(32))-set(chunks)-reserved) if not result['diagnostics'] else None,
                      'static_unloaded_palette_banks':sorted(set(range(16))-set(banks)) if not result['diagnostics'] else None,
                      'load_observations_complete':not result['diagnostics'],'runtime_ownership_verified':False}
    for layer in range(3):
        row={'layer':layer,'status':'unavailable','diagnostics':[]}
        try:
            if not rom.integer(m[3]+layer*12+8):row['status']='empty';result['layers'].append(row);continue
            address=rom.integer(m[3]+layer*12+8);kind=rom.integer(address+2,2)
            b=(inspect_background if kind in (1,3) else inspect_geometry)(rom,sector,index,layer,full=True)
            visual=bytes.fromhex(b['visual_resource']['data_hex'])
            referenced={c&16383 for c in b['cells']};base=(b['bg_control']>>2)&3
            entries=[{'id':0,'referenced':0 in referenced,'available':True,'character_chunks':[],'palette_banks':[],
                      'missing_character_chunks':[],'missing_palette_banks':[],'incompatible_character_chunks':[]}]
            constraints=[]
            if kind in (1,3):
                entries[0].update({'truncated_character_chunks':[],'palette_dependencies_complete':True})
                if any(c&0xC000 for c in b['cells']):constraints.append('flagged_cells_unverified')
                if not b['bg_control']&0x80:constraints.append('8bpp_control_unset')
            for tile in range(1,b['metatiles_including_blank']):
                if kind in (1,3):
                    deps=background_dependencies(visual[(tile-1)*16:tile*16],base,chunks,banks,graphics_chunk_modes(gfx))
                else:
                    descriptors=struct.unpack('<16H',visual[(tile-1)*32:tile*32])
                    deps=metatile_dependencies(descriptors,base,chunks,banks,graphics_chunk_modes(gfx))
                entries.append({'id':tile,'referenced':tile in referenced,**deps})
            row.update({'status':'inspected','tileset_type':kind,'base_block':base,'metatiles':entries,
                        'format':'background_byte_index' if kind in (1,3) else 'terrain_4bpp',
                        'source_preview_constraints':constraints,
                        'unavailable_referenced_ids':[e['id'] for e in entries if e['referenced'] and not e['available']]})
        except PatchError as e:row['diagnostics'].append({'code':'geometry_unavailable','message':str(e)})
        result['layers'].append(row)
    result['dependency_observations_complete']=not result['diagnostics'] and all(l['status']!='unavailable' for l in result['layers'])
    if include_consumers:
        consumers=[];errors=[]
        for s in range(12):
            try:table,count=sector_span(rom,s)
            except PatchError as e:errors.append({'sector':s,'message':str(e)});continue
            for i in range(count):
                try:
                    other=metadata(rom,rom.integer(table+i*4));shared=[]
                    if other[4]==m[4]:shared.append('graphics_list')
                    if other[5]==m[5]:shared.append('palette_list')
                    if shared:consumers.append({'sector':s,'room':i,'shared':shared})
                except PatchError as e:errors.append({'sector':s,'room':i,'message':str(e)})
        result['shared_list_consumers']={'rooms':consumers,'diagnostics':errors,'scope':'identical list pointers only; excludes distinct lists sharing wrappers and alternate states'}
    return result
