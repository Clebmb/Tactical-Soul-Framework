"""Narrow source-palette recolors with snapshot-anchored native bindings.

These resources are globally shared. No allocation, sprite replacement, OAM
claims or arbitrary palette addresses. See docs/CUSTOM-ROOM.md for evidence.
"""
import hashlib,struct
from .core import PatchError

TARGETS={
 'save-statue':(0x0820C3A8,'b66f68faec0767d21b407a910a93ffd3f8dade3dd3313430cf8e68920e45b957'),
 'save-flame':(0x0820C3C8,'3d04b7ddc8ad031e680a0b253b5bfb9e35142fcf08951d459926d78211bcb072'),
 'save-particles':(0x0820C3E8,'cd155b9335bbafb27142bf36ab9a90623190e0af4681d945baaf74a069d6abcd'),
 'zombie':(0x0820A630,'64d52fd7ca464bcbd9ccd658757b3e353e2212a5c0efc4ce2c94813a0b01ecda')}


def blood_palette(data):
    colors=list(struct.unpack('<16H',data))
    for i,value in enumerate(colors[1:],1):
        r,g,b=value&31,(value>>5)&31,(value>>10)&31
        light=(r*3+g*6+b)//10
        colors[i]=max(2,light) | (light//6)<<5 | (light//7)<<10
    return struct.pack('<16H',*colors)


def install_palette_tints(rom,entries):
    if not isinstance(entries,list) or not entries:
        raise PatchError('palette_tints requires a nonempty list')
    planned=[];seen=set()
    for entry in entries:
        if not isinstance(entry,dict) or set(entry)!={'target','style','scope'}:
            raise PatchError('Palette tint requires target,style,scope')
        target=entry['target']
        if not isinstance(target,str) or target not in TARGETS or target in seen:
            raise PatchError('Unknown or duplicate palette tint target')
        if entry['style']!='blood' or entry['scope']!='shared-native-palette':
            raise PatchError('Tint requires blood style and explicit shared-native-palette scope')
        seen.add(target);address,digest=TARGETS[target];old=rom.read(address,32)
        if hashlib.sha256(old).hexdigest()!=digest:
            raise PatchError('Palette tint source preimage mismatch: '+target)
        planned.append((target,address,old,blood_palette(old)))
    for target,address,old,new in planned:
        rom.write(address,new,'palette-tint:'+target,old)
    return [{'target':t,'address':hex(a),'style':'blood','scope':'shared-native-palette'} for t,a,_,_ in planned]
