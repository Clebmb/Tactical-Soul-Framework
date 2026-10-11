"""Existing AoS layer inspection and isolated main-layer cell edits.

Format evidence: local DSVEdit layer.rb, tileset.rb, gba_constants.rb and
GBA dummy filesystem. Resource bytes are private; no general room compiler.
"""
import hashlib,struct
from .core import PatchError,number
from .content import integer
from .rooms import room_address,metadata
from .compression import read_aria,rebuild_aria
from .terrain import encode_definitions,extend_resource


def inspect_geometry(rom,sector,index,layer=0,full=False):
    layer=integer(layer,0,2);pointer=room_address(rom,sector,index)
    values=metadata(rom,pointer);layer_list=values[3]
    listing=rom.read(layer_list,36);record=listing[layer*12:(layer+1)*12]
    z,scroll,bg,pixel_w,pixel_h,meta=struct.unpack("<BBHHHI",record)
    if not meta:raise PatchError("Selected layer is empty")
    meta_bytes=rom.read(meta,16)
    width,height,kind,visual,collision,layout=struct.unpack("<BBHIII",meta_bytes)
    if not 1<=width<=15 or not 1<=height<=15:raise PatchError("Unsupported layer dimensions")
    if kind!=2:raise PatchError("This geometry reader currently supports tileset type 2 only")
    visual_resource=read_aria(rom,visual);collision_resource=read_aria(rom,collision)
    visual_data=bytes.fromhex(visual_resource['data_hex']);collision_data=bytes.fromhex(collision_resource['data_hex'])
    if not visual_data or len(visual_data)%32 or not collision_data or len(collision_data)%16:
        raise PatchError("Incomplete metatile visual/collision records")
    metatiles=1+len(visual_data)//32;collision_metatiles=1+len(collision_data)//16
    if metatiles>512 or collision_metatiles!=metatiles:raise PatchError("Unsupported visual/collision count relationship")
    layout_bytes=rom.read(layout,width*height*128)
    cells=list(struct.unpack('<'+'H'*(len(layout_bytes)//2),layout_bytes))
    if any((v&0x3FFF)>=metatiles for v in cells):raise PatchError("Layer references a missing metatile")
    result={'sector':number(sector),'room':number(index),'layer':layer,'room_address':pointer,
            'layer_list_address':layer_list,'layer_metadata_address':meta,'layout_address':layout,
            'width_screens':width,'height_screens':height,'width_cells':width*8,'height_cells':height*8,
            'z_index':z,'scroll_mode':scroll,'bg_control':bg,'pixel_dimensions':[pixel_w,pixel_h],
            'tileset_type':kind,'visual_tileset_address':visual,'collision_tileset_address':collision,
            'metatiles_including_blank':metatiles,'layout_sha256':hashlib.sha256(layout_bytes).hexdigest(),
            'visual_sha256':hashlib.sha256(visual_data).hexdigest(),'collision_sha256':hashlib.sha256(collision_data).hexdigest(),
            'scope':'type-2 layer records and raw collision bytes; no collision semantic certification'}
    if full:result.update({'layer_list_hex':listing.hex(),'layer_metadata_hex':meta_bytes.hex(),
                           'cells':cells,'visual_resource':visual_resource,'collision_resource':collision_resource})
    return result


def verify_roundtrip(bundle):
    """Rebuild inspected selected metadata/layout/resources without ROM writes."""
    listing=bytes.fromhex(bundle['layer_list_hex']);meta=bytes.fromhex(bundle['layer_metadata_hex'])
    if len(listing)!=36 or len(meta)!=16:raise PatchError("Invalid exported geometry records")
    rebuilt_meta=struct.pack('<BBHIII',bundle['width_screens'],bundle['height_screens'],bundle['tileset_type'],bundle['visual_tileset_address'],bundle['collision_tileset_address'],bundle['layout_address'])
    rebuilt_entry=struct.pack('<BBHHHI',bundle['z_index'],bundle['scroll_mode'],bundle['bg_control'],*bundle['pixel_dimensions'],bundle['layer_metadata_address'])
    if rebuilt_meta!=meta or rebuilt_entry!=listing[bundle['layer']*12:(bundle['layer']+1)*12]:raise PatchError('Exported geometry metadata drift')
    cell_bytes=struct.pack('<'+'H'*len(bundle['cells']),*bundle['cells'])
    if len(cell_bytes)!=bundle['width_screens']*bundle['height_screens']*128:
        raise PatchError("Exported geometry cell count drift")
    if hashlib.sha256(cell_bytes).hexdigest()!=bundle['layout_sha256']:raise PatchError("Exported layout hash drift")
    for key in ['visual_resource','collision_resource']:rebuild_aria(bundle[key],preserve=True)
    return {'layer_list_hex':listing.hex(),'layer_metadata_hex':meta.hex(),'layout_hex':cell_bytes.hex(),
            'visual_compressed_hex':rebuild_aria(bundle['visual_resource']).hex(),
            'collision_compressed_hex':rebuild_aria(bundle['collision_resource']).hex()}


def apply_geometry_edits(rom,entries):
    if not isinstance(entries,list) or not entries:raise PatchError("geometry_edits requires a nonempty list")
    planned=[];seen=set()
    supported={tuple(p) for p in rom.profile.get('geometry_edit_rooms',[])}
    for entry in entries:
        required={'room','layer','expected_layout_sha256','cells'}
        if not isinstance(entry,dict) or not required<=set(entry) or set(entry)-required-{'metatiles'}:
            raise PatchError("Geometry edit requires room,layer,expected_layout_sha256,cells")
        ref=entry['room']
        if not isinstance(ref,dict) or set(ref)!={'sector','room'}:raise PatchError("Invalid geometry room reference")
        s,i=number(ref['sector']),number(ref['room']);layer=integer(entry['layer'],0,2)
        if (s,i) not in supported or layer!=0:raise PatchError("Geometry writes currently allow only registered main layers")
        if (s,i) in seen:raise PatchError("Duplicate geometry room batch")
        seen.add((s,i));bundle=inspect_geometry(rom,s,i,layer,full=True)
        if bundle['layout_sha256']!=entry['expected_layout_sha256']:raise PatchError("Geometry layout preimage mismatch")
        custom=None;count=bundle['metatiles_including_blank']
        if 'metatiles' in entry:
            visual,collision,descriptors=encode_definitions(entry['metatiles'],count)
            # Validate every authored character against actual room loads before
            # allocating anything. Imports are lazy to avoid a renderer cycle.
            from .rendering import read_graphics,read_palettes,minitile,graphics_chunk_modes
            values=metadata(rom,bundle['room_address'])
            chunks,records=read_graphics(rom,values[4]);palettes,_=read_palettes(rom,values[5])
            for value in set(descriptors):minitile(value,(bundle['bg_control']>>2)&3,chunks,palettes,graphics_chunk_modes(records))
            custom=(visual,collision,len(entry['metatiles']));count+=custom[2]
        rows=entry['cells']
        if not isinstance(rows,list) or not rows:raise PatchError("Geometry cells must be nonempty")
        changed=set();cells=bundle['cells'][:]
        for row in rows:
            if not isinstance(row,dict) or set(row)!={'x','y','expect','value'}:raise PatchError("Invalid geometry cell edit")
            x=integer(row['x'],0,bundle['width_cells']-1);y=integer(row['y'],0,bundle['height_cells']-1)
            pos=y*bundle['width_cells']+x
            if pos in changed:raise PatchError("Duplicate geometry cell")
            changed.add(pos);old=integer(row['expect'],0,65535);value=integer(row['value'],0,65535)
            if cells[pos]!=old:raise PatchError("Geometry cell precondition mismatch")
            if old==value:raise PatchError("Geometry edit must change the cell")
            if (value&0x3FFF)>=count:raise PatchError("Geometry cell references missing metatile")
            cells[pos]=value
        if custom and not any((cells[p]&0x3FFF)>=bundle['metatiles_including_blank'] for p in changed):
            raise PatchError('Custom definitions must be used by an edited cell')
        planned.append((bundle,cells,sorted(changed),custom))
    reports=[]
    for bundle,cells,changed,custom in planned:
        label=f"geometry-{bundle['sector']}-{bundle['room']}"
        layout=rom.allocate(label+'-layout',struct.pack('<'+'H'*len(cells),*cells))
        meta=bytearray.fromhex(bundle['layer_metadata_hex']);struct.pack_into('<I',meta,12,layout)
        if custom:
            visual=rom.allocate(label+'-visual',extend_resource(bundle['visual_resource'],custom[0]))
            collision=rom.allocate(label+'-collision',extend_resource(bundle['collision_resource'],custom[1]))
            struct.pack_into('<II',meta,4,visual,collision)
        meta_address=rom.allocate(label+'-metadata',meta)
        listing=bytearray.fromhex(bundle['layer_list_hex']);struct.pack_into('<I',listing,bundle['layer']*12+8,meta_address)
        listing_address=rom.allocate(label+'-layers',listing)
        old=number(bundle['layer_list_address']).to_bytes(4,'little')
        rom.write_integer(bundle['room_address']+8,listing_address,4,label+'-room-pointer',old)
        reports.append({'sector':bundle['sector'],'room':bundle['room'],'layer':bundle['layer'],'changed_cells':changed,
                        'layout_address':layout,'layer_metadata_address':meta_address,'layer_list_address':listing_address,
                        'shared_visual_and_collision_resources_preserved':True,'dimensions_preserved':True,
                        'custom_metatiles_added':custom[2] if custom else 0})
    return reports
