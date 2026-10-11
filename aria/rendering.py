"""Read-only type-2 terrain rendering for future editor frontends.

Independent implementation using local DSVEdit room/gfx/palette/layer sources.
No emulator, Pillow, GUI toolkit or ROM mutations. Missing inherited resources
are errors, never silently substituted graphics. See docs/ROOM-PREVIEWS.md.
"""
import hashlib, struct, zlib
from .core import PatchError
from .geometry import inspect_geometry
from .rooms import room_address, metadata
from .compression import read_aria


def read_graphics(rom, pointer):
    """Resolve bounded AoS VCCCC room entries to 2KB character-memory chunks.

    Ordered loads overwrite previous chunks, as the native resource list does.
    Returns full wrapper evidence separately from the final chunk mapping.
    The load reader preserves 4bpp and 8bpp resources; terrain rendering
    still accepts only compatible 4bpp character chunks.
    """
    chunks, records = {}, []
    for index in range(65):
        address = pointer + index * 8
        wrapper = rom.integer(address)
        if not wrapper:
            if not records: raise PatchError('Inherited/empty graphics lists require explicit prior-room state')
            return chunks, records
        if index == 64: raise PatchError('Unterminated room graphics list')
        wrapper, target, first, count, unknown = struct.unpack('<IBBBB', rom.read(address, 8))
        kind, bpp, reserved, length = rom.read(wrapper, 4)
        if kind not in (0, 1) or bpp not in (4,8):
            raise PatchError('Graphics reader supports raw/LZ 4bpp or 8bpp wrappers only')
        if not count or target + count > 32: raise PatchError('Graphics load exceeds 64KB background memory')
        source = rom.integer(wrapper+4) if kind else wrapper+4
        data = bytes.fromhex(read_aria(rom, source)['data_hex']) if kind else rom.read(source, length*512)
        if (first+count)*2048 > len(data): raise PatchError('Graphics chunk exceeds wrapper payload')
        for offset in range(count): chunks[target+offset] = data[(first+offset)*2048:(first+offset+1)*2048]
        records.append({'entry_address':address,'wrapper_address':wrapper,'data_address':source,
                        'compressed':bool(kind),'bpp':bpp,'reserved':reserved,'unknown':unknown,
                        'target_chunk':target,'first_chunk':first,'chunk_count':count,
                        'data_sha256':hashlib.sha256(data).hexdigest()})
    raise PatchError('Unterminated room graphics list')


def graphics_chunk_modes(records):
    """Final per-2KB-chunk bpp after ordered native loads; later loads win."""
    modes={}
    for record in records:
        for chunk in range(record['target_chunk'],record['target_chunk']+record['chunk_count']):
            modes[chunk]=record['bpp']
    return modes


def read_palettes(rom, pointer):
    """Resolve ordered VCCCC wrappers into 16 RGB555 background palette banks."""
    banks, records = {}, []
    for index in range(65):
        address = pointer+index*8
        source = rom.integer(address)
        if not source:
            if not records: raise PatchError('Inherited/empty palettes require explicit prior-room state')
            return banks, records
        if index == 64: raise PatchError('Unterminated room palette list')
        source, target, first, count, unknown = struct.unpack('<IBBBB', rom.read(address,8))
        zero, reserved, rows, end = rom.read(source,4)
        if zero or end or not count or first+count>rows or target+count>16:
            raise PatchError('Invalid background palette range/header')
        data = rom.read(source+4+first*32,count*32)
        for j in range(count):
            banks[target+j] = list(struct.unpack('<16H',data[j*32:(j+1)*32]))
        records.append({'entry_address':address,'data_address':source,'target_bank':target,
                        'first_bank':first,'bank_count':count,'reserved':reserved,'unknown':unknown,
                        'data_sha256':hashlib.sha256(data).hexdigest()})
    raise PatchError('Unterminated room palette list')


def rgb555(value, transparent=False):
    channels = [(value >> shift) & 31 for shift in (0,5,10)]
    return bytes([(c<<3)|(c>>2) for c in channels]+[0 if transparent else 255])


def transform(pixels, width, height, horizontal=False, vertical=False):
    """Flip an RGBA rectangle. A whole-cell flip also swaps minitile positions."""
    if len(pixels)!=width*height*4: raise PatchError('Invalid RGBA rectangle')
    if not horizontal and not vertical: return bytes(pixels)
    out=bytearray(len(pixels))
    for y in range(height):
        for x in range(width):
            sx=width-1-x if horizontal else x; sy=height-1-y if vertical else y
            out[(y*width+x)*4:(y*width+x+1)*4]=pixels[(sy*width+sx)*4:(sy*width+sx+1)*4]
    return bytes(out)


