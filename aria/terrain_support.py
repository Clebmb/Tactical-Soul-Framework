"""Read-only per-room terrain support and brush dependency diagnostics.

Candidates are investigation leads, never automatic write registration.
"""
import hashlib
from .core import PatchError
from .content import integer
from .rooms import room_address,metadata
from .geometry import inspect_geometry,verify_roundtrip
from .room_catalog import catalog_rooms,room_id
from .room_resources import audit_room_resources

def assess_terrain_support(rom,sector,index):
    sector=integer(sector,0,11);index=integer(index,0,255)
    registered=(sector,index) in {tuple(v) for v in rom.profile.get('geometry_edit_rooms',[])}
    result={'id':room_id(rom.profile['id'],sector,index),'sector':sector,'room':index,
            'registered':registered,'status':'blocked','write_enabled':False,
            'diagnostics':[],'available_metatile_ids':[],
            'scope':'static existing-metatile main-layer assessment; no native gameplay certification or automatic registration'}
    try:
        pointer=room_address(rom,sector,index);m=metadata(rom,pointer);layer=rom.integer(m[3]+8)
        result['room_address']=pointer;result['alternate_state_address']=m[2]
        if not layer:
            result['diagnostics'].append({'code':'empty_main_layer','message':'No editable main-layer metadata'});return result
        kind=rom.integer(layer+2,2);result['tileset_type']=kind
        if kind!=2:
            result['diagnostics'].append({'code':'unsupported_main_format','message':'Terrain writer requires type 2'});return result
        b=inspect_geometry(rom,sector,index,full=True);verify_roundtrip(b)
        result['geometry']={k:b[k] for k in ('width_cells','height_cells','layout_sha256','visual_sha256','collision_sha256','metatiles_including_blank')}
        result['roundtrip_verified']=True
        audit=audit_room_resources(rom,sector,index);main=audit['layers'][0]
        result['diagnostics'].extend(audit['diagnostics'])
        result['diagnostics'].extend(main.get('diagnostics',[]))
        if main['status']!='inspected':
            result['diagnostics'].append({'code':'main_dependencies_unavailable','message':'Main-layer resources could not be inspected'});return result
        result['available_metatile_ids']=[v['id'] for v in main['metatiles'] if v['available']]
        result['unavailable_referenced_ids']=main['unavailable_referenced_ids']
        result['character_tilemap_overlaps']=audit['budget']['character_tilemap_overlaps']
        if result['unavailable_referenced_ids']:
            result['diagnostics'].append({'code':'missing_referenced_dependencies','message':'Some current main-layer metatiles lack static character/palette loads'})
        if result['character_tilemap_overlaps']:
            result['diagnostics'].append({'code':'character_tilemap_overlap','message':'Static character and tilemap ranges overlap'})
        if m[2]:result['diagnostics'].append({'code':'alternate_states_unverified','message':'Nonzero alternate metadata requires separate lifecycle/resource investigation'})
        if result['diagnostics']:return result
        result['status']='registered' if registered else 'static_candidate'
        result['write_enabled']=registered
        if not registered:result['registration_required']='Investigate source/shared resources, isolate edits and verify native entry/traversal/lifecycle before explicitly registering'
    except PatchError as error:
        result['diagnostics'].append({'code':'invalid_terrain_data','message':str(error)})
    return result

def catalog_terrain_support(rom,sector=None,offset=0,limit=32):
    """Page through normal base slots (max128), preserving local diagnostics."""
    catalog=catalog_rooms(rom,sector,offset,limit,False)
    rows=[assess_terrain_support(rom,r['sector'],r['room']) for r in catalog['rooms']]
    return {'schema_version':1,'profile':rom.profile['id'],'image_sha256':hashlib.sha256(rom.data).hexdigest(),
            'offset':catalog['offset'],'limit':catalog['limit'],'next_offset':catalog['next_offset'],
            'total_known_slots':catalog['total_known_slots'],'enumeration_complete':catalog['enumeration_complete'],
            'diagnostics':catalog['diagnostics'],'rooms':rows,
            'page_summary':{status:sum(r['status']==status for r in rows) for status in ('registered','static_candidate','blocked')},
            'scope':'read-only static candidates; registration remains explicit; no runtime or full-campaign certification'}
