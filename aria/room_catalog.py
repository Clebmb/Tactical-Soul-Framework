"""Bounded, paginated read-only room discovery for agent/GUI clients.

Stable IDs identify base-state table slots, not movable ROM pointers. Invalid
sectors, rooms and layers report diagnostics independently. See ROOM-CATALOG.md.
"""
import hashlib,struct
from .core import PatchError,number
from .content import integer
from .rooms import sector_span,metadata
from .geometry import inspect_geometry
from .rendering import render_layer
from .backgrounds import inspect_background,render_background


def diagnostic(code, error):
    return {'code':code,'message':str(error)}


def room_id(profile, sector, index):
    return f'{profile}:s{sector:02d}:r{index:03d}:base'


def inspect_layer(rom, sector, index, listing, layer, check_rendering):
    result={'layer':layer,'geometry_status':'invalid','render_status':'not_checked','diagnostics':[]}
    try:
        z,scroll,bg,pw,ph,pointer=struct.unpack('<BBHHHI',rom.read(listing+layer*12,12))
        result.update({'z_index':z,'scroll_mode':scroll,'bg_control':bg,'pixel_dimensions':[pw,ph],
                       'metadata_address':pointer})
        if not pointer:
            result['geometry_status']='empty';return result
        width,height,kind=struct.unpack('<BBH',rom.read(pointer,4))
        result.update({'width_screens':width,'height_screens':height,'tileset_type':kind})
        if kind not in (1,2,3):
            result['geometry_status']='unsupported'
            result['diagnostics'].append(diagnostic('unsupported_tileset_type',f'Tileset type {kind}; readers support types 1, 2 and 3'))
            return result
        reader=inspect_geometry if kind==2 else inspect_background
        result['geometry']=reader(rom,sector,index,layer)
        result['geometry_format']='terrain_4bpp' if kind==2 else 'background_byte_index'
        result['render_scope']='static_selected_layer' if kind==2 else 'static_source_raster_no_affine_viewport'
        result['geometry_status']='available'
    except PatchError as error:
        result['diagnostics'].append(diagnostic('invalid_geometry',error));return result
    if check_rendering:
        try:
            rendered=(render_layer if kind==2 else render_background)(rom,sector,index,layer)
            result['render_status']='available'
            result['render_summary']={'width':rendered['width'],'height':rendered['height'],
                                      'rgba_sha256':rendered['report']['rgba_sha256'],
                                      'referenced_metatile_count':len(rendered['report']['rendered_metatile_ids'] if kind==2 else rendered['report']['referenced_metatile_ids']),
                                      'scope':result['render_scope'],'viewport_pixels_verified':False}
        except PatchError as error:
            result['render_status']='unavailable'
            result['diagnostics'].append(diagnostic('render_unavailable',error))
    return result


def catalog_rooms(rom, sector=None, offset=0, limit=32, check_rendering=False):
    """Enumerate normal base-state slots; inspect only requested page (max128).

    Header/table errors are data diagnostics. Invalid API options raise.
    ``available`` means decoder/renderer support, never gameplay safety.
    No binary assets or full raster buffers are returned or cached.
    """
    offset=integer(offset,0,3072);limit=integer(limit,1,128)
    if not isinstance(check_rendering,bool):raise PatchError('check_rendering must be boolean')
    sectors=range(12) if sector is None else [integer(sector,0,11)]
    profile=rom.profile['id'];spans=[];slots=[];errors=[]
    for s in sectors:
        try:
            table,count=sector_span(rom,s)
            spans.append({'sector':s,'table_address':table,'room_count':count})
            slots.extend((s,i,table+i*4) for i in range(count))
        except PatchError as error:
            errors.append({'sector':s,**diagnostic('invalid_sector_table',error)})
    rooms=[]
    for s,i,address in slots[offset:offset+limit]:
        entry={'id':room_id(profile,s,i),'sector':s,'room':i,'state':'base',
               'pointer_entry_address':address,'status':'invalid','diagnostics':[],'layers':[]}
        try:
            pointer=rom.integer(address);entry['room_address']=pointer;m=metadata(rom,pointer)
            entry.update({'alternate_state_address':m[2],'graphics_list_address':m[4],
                          'palette_list_address':m[5],'door_count':m[8]&65535,
                          'map_position':[(m[9]>>16)&127,(m[9]>>23)&127]})
            entry['layers']=[inspect_layer(rom,s,i,m[3],layer,check_rendering) for layer in range(3)]
            entry['status']='available' if all(l['geometry_status'] in ('available','empty') and l['render_status']!='unavailable' for l in entry['layers']) else 'partial'
            allowed={tuple(p) for p in rom.profile.get('geometry_edit_rooms',[])}
            entry['terrain_write_registered']=(s,i) in allowed
        except PatchError as error:entry['diagnostics'].append(diagnostic('invalid_room_metadata',error))
        rooms.append(entry)
    following=offset+len(rooms)
    return {'schema_version':2,'profile':profile,'image_sha256':hashlib.sha256(rom.data).hexdigest(),
            'scope':'normal sector base-state slots; no alternate-state enumeration or gameplay certification',
            'rendering_checked':check_rendering,'enumeration_complete':not errors,'sectors':spans,
            'diagnostics':errors,'total_known_slots':len(slots),'offset':offset,'limit':limit,
            'next_offset':following if following<len(slots) else None,'rooms':rooms}
