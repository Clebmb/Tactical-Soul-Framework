"""Read-only type-1/type-3 byte-index background definitions.

Source evidence: local DSVEdit layer.rb and tileset.rb. This is not a
terrain writer, affine viewport renderer or collision semantic decoder.
"""
import hashlib,struct
from .core import PatchError,number
from .content import integer
from .rooms import room_address,metadata
from .compression import read_aria,rebuild_aria


def inspect_background(rom,sector,index,layer=1,full=False):
    """Inspect one byte-index layer; optionally include private lossless data."""
    layer=integer(layer,0,2)
    pointer=room_address(rom,sector,index);listing=metadata(rom,pointer)[3]
    records=rom.read(listing,36);entry=records[layer*12:(layer+1)*12]
    z,scroll,bg,pw,ph,address=struct.unpack('<BBHHHI',entry)
    if not address:raise PatchError('Selected background layer is empty')
    raw_meta=rom.read(address,16)
    width,height,kind,visual,collision,layout=struct.unpack('<BBHIII',raw_meta)
    if not 1<=width<=15 or not 1<=height<=15:raise PatchError('Unsupported background dimensions')
    if kind not in (1,3):raise PatchError('Background reader supports byte-index tileset types 1 and 3 only')
    resource=read_aria(rom,visual) if kind==3 else {'encoding':'raw','data_hex':rom.read(visual,4096).hex()}
    definitions=bytes.fromhex(resource['data_hex'])
    if not definitions or len(definitions)%16 or len(definitions)>8192:
        raise PatchError('Incomplete or oversized byte-index metatile definitions')
    count=1+len(definitions)//16
    raw_layout=rom.read(layout,width*height*128)
    cells=list(struct.unpack('<'+'H'*(len(raw_layout)//2),raw_layout))
    if any((cell&0x3FFF)>=count for cell in cells):raise PatchError('Background references a missing metatile')
    result={'schema_version':1,'sector':number(sector),'room':number(index),'layer':layer,
            'room_address':pointer,'layer_list_address':listing,'layer_metadata_address':address,
            'layout_address':layout,'visual_tileset_address':visual,'collision_tileset_address':collision,
            'width_screens':width,'height_screens':height,'width_cells':width*8,'height_cells':height*8,
            'tileset_type':kind,'z_index':z,'scroll_mode':scroll,'bg_control':bg,'pixel_dimensions':[pw,ph],
            'metatiles_including_blank':count,'definition_bytes':len(definitions),'character_index_bits':8,
            'layout_sha256':hashlib.sha256(raw_layout).hexdigest(),
            'visual_sha256':hashlib.sha256(definitions).hexdigest(),
            'referenced_metatile_ids':sorted({c&0x3FFF for c in cells}),
            'scope':'read-only byte-index background definitions; collision pointer opaque; no rendering or write authorization'}
    if full:result.update({'layer_list_hex':records.hex(),'layer_metadata_hex':raw_meta.hex(),
                           'cells':cells,'visual_resource':resource})
    return result


def verify_background_roundtrip(bundle):
    """Validate a full export and return exact source bytes, without writes."""
    listing=bytes.fromhex(bundle['layer_list_hex']);meta=bytes.fromhex(bundle['layer_metadata_hex'])
    layer=integer(bundle['layer'],0,2);kind=integer(bundle['tileset_type'],1,3)
    if kind not in (1,3) or len(listing)!=36 or len(meta)!=16:raise PatchError('Invalid background export metadata')
    expected=struct.pack('<BBHIII',bundle['width_screens'],bundle['height_screens'],kind,
                         bundle['visual_tileset_address'],bundle['collision_tileset_address'],bundle['layout_address'])
    entry=struct.pack('<BBHHHI',bundle['z_index'],bundle['scroll_mode'],bundle['bg_control'],
                      *bundle['pixel_dimensions'],bundle['layer_metadata_address'])
    if expected!=meta or entry!=listing[layer*12:(layer+1)*12]:raise PatchError('Background metadata drift')
    cells=bundle['cells'];data=struct.pack('<'+'H'*len(cells),*cells)
    if len(data)!=bundle['width_screens']*bundle['height_screens']*128 or hashlib.sha256(data).hexdigest()!=bundle['layout_sha256']:
        raise PatchError('Background layout drift')
    resource=bundle['visual_resource'];definitions=bytes.fromhex(resource['data_hex'])
    if hashlib.sha256(definitions).hexdigest()!=bundle['visual_sha256']:raise PatchError('Background visual drift')
    if not definitions or len(definitions)%16 or len(definitions)>8192 or (kind==1 and len(definitions)!=4096):
        raise PatchError('Invalid background definition size')
    count=1+len(definitions)//16
    if count!=bundle['metatiles_including_blank'] or any((v&0x3FFF)>=count for v in cells):raise PatchError('Background definition references drift')
    if resource.get('encoding')!=('raw' if kind==1 else 'aria-lz10'):raise PatchError('Background encoding drift')
    visual=rebuild_aria(resource) if kind==3 else definitions
    return {'layer_list_hex':listing.hex(),'layer_metadata_hex':meta.hex(),'layout_hex':data.hex(),'visual_source_hex':visual.hex()}


def expand_background_map(bundle):
    """Expand metatiles to row-major byte character indices (no affine transform)."""
    verify_background_roundtrip(bundle)
    if any(c&0xC000 for c in bundle['cells']):raise PatchError('Flagged byte-index cells require native flip verification before rendering')
    definitions=bytes.fromhex(bundle['visual_resource']['data_hex'])
    width=bundle['width_cells']*4;height=bundle['height_cells']*4
    out=bytearray(width*height)
    for n,cell in enumerate(bundle['cells']):
        index=cell&0x3FFF
        tile=definitions[(index-1)*16:index*16] if index else bytes(16)
        for y in range(4):
            for x in range(4):
                sx=3-x if cell&0x4000 else x;sy=3-y if cell&0x8000 else y
                out[((n//bundle['width_cells'])*4+y)*width+(n%bundle['width_cells'])*4+x]=tile[sy*4+sx]
    return width,height,bytes(out)


def minitile_8bpp(index,base_block,chunks,banks,modes):
    """Decode one 64-byte GBA character against explicitly loaded palette banks."""
    from .rendering import rgb555
    index=integer(index,0,255);base_block=integer(base_block,0,3)
    chunk=base_block*8+index//32
    if chunk not in chunks or modes.get(chunk)!=8:raise PatchError(f'Missing compatible 8bpp character chunk {chunk}')
    data=chunks[chunk][(index%32)*64:(index%32+1)*64]
    if len(data)!=64:raise PatchError('Truncated 8bpp character')
    pixels=bytearray()
    for color in data:
        if color==0:pixels.extend(bytes(4));continue
        bank,entry=divmod(color,16)
        if bank not in banks or len(banks[bank])!=16:raise PatchError(f'Missing 8bpp palette bank {bank}')
        pixels.extend(rgb555(banks[bank][entry]))
    return bytes(pixels)


def render_background(rom,sector,index,layer=1):
    """Static source raster; excludes native affine/scroll/blend composition."""
    from .rendering import read_graphics,read_palettes,graphics_chunk_modes,blit
    b=inspect_background(rom,sector,index,layer,True)
    if not b['bg_control']&0x80:raise PatchError('Byte-index background does not declare 8bpp control')
    m=metadata(rom,b['room_address']);chunks,records=read_graphics(rom,m[4]);banks,pals=read_palettes(rom,m[5])
    modes=graphics_chunk_modes(records);tw,th,tilemap=expand_background_map(b)
    base=(b['bg_control']>>2)&3;cache={}
    # Blank metatile is transparent independently of loaded character zero.
    rgba=bytearray(tw*8*th*8*4)
    for n,cell in enumerate(b['cells']):
        if not cell&0x3FFF:continue
        cx=(n%b['width_cells'])*4;cy=(n//b['width_cells'])*4
        for y in range(4):
            for x in range(4):
                character=tilemap[(cy+y)*tw+cx+x]
                if character not in cache:cache[character]=minitile_8bpp(character,base,chunks,banks,modes)
                blit(rgba,tw*8,cache[character],(cx+x)*8,(cy+y)*8,8)
    report={k:v for k,v in b.items() if k not in ('cells','layer_list_hex','layer_metadata_hex','visual_resource')}
    report.update({'scope':'static 8bpp source raster; no affine/scroll/blend/actor composition',
                   'graphics':records,'palettes':pals,'rendered_character_ids':sorted(cache),
                   'rgba_sha256':hashlib.sha256(rgba).hexdigest()})
    return {'width':tw*8,'height':th*8,'rgba':bytes(rgba),'report':report}
