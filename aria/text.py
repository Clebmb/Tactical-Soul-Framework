"""Bounded read-only English labels from immutable original; no dialogue codec."""
from .core import PatchError
POINTERS=0x08506B38
def original_label(rom,text_id):
    offset=rom.offset(POINTERS+4*text_id,4)
    pointer=int.from_bytes(rom.original[offset:offset+4],'little')
    start=rom.offset(pointer,2)
    if rom.original[start:start+2]!=b'\x01\x00':raise PatchError('Unexpected native label header')
    chars=[]
    for b in rom.original[start+2:start+130]:
        if b in (6,10):return ''.join(chars)
        if not 32<=b<=126:raise PatchError('Unsupported character/control in English label')
        chars.append(chr(b))
    raise PatchError('Unterminated native label')
