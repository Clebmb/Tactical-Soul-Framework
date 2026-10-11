"""Static registered AoS sprite previews, without GUI/Pillow or ROM writes.

AoS sprite pages use packed 8x8 indexed tiles arranged on a 128-pixel-wide
source canvas. See docs/SPRITES.md for provenance and boundaries.
"""
import hashlib
import struct
from .core import PatchError
from .compression import read_aria
from .rendering import rgb555
from .sprites import SPRITES, inspect_sprite

SPRITE_RESOURCES = {
    'common': {'pages': [0x081C15F4], 'palette': 0x082099FC, 'bank': 3},
    'julius': {'pages': [0x081F42A4,0x081F52A8,0x081F62AC,0x081F72B0], 'palette': 0x0820C028, 'bank': 0},
    'background-bats': {'pages': [0x081CBE5C], 'palette': 0x08209EE8, 'bank': 0},
    # Raw 4KB page plus single-bank palette from the unidentified actor
    # entry; consumer unknown, see docs/ENEMY-BINDING.md.
    'unknown-actor': {'pages': [0x082052F8], 'palette': 0x0820C550, 'bank': 0},
    # LZ page plus single-bank palette for the second unidentified struct.
    # Static pools only (Arachne create plus two helpers); live consumer
    # unproven, and this palette is NOT the live walker bank-0 palette
    # (0x0820B168, see ENEMY-BINDING.md). Never describe as zombie artwork.
    'unknown-actor-2': {'pages': [0x081CBF84], 'palette': 0x0820A608, 'bank': 0},
}

def read_sprite_page(rom, address):
    """Read a raw/Aria-LZ 4bpp page; reject missing/oversized/partial rows.

    Returns (indexed bytes, provenance). Raw data is wrapper+4; compressed
    wrapper+4 is a pointer and read_aria strips the validated inner header.
    No zero padding or placeholder artwork is introduced.
    """
    if address % 4: raise PatchError('Unaligned sprite graphics wrapper')
    kind,bpp,reserved,chunks = rom.read(address,4)
    if kind not in (0,1) or bpp != 4:
        raise PatchError('Sprite preview requires raw/LZ 4bpp graphics')
    source = rom.integer(address+4) if kind else address+4
    if kind:
        data=bytes.fromhex(read_aria(rom,source)['data_hex'])
    else:
        if not 1 <= chunks <= 16: raise PatchError('Sprite page size outside 8KB budget')
        data=rom.read(source,chunks*512)
    if not 512 <= len(data) <= 8192 or len(data)%512:
        raise PatchError('Sprite graphics must contain complete 128-pixel tile rows within 8KB')
    return data,dict(wrapper_address=address,data_address=source,encoding='aria-lz10' if kind else 'raw',
                     bpp=bpp,reserved=reserved,header_chunks=chunks,width=128,height=len(data)//64,
                     byte_count=len(data),data_sha256=hashlib.sha256(data).hexdigest())

def resolve_sprite_resources(rom, name, palette_bank=None):
    """Resolve explicit registrations, not arbitrary native resource discovery.

    palette_bank selects a source bank (common users have differing palettes),
    not a runtime OBJ palette allocation. Returned byte payloads stay private.
    """
    if name not in SPRITE_RESOURCES: raise PatchError('Unregistered sprite resources')
    registration=SPRITE_RESOURCES[name]
    bank=registration['bank'] if palette_bank is None else palette_bank
    pointer=registration['palette']
    zero,mode,rows,end=rom.read(pointer,4)
    if zero or mode!=4 or end or not 1<=rows<=16:
        raise PatchError('Unsupported sprite palette header')
    if isinstance(bank,bool) or not isinstance(bank,int) or not 0<=bank<rows:
        raise PatchError('Sprite source palette bank out of range')
    raw=rom.read(pointer+4+bank*32,32)
    pages=[];records=[]
    for address in registration['pages']:
        data,record=read_sprite_page(rom,address);pages.append(data);records.append(record)
    return dict(pages=pages,palette=list(struct.unpack('<16H',raw)),
                provenance=dict(pages=records,palette=dict(wrapper_address=pointer,bank=bank,bank_count=rows,
                    data_address=pointer+4+bank*32,data_sha256=hashlib.sha256(raw).hexdigest())))

