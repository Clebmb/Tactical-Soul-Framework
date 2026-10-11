"""Authored type-2 metatile definitions; bounded ordinary empty/solid collision.

These define new 32px arrangements of existing loaded 8px characters. They do
not import graphics or allocate VRAM. Native collision bytes 0 and 3 only.
"""
import struct
from .core import PatchError
from .content import integer,lz77


def encode_definitions(definitions, first_id):
    if not isinstance(definitions,list) or not 1<=len(definitions)<=32:
        raise PatchError('Custom metatiles require 1..32 definitions')
    if first_id+len(definitions)>512:raise PatchError('Custom metatile count exceeds 512')
    visual=bytearray();collision=bytearray();descriptors=[]
    for offset,row in enumerate(definitions):
        if not isinstance(row,dict) or set(row)!={'id','minitiles','collision'}:
            raise PatchError('Custom metatile requires id,minitiles,collision')
        if integer(row['id'],1,511)!=first_id+offset:
            raise PatchError('Custom metatile IDs must append contiguously')
        if not isinstance(row['minitiles'],list) or len(row['minitiles'])!=16:
            raise PatchError('Custom metatile requires sixteen u16 minitiles')
        if not isinstance(row['collision'],list) or len(row['collision'])!=16:
            raise PatchError('Custom metatile requires sixteen collision bytes')
        values=[integer(v,0,65535) for v in row['minitiles']]
        kinds=[integer(v,0,3) for v in row['collision']]
        if any(v not in (0,3) for v in kinds):raise PatchError('Only empty (0) and full solid (3) collision supported')
        visual.extend(struct.pack('<16H',*values));collision.extend(kinds);descriptors.extend(values)
    return bytes(visual),bytes(collision),descriptors


def extend_resource(resource, suffix):
    """Rebuild an isolated Aria stream, preserving original inner flag byte."""
    data=bytes.fromhex(resource['data_hex'])+suffix
    header=bytes.fromhex(resource['inner_header_hex'])
    return lz77(bytes([header[0]])+(len(data)+4).to_bytes(3,'little')+data)
