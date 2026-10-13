"""Read-only candidate attribution; matching pointers alone do not prove use."""
import struct

def match_song_headers(memory, memory_base, catalog):
    """Match aligned little-endian words against explicit song header identities.

    Catalog entries are (identity, ROM header address); aliases remain separate.
    No RAM layout, active-player status, or song semantics are inferred.
    """
    if not isinstance(memory,bytes) or len(memory)>0x100000 or len(memory)%4:
        raise ValueError('memory must be aligned immutable bytes, at most 1 MiB')
    if type(memory_base) is not int or not 0<=memory_base<=0xffffffff or memory_base%4 or memory_base+len(memory)>0x100000000:
        raise ValueError('invalid aligned memory base/range')
    if not isinstance(catalog,(list,tuple)) or len(catalog)>4096:
        raise ValueError('catalog must contain at most 4096 entries')
    pointers={}
    for item in catalog:
        if not isinstance(item,(list,tuple)) or len(item)!=2:
            raise ValueError('catalog requires identity/address pairs')
        identity,address=item
        if not isinstance(identity,str) or not identity or type(address) is not int or not 0<address<=0xffffffff or address%4:
            raise ValueError('invalid song identity/header address')
        pointers.setdefault(address,[]).append(identity)
    result=[]
    for offset in range(0,len(memory),4):
        pointer=struct.unpack_from('<I',memory,offset)[0]
        for identity in pointers.get(pointer,()):
            if len(result)>=20000:raise ValueError('header match budget exceeds 20000 results')
            result.append({'identity':identity,'header':pointer,'memory_address':memory_base+offset})
    return tuple(result)