def render_sprite_frame(frame, resources):
    """Return tightly bounded RGBA, dimensions and original signed frame origin.

    Earlier part records are drawn last. Zero palette indices are transparent;
    H/V flips operate on the entire part. Source x/y snap down to eight pixels.
    Unsupported flags, shape mismatch, missing pages and crop overflow fail.
    Hitboxes are returned separately by inspect_sprite, not painted as artwork.
    """
    parts=frame['parts'];pages=resources['pages'];palette=resources['palette']
    if len(parts)>128 or len(pages)>16 or len(palette)!=16:
        raise PatchError('Sprite preview resource budget exceeded')
    if not parts:return dict(width=1,height=1,origin=[0,0],pixels=bytes(4),part_count=0)
    for part in parts:
        if part['object_dimensions'] != [part['width'],part['height']] or part['width']<=0 or part['height']<=0:
            raise PatchError('Sprite part dimensions disagree with supported OBJ shape')
        if part['flip_bits'] & ~3: raise PatchError('Unsupported sprite flip flags')
    left=min(p['x'] for p in parts);top=min(p['y'] for p in parts)
    width=max(p['x']+p['width'] for p in parts)-left
    height=max(p['y']+p['height'] for p in parts)-top
    if not 1<=width<=512 or not 1<=height<=512: raise PatchError('Sprite frame canvas exceeds budget')
    pixels=bytearray(width*height*4)
    colors=[rgb555(value,transparent=(i==0)) for i,value in enumerate(palette)]
    for part in reversed(parts):
        page=part['gfx_page']
        if not 0<=page<len(pages): raise PatchError('Sprite part references missing graphics page')
        data=pages[page]
        if not 512<=len(data)<=8192 or len(data)%512: raise PatchError('Invalid sprite page rows')
        sx=(part['gfx_x']//8)*8;sy=(part['gfx_y']//8)*8
        w,h=part['width'],part['height']
        if sx<0 or sy<0 or sx+w>128 or sy+h>len(data)//64:
            raise PatchError('Sprite part crop exceeds graphics payload')
        for y in range(h):
            for x in range(w):
                source_x=sx+(w-1-x if part['flip_bits']&2 else x)
                source_y=sy+(h-1-y if part['flip_bits']&1 else y)
                tile=(source_y//8)*16+source_x//8
                offset=tile*32+(source_y%8)*4+(source_x%8)//2
                packed=data[offset]
                index=(packed >> (4*(source_x%2)))&15
                if not index:continue
                target=((part['y']-top+y)*width+part['x']-left+x)*4
                pixels[target:target+4]=colors[index]
    return dict(width=width,height=height,origin=[left,top],pixels=bytes(pixels),part_count=len(parts))

def preview_sprite(rom, name, frame_index=0, palette_bank=None):
    """Return render payload plus JSON-safe evidence for one registered frame."""
    if name not in SPRITES: raise PatchError('Unregistered sprite')
    sprite=inspect_sprite(rom,SPRITES[name])
    if isinstance(frame_index,bool) or not isinstance(frame_index,int) or not 0<=frame_index<sprite['frame_count']:
        raise PatchError('Sprite frame index out of range')
    resources=resolve_sprite_resources(rom,name,palette_bank)
    rendered=render_sprite_frame(sprite['frames'][frame_index],resources)
    report=dict(schema_version=1,sprite=name,frame_index=frame_index,frame_count=sprite['frame_count'],
                width=rendered['width'],height=rendered['height'],origin=rendered['origin'],
                part_count=rendered['part_count'],rgba_sha256=hashlib.sha256(rendered['pixels']).hexdigest(),
                resources=resources['provenance'],status='static_source_preview',
                limitations=['Not native OAM/effects/animation dispatch evidence','No actor graphics writes or VRAM allocation'])
    return dict(**rendered,report=report)
