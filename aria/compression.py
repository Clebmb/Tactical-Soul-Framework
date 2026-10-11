"""Bounded GBA LZ10 decoding and Aria's preserved four-byte inner header.

Independent implementation from documented LZ10 format and local DSVEdit
format evidence. No compression guessing or unbounded output allocation.
"""
import struct
from .core import PatchError
from .content import lz77

def decode_lz10(data, max_output=0x20000):
    if len(data)<4 or data[0]!=0x10:
        raise PatchError("Expected GBA LZ10 header")
    size=int.from_bytes(data[1:4],"little")
    if not 1<=size<=max_output:
        raise PatchError("LZ10 decoded size outside bound")
    out=bytearray();pos=4
    def read():
        nonlocal pos
        if pos>=len(data):raise PatchError("Truncated LZ10 stream")
        value=data[pos];pos+=1;return value
    while len(out)<size:
        flags=read()
        for bit in range(7,-1,-1):
            if len(out)==size:break
            if flags&(1<<bit):
                a,b=read(),read();length=(a>>4)+3;distance=((a&15)<<8|b)+1
                if distance>len(out) or len(out)+length>size:
                    raise PatchError("Invalid LZ10 backreference")
                for _ in range(length):out.append(out[-distance])
            else:out.append(read())
    return bytes(out),pos

def read_aria(rom,address):
    start=rom.offset(address,4)
    data=rom.read(address,min(0x25000,len(rom.data)-start))
    expanded,consumed=decode_lz10(data)
    if len(expanded)<4:raise PatchError("Missing Aria inner header")
    header=expanded[:4]
    if int.from_bytes(header,"little")>>8!=len(expanded):
        raise PatchError("Aria inner size disagrees with outer size")
    return {"encoding":"aria-lz10","data_hex":expanded[4:].hex(),
            "inner_header_hex":header.hex(),"compressed_hex":data[:consumed].hex(),
            "compressed_bytes":consumed}

def rebuild_aria(resource, preserve=True):
    data=bytes.fromhex(resource["data_hex"]);header=bytes.fromhex(resource["inner_header_hex"])
    if len(header)!=4 or int.from_bytes(header,"little")>>8!=len(data)+4:
        raise PatchError("Invalid Aria inner header size")
    expanded=header+data
    if preserve:
        stream=bytes.fromhex(resource["compressed_hex"])
        decoded,n=decode_lz10(stream)
        if decoded!=expanded or n!=len(stream):raise PatchError("Saved compressed stream does not match decoded resource")
        return stream
    return lz77(expanded)
