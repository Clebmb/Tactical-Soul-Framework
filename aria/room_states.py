"""Bounded read-only alternate-state discovery; never evaluates event flags."""
import hashlib
from .core import PatchError
from .content import integer
from .rooms import room_address,metadata
from .room_catalog import room_id
from .rendering import read_graphics,read_palettes
from .room_resources import bg_tilemap_ranges


def inspect_room_states(rom,sector,index,max_states=32):
    """Follow metadata state links with explicit cycle/limit diagnostics.

    Ordinal IDs identify a base-slot chain, not global state identity. A state
    shared by different base slots can therefore have different contextual IDs.
    """
    sector=integer(sector,0,11);index=integer(index,0,255)
    max_states=integer(max_states,1,64);pointer=room_address(rom,sector,index)
    base_id=room_id(rom.profile['id'],sector,index);seen={};states=[];diagnostics=[]
    while pointer:
        if pointer in seen:
            diagnostics.append({'code':'state_cycle','address':pointer,'target_ordinal':seen[pointer]});break
        if len(states)==max_states:
            diagnostics.append({'code':'state_limit','address':pointer,'max_states':max_states});break
        ordinal=len(states)
        try:
            if pointer%4:raise PatchError('Unaligned room-state metadata pointer')
            values=metadata(rom,pointer)
        except PatchError as error:
            diagnostics.append({'code':'invalid_state_metadata','address':pointer,'message':str(error)});break
        seen[pointer]=ordinal
        row={'id':base_id if not ordinal else base_id.removesuffix(':base')+f':alternate:{ordinal:02d}',
             'ordinal':ordinal,'room_address':pointer,'metadata_sha256':hashlib.sha256(rom.read(pointer,36)).hexdigest(),
             'lcd_control':values[0],'state_swap_event_flag':values[1],'next_state_address':values[2],
             'layer_list_address':values[3],'graphics_list_address':values[4],'palette_list_address':values[5],
             'entity_list_address':values[6],'door_list_address':values[7],'door_count':values[8]&65535,
             'layers':[],'loads':{},'diagnostics':[],'write_registered':False}
        for layer in range(3):
            try:
                entry=rom.read(values[3]+layer*12,12);address=int.from_bytes(entry[8:12],'little')
                item={'layer':layer,'metadata_address':address,'status':'empty'}
                if address:
                    data=rom.read(address,16)
                    item.update({'status':'metadata_read','width_screens':data[0],'height_screens':data[1],
                                 'tileset_type':int.from_bytes(data[2:4],'little')})
                row['layers'].append(item)
            except PatchError as error:row['diagnostics'].append({'code':'invalid_layer_metadata','layer':layer,'message':str(error)})
        for kind,reader,address in [('graphics',read_graphics,values[4]),('palettes',read_palettes,values[5])]:
            try:
                # An empty list or null pointer cannot prove which prior room
                # supplied assets. Expose it; never pick the base-state loads.
                if not address or not rom.integer(address):
                    row['loads'][kind]={'status':'inherited_or_empty','prior_state_required':True};continue
                loaded,records=reader(rom,address)
                row['loads'][kind]={'status':'resolved','records':records,'loaded_slots':sorted(loaded)}
            except PatchError as error:
                row['loads'][kind]={'status':'unavailable','message':str(error)}
        try:row['tilemap_ranges']=bg_tilemap_ranges(rom,values[3])
        except PatchError as error:row['diagnostics'].append({'code':'tilemaps_unavailable','message':str(error)})
        states.append(row);pointer=values[2]
    return {'schema_version':1,'base_room_id':base_id,'sector':sector,'room':index,
            'image_sha256':hashlib.sha256(rom.data).hexdigest(),'states':states,'diagnostics':diagnostics,
            'chain_complete':not diagnostics,
            'scope':'linked metadata/load observations only; event selection, prior-room inheritance and native transitions unverified'}
