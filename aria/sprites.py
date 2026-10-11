"""Bounded read-only AoS sprite structure inspection. See docs/SPRITES.md.

This parses source records, not runtime player animation or OAM ownership.
Unknown animation functions produce local diagnostics rather than guessed data.
"""
import struct
from .core import PatchError

SPRITES = {
    'common': 0x0820ED60,
    'julius': 0x08252748,
    'background-bats': 0x0820FE44,
    # Unidentified actor-table struct: 21 frames/9 animations, valid roundtrip.
    # Magenta-tracer evidence disproves hallway zombie/walker/mound/death use;
    # the consumer is unknown. See docs/ENEMY-BINDING.md. Never describe this
    # as zombie artwork.
    'unknown-actor': 0x0825847C,
    # Second unidentified struct: 35 frames/10 animations, valid roundtrip.
    # Static code pools in Arachne create (enemy 23) plus two helper functions
    # reference this struct and its page/palette, but no live consumer is
    # proven: magenta-tracer evidence disproves hallway zombie/walker use of
    # the page, and the live walker palette differs. See
    # docs/ENEMY-BINDING.md. Never describe this as zombie artwork.
    'unknown-actor-2': 0x08217464,
}

def inspect_sprite(rom, pointer):
    """Return JSON-safe frames, parts, hitboxes and animation steps without writes.

    Limits are engineering budgets, not native format maxima. Pointers must be
    aligned for their record type. Null animation entries and aliases survive.
    Every decoded fixed record is repacked and compared with its input bytes.
    """
    records = 0
    def record(address, fmt, alignment=4):
        nonlocal records
        if address % alignment: raise PatchError('Unaligned sprite record')
        records += 1
        if records > 32768: raise PatchError('Sprite record budget exceeded')
        raw = rom.read(address, struct.calcsize(fmt))
        values = struct.unpack(fmt, raw)
        if struct.pack(fmt, *values) != raw: raise PatchError('Sprite roundtrip failed')
        return values
    count, animation_count, frame_list, first_animation, animation_list = record(pointer, '<HHIII')
    if not 1 <= count <= 1024 or animation_count > 256:
        raise PatchError('Sprite frame/animation count exceeds budget')
    frames = []
    diagnostics = []
    for i in range(count):
        unknown, nh, np, unknown16, hp, pp = record(frame_list+i*16, '<IBBHII')
        if np > 128 or nh > 128: raise PatchError('Sprite frame part/hitbox budget exceeded')
        parts = []
        for j in range(np):
            values = record(pp+j*12, '<bbH8B', 2)
            part = dict(zip(('x','y','unknown16','gfx_x','gfx_y','width','height','shape_size','gfx_page','flip_bits','unused'), values))
            shape = part['shape_size'] & 3; size = (part['shape_size'] >> 4) & 3
            dimensions = (((8,8),(16,16),(32,32),(64,64)),((16,8),(32,8),(32,16),(64,32)),((8,16),(8,32),(16,32),(32,64)))
            part['object_dimensions'] = list(dimensions[shape][size]) if shape < 3 else None
            if part['object_dimensions'] != [part['width'],part['height']]:
                diagnostics.append(f'frame {i} part {j}: dimensions differ from OBJ shape/size')
            parts.append(part)
        hitboxes = [list(record(hp+j*4, '<bbBB', 1)) for j in range(nh)]
        frames.append(dict(index=i,unknown32=unknown,unknown16=unknown16,parts=parts,hitboxes=hitboxes))
    animations = []; seen = {}
    for i in range(animation_count):
        address, = record(animation_list+i*4, '<I')
        entry = dict(index=i,address=address)
        if not address: entry['status']='null'
        elif address in seen: entry.update(status='alias',alias_of=seen[address])
        else:
            seen[address]=i
            steps, function = record(address, '<HH', 2)
            entry.update(function=function,step_count=steps)
            if function not in (1,2,3):
                entry['status']='unsupported_function'
                diagnostics.append(f'animation {i}: unsupported function {function}')
            else:
                if steps > 1024: raise PatchError('Animation step budget exceeded')
                fmt = {1:'<BBH',2:'<HHbbBB',3:'<HHbbBBbbBB'}[function]
                decoded=[]
                for j in range(steps):
                    values=record(address+4+j*struct.calcsize(fmt),fmt,2)
                    if values[0]>=count: raise PatchError('Animation references missing frame')
                    decoded.append(list(values))
                entry.update(status='decoded',steps=decoded)
        animations.append(entry)
    return dict(schema_version=1,address=pointer,frame_count=count,animation_count=animation_count,
                first_animation_pointer=first_animation,frames=frames,animations=animations,
                diagnostics=diagnostics,records_roundtripped=records,read_only=True,
                limitations=['No runtime animation dispatch, graphics loading or sprite writes',
                             'Soma dummy is not the real dynamically loaded player animation'])
