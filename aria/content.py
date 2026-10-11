"""Original indexed-asset codecs and checked ROM bindings; no external libraries."""
import hashlib,json,re,struct,wave
from pathlib import Path
from .core import PatchError,number

def integer(value,lo,hi):
    if type(value) is not int:raise PatchError("Content numeric fields must be JSON integers")
    if not lo<=value<=hi:raise PatchError(f"Content value outside {lo}..{hi}")
    return value

def local(folder,name):
    p=(folder/name).resolve()
    if not p.is_relative_to(folder.resolve()):raise PatchError("Content source escapes manifest folder")
    return p

def palette(colors):
    if not isinstance(colors,list) or not 1<=len(colors)<=256:raise PatchError("Palette requires 1..256 RGB colors")
    out=bytearray()
    for c in colors:
        if not isinstance(c,list) or len(c)!=3:raise PatchError("Colors must be [R,G,B]")
        r,g,b=[integer(v,0,255) for v in c]
        out+=struct.pack('<H',(r>>3)|((g>>3)<<5)|((b>>3)<<10))
    return bytes(out)

def tiles(spec):
    if not isinstance(spec,dict):raise PatchError("Tile source must be an object")
    if set(spec)!={'width','height','pixels'}:raise PatchError("Tiles require width,height,pixels only")
    w=integer(spec['width'],8,1024);h=integer(spec['height'],8,1024)
    if not isinstance(spec['pixels'],list) or w%8 or h%8 or len(spec['pixels'])!=w*h:raise PatchError("Tiles require 8-pixel dimensions and exact row-major pixel count")
    pixels=[integer(v,0,15) for v in spec['pixels']];out=bytearray()
    for ty in range(0,h,8):
        for tx in range(0,w,8):
            for y in range(8):
                for x in range(0,8,2):
                    i=(ty+y)*w+tx+x;out.append(pixels[i]|pixels[i+1]<<4)
    return bytes(out)

def lz77(data):
    if not 0<len(data)<=0xFFFFFF:raise PatchError("LZ77 payload size invalid")
    out=bytearray(struct.pack('<I',len(data)<<8|0x10))
    for i in range(0,len(data),8):out.append(0);out+=data[i:i+8]
    out+=bytes(-len(out)%4);return bytes(out)

def encode(kind,path):
    if kind=='palette_rgb8':return palette(json.loads(path.read_text()))
    if kind=='tiles4':return tiles(json.loads(path.read_text()))
    if kind=='pcm_s8':
        with wave.open(str(path),'rb') as w:
            if w.getnchannels()!=1 or w.getsampwidth()!=1 or w.getcomptype()!='NONE':raise PatchError("PCM input must be uncompressed mono unsigned 8-bit WAV")
            if not 4000<=w.getframerate()<=32768:raise PatchError("PCM rate outside 4000..32768 Hz")
            data=w.readframes(w.getnframes())
            if not data or len(data)>32768:raise PatchError("PCM requires 1..32768 samples")
            return bytes(v^128 for v in data)
    raise PatchError("Unknown content format: "+str(kind))

def install_content(rom,spec,folder):
    if not isinstance(spec,list) or not spec:raise PatchError("content must be a nonempty list")
    report=[];ids=set()
    for asset in spec:
        if not isinstance(asset,dict):raise PatchError('Each content entry must be an object')
        allowed={'id','format','source','provenance','encoding','replace','pointers','target'}
        if set(asset)-allowed or not {'id','format','source','provenance'}<=set(asset):raise PatchError("Unknown/missing content properties")
        name=asset['id']
        if not isinstance(name,str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}',name) or name in ids:raise PatchError("Content IDs must be unique safe names")
        ids.add(name)
        if not isinstance(asset['provenance'],str) or not asset['provenance'].strip():raise PatchError("Content requires provenance")
        path=local(folder,asset['source']);payload=encode(asset['format'],path)
        encoding=asset.get('encoding','raw')
        if encoding=='lz77':payload=lz77(payload)
        elif encoding!='raw':raise PatchError("Content encoding must be raw or lz77")
        if 'target' in asset:
            if 'replace' in asset or 'pointers' in asset:raise PatchError('Named target cannot combine with manual bindings')
            from .resources import replace_named
            address=replace_named(rom,asset['target'],asset['format'],encoding,payload,'content:'+name);mode='named_replace'
        elif 'replace' in asset:
            if asset.get('pointers'):raise PatchError("Choose same-size replace or allocated pointer bindings")
            bind=asset['replace']
            if set(bind)!={'address','size','expected_sha256'} or number(bind['size'])!=len(payload):raise PatchError("Replacement must declare exact encoded size")
            address=number(bind['address']);before=rom.read(address,len(payload))
            if hashlib.sha256(before).hexdigest()!=bind['expected_sha256']:raise PatchError("Content replacement preimage mismatch")
            rom.write(address,payload,'content:'+name,before);mode='replace'
        else:
            address=rom.allocate('content:'+name,payload,4);mode='allocated'
            for bind in asset.get('pointers',[]):
                if set(bind)!={'address','expected'}:raise PatchError("Pointer binding requires address and expected native pointer")
                rom.write_integer(bind['address'],address,4,'content-pointer:'+name,number(bind['expected']).to_bytes(4,'little'))
        row={'id':name,'format':asset['format'],'encoding':encoding,'address':address,'size':len(payload),'sha256':hashlib.sha256(payload).hexdigest(),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'provenance':asset['provenance'],'mode':mode,'pointer_count':len(asset.get('pointers',[]))}
        if asset['format']=='pcm_s8':
            with wave.open(str(path),'rb') as w:row['sample_rate']=w.getframerate();row['samples']=w.getnframes()
        if 'target' in asset:row['target']=asset['target']
        report.append(row)
    return report
