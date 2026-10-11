"""Build the original multi-feature callback and checked ROM/RAM claims."""
import hashlib,json,struct
from pathlib import Path
from .core import PatchError,number
from .compiler import ensure_callback
from .hooks import install_frame_hook
ROOT=Path(__file__).resolve().parents[1]
BUILTINS={'still_regen':{'interval':(1,36000,120),'amount':(1,999,1)},'focus_heal':{'amount':(1,999,5),'mana_cost':(1,999,3),'cooldown':(1,36000,180)}}

def plan_abilities(spec,profile):
    if not isinstance(spec,dict) or set(spec)-{'features','runtime','ram_claims'}:raise PatchError('Unknown abilities properties')
    if not isinstance(spec.get('features'),list) or not spec['features']:raise PatchError('abilities requires a nonempty feature list')
    selected={}
    for feature in spec['features']:
        if not isinstance(feature,dict):raise PatchError('Ability feature must be an object')
        name=feature.get('id')
        if name not in BUILTINS or name in selected:raise PatchError('Unknown/duplicate ability feature')
        fields=BUILTINS[name]
        if set(feature)-({'id'}|set(fields)):raise PatchError('Unknown ability parameters')
        values={}
        for field,(low,high,default) in fields.items():
            value=number(feature.get(field,default))
            if not low<=value<=high:raise PatchError('Ability parameter out of range: '+field)
            values[field]=value
        selected[name]=values
    arena=profile['ability_runtime'];start,end=number(arena['ram_start']),number(arena['ram_end'])
    if (number(arena['config_address']),arena['config_size'],arena['abi_version'],start,end)!=(0x0867F000,40,1,0x0203D000,0x0203D400):raise PatchError('Ability profile differs from compiled SDK ABI')
    claims=[{'id':'dispatcher','start':start,'size':64},{'id':'still_regen','start':start+64,'size':16},{'id':'focus_heal','start':start+80,'size':16}]
    extra=spec.get('ram_claims',[])
    if not isinstance(extra,list):raise PatchError('ram_claims must be a list')
    for claim in extra:
        if not isinstance(claim,dict) or set(claim)!={'id','start','size'}:raise PatchError('RAM claim needs id/start/size')
        name=claim['id'];address,size=number(claim['start']),number(claim['size'])
        if not isinstance(name,str) or not name or any(c['id']==name for c in claims):raise PatchError('Duplicate/invalid RAM claim name')
        if size<=0 or address%4 or size%4 or address<start or address+size>end:raise PatchError('RAM claim outside arena or unaligned')
        if any(address<c['start']+c['size'] and c['start']<address+size for c in claims):raise PatchError('Overlapping ability RAM claims')
        claims.append({'id':name,'start':address,'size':size})
    regen=selected.get('still_regen',{'interval':120,'amount':1});focus=selected.get('focus_heal',{'amount':5,'mana_cost':3,'cooldown':180})
    mask=(1 if 'still_regen' in selected else 0)|(2 if 'focus_heal' in selected else 0)
    words=[0x444D4346,1,mask,0,regen['interval'],regen['amount'],256,focus['amount'],focus['mana_cost'],focus['cooldown']]
    tag=int.from_bytes(hashlib.sha256(struct.pack('<10I',*words)).digest()[:4],'little');words[3]=tag
    return struct.pack('<10I',*words),{'abi':1,'features':selected,'ram_claims':claims,'config_tag':hex(tag),'input':'focus_heal uses native R; input is not consumed','persistence':'transient, no SRAM extension'}

def install_abilities(rom,spec,manifest_folder,compile_requested=False):
    payload,report=plan_abilities(spec,rom.profile)
    folder=ROOT/'native/abilities'
    if 'runtime' in spec:
        folder=(Path(manifest_folder)/spec['runtime']).resolve()
        if not folder.is_relative_to(Path(manifest_folder).resolve()):raise PatchError('Custom ability runtime must stay in manifest folder')
    build=json.loads((folder/'build.json').read_text())
    if not {'file','source','linker','fingerprint','dependencies'}<=set(build):raise PatchError('Ability runtime build.json must declare source, linker, binary, fingerprint and dependencies')
    if not {'dominance.h','features.h','build.json'}<=set(build['dependencies']):raise PatchError('Ability runtime must fingerprint its SDK headers and build descriptor')
    if build.get('linked_address')!='0x08680000':raise PatchError('Ability SDK requires fixed callback origin')
    ensure_callback(folder,build,compile_requested)
    binary=(folder/build['file']).resolve()
    if not binary.is_relative_to(folder.resolve()):raise PatchError('Ability binary outside runtime folder')
    install_frame_hook(rom,binary.read_bytes(),build['linked_address'])
    address=number(rom.profile['ability_runtime']['config_address'])
    off=rom.offset(address,len(payload));rom.write(address,payload,'ability-config',rom.original[off:off+len(payload)])
    report['config_address']=hex(address);report['runtime_sha256']=hashlib.sha256(binary.read_bytes()).hexdigest()
    return report