def minitile(descriptor, base_block, chunks, palettes, chunk_modes=None):
    """Decode one native 8x8 4bpp tile, including palette and local flips."""
    tile=descriptor&0x3FF
    chunk=base_block*8+tile//64
    if chunk not in chunks: raise PatchError(f'Missing graphics chunk {chunk}; inherited resources unsupported')
    if chunk_modes is not None and chunk_modes.get(chunk)!=4:
        raise PatchError(f'Character chunk {chunk} is not compatible 4bpp data; 8bpp terrain rendering remains unsupported')
    bank=descriptor>>12
    if bank not in palettes: raise PatchError(f'Missing palette bank {bank}')
    start=(tile%64)*32; packed=chunks[chunk][start:start+32]
    if len(packed)!=32: raise PatchError('Truncated character chunk')
    colors=palettes[bank];pixels=bytearray()
    for value in packed:
        for index in (value&15,value>>4): pixels.extend(rgb555(colors[index],index==0))
    return transform(pixels,8,8,bool(descriptor&0x400),bool(descriptor&0x800))


def blit(out, width, tile, x, y, size):
    for row in range(size):
        start=((y+row)*width+x)*4
        out[start:start+size*4]=tile[row*size*4:(row+1)*size*4]


def render_layer(rom, sector, index, layer=0):
    """Return {width,height,rgba,atlas_width,atlas_height,atlas_rgba,report}.

    Images are native-size, straight-alpha RGBA. Layer zero's implicit blank
    metatile is transparent regardless of character zero's contents. No actor,
    parallax, blend, animation, backdrop or multi-layer compositing is implied.
    """
    bundle=inspect_geometry(rom,sector,index,layer,full=True)
    m=metadata(rom,room_address(rom,sector,index))
    chunks,gfx=read_graphics(rom,m[4]);palettes,pals=read_palettes(rom,m[5]);modes=graphics_chunk_modes(gfx)
    base=(bundle['bg_control']>>2)&3
    visual=bytes.fromhex(bundle['visual_resource']['data_hex'])
    tiles=[bytes(32*32*4)]
    # Render only referenced metatiles: unused native definitions may refer to
    # character memory deliberately not loaded by this room. Atlas holes remain
    # transparent and its report explicitly lists rendered IDs.
    referenced=sorted({v&0x3FFF for v in bundle['cells']})
    cache={0:tiles[0]}
    for tile_id in referenced:
        if tile_id==0: continue
        descriptors=struct.unpack('<16H',visual[(tile_id-1)*32:tile_id*32])
        out=bytearray(32*32*4)
        for n,descriptor in enumerate(descriptors): blit(out,32,minitile(descriptor,base,chunks,palettes,modes),(n%4)*8,(n//4)*8,8)
        cache[tile_id]=bytes(out)
    width=bundle['width_cells']*32;height=bundle['height_cells']*32
    out=bytearray(width*height*4)
    for n,cell in enumerate(bundle['cells']):
        tile=transform(cache[cell&0x3FFF],32,32,bool(cell&0x4000),bool(cell&0x8000))
        blit(out,width,tile,(n%bundle['width_cells'])*32,(n//bundle['width_cells'])*32,32)
    aw=16*32;ah=((bundle['metatiles_including_blank']+15)//16)*32
    atlas=bytearray(aw*ah*4)
    for tile_id,tile in cache.items(): blit(atlas,aw,tile,(tile_id%16)*32,(tile_id//16)*32,32)
    report={k:v for k,v in bundle.items() if k not in ('cells','layer_list_hex','layer_metadata_hex','visual_resource','collision_resource')}
    report.update({'graphics':gfx,'palettes':pals,'base_block':base,'rendered_metatile_ids':referenced,
                   'rgba_sha256':hashlib.sha256(out).hexdigest(),'color_effects':(m[8]>>16)&65535,
                   'scope':'static selected type-2 layer; referenced-metatile atlas; no runtime effects or layer composition'})
    return {'width':width,'height':height,'rgba':bytes(out),'atlas_width':aw,'atlas_height':ah,'atlas_rgba':bytes(atlas),'report':report}


def png_rgba(width,height,pixels):
    """Dependency-free PNG encoding; no source image decoding or execution."""
    if not 1<=width<=4096 or not 1<=height<=4096 or len(pixels)!=width*height*4:
        raise PatchError('Invalid PNG dimensions or RGBA byte count')
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xFFFFFFFF)
    raw=b''.join(b'\0'+pixels[y*width*4:(y+1)*width*4] for y in range(height))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
